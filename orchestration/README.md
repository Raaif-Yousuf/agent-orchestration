# orchestration

I run several coding agents in parallel on one repository, and this section is
the practice that makes that survive contact with a real machine instead of
quietly rebuilding finished work, swapping two agents' files, or merging
something nobody actually checked. If I kept only one section of this
toolkit, it would be this one. Everything here came out of a real wave going
wrong in a specific, recorded way, not out of a diagram.

## The model

One orchestrator, several workers. The orchestrator owns direction (what gets
worked, in what order, and whether it needs doing at all), verification
(checking a worker's claim against the diff, never against its report alone),
and the merge (nobody else touches the trunk branch). A worker owns exactly
one workspace and one branch: it reads the brief it is given, writes code,
runs only the tests that cover what it touched, commits, pushes its branch,
and stops. It never merges, never touches another worker's workspace, and
never dispatches sub-agents of its own. Almost every failure mode recorded in
this section is one of those two roles quietly doing the other's job: an
orchestrator hand-writing what a shared brief should have said and dropping
half of it, or a worker deciding it can spawn its own helper because the task
"is basically read-only."

Workers run in their own isolated workspace, one per branch, so that two
agents editing at once cannot collide on the same working tree. I use git
worktrees for this; nothing here depends on that specifically, but the
isolation itself is not optional, because two agents sharing one working
directory is how one agent's in-progress edit becomes another agent's typo.

## What is here

- [`dispatch-patterns.md`](dispatch-patterns.md): when to spawn a fresh agent
  versus send a follow-up to one already running, how to split work into
  lanes, how to pick a model per lane instead of defaulting every lane to the
  same one, and how to phrase adversarial or guard work so it describes a
  behavior instead of naming an adversary.
- [`worker-brief-template.md`](worker-brief-template.md): the copy-pasteable
  brief, split into a standing part every lane shares and a lane-specific part
  written fresh each time, with a table of what the standing part must
  contain and why each line earns its place.
- [`parallelism.md`](parallelism.md): how many agents to run at once, why
  that number is a negotiated ceiling rather than a fixed setting, and the
  specific ways a wave goes wrong when too many agents compete for one
  machine.
- [`context-and-handoff.md`](context-and-handoff.md): the context budget on
  both sides of a dispatch, when to retire a worker rather than let it run to
  exhaustion, and what a handoff has to contain to be worth reading.
- [`verifying-agent-work.md`](verifying-agent-work.md): the merge side, where
  most of the value in this section lives. A wave that dispatches well and
  verifies badly still ships broken work; a wave that dispatches carelessly
  and verifies well just costs more time.
- [`wave-brief.md`](wave-brief.md): a ready-to-copy standing brief, written
  project-agnostic with placeholders. This is the file every lane-specific
  brief points to as its first line, instead of retyping the same rules into
  every dispatch.

## How to use this section

Read `dispatch-patterns.md` and `parallelism.md` before your first wave.
Drop `wave-brief.md` into your own repository, fill in its placeholders once,
and point every worker brief at it. Read `verifying-agent-work.md` before you
merge anything, not after something has already gone wrong. When a wave finds
a new way to fail, the fix belongs in these files, not in that session's
prompts; a lesson that lives only in one conversation is a lesson the next
wave pays for again.

## Where this came from

The shape is not mine. The orchestrator-worker pattern, and using isolated
workspaces so parallel agents cannot step on each other's files, both come
from outside practice. See `docs/sources.md` for the full list; the load-
bearing ones are Anthropic's writeup on building effective agents (the
orchestrator-worker pattern by name), the Claude Code sub-agent documentation
(context isolation, how a subagent is invoked and resumed), OpenAI's practical
guide to building agents (the manager pattern, delegating through tool
calls), and the public `superpowers` skill set for Claude Code (parallel
agent dispatch and git-worktree isolation as composable skills rather than
one-off scripts).

What is mine, built up over real waves and kept because it kept paying for
itself even after I got tired of writing it down again: the standing
wave-brief as a single file every brief points to instead of being retyped
per lane, on the theory that a paraphrase silently drops whatever I did not
happen to remember while still looking complete; writing prompts around the
specific false pass an obvious check would miss, rather than around what the
feature looks like; choosing the model per lane by what the lane has to do
instead of defaulting every lane to one model out of habit; and the
verification checklist in `verifying-agent-work.md`, the specific set of
things I now check on every merge because an agent's report has been wrong
about each one of them at least once.
