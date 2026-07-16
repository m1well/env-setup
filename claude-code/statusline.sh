#!/bin/bash
# Claude Code statusline (single line, muted colors)
# Order: dir  [Model · Effort]  bar PCT%  |  5h: X% (resets HH:MM) 7d: Y%

input=$(cat)

DIR=$(echo "$input" | jq -r '.workspace.current_dir')
MODEL=$(echo "$input" | jq -r '.model.display_name')
EFFORT=$(echo "$input" | jq -r '.effort.level // empty')
PCT=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)
FIVE_H=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
FIVE_H_RESETS_AT=$(echo "$input" | jq -r '.rate_limits.five_hour.resets_at // empty')
WEEK=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')

# Light/muted colors - a bit brighter than pure dim, still not flashy
GREEN='\033[32m'
YELLOW='\033[33m'
RED='\033[31m'
# Base tone for the plain (non-status) text: lighter than the terminal
# default, but not full white
LIGHT='\033[37m'
RESET='\033[0m'

# --- Part 0: current directory (just the folder name, not the full path) ---
DIR_NAME="${DIR##*/}"

# --- Part 1: model + effort ---
if [ -n "$EFFORT" ]; then
    MODEL_PART="${MODEL} · ${EFFORT}"
else
    MODEL_PART="${MODEL}"
fi

# --- Part 2: context bar (green <=15%, yellow <=50%, red >50%) ---
# The bar itself is colored; the percentage next to it stays plain (LIGHT).
if [ "$PCT" -le 15 ]; then
    BAR_COLOR="$GREEN"
elif [ "$PCT" -le 50 ]; then
    BAR_COLOR="$YELLOW"
else
    BAR_COLOR="$RED"
fi

BAR_WIDTH=18
FILLED=$((PCT * BAR_WIDTH / 100))
[ "$FILLED" -gt "$BAR_WIDTH" ] && FILLED=$BAR_WIDTH
# Always show at least one filled segment once usage is above 0%,
# so low percentages stay visible even on a wide bar
[ "$PCT" -gt 0 ] && [ "$FILLED" -eq 0 ] && FILLED=1
EMPTY=$((BAR_WIDTH - FILLED))
BAR=""
[ "$FILLED" -gt 0 ] && printf -v FILL "%${FILLED}s" && BAR="${FILL// /▓}"
[ "$EMPTY" -gt 0 ] && printf -v PAD "%${EMPTY}s" && BAR="${BAR}${PAD// /░}"

# --- Part 3: rate limit usage, each value colored on its own (green <=70%, yellow <=90%, red >90%) ---
rate_limit_color() {
    local value_int
    value_int=$(printf '%.0f' "$1")
    if [ "$value_int" -le 70 ]; then
        echo "$GREEN"
    elif [ "$value_int" -le 90 ]; then
        echo "$YELLOW"
    else
        echo "$RED"
    fi
}

# Convert a Unix epoch to local 24h HH:MM.
# Tries macOS/BSD date first (-r), falls back to GNU date (-d) for Linux.
format_reset_time() {
    local epoch="$1"
    date -r "$epoch" +%H:%M 2>/dev/null || date -d "@$epoch" +%H:%M 2>/dev/null
}

RL=""
if [ -n "$FIVE_H" ]; then
    FIVE_H_COLOR=$(rate_limit_color "$FIVE_H")
    RL="5h: ${FIVE_H_COLOR}$(printf '%.0f' "$FIVE_H")%${LIGHT}"
    if [ -n "$FIVE_H_RESETS_AT" ]; then
        FIVE_H_RESET_TIME=$(format_reset_time "$FIVE_H_RESETS_AT")
        [ -n "$FIVE_H_RESET_TIME" ] && RL="${RL} (resets ${FIVE_H_RESET_TIME})"
    fi
fi
if [ -n "$WEEK" ]; then
    WEEK_COLOR=$(rate_limit_color "$WEEK")
    RL="${RL:+$RL }7d: ${WEEK_COLOR}$(printf '%.0f' "$WEEK")%${LIGHT}"
fi

# --- Assemble output ---
# Base text runs in LIGHT; the bar and rate-limit numbers switch to their
# own color and switch back to LIGHT right after (not RESET), so the rest
# of the line stays lightened instead of falling back to terminal default.
OUT="${LIGHT}${DIR_NAME}  |  [$MODEL_PART]  ${BAR_COLOR}${BAR}${LIGHT} ${PCT}%"
[ -n "$RL" ] && OUT="${OUT}  |  ${RL}"
OUT="${OUT}${RESET}"

echo -e "$OUT"

