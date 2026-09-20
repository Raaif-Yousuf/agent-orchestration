# tooling/hooks

Three `PreToolUse` hooks I run on every repository where agents work
unattended. Each one enforces, mechanically, a rule that was already written
down in prose and still got broken repeatedly by agents who had read it. A
rule broken more than once by people who read it is not a documentation
problem, it is a missing hook.

- `block-git-stash.py`: refuses a mutating `git stash` (`push`, `pop`,
  `apply`, `drop`, and friends). `git stash list` and `git stash show` stay
  allowed.
- `block-agent-dispatch-in-worktree.py`: refuses `Agent`/sub-agent dispatch
  when the session's `cwd` is inside a linked git worktree rather than the
  primary checkout.
- `block-recursive-delete.py`: refuses a recursive, forced delete
  (`rm -rf`, `Remove-Item -Recurse -Force`, and their aliases) aimed at a
  path that resolves inside the repository.

All three are Python 3, standard library only, with no imports from the rest
of a project, so you can drop any one of them into another repository on its
own. Each file's own docstring explains the specific incident it exists to
prevent and exactly what it does and does not block; this file is about
wiring them up and testing them by hand.

## Why a hook and not just a brief

A brief is prose an agent's own turn can decide to override under pressure,
especially when the situation matches a reflex (a revert check reaches for
`git stash`; tidying up reaches for `rm -rf`). A hook is not prose: it runs
outside the model's own reasoning, on every matching tool call, every time,
regardless of how the request was phrased. Keep the brief too, for the agent
that reads it before it ever tries the blocked command, but the hook is what
actually holds the line.

## Registering the hooks

Add this to the `hooks` block of a project's `.claude/settings.json` (see
`tooling/settings/` for a full example file). Adjust `scripts/hooks/` to
wherever you actually put these files:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|PowerShell",
        "hooks": [
          {
            "type": "command",
            "command": "python3 tooling/hooks/block-git-stash.py",
            "timeout": 10
          },
          {
            "type": "command",
            "command": "python3 tooling/hooks/block-recursive-delete.py",
            "timeout": 10
          }
        ]
      },
      {
        "matcher": "Agent|Task",
        "hooks": [
          {
            "type": "command",
            "command": "python3 tooling/hooks/block-agent-dispatch-in-worktree.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

The `matcher` field is a regex over the tool name. `PreToolUse` fires before
the tool runs and receives the tool's input on stdin; a hook can then answer
with silence (no opinion), or a JSON decision of `allow`, `deny`, or `ask`.
Confirmed against the current hooks reference
(<https://docs.claude.com/en/docs/claude-code/hooks>, which currently
redirects to <https://code.claude.com/docs/en/hooks>): the payload includes
`session_id`, `cwd`, `permission_mode`, `hook_event_name`, `tool_name`,
`tool_input`, and `tool_use_id`; a decision is written as

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "...",
    "systemMessage": "..."
  }
}
```

on stdout with exit code 0. One difference from what the hooks in this
directory were originally written against: the current docs also list an
`updatedInput` field a hook can return to rewrite the tool call instead of
just allowing or denying it, and note that exit code 2 blocks unconditionally
regardless of what JSON is printed. None of the three hooks here use either
of those; they only ever emit `allow`-by-silence or `deny`, and only ever
exit 0, which the docs confirm is honored either way.

## Testing a hook by hand

The real tests are `tests/test_hooks.py`, run through `pytest`. This section
is for a human probing one of these hooks by hand from a shell, which is
worth writing down once because it has already produced a false result.

### The Git Bash backslash trap

**Never hand a Windows path to one of these hooks as an inline backslash
string through Git Bash.** Use forward slashes, or write the JSON payload to
a file first.

This command, run from Git Bash to check whether
`block-agent-dispatch-in-worktree.py` denies dispatch from a real linked
worktree:

```
echo '{"tool_name":"Agent","tool_input":{},"cwd":"C:\\Users\\<you>\\repo-wt\\some-branch"}' | python tooling/hooks/block-agent-dispatch-in-worktree.py
```

produces **no output and exit 0**, which reads as "the hook does not fire": a
dead guard. The same payload, written with forward slashes and piped from a
file instead of an inline `echo`, correctly emits the deny JSON. The
backslashes did not survive the shell, so the hook received a `cwd` that was
not a real path; its internal path resolution then failed exactly as
designed and the hook failed OPEN (allowed), which is the right behaviour for
"cannot tell" but is indistinguishable from a genuine allow without more
information. A hook that breaks the session over its own parsing bug would be
worse than the bug it guards, so failing open here is correct; the trap is
only in how you **verify** it by hand.

Prefer this shape instead:

```
mkdir -p .scratch
printf '{"tool_name":"Agent","tool_input":{},"cwd":"C:/Users/<you>/repo-wt/some-branch"}' > .scratch/probe.json
python tooling/hooks/block-agent-dispatch-in-worktree.py < .scratch/probe.json
```

Forward slashes resolve fine on Windows through `git -C <path>`, and a file
sidesteps whatever quoting layer mangled the inline string.

### Telling "denied" apart from "could not tell"

`block-agent-dispatch-in-worktree.py --explain <cwd>` prints which of three
branches a `cwd` takes: `PRIMARY CHECKOUT`, `LINKED WORKTREE`, or `UNKNOWN`,
instead of the `PreToolUse` contract's silent exit 0 either way. Reach for
this whenever a manual probe of that hook comes back with no output and you
are not sure whether that means "allowed, this is the primary checkout" or
"the path could not be resolved at all". It never affects the real hook
decision; it is read-only.

`block-git-stash.py` and `block-recursive-delete.py` have no equivalent flag:
their decision space is a single boolean (deny or allow) with no third
"could not tell" state to distinguish, so there is nothing an `--explain`
mode would add.
