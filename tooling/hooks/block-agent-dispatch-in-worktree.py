"""PreToolUse hook: refuse `Agent` (sub-agent) dispatch from inside a worktree.

WHY THIS EXISTS AS CODE AND NOT AS A SENTENCE
---------------------------------------------
A standing wave brief can say, in plain words, "never dispatch your own
sub-agents, not even a `fork`, not even for 'read-only research'; the
orchestrator dispatches, you execute." On real waves that rule has been
broken anyway, more than once, by agents who had it in their own brief:

- One forked sub-agent was dispatched for "pure research, do NOT modify any
  code" without workspace isolation. It shared its parent's worktree and git
  identity directly, edited a file, and committed on the parent's branch
  under attribution indistinguishable from the parent agent's own. The
  outcome happened to be correct; the process gave nobody a way to know that
  without independently re-checking the diff.
- A second agent's sub-agent wrote an entire feature into the worktree its
  parent was concurrently editing, hit its turn limit mid-edit, and left a
  component imported but never rendered: a live wired-to-nothing, introduced
  by an agent nobody dispatched.
- A third instance: a wave agent called `Agent` once while waiting on its own
  background step, the same "blocked on a slow step, reached for the wrong
  tool" shape as the other two. The prompt sent was a deliberate no-op ("do
  nothing, return"), and the resulting sub-agent still ran several tool calls
  before returning, because a sub-agent inherits the parent's full context and
  worktree, so an instruction to it, even "do nothing", is a suggestion its
  own model turn evaluates and can override, never a constraint the caller
  can enforce from outside.

A rule broken repeatedly by people who had it in their own brief is not a
documentation problem. This hook is the enforcement, matched to
`block-git-stash.py`'s shape, because a ban with no alternative loses to the
reflex every time.

WHAT SIGNAL "INSIDE A WORKTREE" USES, AND WHY
----------------------------------------------
`git rev-parse --git-dir` vs. `git rev-parse --git-common-dir`, both resolved
to absolute paths, run against the session's `cwd`. In the PRIMARY checkout
the two are the same path (there is exactly one `.git`, and it IS the common
dir). In every LINKED worktree (`git worktree add ...`) they differ:
`--git-dir` points at `<main-repo>/.git/worktrees/<name>` (this worktree's
own per-worktree admin area: HEAD, index, ORIG_HEAD) while
`--git-common-dir` points at the shared `<main-repo>/.git` that owns the
objects, refs and config every worktree shares. That divergence is git's own
worktree bookkeeping, not a string this hook maintains, so it is not
spoofable by accident: a worktree cannot be renamed or moved to some other
root without this signal still telling it apart from the primary checkout
correctly, because it is asking git what git already knows about itself
rather than pattern-matching a path. The rejected alternative was "is `cwd`
under the known worktree root": that requires the root to be known in
advance and breaks the moment a worktree lives somewhere else.

THE CALL: BLOCK EVERY `Agent` CALL, NOT JUST `fork`
-----------------------------------------------------
It is tempting to write a narrower hook: block `fork` (and whatever else
"inherits the cwd"), allow read-only search subagent types. That narrower
rule depends on a claim, that worktree-sharing is a property of the subagent
type, which a typical `Agent` tool schema disproves: isolation is a
call-level parameter (for example `isolation: "worktree"`), independent of
subagent type, and it defaults to sharing the caller's cwd and `.git` for
every type, including a plain fork. A subagent type described as "read-only
search" is often still granted a shell tool with no narrower permission set,
so it can run `git commit` from the shared worktree exactly as a fork could;
the description is a convention its own tool grant does not enforce. Because
that claim cannot be verified as generally true, this hook takes the strict
reading: block `Agent` dispatch outright from inside any worktree, regardless
of subagent type or isolation setting. A wave agent that needs more hands
says so in its report; only the orchestrator, from the primary checkout,
dispatches.

WHAT IT DOES NOT BLOCK
-----------------------
An `Agent` call made from the PRIMARY checkout is untouched: the orchestrator
must be able to dispatch constantly, and a hook that stopped that would be
worse than the bug it guards (this mirrors `block-git-stash.py`'s own
priority: never break the session over a hook's own caution). Nothing here
inspects or restricts `Bash`/`PowerShell`/`Edit`/etc.; those already have
their own gates.

CONTRACT
--------
Reads the PreToolUse payload on stdin, writes a JSON decision on stdout.
Silence plus exit 0 means "no opinion". It never blocks on its own failure: a
malformed payload, a missing `git`, or any unexpected exception exits 0
quietly -- a hook that breaks the orchestrator's own dispatching because IT
has a bug is worse than the sub-agent it is trying to catch.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

MESSAGE = """`Agent` dispatch is blocked from inside a worktree.

A wave agent must not dispatch its own sub-agents, not even a fork, not even
for "read-only research". A fork is NOT isolated by default: it shares this
worktree and this git identity, so an instruction you give it (read-only, do
not commit) is unenforceable. That has already gone wrong on real waves: one
fork committed to its parent's branch under indistinguishable attribution,
and another left a live wired-to-nothing feature mid-edit in its parent's own
worktree.

Do the work yourself, in this worktree. If the task genuinely needs more
hands than one agent, say so plainly in your report and stop; that is the
orchestrator's call to make from the primary checkout, not yours to make by
spawning something invisible to it.

