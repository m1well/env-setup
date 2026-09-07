#!/usr/bin/env bash
#
# session-review.sh - makes Claude review its own changes before it calls a task done.
#
# Modes (the hook event decides which one runs):
#   baseline  UserPromptSubmit - remembers the working tree as the task starts
#   check     Stop             - if the tree moved since then, blocks the stop once
#                               and asks for a cleanup pass plus the docs question
#
# Fires at most once per prompt and only inside a git work tree that actually
# changed, so plain questions and read-only turns end normally.
#
# Turns smaller than CLAUDE_SESSION_REVIEW_MIN added lines (15 by default) pass
# through untouched - there is nothing to tidy in a three line fix.
#
# CLAUDE_SESSION_REVIEW env var: on (default) | off
#

set -uo pipefail

MODE="${1:-check}"
[ "${CLAUDE_SESSION_REVIEW:-on}" = "off" ] && exit 0

MIN_LINES="${CLAUDE_SESSION_REVIEW_MIN:-15}"
STATE_DIR="${TMPDIR:-/tmp}/claude-session-review"
PAYLOAD="$(cat)"
SESSION="$(jq -r '.session_id // "unknown"' <<<"${PAYLOAD}" 2>/dev/null)" || exit 0
PROMPT="$(jq -r '.prompt_id // "none"' <<<"${PAYLOAD}" 2>/dev/null)"
CWD="$(jq -r '.cwd // empty' <<<"${PAYLOAD}" 2>/dev/null)"
[ -n "${CWD}" ] && [ -d "${CWD}" ] || CWD="${PWD}"

BASELINE="${STATE_DIR}/${SESSION}.baseline"
DONE="${STATE_DIR}/${SESSION}.${PROMPT}.done"

git -C "${CWD}" rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

# path plus mtime and size of everything git considers dirty - survives a repo
# without a HEAD commit and does not move just because the autostage hook ran
treeState() {
  git -C "${CWD}" status --porcelain -uall 2>/dev/null | cut -c4- | sort |
    while IFS= read -r f; do
      meta="$(stat -f '%m:%z' "${CWD}/${f}" 2>/dev/null ||
              stat -c '%Y:%s' "${CWD}/${f}" 2>/dev/null || echo '-')"
      printf '%s|%s\n' "${f}" "${meta}"
    done | shasum | cut -d' ' -f1
}

# added lines only: a diff that deletes 40 lines has already tidied up
addedLines() {
  local base staged untracked=0 f
  # a repo without a first commit has no HEAD to diff against - use the empty tree
  base="HEAD"
  git -C "${CWD}" rev-parse --verify -q HEAD >/dev/null 2>&1 ||
    base="$(git -C "${CWD}" hash-object -t tree /dev/null)"
  staged="$(git -C "${CWD}" diff "${base}" --numstat 2>/dev/null |
            awk '$1 ~ /^[0-9]+$/ {s += $1} END {print s + 0}')"
  while IFS= read -r f; do
    [ -n "${f}" ] || continue
    untracked=$((untracked + $(wc -l <"${CWD}/${f}" 2>/dev/null || echo 0)))
  done <<<"$(git -C "${CWD}" ls-files --others --exclude-standard 2>/dev/null)"
  echo $((staged + untracked))
}

if [ "${MODE}" = "baseline" ]; then
  mkdir -p "${STATE_DIR}"
  { treeState; addedLines; } >"${BASELINE}"
  exit 0
fi

[ -e "${DONE}" ] && exit 0
[ -r "${BASELINE}" ] || exit 0
{ read -r BASE_STATE; read -r BASE_ADDED; } <"${BASELINE}"
BASE_ADDED="${BASE_ADDED:-0}"
[ "$(treeState)" = "${BASE_STATE}" ] && exit 0
# only what this turn added counts, not what the previous one left behind
[ "$(( $(addedLines) - BASE_ADDED ))" -lt "${MIN_LINES}" ] && exit 0

: >"${DONE}"

IMPORTS="$("$(dirname "$0")/unused-imports.sh" "${CWD}" 2>/dev/null)"

cat >&2 <<'MSG'
Not an error. This turn changed files, so the closing check runs once before you finish.

1. Read your own diff: `git diff HEAD`, plus `git status --short` for new files.

2. Clean up what you wrote, behaviour-preserving only:
   - code longer than it needed to be: a helper called once, a variable that only
     forwards a value, a wrapper that adds no behaviour, a needless abstraction
   - leftovers: debug output, commented-out attempts, unused imports or params, dead branches
   - duplication you introduced, or something that already existed and you rebuilt
   - scope creep: changes the task never asked for
   - comments that break the comment rules
   Apply what is safe. Two or three lines on what you cleaned up, and name what you
   left alone on purpose. Nothing to clean? Say "diff is clean" and move on.

3. Docs: unless the task already named the docs to update, do NOT touch any. List the
   concrete files that mention what changed and ask which ones to update. Nothing
   references it? One line saying so.
MSG

if [ -n "${IMPORTS}" ]; then
  {
    printf '\nUnused import candidates in the files you touched, part of step 2. Check each\n'
    printf 'one in the file before you delete it: a Kotlin extension function or operator,\n'
    printf 'a decorator, or a type used only inside a generic is in use without its name\n'
    printf 'showing up here. Delete the dead ones, keep the rest and say which and why.\n\n'
    printf '%s\n' "${IMPORTS}"
  } >&2
fi

exit 2
