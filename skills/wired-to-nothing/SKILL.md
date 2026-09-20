---
name: wired-to-nothing
description: Use before reporting any feature, fix, or wiring change as done. Also use when a fix "should work" but the reported symptom persists, or when reviewing a change that adds a handler, hook, route, config flag, or installer step.
---

# Wired to nothing

The bug class: code that compiles, runs, passes its tests, is reviewed as
correct, and does nothing at runtime, because nothing in the running system
calls it. A handler registered nowhere. A hook whose effect never fires
because its dependency mounts on the wrong render. A route no client ever
requests. A config flag read by nothing. An installer step that never
actually runs on a real machine.

This is the single most expensive recurring bug shape on real, measured
work, and it is structural, not a matter of carelessness: a unit test
supplies the caller that production is missing. The test mounts the thing
and calls it directly, which is exactly the step that is absent in the real
system. So a green suite is not evidence against this bug; it is often the
delivery mechanism for it.

## The one rule

Before you say a change is done, name the single **observable** that would
differ between "this works" and "this is wired to nothing", and go check
that observable. Not the test suite. Not the diff. Not a trace of the call
sites. A thing you can actually see: a rendered string, a log line, a row
that appears in storage, a process that exits differently.

If you cannot name that observable, you do not yet know whether the work is
done. Say so, plainly, instead of reporting success.

## Check by shape

Match what you changed to a row below and run the check. Grep the consumer
side, not the definition, in every case: the definition existing is never
the question.

| You added/changed | The check |
|---|---|
| A backend route | Grep the client code for the literal path. A route nothing calls compiles, runs, and passes its own tests while being completely unreachable. Then assert the route is actually **mounted** on the running app object, not just defined in a file that imports cleanly. |
| An internal module or library function | Grep the whole tree for imports of it outside its own test file. If only its own test imports it, it is unreachable in production. |
| A hook, callback, or event handler | Grep the **consumer** side, not the definition. A hook can have tests and callers listed in the diff and still be a no-op, if the thing it depends on (a ref, a mount, a subscription) is not actually present when it runs. |
| A UI control | Trace it forward to a value that actually leaves the component (a network call, a stored preference, a prop passed down). A visible, clickable control that reads or writes nothing is not wired just because it renders. |
| A config flag or dependency-driven behavior | Read the pinned dependency's actual source, not its documentation. Defaults change between versions and the doc lags. |
| An installer or packaging step | Run the real packaging tool end to end and inspect its output, not just its exit code. Packaging tools frequently succeed while silently omitting or truncating what you told them to include. |
| A packaged-build-only behavior | Grep the **compiled or bundled output**, not the source. Source correctness says nothing about what actually got bundled. |
| A parameter threaded through several layers | Confirm the value is actually **different** at the destination, not just present. Two call sites that both read the same shared default can both look "wired" while the parameter changes nothing. |
| A generated artifact (export, document, report, stored record) | Read the artifact back with a real reader for its format, never the generator's own return value. Read the produced value alongside any warning or log the code emitted about it; some defects are only visible when both are read together. |
| A hard-coded list or roster | Grep for sibling copies of the same list elsewhere in the tree. The entry you added can be completely real while a duplicate roster nobody grepped for still lacks it. |

## Smells that mean "check harder"

- The fix is one line and the symptom was dramatic.
- It passed on the first run with no surprises.
- You are about to write "should now work" instead of "does work".
- The file you changed is one whose tests all mount it directly, with no
  path from a real entry point.
- Nothing you can point to actually observed the new behavior; you inferred
  it from reading the code.

## When the fix "should work" but the symptom persists

Stop adding fixes. A reported symptom is often two or three independent
causes stacked, and fixing the first one hides the rest without resolving
anything. Re-run the exact same action and check whether the observable
moved at all. If it did not move even slightly, the fix you just wrote is
not partially working, it is not running.

Record the mechanism honestly: `MEASURED:` plus what you actually observed,
or `THEORY (unverified):` if you have not confirmed it. When you disprove an
earlier theory, replace it rather than leaving both written down.

## Shape: an optional parameter no caller ever sets

A parameter with a sensible default is invisible in this class, because the
default makes the missing caller look like a deliberate choice. For any
optional input that changes output, grep the calling code for the field
name. A field only a test ever sets has no real caller, and every consumer
of the feature is silently getting the default forever.

## Shape: parallel work that each exports a hook nobody imports

When a feature is split across several people or agents working the same
surface in parallel, each slice's own test suite goes green, each slice
merges cleanly, and the merged whole can still be dead: slice A assumed
slice B would call it, slice B assumed the reverse, and neither test caught
it because each test supplied the caller the other slice was supposed to
provide. The merge of split work is not done until one real observable
crosses every seam the split created, driven end to end, not per slice.

## Shape: a constant that documents a behavior nothing implements

A named constant with a long, careful comment describing the behavior it
controls is weak evidence that behavior exists, and a confident comment is
actively misleading because it discourages the reader from checking. Grep
for who **reads** the constant, not who documents it. If the only consumer
is a test that recomputes the same formula inline and checks the two agree
with each other, that test is an identity, not a test: it can never fail
for the reason you care about, because it never calls the real function.

## What honest reporting looks like

State which observable you checked and what it showed. If you could not
check one (no packaged build available, no way to drive a real browser, no
live external dependency), say that plainly and record it as an open
verification item instead of a done one. "Tests pass" is not evidence a
feature is reachable in production; it is the exact evidence this bug class
hides behind.