(If you are the orchestrator and believe you are seeing this in error: this
hook only fires when `cwd` resolves to a linked git worktree, never the
primary checkout. Dispatch from the primary checkout instead.)"""


def _git_paths(cwd: str) -> tuple[str, str] | None:
    """Return (git_dir, git_common_dir), both absolute, or None if unavailable.

    None covers: no git on PATH, `cwd` not inside any git repository, or any
    other failure -- all of which this hook treats as "cannot tell", and it
    fails OPEN (does not block) rather than guess, per the contract above.
    """
    try:
        proc = subprocess.run(
            [
                "git",
                "-C",
                cwd,
                "rev-parse",
                "--path-format=absolute",
                "--git-dir",
                "--git-common-dir",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception:
        return None
    if proc.returncode != 0:
        return None
    lines = proc.stdout.splitlines()
    if len(lines) != 2:
        return None
    git_dir, git_common_dir = lines[0].strip(), lines[1].strip()
    if not git_dir or not git_common_dir:
        return None
    return git_dir, git_common_dir


def classify(cwd: str) -> str:
    """One of "primary", "linked_worktree", or "unknown".

    `is_linked_worktree()` below collapses "unknown" (git unavailable, `cwd`
    not inside a repo, a malformed `rev-parse` result -- any reason
    `_git_paths` returns None) into `False`, same as a genuine primary-
    checkout allow. That collapse is the right hook DECISION (doubt means
    allow, never block the orchestrator on a guess), but it means "the hook
    correctly determined this is the primary checkout" and "the hook could
    not determine anything at all" are the exact same silent exit 0 with no
    output. A shell-quoting slip that mangles a Windows path (see this
    directory's README on the Git Bash backslash trap) can produce the second
    case while looking, to a human watching stdout, exactly like the first --
    a dead guard would look identical. `explain()` below reports this
    three-way split directly so that ambiguity is never silent again; the
    hook's own PreToolUse decision (`verdict`/`is_linked_worktree`) is
    unchanged.
    """
    paths = _git_paths(cwd)
    if paths is None:
        return "unknown"
    git_dir, git_common_dir = paths
    norm = lambda p: os.path.normcase(os.path.normpath(p))  # noqa: E731
    return "linked_worktree" if norm(git_dir) != norm(git_common_dir) else "primary"


def is_linked_worktree(cwd: str) -> bool:
    """True only when `cwd` resolves to a linked worktree, never on doubt.

    The primary checkout has `--git-dir == --git-common-dir` (there is
    exactly one `.git`, and it owns itself). A linked worktree's `--git-dir`
    is its own `.git/worktrees/<name>` admin area, distinct from the shared
    `--git-common-dir`. Any failure to determine this (no git, no repo, a
    malformed result) returns False: doubt means allow, matching this hook's
    "never block the orchestrator on a guess" contract. Delegates to
    `classify()` so the hook's real decision and its `--explain` diagnostic
    can never disagree about which branch a given `cwd` takes.
    """
    return classify(cwd) == "linked_worktree"


def explain(cwd: str) -> str:
    """Diagnostic text for `--explain <cwd>`: which of the three `classify()`
    branches this `cwd` takes, spelled out in one line so a shell-quoting
    slip reads as "could not determine" instead of silently looking exactly
    like a real allow. Never used by the real PreToolUse path; a pure
    read-only affordance for testing the hook by hand."""
    result = classify(cwd)
    if result == "unknown":
        return (
            f"UNKNOWN for cwd={cwd!r}: could not resolve --git-dir/--git-common-dir "
            "(no git on PATH, cwd not inside any git repository, or a malformed "
            "`git rev-parse` result -- often a shell that mangled the path before "
            "git ever saw it). Fails OPEN: Agent dispatch is ALLOWED, and this is "
            "the ambiguous case that is otherwise indistinguishable from a genuine "
            "primary-checkout allow."
        )
    git_dir, git_common_dir = _git_paths(cwd)  # cannot be None when result != "unknown"
    if result == "primary":
        return (
            f"PRIMARY CHECKOUT for cwd={cwd!r}: --git-dir == --git-common-dir "
            f"== {git_common_dir!r}. Agent dispatch ALLOWED."
        )
    return (
        f"LINKED WORKTREE for cwd={cwd!r}: --git-dir={git_dir!r} != "
        f"--git-common-dir={git_common_dir!r}. Agent dispatch DENIED."
    )


def verdict(cwd: str) -> str | None:
    """Return the reason to deny, or None to stay silent."""
    if is_linked_worktree(cwd):
        return MESSAGE
    return None


def main() -> int:
    # `--explain <cwd>` is a diagnostic mode, never reached by the real
    # PreToolUse invocation (which always feeds JSON on stdin with no argv).
    # It exists so testing this hook by hand distinguishes "allowed because
    # primary checkout" from "allowed because the cwd could not be determined
    # at all" -- see `explain()` and its own docstring.
    if len(sys.argv) >= 3 and sys.argv[1] == "--explain":
        print(explain(sys.argv[2]))
        return 0

    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    try:
        cwd = payload.get("cwd") or os.getcwd()
        reason = verdict(cwd)
        if reason is None:
            return 0
        json.dump(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                },
                "systemMessage": "Blocked an Agent dispatch from inside a worktree.",
            },
            sys.stdout,
        )
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
