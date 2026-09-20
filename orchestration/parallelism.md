# parallelism

How many agents to run at once, and why the honest answer is not a number.

## The cap is a negotiated ceiling, not a setting

Whatever concurrency limit gets named at the start of a session is a starting
point, not a fixed ceiling for the rest of the day. It moves, usually upward,
the moment the person running the wave sees how much work is actually
queued, and a raise given for one wave is usually good for that wave only. Do
not carry a one-off raise forward into the next wave as if it were the new
default; ask again if it matters, or default back down.

Two small rules that save real back-and-forth:

- **Ask once, then take what you are given.** Do not re-litigate the number
  mid-wave unless the facts on the ground changed (see the failure modes
  below). Repeatedly asking about a limit that was already answered is its
  own kind of waste.
- **When one instruction names two numbers, take the lower one.** "No more
  than five at once, but let's start with three" means three. This comes up
  more often than it sounds like it should, usually because the number gets
  revised downward in the same breath it was given.

## The real constraint is not agent count

Agent count is a proxy. The actual constraint is concurrent resource use on
one machine, and the resource that runs out first is rarely the one that
looks alarming. Several full test suites running at once can saturate a
single development machine badly enough that things with no logical
connection to any agent's work start failing: network calls time out, a
test runner that normally finishes in well under two minutes takes four
times as long, and along the way you get collection errors and failures that
have nothing to do with any real defect, purely from resource contention. On
one measurement, a suite that normally ran in about 95 seconds took about
376 seconds under four concurrent agents, with collection errors and
phantom failures showing up that were not present on a quiet run of the same
code. Free memory is also a poor gauge on its own: a machine can show
comfortable free physical memory right up until whatever the operating
system actually enforces as its limit (committed memory, not free RAM, on
a machine with a page file) is nearly exhausted, and the two do not move
together in a way that gives you useful warning. If you have a way to watch
the thing your OS actually enforces rather than the number that merely looks
scary, watch that instead.

The number of agents matters only insofar as it drives this. Ten agents that
each run one fast, narrow test file are lighter on a machine than two agents
each running a full suite.

## The rule that follows from this

Agents run only the tests that cover what they touched, never a full suite,
and never with a test-parallelism flag that multiplies one process into
several (an `-n auto`-style flag is not "targeted," it is a multiplier on top
of a targeted run, and it turns one agent's careful narrow selection back
into the exact contention problem the narrow selection was meant to avoid).
The orchestrator runs the full suite exactly once, alone, after the wave's
merges are done, with no agent still working. This is not a courtesy, it is
the only way a full-suite result means anything: a full suite run while
agents are still active can fail from contention and look exactly like a
real regression, or pass by luck and hide one.

## Failure modes of running many agents at once

**Agents stall waiting on their own background jobs.** An agent that starts
a long build or test run in the background and then ends its turn "waiting
for it to finish" has stalled: nothing wakes it when a backgrounded job
completes, and it will sit there, sometimes reporting the same "still
waiting" status repeatedly, while its actual work sits uncommitted. The fix
is not to tell it to keep waiting; check the process yourself, and send it
the facts: the job is done, here is what came out of it, stop polling and
run the remaining steps in the foreground. Do not just say "continue" and
hope it re-orients; a stalled agent needs the concrete state, not
encouragement.

**An orphaned background job outlives the agent that started it.** An agent
can finish its task, report, and still be quietly holding a long background
run alive, one it may have judged not worth blocking on but never actually
stopped. That job keeps consuming machine resources long after the agent
that could account for it is gone, and it competes directly with whatever
the orchestrator runs next, including the full-suite verification run this
whole model depends on running clean. Check for processes tied to a
worktree or lane after every agent reports done, and kill anything still
alive by its process ID, never by image name (see `worker-brief-template.md`
on why image-name kills are banned outright). Put the instruction to finish
or kill background work before reporting into every brief, positively
phrased ("do not leave a long job running when you finish"), because a ban
with no replacement instruction loses to the reflex of just letting it run.

**Two sessions, or two machines, working one repository at once duplicate
work.** If more than one orchestrating session might be touching the same
repository, check for that before you touch the trunk branch. The
tell is subtle: a merge that answers "already up to date" for a branch you
verified minutes earlier was not yet merged, or the trunk branch moving
without a commit you made. Neither session is wrong to be there, and the
answer is not to race. Split ownership explicitly: one session owns every
merge and the trunk branch; the other owns dispatch and lane work only,
handing over finished branches as a list rather than merging them itself.
Whichever session is actively merging gets to set the concurrency number for
both, because a starved merge gate that flakes and retries under load looks
exactly like a real failure, and their queue is finished work while the
dispatching session's is not. The same shape, one layer further out: two
separate machines working the same backlog without syncing first will
independently rebuild the same fixes, sometimes as two different, both
individually correct, changes to the very same function that then merge
without a single conflict and combine into something that is wrong in
combination. A clean merge is not proof that nothing overlapped; see
`verifying-agent-work.md`.
