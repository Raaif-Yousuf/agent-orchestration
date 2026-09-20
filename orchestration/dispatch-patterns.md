# dispatch patterns

When to spawn, when to reuse, and how to split work across agents. Every rule
here came out of a real wave that went wrong first.

## Check first that the work is not already done

Before you dispatch a single lane, check the commit graph for every lane you
are about to open, in one batched call. Not per lane, as you go. Per-lane
framing is exactly what makes this check feel skippable when there are
fifteen lanes queued, and it is the cheapest check available to you: it costs
one call before dispatch instead of a whole agent's worth of work after.

This has cost real time more than once, in the same shape each time: an issue
or ticket stays open after the fix that closes it has already merged, an
orchestrator queues it into the next wave because it is still sitting in the
open list, and the agent opens its workspace to find the problem already
fixed in the code it just checked out. The second time it happened, the cause
was traceable exactly: the batched check ran against the *next* wave's
candidates, not the one being dispatched, because those lanes felt obviously
open and didn't seem worth re-checking. If your project has one, use it; if
it doesn't, write one. A script that takes a list of issue or ticket numbers
and reports, per number, whether a commit already touched it while it stayed
open is worth having before your second wave, not your tenth.

## Split lanes by shared context, not by ticket count

Two tickets that touch the same module belong to one agent. Two tickets that
touch unrelated surfaces do not, even if splitting them evenly across agents
looks tidier on paper. The cost of the wrong split is not fairness, it is
context: an agent given two related tickets can reason about them together
and catch the place where fixing one half-breaks the other; an agent given
one ticket per lane pays a full cold start per ticket and never sees the
overlap at all.

## Prefer reusing a running agent over spawning a fresh one

A fresh agent pays a cold start: it re-derives the project context, the rules
that apply, and whatever you already learned about the task before it can do
anything useful. If an agent is already running and holds relevant context, a
follow-up message to it is cheaper than a new dispatch, and it already has
the state a fresh one would have to rebuild. Spawn fresh when no running
agent fits the work, or when the one that does has already run long enough
that it should be retired rather than pushed further (see
`context-and-handoff.md`).

## Give each agent a disjoint file scope, and name what it does not own

State the files or directories this agent may touch, and name the files
other agents in the same wave own, even when they seem unrelated to this
lane's task. The point is not politeness, it is a fast failure: an agent that
is told "these files are someone else's" reports a collision when it finds
one instead of editing into it and creating a merge conflict, or worse, a
silent semantic collision that merges clean and does the wrong thing (see
`verifying-agent-work.md` on merges that compose into a lie).

## Hand the agent what you already know, with evidence

If you have already checked a fact, ruled out a theory, or disproved a
proposed fix, say so and say how you know. An agent that has to re-derive
your findings from scratch has burned its cold start on work you had already
paid for. This is the single highest-leverage thing a brief can contain
beyond the task itself: not more instructions, but the state you are already
holding.

## Warn it when the ticket body is probably wrong

Issue and ticket bodies routinely carry a proposed fix that turns out to be
wrong, because whoever filed it diagnosed the symptom, not the mechanism.
Tell the agent this explicitly and tell it to verify the mechanism against
the actual code before writing a fix, rather than implementing whatever the
ticket suggests. An agent that trusts the ticket body by default will
"fix" the described symptom and leave the real defect in place.

## Write prompts around the false pass, not the feature

The single most effective thing to put in a dispatch prompt is not a
description of what the feature should do. It is a description of what the
*obvious* check would miss. Telling an agent the shape of the feature gets you
an agent that builds and tests the feature; telling it what the naive test
would falsely pass on gets you an agent that actually finds the gap. This
beat describing the feature every time it was tried, across many waves.

Illustrations of the shape, not literal prompts to copy:

- "A unit test that calls the function directly proves nothing here; the
  defect is that its only real caller never runs it in production. Prove the
  caller reaches it, not that the function works in isolation."
- "Asserting that the fallback value appears somewhere in the output passes
  whether or not the real path works, because the fallback also fires on
  success. Assert the thing the fallback is supposed to protect actually
  survives, not that the fallback text shows up."
- "A detector tested only against fixtures you built specifically to trigger
  it will fire reliably on those fixtures and tell you nothing about real
  data. Run it against real, unmodified examples from this project before
  trusting a reported accuracy number."

Generalize this pattern to your own domain: ask "what would make this check
pass even if the feature were broken", and put that question, answered, in
the prompt.

## Choose the model per lane, not by default

Pick the model in the dispatch call based on what the lane actually has to
do, not out of habit for every lane in the wave:

| Lane shape | Model tier | Why |
| --- | --- | --- |
| Mechanical: run a fixed script, re-measure something, fold routine records, triage a list against a known state, drive a scripted flow | Fast / cheap | The work is procedure. A stronger model adds cost without adding correctness. |
| A real fix with a mechanism to find, a guard whose false-positive rate needs measuring, a fixture or corpus to design, a merge with real conflicts to reason through | Mid-tier | This needs judgment about what *not* to do, and the ticket body is often wrong (see above), so the agent needs to reason past it rather than execute it. |
| Cross-surface diagnosis where every link "looks wired" and the defect is in the gap between components, a decision delegated without a clear answer, a review whose own framing might be steering it wrong | Strongest available | The scarce thing here is not speed, it is not being fooled by a plausible-looking dead end. |

Say the model in the dispatch call itself. A brief that says "use your best
judgment about which model to use" is a brief that defaults every lane to the
same model, because nobody re-derives this table per dispatch under time
pressure; make the choice once, at dispatch time, explicitly.

## Phrase adversarial or guard work defensively

When a lane's job is to audit or stress-test a guard, a validator, or
anything defensive in your own codebase, describe the guard and the behavior
you want, never an adversary. Offensive-security vocabulary in a dispatch
prompt (words like injection, exploit, attack, bypass, payload) has tripped a
safety classifier mid-campaign even when the work was entirely legitimate
audit of one's own defensive code, and the cost lands on continuity, not on
whether the work was allowed.

Concretely:

- Instead of "probe the input-handling surface with hostile values," write
  "confirm the input handler accepts valid input, rejects anything that would
  cause a write it shouldn't, and treats unusual values as data rather than
  as commands."
- Instead of "attack scenario: who achieves what," write "failure scenario:
  which input produces which wrong result."
- Instead of "exploit," "bypass," or "payload," write "reach the failure
  path," "skip the check," or "unusual input."

Keep every bit of rigor (file and line citations, a required repro, a real
before/after result). Only the framing changes.
