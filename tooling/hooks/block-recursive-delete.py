"""PreToolUse hook: refuse a recursive force-delete aimed inside the repository.

WHY THIS EXISTS AS CODE AND NOT AS A SENTENCE
---------------------------------------------
A shared scratch directory (tracked in git, one per repository, used by every
worktree and every agent) holds files other commits own. An agent tidying up
its own scratch files cannot tell its files from anyone else's, and
`rm -rf` does not ask.

On one real overnight wave, four different agents each independently ran
`rm -rf` on that shared scratch directory, and all four deleted the same
tracked files that belonged to an earlier commit. All four caught it with
`git status` afterward and restored with `git checkout --` before committing.
That is four saves by luck, not a control: most of those runs happened after
the ban was already written into a shared wave brief, and one agent had the
exact count of prior offenders in its own brief and still did it, reporting
afterward that it ran the command "out of habit."

This is the same arc `git stash` took on the same repository: banned in the
wave brief, banned in an orchestration skill, banned verbatim in individual
briefs, broken repeatedly anyway, and only actually stopped by a hook (see
`block-git-stash.py`). A rule broken four times in one night by agents who
read it is not a documentation problem. This hook is the enforcement, and the
message it prints is the replacement, because a ban with no alternative loses
to the reflex.

WHAT IT BLOCKS
--------------
A delete that is BOTH recursive and forced, aimed at a path that resolves
inside this repository. Both halves matter: `rm -r` on its own prompts, and a
non-recursive `rm` cannot take a directory, so the dangerous spelling is the
combination. Covers POSIX `rm` (`-rf`, `-fr`, `-r -f`, `--recursive --force`)
and PowerShell `Remove-Item -Recurse -Force` with its aliases (`ri`, `rd`,
`rmdir`, `del`, `erase`) and prefix-matched parameters, which PowerShell
accepts (`-Recurse -For`).

WHAT IT DOES NOT BLOCK
-----------------------
- Deleting specific files by name: `rm .scratch/my_probe.log`. That is the
  replacement this hook tells you to use, so blocking it would be perverse.
- A recursive delete aimed OUTSIDE the repository: a session's own scratch
  directory outside the repo tree, `/tmp`, a system temp dir. Agents are
  routinely told to put temporary files there, and cleaning those up is
  correct.
- `git clean`, which has its own semantics and respects `.gitignore`.
- Prose that merely mentions the string. A brief being written, a grep, a
  commit message describing this very ban: the pattern requires the command
  in command position, and `cat <<EOF` heredoc BODIES are blanked before
  scanning, the same way and for the same reason as in `block-git-stash.py`.

CONTRACT
--------
Reads the PreToolUse payload on stdin, writes a JSON decision on stdout.
Silence plus exit 0 means "no opinion", which is the correct response to
everything except a recursive force-delete inside the repo. It never blocks
on its own failure: a malformed payload or an unexpected exception exits 0
quietly, because a hook that breaks the session when IT has a bug is worse
than the bug it guards.

CONFIGURE FOR YOUR OWN REPO
----------------------------
`SCRATCH_DIR_NAME` below names the one shared, tracked scratch directory this
hook was written to protect (adjust it, or drop the reasoning specific to it,
if your project has no such directory). `REPO_ROOT` is computed from this
file's own location two levels up; if you copy this file somewhere other than
`<repo>/tooling/hooks/`, adjust that constant to match.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import sys

# Adjust to your own repo layout: this file is expected to live at
# <repo_root>/tooling/hooks/block-recursive-delete.py.
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

# The name of the shared, tracked scratch directory this hook exists to
# protect. Purely documentation here; the hook blocks a recursive force-delete
# anywhere inside the repo, not just this path.
SCRATCH_DIR_NAME = ".scratch"

# `cat <<DELIM ... DELIM` bodies are data, not shell. Identical reasoning to
# block-git-stash.py's own copy: scoped to `cat` specifically, because a
# heredoc fed to an interpreter (`bash <<EOF`, `python <<EOF`) really is
# executed and blanking THAT body would let a real delete through unseen.
_CAT_HEREDOC_OPENER = re.compile(r"\bcat\b[^\n]*<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")

# Command position: start of line, or after a shell separator, optionally
# behind a run of inline environment assignments.
_CMD_POS = r"(?:^|[;&|\n(]|&&|\|\|)\s*(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*"

# POSIX rm. The argument run is captured so flags and targets can be split
# apart properly rather than guessed at with a second regex.
_RM = re.compile(_CMD_POS + r"(?:/usr/bin/)?rm\b(?P<args>[^;&|\n]*)", re.IGNORECASE)

# PowerShell Remove-Item and every alias that reaches the same cmdlet.
_REMOVE_ITEM = re.compile(
    _CMD_POS + r"(?:Remove-Item|ri|rd|rmdir|del|erase)\b(?P<args>[^;&|\n]*)",
    re.IGNORECASE,
)

MESSAGE = f"""A recursive force-delete aimed inside this repository is blocked.

`{SCRATCH_DIR_NAME}/` (or whatever your project's shared scratch directory is
named) is SHARED and may be TRACKED. It can hold files other commits own, and
on a real wave four agents independently deleted the same tracked files this
way, each one meaning to remove only their own.

Delete the specific files you created, by name, then prove the tree is clean:

    rm {SCRATCH_DIR_NAME}/<the exact files you wrote>
    git status --short          # must show nothing you did not intend

If you want a scratch directory that is genuinely yours to destroy, use your
session's own scratch directory outside the repository tree. A recursive
delete there is not blocked.

