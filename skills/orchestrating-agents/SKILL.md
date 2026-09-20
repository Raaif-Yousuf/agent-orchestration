---
name: orchestrating-agents
description: Use when dispatching work to multiple subagents, writing a worker brief, deciding how many agents to run at once, or merging an agent's branch back in. Also use when an agent reports work as done or an agent goes quiet.
---

# Orchestrating agents

This is the trigger and first-moves layer. The detail (brief templates, the
standing rules every worker gets, the merge sequence) lives in
`orchestration/README.md` and `orchestration/worker-brief-template.md`; read
those before writing a real wave brief. This file is what to do before you
open either.

You are the orchestrator: agents do the work, you decide direction, verify
what they claim, and own the merge. Nothing below is hypothetical; every
rule here exists because skipping it cost real time on real work.

## Before you dispatch anything

**Check whether the work is already done, for every lane, in one pass,
before dispatching a single agent.** Search the commit graph for each
lane's identifier before assuming any of them are open. Do this for the
wave you are about to dispatch, not the next one you are planning; a lane
that "obviously" needs doing is exactly the one that turns out to be
finished already.

**Split lanes by shared context, not by ticket count.** Two tasks that
touch the same module or the same file belong to one agent, sequentially;
two tasks touching unrelated surfaces belong to separate agents, in
parallel. Splitting by headcount instead of by what each task actually
touches is how two lanes silently step on the same file.

**One worktree and one branch per agent, always.** Never point two agents
at the same worktree, and never let an agent work in the primary checkout.
`git stash` is banned the moment more than one worktree is active, because
a stash is shared across every worktree of a repository and two agents
stashing in the same window can swap their working sets. See `fixing-a-bug`
for the safe revert-check alternative.

**Name the skills the worker must invoke, by name, with the tool that
invokes them.** Do not paraphrase a skill's content into the brief instead.
A paraphrase silently drops whatever you did not happen to remember, and it
drops it invisibly, the same way a guard that looks complete but runs
nothing is invisible until forced. If the work touches a bug fix, name
`fixing-a-bug`. If it touches anything that will be reported as done, name
`wired-to-nothing`. If it touches a tracked issue, name `working-an-issue`.

**Cap concurrency by what keeps the machine usable, not by how many lanes
you have.** Ask what the ceiling is rather than assuming; running full test
suites concurrently across several agents can saturate a machine badly
enough that unrelated commands start failing on timeouts, and a starved
worker looks exactly like a real failure from the outside.

## While they run

Agents stall waiting on their own background tasks more often than they
stall on anything else. When one goes quiet, check the actual process or
log yourself and send back the fact, not an encouragement: "the build
finished four minutes ago, here is its size and timestamp, stop polling and
run the remaining steps now."

Never kill a process by image name. Only kill process IDs you started
yourself; a wide kill takes down other agents' work and the operator's own
running processes along with the one you meant to stop.

If an agent's worktree contains changes it did not write, that agent should
stop and report it rather than checking out over someone else's in-flight
work.

## Verifying what they report

Check the claim against the actual diff, not the agent's narration of the
diff. An agent's report describes what it intended to do; it is not proof
of what it did. Read the tests it wrote well enough to know what they
actually assert, not just how many there are: a test can assert the
reported bug as correct behavior and still count toward a passing total.

For a diff you are not confident about, use a dedicated review agent
(`cold-diff-reviewer`) rather than re-reading it yourself under the same
framing you already have. Give it only the diff and the file paths, nothing
about the ticket or your own theory of the fix: framing is exactly what
makes a reviewer agree with a broken diagnosis, and handing over your own
theory first spends the independence that a second review exists to buy.

## Merging

The orchestrator owns the merge, always. Merge one branch at a time and run
the full merge gate after each one, reading its own output rather than a
relayed exit code (see `verifying-a-green-gate`). Never let a worker agent
merge its own branch, open a pull request on its own behalf, or close the
issue it worked; those are integration decisions and they belong to
whoever is watching the whole set of lanes, not to the lane that happened
to finish first.
