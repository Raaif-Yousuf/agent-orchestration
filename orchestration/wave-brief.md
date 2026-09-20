# wave brief

This is the standing brief every agent in a wave gets. Copy this file into
your own repository (a `WAVE_BRIEF.md` at the root of wherever your worktrees
live works well), fill in the placeholders once, and make the first line of
every lane-specific brief:

> First action: read `<path to this file>` in full and follow it exactly.

Everything below is what every agent needs in front of it before writing
code. It exists as one file, read by every agent, instead of being retyped
into every lane-specific brief, for a concrete reason: a paraphrase drops
whatever the person writing it did not happen to remember, and it drops
silently, because the brief still reads as complete. Keep this file current.
When a wave finds a new way to go wrong, the fix lands here, not in that
session's prompts.

---

## What you are

You are one of several agents working this repository in parallel. The
orchestrator owns the trunk branch and every merge. You own exactly one
workspace and one branch.

## Skills or checklists to use before writing code

Fill this in with your own project's equivalents, and name them explicitly
in every brief rather than describing their contents from memory:

- `<your project's issue-intake or "starting work" checklist>` before
  starting any ticket or issue.
- `<your project's bug-fixing checklist>` before writing any fix code, and
  again if a fix "should work" but the symptom persists.
- `<your project's "is this actually wired in" checklist>` before reporting
  anything as done. Code that compiles, runs, and passes its own tests while
  doing nothing at runtime is one of the most expensive and hardest-to-catch
  bug classes there is, precisely because a narrow test suite never exercises
  the real caller.

## Hard bans

All of the following have cost real time on a real wave at least once.

1. **Never run the full test suite, and never add a test-parallelism flag
   (an `-n auto` style flag) to a targeted run.** Run only the test file or
   test path covering what you touched:
   `<your project's targeted-test-run command, e.g. pytest tests/test_foo.py>`.
   A parallelism flag turns one agent's careful, narrow selection back into
   many processes, which is the exact contention this rule exists to avoid.
   If your selection is slow enough that you want to parallelize it, the
   selection is too broad; narrow it further instead.

   Watch for a targeted run that silently collects zero tests (a filter or
   config option deselecting everything back out) and reports a clean-looking
   exit anyway. A test command that exits 0 having run nothing is not a pass;
   check the count in the output, not just the exit code.

2. **Never use your version control system's "stash changes" feature while
   more than one workspace on this repository is active.** Multiple
   worktrees or checkouts of one repository typically share a single stash
   stack, so a stash made in one workspace is visible in, and poppable from,
   every other. Two agents stashing in the same window have swapped their
   working sets this way. Use this instead when you need to set changes
   aside temporarily, for example to verify a fix actually causes a test to
   fail without it:

   ```
   git diff > .scratch/fix.patch      # keep the fix
   git checkout -- <the source files only>   # keep any new tests
   <run your targeted tests; they must go red>
   git apply .scratch/fix.patch       # restore
   git diff --stat                    # prove the restore is byte-exact
   ```

   This does not work for a brand-new file that has never been committed:
   `git diff` is silent on untracked files, so the patch comes out empty and
   restores nothing. Copy the file instead:

   ```
   cp <new file> .scratch/new_file.bak
   <break the thing you want to prove is load-bearing>
   <run your targeted tests; they must go red>
   cp .scratch/new_file.bak <new file>
   git status --short                 # nothing unexpected
   ```

   Two sharper edges: `git checkout -- <file>` restores from the index, not
   from the last commit, so if you already staged the fix before reverting,
   either unstage first or use `git checkout HEAD -- <file>` explicitly. And
   once the fix is committed, `git checkout -- <file>` (even `git checkout
   HEAD -- <file>`) is a no-op, because working tree, index, and the commit
   already agree; there is nothing left to revert from. A revert check that
   "passes" suspiciously easily after a commit is not a real check. Once
   committed, name the pre-fix commit explicitly:
   `git checkout HEAD~1 -- <file>`, run the check, then `git checkout HEAD --
   <file>` to restore (there is no patch file at that point; the fix is
   already committed).

3. **Never kill a process by image name.** Not by matching all processes with
   a given executable name. That has killed an operator's own running
   application and other agents' unrelated runs in the same stroke, because
   the process being cleaned up shared an executable with things that had
   nothing to do with it. Record the process ID at spawn, and kill only that
   ID.

4. **Never close an issue or ticket.** File new ones freely, comment on
   existing ones freely. The orchestrator closes an issue on merge, not
   before; closing one for a fix that has not yet merged creates a state that
   looks done and is not.

5. **Never raise a ratchet, baseline, or allowlist to make a failing check
   pass.** If a guard goes red, fix the thing it is checking. If you
   genuinely believe the baseline itself should move, stop and report the
   reasoning instead of committing the change; do not decide it unilaterally.
   Note that a baseline built by re-scanning the whole project fresh each
   time can legitimately shrink on its own when unrelated work closes a
   pre-existing gap; regenerating it to a *smaller* number in that case is
   expected and fine. Only raising it to silence real growth is banned.

