#!/usr/bin/env bash
#
# claude-sound.sh — plays a macOS system sound for Claude Code hook events.
# Usage: claude-sound.sh <event>
#   stop         -> Claude finished working ("done, your turn")
#   notification -> Claude needs you (permission prompt / idle waiting)
#

SOUND_DIR="/System/Library/Sounds"

case "$1" in
  stop)         SOUND="Glass" ;;   # done
  notification) SOUND="Funk"  ;;   # waiting
  *)            SOUND="Tink"  ;;   # fallback
esac

SOUND_FILE="${SOUND_DIR}/${SOUND}.aiff"
[ -r "${SOUND_FILE}" ] && afplay "${SOUND_FILE}" >/dev/null 2>&1

exit 0
