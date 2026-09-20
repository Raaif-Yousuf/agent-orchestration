# context and handoff

The budget on both sides of a dispatch, and what a handoff has to contain to
be worth reading.

## A fresh agent pays a cold start

Every new agent dispatch re-derives context from scratch: the project's own
rules, the shape of the task, whatever has already been ruled out. That
re-derivation is not free, and it is the reason `dispatch-patterns.md` says
to prefer reusing a running agent over spawning a new one whenever a running
one already holds relevant state. It is also the reason to batch related
work into one agent instead of splitting it across several: two tickets that
touch the same module, handed to two different fresh agents, means paying
the cold start twice for context that only needed deriving once.

## Retire a worker at about half its context, not at exhaustion

Tell every worker, in its brief, to watch its own context usage and to stop
at a clean, committed point once it crosses roughly half. Past that point,
it is safer to hand the remaining work to a fresh agent (with a proper
handoff, see below) than to keep pushing the same one toward its limit. The
orchestrator generally cannot observe a worker's context usage directly, so
this has to be delegated: the instruction has to be in the brief, because
nothing else will catch it. A worker that runs itself to exhaustion instead
of stopping at a checkpoint risks losing whatever it has not yet committed,
and unlike a clean handoff, that loss carries no record of what was
attempted or why.

## The orchestrator's own context is the scarcer resource

A wave with ten workers has ten context budgets to spend, but only one
orchestrator context to spend them from, and it is the one that has to last
the whole wave: dispatching every lane, reading every report, and verifying
every diff before merge. Protect it deliberately:

- Workers report outcomes, numbers, and file paths, not narration. A report
  that says "I looked at the config file, then I checked the tests, then I
  decided to..." costs the orchestrator's context to read and gives back
  nothing a diff would not show faster.
- Nobody but the orchestrator reads a worker's transcript, and even the
  orchestrator only does so when something in the final report already looks
  wrong. Treat the transcript as write-only under normal conditions; if a
  worker is producing content on the assumption someone is watching it
  unfold in real time, that assumption is costing tokens for no reader.
- When the orchestrator finds itself thinking "I'll just do this bit
  myself" mid-wave, that is worth noticing rather than acting on
  reflexively: the orchestrator's context is exactly what the delegation
  model exists to protect, and doing a worker's job by hand spends it on
  work a worker could have done in its own, separate budget.

## What a handoff must contain

Whenever a worker is retired mid-task, or a wave is picked back up in a
later session, the handoff needs to answer four things without requiring the
reader to re-read the whole transcript: what is done, what remains, what
state it is in right now (branch, last commit, whether tests pass), and
anything learned along the way that the next agent or session would
otherwise have to re-discover. Use `templates/handoff.md` in this toolkit for
the concrete structure; this file is about the standard, not the form.

## Two things that look like isolation boundaries and are not

**A worker's scratch or scratchpad directory is not private to that
worker.** If multiple agents are given the same scratchpad path convention,
two of them can write to the identical file path in the same window, and one
agent's write can silently clobber or get attached to the wrong commit by
another. Do not treat a scratchpad path as a boundary between agents. If a
worker needs a place to put a throwaway file (a commit-message draft, a
probe script, notes to itself), it should write inside its own workspace,
under a path unique to that workspace, not into a directory conventionally
shared across the whole wave.

**A forked sub-agent is not isolated from the agent that forked it.** A fork
inherits the parent's full context, which is exactly what makes it feel safe
to use for "just a quick read-only check," but it also shares the parent's
working tree and its git identity. Nothing about "read-only" in a fork's own
prompt is enforced anywhere: a fork told not to write code can still write
code, and if it commits, that commit is indistinguishable in history from
the parent's own. This has actually happened, more than once, from an agent
that was never asked to spawn anything: a worker dispatched its own fork for
what it called read-only research, and the fork wrote real source, added
files, and committed all of it onto the parent's branch under the parent's
identity. If a worker genuinely needs more hands, the answer is to say so in
its report and let the orchestrator decide, not to reach for a fork on the
assumption that "isolated" in the name means isolated in practice.

## What "about half" actually means in practice

Do not wait for a hard number from your tooling before treating this as
real. "About half" is a judgment call a worker makes about itself: has it
read and reasoned over roughly as much as it usefully can before quality
starts to degrade, is it repeating itself or re-reading files it already
read, is the task's remaining scope still larger than what it has already
covered. Any of those is closer to the retirement point than a worker
mid-task tends to admit, because stopping feels like giving up on nearly
finished work. It is not: a clean commit and an honest handoff at 50% is
worth more than a worker pushing to 90% and running out mid-edit with
nothing recoverable. Bias toward stopping early rather than late.

## Two sessions is a context problem too

If more than one orchestrating session is active against the same
repository at once, each one is working from a partial and possibly stale
view of what the other has already done, merged, or decided. That is a
handoff problem at the level above individual workers: the fix is the same
in kind, an explicit statement of what is owned by whom and what state
things are in, agreed once rather than assumed. See `parallelism.md` for
the concrete tell that this has happened and how to split ownership once it
has.
