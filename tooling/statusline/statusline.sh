#!/bin/bash
# Claude Code status line.
#
# PERFORMANCE NOTE: Claude Code cancels an in-flight status line script as soon
# as the next update triggers (updates are debounced at 300ms). On Windows every
# subprocess spawn costs ~50-80ms, so a naive "echo | jq" per field version took
# ~950ms and was routinely killed mid-run during active turns -- which is why the
# bar appeared frozen for whole sessions. Everything below is deliberately kept
# to four spawns total: one jq, one awk, one date, one git.
set -u
input=$(cat)

# ---- One jq pass for every field we need ----
mapfile -t F < <(jq -r '
  [ (.model.display_name // "Unknown"),
    (.effort.level // ""),
    (.context_window.context_window_size // 200000),
    (.context_window.current_usage.cache_read_input_tokens // 0),
    (.context_window.current_usage.cache_creation_input_tokens // 0),
    (.context_window.current_usage.input_tokens // 0),
    (.context_window.current_usage.output_tokens // 0),
    (.context_window.used_percentage // ""),
    (.session_id // "default"),
    (.cwd // ""),
    (.rate_limits.five_hour.used_percentage // ""),
    (.rate_limits.five_hour.resets_at // ""),
    (.rate_limits.seven_day.used_percentage // "")
  ] | .[] | tostring' <<<"$input" 2>/dev/null)

# The jq on PATH here may be a native Windows build: it writes CRLF, and
# `mapfile -t` strips only the \n, leaving a \r glued to every value. Left in
# place, "high\r" misses the effort `case` below and "2000\r" blows up
# arithmetic. Strip it explicitly rather than relying on command substitution
# (which drops a trailing \r for you) to always be in the pipeline.
for i in "${!F[@]}"; do F[$i]=${F[$i]%$'\r'}; done

model=${F[0]:-Unknown}
model=${model%% (*}          # strip parenthetical suffix like " (1M context)"
effort_level=${F[1]}
context_size=${F[2]:-200000}
cache_read=${F[3]:-0}
cache_creation=${F[4]:-0}
input_tokens=${F[5]:-0}
output_tokens=${F[6]:-0}
used=${F[7]}
session_id=${F[8]:-default}
cwd=${F[9]}
five_hour_used=${F[10]}
five_hour_resets=${F[11]}
week_used=${F[12]}

case "$effort_level" in
  low) effort_tag=" [L]" ;;
  medium) effort_tag=" [M]" ;;
  high) effort_tag=" [H]" ;;
  xhigh) effort_tag=" [XH]" ;;
  max) effort_tag=" [MAX]" ;;
  *) effort_tag="" ;;
esac

# Token counts are integers, so bash arithmetic is enough -- no awk needed here.
total_tokens=$(( cache_read + cache_creation + input_tokens + output_tokens ))
[ -z "$used" ] && used=$(( context_size > 0 ? total_tokens * 100 / context_size : 0 ))

# Sticky cache: right after /compact (and before a session's first API turn) the
# harness zeroes the ENTIRE context_window block, so a literal 0% would flash.
# Hold the last real reading for this session until a live number arrives.
cache_file="${TMPDIR:-/tmp}/claude-statusline-${session_id}.cache"
if [ "$total_tokens" -gt 0 ]; then
  echo "${total_tokens} ${used}" > "$cache_file" 2>/dev/null
elif [ -r "$cache_file" ]; then
  read -r cached_tokens cached_used < "$cache_file"
  [ -n "$cached_tokens" ] && total_tokens=$cached_tokens
  [ -n "$cached_used" ] && used=$cached_used
fi

# Sticky cache, same reason: the harness omits .rate_limits entirely until a
# session's first API request lands. These are ACCOUNT-wide rather than
# session-scoped, so the cache is global and the last reading is still correct.
rl_cache="${HOME}/.claude/.statusline-ratelimits.cache"
if [ -n "$five_hour_used" ] || [ -n "$week_used" ]; then
  printf '%s|%s|%s\n' "$five_hour_used" "$five_hour_resets" "$week_used" > "$rl_cache" 2>/dev/null
elif [ -r "$rl_cache" ]; then
  IFS='|' read -r five_hour_used five_hour_resets week_used < "$rl_cache"
fi

# ---- One awk pass: clamp, ROUND, and pick colors ----
# The harness sends raw floats (e.g. 28.999999999999996), which would otherwise
# print verbatim as "5h:28.999999999999996%". Everything is rounded here.
bar_width=20
mapfile -t A < <(awk -v used="$used" -v five="$five_hour_used" -v week="$week_used" \
                     -v tok="$total_tokens" -v ctx="$context_size" -v bw="$bar_width" '
  # white below 50%, white->yellow->red across 50-85%, solid red at/above 85%
  function rgb(p,   r, g, b, t) {
    if (p <= 50)      { r = 255; g = 255; b = 255 }
    else if (p >= 85) { r = 255; g = 0;   b = 0   }
    else {
      t = (p - 50) / 35
      r = 255
      g = 255 * (1 - t)
      b = (t <= 0.5) ? 255 * (1 - 2 * t) : 0
    }
    return sprintf("%d;%d;%d", r, g, b)
  }
  function kfmt(n) { return (n >= 1000) ? sprintf("%.0fk", n / 1000) : sprintf("%d", n) }
  BEGIN {
    u = used + 0
    if (u < 0) u = 0
    if (u > 100) u = 100
    printf "%.0f\n", u

    f = u * bw / 100
    if (f < 0) f = 0
    if (f > bw) f = bw
    printf "%.0f\n", f

    print rgb(u)

    if (five == "") { print ""; print "" } else { printf "%.0f\n", five + 0; print rgb(five + 0) }
    if (week == "") { print ""; print "" } else { printf "%.0f\n", week + 0; print rgb(week + 0) }

    print kfmt(tok)
    print kfmt(ctx)
  }')

used=${A[0]}
filled=${A[1]}
rgb_used=${A[2]}
five_hour_used=${A[3]}
rgb_five=${A[4]}
week_used=${A[5]}
rgb_week=${A[6]}
tokens_display=${A[7]}
context_display=${A[8]}

bar=""
for ((i = 0; i < filled; i++)); do bar="${bar}#"; done
for ((i = filled; i < bar_width; i++)); do bar="${bar}·"; done

status=$(printf '%s%s | \033[38;2;%sm[%s] %s%%\033[0m | %s/%s' \
  "$model" "$effort_tag" "$rgb_used" "$bar" "$used" "$tokens_display" "$context_display")

# ---- Git branch / worktree, in a single rev-parse ----
[ -z "$cwd" ] && cwd="$(pwd)"
if git_info=$(git -C "$cwd" rev-parse --abbrev-ref HEAD --show-toplevel --git-dir --git-common-dir 2>/dev/null); then
  mapfile -t G <<<"$git_info"
  branch=${G[0]}
  toplevel=${G[1]}
  git_dir=${G[2]}
  git_common_dir=${G[3]}
  [ "$branch" = "HEAD" ] && branch="detached"
  # A linked worktree has its own .git dir distinct from the shared common dir.
  if [ -n "$git_dir" ] && [ "$git_dir" != "$git_common_dir" ]; then
    status="${status} | wt:${toplevel##*/} (${branch})"
  else
    status="${status} | ${branch}"
  fi
fi

if [ -n "$five_hour_used" ]; then
  reset_display=""
  [ -n "$five_hour_resets" ] && reset_display=$(date -d "@${five_hour_resets}" "+%-I:%M%p" 2>/dev/null)
  status=$(printf '%s | 5h:\033[38;2;%sm%s%%\033[0m' "$status" "$rgb_five" "$five_hour_used")
  [ -n "$reset_display" ] && status="${status} (resets ${reset_display})"
fi

if [ -n "$week_used" ]; then
  status=$(printf '%s | 7d:\033[38;2;%sm%s%%\033[0m' "$status" "$rgb_week" "$week_used")
fi

echo "$status"
