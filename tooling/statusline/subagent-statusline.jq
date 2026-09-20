# Renders one row per subagent in the agent panel below the prompt.
#
# Invoked DIRECTLY by jq (see settings.json's subagentStatusLine.command)
# rather than through a bash wrapper: this program runs on every panel tick,
# and on Windows each process spawn costs ~50-80ms, so cutting bash out of the
# chain roughly halves the run (~105ms -> ~45ms). That matters because when a
# tick fails or exceeds the harness's timeout, Claude Code drops EVERY
# decoration and the whole panel snaps back to its native layout until the
# next tick lands -- which is the "glitch between the old and new layout"
# seen when the machine is loaded.
#
# This is a THIN override: the row text is the harness's own label (the
# `label` field is built by Claude Code as
# `agentLabel(task) || task.description`, i.e. exactly what the stock row
# shows), with only the model name and the context percentage appended, plus
# the stock elapsed-time column pinned to the right.
#
# Why the time has to be rebuilt here: when a row carries an override, the
# panel renders ONLY [gutter][content] -- its three-column layout
# (name | summary | right-aligned "45s . ^ 12.3k tokens") is skipped
# entirely, because the status column's shared width is computed only from
# rows whose decoration is undefined. So the elapsed time is recreated below
# and right-padded by hand.
#
# `.columns` is already the usable content width -- the harness passes
# `terminalColumns - gutterWidth` -- so pad to exactly that, no margin.
#
# Requires a reasonably recent Claude Code for `task.model` /
# `task.contextWindowSize` and `task.effort` to be populated; on an older
# version those fields are simply absent and the fallbacks below degrade
# gracefully. Output is one {"id":..., "content":...} JSON object per line.
# A native Windows jq emits CRLF; the trailing \r is JSON whitespace and
# JSON.parse tolerates it, so no post-processing is needed.

def modelname:
  if . == null or . == "" then null
  elif . == "claude-opus-5"   then "Opus 5"
  elif . == "claude-sonnet-5" then "Sonnet 5"
  elif . == "claude-fable-5"  then "Fable 5"
  elif startswith("claude-haiku-4-5") then "Haiku 4.5"
  else (sub("^claude-"; "") | sub("-[0-9]{8}$"; ""))
  end;

def efforttag:
  if . == null then ""
  elif type == "number" then " [\(.)]"
  elif . == "low"    then " [L]"
  elif . == "medium" then " [M]"
  elif . == "high"   then " [H]"
  elif . == "xhigh"  then " [XH]"
  elif . == "max"    then " [MAX]"
  else " [\(.)]"
  end;

# Same white -> yellow -> red ramp as the main status line.
def rgb:
  if . <= 50 then "255;255;255"
  elif . >= 85 then "255;0;0"
  else ((. - 50) / 35) as $t
    | "255;\((255 * (1 - $t)) | floor);\(if $t <= 0.5 then (255 * (1 - 2 * $t)) | floor else 0 end)"
  end;

# Mirrors the harness formatter: "45s", "2m 5s", "1h 2m 5s", "1d 2h 3m",
# including its carry when the rounded seconds land on 60.
def elapsed:
  (if . < 0 then 0 else . end | floor) as $ms
  | if $ms < 60000 then "\(($ms / 1000) | floor)s"
    else (($ms / 86400000) | floor) as $d
    | ((($ms % 86400000) / 3600000) | floor) as $h
    | ((($ms % 3600000) / 60000) | floor) as $mi
    | ((($ms % 60000) / 1000) | round) as $s
    | (if $s == 60 then 0 else $s end) as $ss
    | (if $s == 60 then $mi + 1 else $mi end) as $m1
    | (if $m1 == 60 then 0 else $m1 end) as $mm
    | (if $m1 == 60 then $h + 1 else $h end) as $h1
    | (if $h1 == 24 then 0 else $h1 end) as $hh
    | (if $h1 == 24 then $d + 1 else $d end) as $dd
    | if $dd > 0 then "\($dd)d \($hh)h \($mm)m"
      elif $hh > 0 then "\($hh)h \($mm)m \($ss)s"
      elif $mm > 0 then "\($mm)m \($ss)s"
      else "\($ss)s"
      end
    end;

"\u001b" as $esc
| (.columns // 80) as $cols
| (now * 1000) as $nowms
| .tasks // []
| .[]
| . as $t
| ($t.model | modelname) as $m
| ($t.effort | efforttag) as $e
| (if ($t.tokenCount // null) != null and (($t.contextWindowSize // 0) > 0)
   then (($t.tokenCount * 100) / $t.contextWindowSize) | floor
   else null end) as $pct
# Stock row text, straight from the harness.
| (($t.label // $t.description // $t.name // "agent") | gsub("\\s+"; " ")) as $label
| (if ($t.startTime // null) == null then ""
   else ($nowms - $t.startTime) | elapsed end) as $time
| ([ (if $m == null then null else $m + $e end),
     (if $pct == null then null else "\($pct)%" end)
   ] | map(select(. != null))) as $plain
| ([ (if $m == null then null else $m + $e end),
     (if $pct == null then null else
        "\($esc)[38;2;\($pct | rgb)m\($pct)%\($esc)[0m" end)
   ] | map(select(. != null))) as $colored
# Visible width ignores the ANSI escapes, so budget against the uncolored form.
| (if ($plain | length) == 0 then 0 else ($plain | join(" · ") | length) + 3 end) as $suffixlen
| (if $time == "" then 0 else ($time | length) + 1 end) as $timelen
| ($cols - $suffixlen - $timelen) as $room
| (if ($label | length) <= $room or $room < 8 then $label
   else ($label[0:$room - 1]) + "…" end) as $shown
| ([$shown] + $colored | join(" · ")) as $left
| (($shown | length) + $suffixlen) as $leftlen
# Right-pad so the elapsed time lands flush against the right edge.
| (if $time == "" then $left
   else ($cols - $leftlen - ($time | length)) as $gap
     | $left + (" " * (if $gap < 1 then 1 else $gap end)) + $time
   end) as $content
| {id: $t.id, content: $content}