6. **Never commit outside your own workspace.** Only your branch, in your own
   workspace.

7. **Never dispatch sub-agents of your own, including a "fork" or any other
   mechanism your tooling offers for spawning nested agents.** A forked
   sub-agent is not isolated the way its name suggests: it can share your
   workspace and your identity, so "just read-only research" is not
   enforced, and anything it writes or commits is indistinguishable from your
   own work in the history. This has produced a real, uninstructed commit of
   new source code onto a lane's branch before, from an agent that was never
   asked to spawn anything. If a task genuinely needs more hands, say so in
   your report and stop; that decision belongs to the orchestrator, who knows
   what else is currently running.

8. **Never delete a directory recursively and forcibly inside the
   repository**, including your own scratch directory. Delete the specific
   files you created, by name, and confirm with `git status --short` that
   nothing unexpected disappeared. A recursive forced delete aimed at your
   own scratch files has taken tracked files from an unrelated commit down
   with it more than once.

9. **Never overwrite a file with a full-file write tool without having read
   it first in this session.** A full-file write silently replaces whatever
   was there. If you believe a file is new, check first; if it already
   exists, edit it instead of overwriting it. This costs one command and
   prevents a failure that is otherwise silent and total.

## Repo rules that apply

Fill this in per project: the specific conventions your codebase enforces
that a worker in a worktree needs in front of it, not the full house style
guide. Include, at minimum, where the project's shared toolchain (virtual
environment, package cache, node_modules) lives if it is shared across
worktrees rather than copied per worktree, and whether it is safe for a
worker to install a new dependency into it during a wave. If it is shared,
say explicitly: do not install anything into it mid-wave; a package install
from one lane can break every other lane's imports with no warning and no
obvious cause, because nothing in that lane's own diff explains the failure.

## Working method

- **The issue or ticket body is often wrong about the proposed fix.** Verify
  the mechanism against the actual code first. If the body's proposed fix is
  wrong, say so in your report and fix the real thing instead of what was
  asked for.
- **Run long steps in the foreground, with an explicit long timeout**, rather
  than letting them run in the background on the assumption something will
  notify you when they finish. Nothing does. An agent that ends its turn
  "waiting for the build" has stalled; it will not be woken by the build
  finishing. If a single step genuinely cannot finish inside whatever timeout
  your tooling allows, split it into two foreground steps rather than
  backgrounding either half, and say so in your report.
- **Before reporting anything as done, name the one observable that would
  differ if your change were wired to nothing**, and go check it. Tracing the
  source code link by link is not that check; it proves the code exists, not
  that anything calls it.
- **A screenshot or captured output is not saved unless you explicitly save
  it.** If a piece of evidence for a finding is not committed somewhere
  retrievable, treat it as not existing.
- **If your workspace contains changes you did not write, stop and report
  it.** Do not check out over them; someone else's unmerged work may be
  sitting there.
- **Do not install a new dependency or run anything that mutates a shared
  toolchain during a wave.** If your task genuinely needs one, say so in your
  report and stop, rather than installing it and silently breaking every
  other concurrent lane.

## Commit and stop

Commit on your own branch. Uncommitted work dies with you; nothing about a
checkpoint commit costs anything, and a branch with several small commits
merges exactly like a branch with one. Commit a checkpoint as soon as you
have something that would be painful to lose, and again before any
long-running step, not only at the very end. Do not merge, do not push to
anything but your own branch, do not touch the trunk branch.

## Do not narrate

Only your final report is read, and only by the orchestrator. Progress
prose ("Now I will...", "Let me check..."), restating this brief back, and
summaries of steps you already took cost tokens for nobody. Report outcomes,
numbers, file paths, what you could not do and why, and the sections below.

## Your report must end with these sections

```
BRANCH: <branch> @ <commit>

WIRED CHECK: <the one observable you verified, and what you actually saw>

FINDINGS:
- <a bug, a suspected bug, an improvement, or an area that needs work>
- ...
```

Be generous in findings. Suspicions count: "this looked fragile," "this has
no test," "these two things disagree" are all worth reporting even when
you are not certain. Say plainly when you are unsure rather than rounding
up to confidence you don't have.

## Where to put throwaway files

Not in your workspace root, and not in a scratchpad path shared across the
whole wave; a shared scratch path is not private to you, and two agents
writing to the same path in the same window have overwritten each other's
files there. Use a path inside your own workspace, under something like
`.scratch/`, that you clean up before finishing, or your session's own
private scratch directory if your tooling gives you one that is genuinely
per-agent.

## Test command reference

- Targeted run (what every agent uses): `<your project's targeted test
  command>`
- Full suite (orchestrator only, once, after all merges, with no agent
  still active): `<your project's full test command>`
- Branch-scoped pre-commit check, if your project has one:
  `<your project's fast branch-scoped check command>`
