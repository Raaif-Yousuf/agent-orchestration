# worker brief template

Every brief a worker gets has two parts: a standing part that is identical
for every agent in every wave, and a lane-specific part that changes per
dispatch. Keep them separate, and keep the standing part in one file.

## Why the standing part is a file, not a paragraph you retype

The failure mode is specific: an orchestrator writes the principles of a rule
or a skill into a brief by hand, by memory, instead of naming the file or
skill that carries it, and drops whatever they did not happen to remember.
The drop is silent, because the brief still reads as complete; nothing in it
signals that a line is missing. The fix is not "remember better," it is
structural: put the standing rules in one file (`wave-brief.md` in this
section is a ready-to-copy version), and make the first line of every
lane-specific brief "read `<path to that file>` in full and follow it
exactly."

It is also the cheap shape. One file, read by every agent in the wave, costs
one edit when a wave finds a new failure mode. Ten briefs with the same rules
pasted into each cost ten edits, and the tenth one is the one that gets
missed.

## The standing part: what it must contain, and why

| Must include | Why |
| --- | --- |
| The skills or checklists this project uses for bug-fixing, issue intake, and confirming a change is actually wired in, invoked **by name** with your agent tool's skill/subagent mechanism | Naming beats paraphrasing. An orchestrator who writes the principles of a skill into a brief by hand instead of naming it drops whatever they did not happen to remember, and it drops silently. |
| Run long steps in the foreground, with an explicit long timeout, never backgrounded on the assumption something will notify you when it finishes | Nothing notifies an agent when a backgrounded step ends. Agents have stalled for entire turns "waiting for the build to finish," polling a task that will never wake them, while their real work sat uncommitted. |
| Commit on your branch, then stop | Uncommitted work dies with the agent. A branch with three small commits merges exactly like a branch with one; the only thing an uncommitted working tree buys is the chance to lose it. |
| Run only the tests that cover what you touched, never the full suite | Several agents each running a full test suite at once saturates a single machine badly enough that unrelated things start failing for reasons that have nothing to do with any agent's actual change. See `parallelism.md`. |
| Never merge, under any circumstances | The orchestrator owns the merge and verifies the diff before it lands. A worker that merges its own branch has removed the one checkpoint the whole model depends on. |
| Never close an issue or ticket | The orchestrator closes it on merge, not before. An agent that closes an issue for an unmerged fix creates a "closed but not actually done" state that looks identical to "done" until someone goes looking, which is usually much later and usually the hard way. |
| Never `git stash` while more than one workspace is active on the repository | Multiple worktrees of one repository share a single stash stack. Two agents stashing in the same window can pop each other's changes; their working sets swap without either agent doing anything wrong. Give the alternative in commands (see `wave-brief.md`), not just the ban, or the ban loses to the reflex the first time an agent wants to set something aside. |
| Never kill a process by image name; kill only process IDs you started yourself | Killing "all python processes" or "all node processes" to clean up a lane's own test server has killed the operator's own running application and other agents' runs in the same stroke. Record the PID at spawn and kill only that PID. |
| Stop and report if your workspace contains changes you did not write | This has paid for itself directly: an agent found another agent's in-flight work sitting in what it expected to be a clean workspace, stopped, and asked, instead of checking out over it and destroying it. |
| The one observable that would differ if this change were wired to nothing | Code that compiles, passes its own tests, and does nothing at runtime is one of the most expensive recurring bug classes in agent-built software, because nothing in a narrow test suite ever exercises the real caller. A brief that does not name a concrete, checkable observable gets a report that says "done" and means "the code exists." |
| The exact report format required (see `wave-brief.md`) | Free-form reports get read unevenly, and the two or three lines that actually matter to a merge decision get buried in narration the orchestrator has to sift through. |
| "Do not narrate. Only your final report is read, by the orchestrator; spend no tokens on progress prose, restating this brief, or announcing what you are about to do." | The orchestrator's own context is the scarce resource in a wave (see `context-and-handoff.md`). Narration is tokens spent on nobody: nobody reads a worker's transcript except the orchestrator scanning for what went wrong, and only after something already looks wrong. |

## The lane-specific part: fields to fill on every dispatch

```
First action: read <path to your standing wave-brief file> in full and
follow it exactly. Everything below is lane-specific and adds to it; it
never overrides it.

YOUR WORKSPACE: <worktree path or workspace identifier>
YOUR BRANCH: <branch name, already created/checked out there>

YOUR SCOPE, and nothing else: <the files or directories this lane owns>.
Other lanes in this wave own: <name the other lanes' scopes, even if they
look unrelated>. Do not edit those; report a collision instead.

WHAT I ALREADY KNOW: <facts you have checked, theories you have ruled out
and why, anything already disproved. An agent that re-derives this has
burned its cold start for nothing.>

THE TICKET/ISSUE BODY MAY BE WRONG: <say so explicitly whenever there's
reason to doubt the proposed fix, and say what to verify instead.>

THE FALSE PASS TO AVOID: <what the obvious check would miss; see
dispatch-patterns.md. This is worth more than a description of the feature.>

RULES THAT APPLY HERE: <the subset of your project's rules this lane's
files actually touch, not the full list.>

THE ONE WIRED CHECK: <the single observable that would differ if this
change did nothing.>

MODEL: <set in the dispatch call itself, chosen per dispatch-patterns.md's
table, not defaulted.>
```

## What not to put in the lane-specific part

Do not re-explain anything the standing file already says. If you find
yourself writing "and also, never git stash" into a lane-specific brief,
that is a signal the standing file did not do its job, or that you have
stopped trusting it, either of which is worth fixing at the source rather
than patching around per dispatch.

## A worked example of the split

Standing part (read once, from `wave-brief.md`): every ban, the report
format, the "do not narrate" instruction, the skill names.

Lane-specific part, filled in for one real dispatch:

```
YOUR WORKSPACE: worktrees/wave-4/rate-limit-fix
YOUR BRANCH: agent/rate-limit-fix

YOUR SCOPE: src/middleware/rate_limit.py and its test file only. Another
lane in this wave owns src/middleware/auth.py; do not touch it even though
both files sit in the same directory.

WHAT I ALREADY KNOW: the limiter's counter resets on process restart, not on
a rolling window, which is why the reported symptom (limit resets early
under load) looks like a race but isn't; I traced this by reading the
counter's storage backend, not by reproducing it.

THE TICKET SAYS to add a lock around the counter increment. That will not
fix a per-process counter reset; verify the storage backend first.

THE FALSE PASS: a test that hits the endpoint once and checks it isn't
rate-limited proves nothing about the reset behavior. Prove the counter
survives a restart, not that one request goes through.

THE ONE WIRED CHECK: after your fix, restart the process mid-window and
confirm the counter value, not just the limit's exists in config.

MODEL: mid-tier (real mechanism to find, ticket's proposed fix is wrong).
```

Notice what is absent: no restatement of the stash ban, the image-name kill
ban, the report format, or "do not narrate." Those live in the standing
file, read once, and this brief does not repeat them.

## Keep the standing file current, not the prompts

When a wave surfaces a new failure mode, whether that's a new hard ban, a
new required check, or a rule that turned out to be wrong, the fix belongs
in the standing file, not in that session's remaining prompts. A rule that
only lives in one conversation is a rule the next wave pays to relearn.