To discard uncommitted changes to tracked files, `git checkout -- <paths>` is
the right tool and is not blocked. To remove untracked files with
.gitignore respected, `git clean` is not blocked either."""


def _strip_cat_heredoc_bodies(command: str) -> str:
    """Blank out the BODY lines of every `cat <<DELIM ... DELIM` heredoc,
    leaving the opener and terminator lines in place so a real delete sitting
    outside any heredoc on the same command is still seen in command
    position."""
    lines = command.split("\n")
    out: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        opener = _CAT_HEREDOC_OPENER.search(line)
        out.append(line)
        i += 1
        if not opener:
            continue
        delim = opener.group(2)
        while i < n and lines[i].strip() != delim:
            out.append("")  # keep line numbers stable; content is not needed
            i += 1
        if i < n:
            out.append(lines[i])
            i += 1
    return "\n".join(out)


def _split_args(args: str) -> list[str]:
    """Tokenise an argument run, dropping surrounding quotes. Deliberately
    simple: this hook only needs to tell flags from paths, and a quoting
    subtlety that defeats it fails toward SILENCE, which is the safe
    direction for a hook (the delete still has to pass normal permission
    checks)."""
    return [t.strip("'\"") for t in args.split() if t.strip("'\"")]


def _posix_rm_is_recursive_force(tokens: list[str]) -> bool:
    """True only when BOTH recursive and force are present. `rm -r` alone
    prompts, and a plain `rm` cannot take a directory at all, so the
    combination is the spelling worth refusing."""
    recursive = force = False
    for tok in tokens:
        if tok == "--":
            break
        if tok.startswith("--"):
            if tok == "--recursive":
                recursive = True
            elif tok == "--force":
                force = True
        elif tok.startswith("-") and len(tok) > 1:
            # A short-flag cluster: -rf, -fr, -Rf, and each letter alone.
            for ch in tok[1:]:
                if ch in "rR":
                    recursive = True
                elif ch == "f":
                    force = True
    return recursive and force


def _powershell_is_recursive_force(tokens: list[str]) -> bool:
    """PowerShell accepts any unambiguous PREFIX of a parameter name, so
    `-Recurse -For` is a real, working spelling and must match."""
    recursive = force = False
    for tok in tokens:
        if not tok.startswith("-"):
            continue
        name = tok.lstrip("-").split(":")[0].lower()
        if name and "recurse".startswith(name):
            recursive = True
        elif name and "force".startswith(name):
            force = True
    return recursive and force


def _targets(tokens: list[str]) -> list[str]:
    """The non-flag arguments. A PowerShell named parameter's VALUE (the token
    right after `-Path`/`-LiteralPath`) is a target, not a flag, and falls out
    of this correctly because it does not itself start with `-`."""
    out: list[str] = []
    seen_ddash = False
    for tok in tokens:
        if tok == "--":
            seen_ddash = True
            continue
        if not seen_ddash and tok.startswith("-"):
            continue
        out.append(tok)
    return out


def _is_inside_repo(target: str) -> bool:
    """Does this path resolve inside the repository?

    A bare relative path counts: the hook cannot know the shell's cwd, and an
    agent's cwd is essentially always its worktree. Failing toward 'inside'
    for a relative path is the direction that protects a tracked scratch
    directory, which is the whole point. An absolute path is resolved and
    compared honestly, so a session's own scratch directory and system temp
    dirs stay allowed.
    """
    if not target or target.startswith("$") or "*" in target or "?" in target:
        # A variable or a glob cannot be resolved here. Treat a glob as inside
        # (it is almost certainly repo-relative) and a variable as unknown,
        # which is the same conservative direction.
        return "*" not in target or not os.path.isabs(target)
    expanded = os.path.expandvars(os.path.expanduser(target))
    path = pathlib.Path(expanded)
    # A leading slash is absolute in the POSIX sense even on Windows, where
    # `Path("/tmp/x").is_absolute()` is False because there is no drive.
    # Agents here may run under a POSIX-style shell as often as PowerShell, so
    # `/tmp/...` is a real spelling that must not read as repo-relative.
    # Resolving it lands it on the current drive's root, which is outside the
    # repo, which is correct.
    posix_rooted = expanded.startswith("/") or expanded.startswith("\\")
    if not path.is_absolute() and not posix_rooted:
        return True
    try:
        resolved = path.resolve()
    except (OSError, ValueError):
        return False
    try:
        resolved.relative_to(REPO_ROOT)
        return True
    except ValueError:
        return False


def verdict(command: str) -> str | None:
    """Return the reason to deny, or None to stay silent."""
    scanned = _strip_cat_heredoc_bodies(command or "")

    for pattern, is_rf in (
        (_RM, _posix_rm_is_recursive_force),
        (_REMOVE_ITEM, _powershell_is_recursive_force),
    ):
        for match in pattern.finditer(scanned):
            tokens = _split_args(match.group("args"))
            if not is_rf(tokens):
                continue
            targets = _targets(tokens)
            if not targets:
                # `rm -rf` with no target does nothing; say nothing.
                continue
            if any(_is_inside_repo(t) for t in targets):
                return MESSAGE
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    try:
        command = (payload.get("tool_input") or {}).get("command") or ""
        reason = verdict(command)
        if reason is None:
            return 0
        json.dump(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                },
                "systemMessage": "Blocked a recursive force-delete inside the repo; "
                "check for a shared/tracked scratch directory.",
            },
            sys.stdout,
        )
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
