#!/usr/bin/env bash
#
# unused-imports.sh - lists imports in changed Kotlin, Java and TypeScript files
# whose symbol appears nowhere else in the file.
#
# Candidates, not verdicts. A Kotlin extension function, an operator overload or
# a TypeScript decorator is used without its name showing up, so every hit needs
# a check before the line goes. Side-effect imports (`import './styles.css'`)
# and wildcard imports are skipped outright.
#
# Usage: unused-imports.sh [repo-dir]   (defaults to the current directory)
#

set -uo pipefail

CWD="${1:-${PWD}}"
git -C "${CWD}" rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

FILES="$( { git -C "${CWD}" diff --cached --name-only --diff-filter=ACM
            git -C "${CWD}" diff --name-only --diff-filter=ACM
            git -C "${CWD}" ls-files --others --exclude-standard
          } 2>/dev/null | sort -u | grep -E '\.(kt|java|ts|tsx)$')"
[ -n "${FILES}" ] || exit 0

scan() {
  awk -v path="$2" '
    { line[NR] = $0 }

    function used(sym,   pattern) {
      pattern = "(^|[^A-Za-z0-9_$])" sym "($|[^A-Za-z0-9_$])"
      return body ~ pattern
    }

    function report(num, stmt, sym) {
      if (sym != "" && !used(sym)) printf "%s:%d  %s  (%s)\n", path, num, stmt, sym
    }

    END {
      isTs = (path ~ /\.tsx?$/)

      # join multi-line TypeScript imports onto their opening line
      for (i = 1; i <= NR; i++) {
        stmt = line[i]
        start = i
        if (stmt !~ /^[ \t]*import[ \t({*"'"'"']/) { rest = rest "\n" line[i]; continue }
        while (isTs && stmt !~ /from|;[ \t]*$/ && i < NR) {
          i++
          gsub(/^[ \t]+/, "", line[i])
          stmt = stmt " " line[i]
        }
        imports[start] = stmt
      }
      body = rest

      for (num in imports) {
        stmt = imports[num]
        gsub(/^[ \t]+|[ \t]+$/, "", stmt)

        if (!isTs) {
          if (stmt ~ /\*[ \t]*;?[ \t]*$/) continue           # wildcard
          sym = stmt
          sub(/;[ \t]*$/, "", sym)
          if (sym ~ / as /) { sub(/^.* as[ \t]+/, "", sym) }
          else { sub(/^.*[.]/, "", sym) }
          report(num, stmt, sym)
          continue
        }

        if (stmt ~ /^import[ \t]*["'"'"']/) continue          # side effect only
        clause = stmt
        sub(/[ \t]+from[ \t]+.*$/, "", clause)
        sub(/^import[ \t]+/, "", clause)
        sub(/^type[ \t]+/, "", clause)

        if (clause ~ /\*[ \t]+as[ \t]+/) {
          sym = clause
          sub(/^.*as[ \t]+/, "", sym)
          gsub(/[ \t;]/, "", sym)
          report(num, stmt, sym)
          continue
        }

        named = clause
        if (named ~ /[{]/) { sub(/^[^{]*[{]/, "", named); sub(/[}].*$/, "", named) }
        else { named = "" }

        defaultSym = clause
        sub(/[{].*$/, "", defaultSym)
        gsub(/[ \t,;]/, "", defaultSym)
        if (defaultSym != "") report(num, stmt, defaultSym)

        n = split(named, parts, ",")
        for (j = 1; j <= n; j++) {
          sym = parts[j]
          sub(/^[ \t]*type[ \t]+/, "", sym)
          if (sym ~ / as /) sub(/^.* as[ \t]+/, "", sym)
          gsub(/[ \t]/, "", sym)
          if (sym != "") report(num, stmt, sym)
        }
      }
    }
  ' "$1"
}

while IFS= read -r f; do
  [ -f "${CWD}/${f}" ] && scan "${CWD}/${f}" "${f}"
done <<<"${FILES}"

exit 0
