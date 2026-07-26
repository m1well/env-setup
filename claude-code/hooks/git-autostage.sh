#!/usr/bin/env bash
#
# git-autostage.sh — stages all working tree changes when Claude finishes a turn.
# Used as a Stop hook; reads the hook payload (JSON) from stdin.
#
# No-op when:
#   - the working directory is not inside a git work tree
#   - a merge / rebase / cherry-pick is in progress (staging would mark
#     conflict markers as resolved)
#   - there is nothing left to stage
#

set -uo pipefail

CWD="$(jq -r '.cwd // empty' 2>/dev/null)"
[ -n "${CWD}" ] && [ -d "${CWD}" ] || CWD="${PWD}"

git -C "${CWD}" rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

GIT_DIR="$(git -C "${CWD}" rev-parse --absolute-git-dir 2>/dev/null)" || exit 0
for MARKER in MERGE_HEAD REBASE_HEAD CHERRY_PICK_HEAD rebase-merge rebase-apply; do
  [ -e "${GIT_DIR}/${MARKER}" ] && exit 0
done

# everything `git add -A` would newly pick up: unstaged tracked + untracked files
PENDING="$( { git -C "${CWD}" diff --name-only
              git -C "${CWD}" ls-files --others --exclude-standard
            } 2>/dev/null | sort -u | wc -l | tr -d ' ')"
[ "${PENDING}" -eq 0 ] && exit 0

git -C "${CWD}" add -A >/dev/null 2>&1 || exit 0

jq -nc --arg msg "git: staged ${PENDING} file(s)" '{systemMessage: $msg}'

exit 0
