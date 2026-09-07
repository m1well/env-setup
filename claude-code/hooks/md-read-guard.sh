#!/usr/bin/env bash
#
# md-read-guard.sh - keeps Claude from reading markdown files on its own initiative.
#
# Modes (the hook event decides which one runs):
#   record  UserPromptSubmit - remembers the prompt text of this session
#   check   PreToolUse:Read  - asks before reading a markdown file the prompt
#                             never mentioned
#
# Always allowed without asking: anything under a .claude directory, SKILL.md,
# CLAUDE.md / CLAUDE.local.md / AGENTS.md, and files whose name shows up in one
# of the last prompts.
#
# CLAUDE_MD_GUARD env var: ask (default) | deny | off
#

set -uo pipefail

MODE="${1:-check}"
GUARD="${CLAUDE_MD_GUARD:-ask}"
[ "${GUARD}" = "off" ] && exit 0

STATE_DIR="${TMPDIR:-/tmp}/claude-md-guard"
PAYLOAD="$(cat)"
SESSION="$(jq -r '.session_id // "unknown"' <<<"${PAYLOAD}" 2>/dev/null)" || exit 0
PROMPTS="${STATE_DIR}/${SESSION}.prompts"

if [ "${MODE}" = "record" ]; then
  mkdir -p "${STATE_DIR}"
  jq -r '.user_input // empty' <<<"${PAYLOAD}" >>"${PROMPTS}" 2>/dev/null
  tail -n 40 "${PROMPTS}" >"${PROMPTS}.tmp" && mv "${PROMPTS}.tmp" "${PROMPTS}"
  exit 0
fi

FILE="$(jq -r '.tool_input.file_path // empty' <<<"${PAYLOAD}" 2>/dev/null)"
[ -n "${FILE}" ] || exit 0
CWD="$(jq -r '.cwd // empty' <<<"${PAYLOAD}" 2>/dev/null)"
[ -n "${CWD}" ] && [ -d "${CWD}" ] || CWD="${PWD}"

case "${FILE}" in
  *.md|*.markdown|*.mdx) ;;
  *) exit 0 ;;
esac

case "${FILE}" in
  */.claude/*|*/CLAUDE.md|*/CLAUDE.local.md|*/AGENTS.md|*/SKILL.md) exit 0 ;;
esac

BASE="$(basename "${FILE}")"
STEM="${BASE%.*}"

# a file some CLAUDE.md links to is fair game - the instructions already point at it
ROOT="$(git -C "${CWD}" rev-parse --show-toplevel 2>/dev/null)"
INSTRUCTIONS=("${HOME}/.claude/CLAUDE.md")
for d in "${CWD}" "${ROOT}"; do
  [ -n "${d}" ] || continue
  INSTRUCTIONS+=("${d}/CLAUDE.md" "${d}/CLAUDE.local.md" "${d}/.claude/CLAUDE.md")
done
grep -qiF "${BASE}" "${INSTRUCTIONS[@]}" 2>/dev/null && exit 0

if [ -r "${PROMPTS}" ]; then
  grep -qiF "${BASE}" "${PROMPTS}" && exit 0
  [ "${#STEM}" -ge 4 ] && grep -qiF "${STEM}" "${PROMPTS}" && exit 0
  # blanket permission like "read all md files" / "check the docs folder"
  grep -qiE 'all (the )?(md|markdown)|jede? (md|markdown)|alle (md|markdown)|docs?[ /-]?(folder|ordner|verzeichnis)' \
    "${PROMPTS}" && exit 0
fi

DECISION="ask"
[ "${GUARD}" = "deny" ] && DECISION="deny"

jq -nc --arg d "${DECISION}" --arg f "${FILE}" '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: $d,
    permissionDecisionReason: ("md-read-guard: nothing in the prompt asked for \($f). " +
      "Markdown is read on request only - say in one line why you want it and ask, " +
      "or work from the code instead.")
  }
}'

exit 0
