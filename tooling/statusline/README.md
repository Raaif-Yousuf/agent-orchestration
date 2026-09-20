# tooling/statusline

A status line script and a subagent-panel renderer, both built around three
things that are not obvious until a status line silently breaks on you.

## Why this needed engineering, not just a jq one-liner

**The harness cancels an in-flight script the moment the next update fires.**
Confirmed against the current status line reference
(<https://docs.claude.com/en/docs/claude-code/statusline>, which currently
redirects to <https://code.claude.com/docs/en/statusline>): updates are
debounced, and a script still running when the next one is due gets killed
mid-run. On Windows, every subprocess spawn costs somewhere around 50 to 80
milliseconds, so a script written the obvious way, one `echo | jq` per field,
takes the better part of a second and is routinely killed before it finishes
during an active turn. The bar then appears frozen for the rest of the
session, because it never gets to complete an update. The fix is not a
faster shell, it's fewer processes: `statusline.sh` does one `jq` pass that
extracts every field it needs in a single JSON array, one `awk` pass that
does all the clamping, rounding, and ANSI color math, one `date` call, and
one `git rev-parse`. Four spawns total, regardless of how many fields the
bar shows.

**A native Windows `jq` writes CRLF.** `mapfile -t` only strips the trailing
`\n` from each line it reads, not a `\r` in front of it, so every value comes
back with a `\r` glued to the end. Left alone, that turns `"high"` into
`"high\r"`, which silently fails to match any case in a `case` statement, and
turns a numeric string into something that blows up bash's `$(( ))`
arithmetic with a syntax error. The script strips it explicitly after the
`jq` pass rather than depending on some later step to happen to discard it.

**The harness's own data goes stale or missing at predictable moments, and a
naive script shows the wrong number instead of the last real one.** Right
after a context compaction, and before a session's first request has
completed, the context-window block in the JSON the script receives is
zeroed or missing entirely; the rate-limit block is omitted until the first
request of a session lands. A script that trusts the input literally flashes
`0%` at exactly the moment a real number would be most reassuring. The fix is
a small sticky cache: when a real reading comes in, write it to a cache file
keyed by session id (for context usage) or a global file (for rate limits,
which are account-wide, not session-scoped); when the input is empty, read
the last cached value back instead of printing zero.

## Files

- `statusline.sh`: the main status line. Wire it up with:

  ```json
  {
    "statusLine": {
      "type": "command",
      "command": "\"<path to bash.exe>\" \"<path to>/statusline.sh\"",
      "refreshInterval": 15
    }
  }
  ```

  On Windows, point at Git's `bash.exe` explicitly rather than relying on
  `sh` being on `PATH` for the process the harness spawns.

- `subagent-statusline.jq`: renders one row per running subagent in the
  panel below the prompt. It's invoked by `jq` directly, not through a bash
  wrapper, because this one runs on every panel tick rather than once per
  status line refresh, and cutting bash out of that chain roughly halves the
  time per tick. When a tick fails or runs past the harness's timeout,
  Claude Code drops every row decoration for that tick and the panel snaps
  back to its native layout until the next tick lands, which is the
  stock-versus-decorated flicker you get if this script errors on
  unexpected input. Wire it up with:

  ```json
  {
    "subagentStatusLine": {
      "type": "command",
      "command": "\"<path to jq.exe>\" -c -r -f \"<path to>/subagent-statusline.jq\""
    }
  }
  ```

Both scripts read one JSON object on stdin per invocation and print plain
text (`statusline.sh`) or one JSON object per line (`subagent-statusline.jq`)
on stdout.

## Requirements

`statusline.sh` needs `jq` and `awk` on `PATH` (Git for Windows ships both).
It passes `shellcheck --severity=warning` with no disables. `awk` output is
consumed positionally, so if you add a field, add it to both the `awk`
script's `BEGIN` block and the corresponding `mapfile` index below it.
