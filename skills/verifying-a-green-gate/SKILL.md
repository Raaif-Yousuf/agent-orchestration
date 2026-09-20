---
name: verifying-a-green-gate
description: Use whenever you add, inherit, or rely on a guard, gate, ratchet, or CI check, and whenever a check reports success on something you have not personally watched fail. Also use before trusting a green merge gate as proof a branch is safe.
---

# Verifying a green gate

A gate that is green because it works and a gate that is green because it
is dead are indistinguishable from the outside. The only way to tell them
apart is to force the condition the gate exists to catch and watch it turn
red. This is the strongest and most repeatedly useful discipline in this
set: on real work, forcing every guard to fail on demand has turned up a
real coverage hole close to every time it has actually been tried.

## The failure family

A check whose failure mode is indistinguishable from success, or that
actively converts a failure into a positive signal, is strictly worse than
a check that crashes. A crash gets noticed and fixed. This gets trusted.

Recognizable shapes, all measured on real work:

- **A guard registered nowhere.** It exists as a file, has tests, and is
  never wired into the thing that runs at merge or CI time. It has been
  green from the day it was written because it has never actually run.
- **A scanner whose pattern silently stopped matching.** A regex anchor
  that cannot cross a line ending after a file's line-ending convention
  changed; a glob that stopped matching after a directory moved. The
  scanner's own "remaining count" then reads exactly like a shrinking
  backlog, which is the worst possible failure mode: it looks like
  progress. Only a vacuity assertion (the scanner must find at least
  roughly the expected number of real matches) catches this.
- **The exit code of a compound shell command.** `cmd > log 2>&1; echo $?`
  reports the status of whatever ran last, not of `cmd`. A background
  wrapper that relays "exit code 0" for a run that never executed, or whose
  own log ends with an explicit failure line, has happened on real work
  more than once. Read the tool's own last-line output or its own
  machine-readable verdict file. Never trust a relayed exit code for a
  backgrounded or piped command.
- **A test double narrower than what it stands in for.** A mock, stub, or
  fake that accepts a shape production would reject (or vice versa) makes
  every test that uses it structurally unable to see a whole class of real
  bug.
- **A mutation arm that stays green.** In a multi-part fix or guard, revert
  each part independently. Every part that stays green when reverted is a
  part no test can see. This is a finding to report and close, never a
  pass.
- **A hand-maintained denominator.** A guard that checks "every X is
  covered" against a manually maintained list of known X's cannot see the X
  nobody added to the list. The list and the guard drift together and
  agree with each other by construction.
- **A check that cannot fail by design.** A verifier that shares its core
  matching logic with the thing it verifies will confirm the thing's own
  mistakes with full confidence, because they are, in effect, the same
  check asked twice. A presence-only assertion (`"key" in result`) on a
  computed value can pass while the computation behind it silently broke.

## The practice

For every guard you write, inherit, or are about to rely on:

1. **State what it is supposed to catch**, in one sentence, as a concrete
   bad state rather than an abstract property.
2. **Force that bad state on purpose**, in a scratch branch or a local
   revert. Not a hypothetical, an actual mutation of the actual code or
   data the guard reads.
3. **Watch it go RED**, and read the failure message. It must name the real
   problem, not just fail generically.
4. **Restore the good state and watch it go GREEN again.**
5. **If it stayed green in step 3, that is the finding.** Report the guard
   as blind, not as passing, and fix the guard before trusting anything it
   has ever reported.

This is the mutation-check recipe from `fixing-a-bug`, applied to gates
themselves rather than to a single fix. Do it once per guard, not once per
change the guard happens to see.

## Reading a merge or CI gate specifically

- **Never trust a relayed exit code from a backgrounded run.** Open the
  gate's own log and read its own last line, or its own machine-readable
  verdict output, if it writes one.
- **Structural gates (size ratchets, import-boundary checks, doc-drift
  checks) often only run at merge time, not in a single branch's own
  test run.** A branch's own green run is not proof the merge gate will
  also be green; run the merge gate itself before trusting a merge.
- **A raised baseline, widened allowlist, or regenerated snapshot is a
  claim, not a fix.** If a ratchet moved, the question is what was tried
  first, and whether the underlying thing actually shrank or the number was
  simply banked.
- **A large mechanical diff (a rename, a formatting sweep, a bulk rewrite)
  should be checked for symmetry, not sampled.** A rewrite that is supposed
  to be one line out, one line in per file is checkable with a line-count
  diff across every changed file; anything asymmetric must be explainable
  as a deliberate addition, and if it is not, content was silently dropped
  somewhere in the sweep.

## Red flags

- "It's been green for a while, it must be fine": a check that has never
  been forced to fail has never actually been tested itself.
- "The count went down, that's good news": a shrinking count from a
  scanner is exactly what a scanner going blind looks like from outside.
  Confirm the scanner can still see a planted violation before reading a
  falling number as progress.
- "The exit code says zero": for anything backgrounded or piped, read the
  tool's own output instead.
- "Every mutation arm passed": a green arm is a coverage hole, not a pass.
- "I regenerated the baseline to make it pass": ask what actually changed
  underneath, not just what number now satisfies the check.
