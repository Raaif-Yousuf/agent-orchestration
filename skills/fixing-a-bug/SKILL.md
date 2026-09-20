---
name: fixing-a-bug
description: Use before writing any fix for a reported bug, regression, or defect, before trusting the issue's proposed fix, and whenever a green test suite coexists with a symptom that is still real.
---

# Fixing a bug

A green test suite is not evidence. Code that compiles, runs, passes its
tests and does nothing at runtime is a recurring, expensive bug class on
real work (see `wired-to-nothing`), and no test has ever caught an instance
of it alone; every one needed a targeted manual check. Suites have also
shipped tests that assert the bug as intended behavior, and mutation checks
green enough to mean no test can actually see the fix.

The order below exists because each step catches a failure the next one
cannot. Do not reorder it.

## The order

1. Write the failing test first, at the symptom level.
2. Watch it fail, and read the failure message.
3. Broaden it into a small matrix.
4. Mutation-check: break the code on purpose, confirm the tests go red.
5. Narrow the cause: whole repo, to a few files, to roughly a hundred lines.
6. Fix it.
7. Revert-check: undo the fix, confirm the new tests fail, restore.
8. Full green on the targeted tests, plus the repo's fast guard set.

## 1. Failing test first, at the symptom level

Write the test from the reported observable, not from your theory of the
cause. State it as an assertion a user would recognize ("a valid input is
rejected", "the second run produces a different total than the first"), not
as an assertion about internal state you have not yet inspected.

If you cannot write a failing test from the symptom, that absence is itself
the finding. Say so, name what makes it unreachable (needs a packaged
build, needs real hardware, needs a live external service), and record it
as an open verification item. Then narrow the cause manually and come back.
Do not skip straight to fixing because the test was awkward to write.

## 2. Watch it fail, and read the failure

Not "it errored." The message has to describe the real defect. A test that
fails on an `ImportError` or a broken fixture of your own making is not yet
testing anything.

Doubt the harness before you doubt the product. Check the value as stored,
not as displayed (a terminal can mangle an encoding while the underlying
value is fine). Check your fixture still exists at the point you assert
against it; an earlier trimming step can silently strip the row your test
depends on.

## 3. Broaden into a matrix

One reproduction is an anecdote. Sweep the dimensions the bug plausibly
lives in, and assert against the stated rule, not against whatever the code
currently does. Ask what else is on this axis: other sizes, other
categories, empty input, the largest realistic input, the value that is
`None` rather than simply absent. A targeted single-case fix has repeatedly
turned out to leave a second, worse case in the same family untouched.

## 4. Mutation-check: break the code on purpose

Mandatory, not optional. Before trusting any test or guard, damage the
production code on purpose and confirm the test goes red with a message
that names the real problem. Then restore it.

For a guard with several independent conditions, prove every one fires on
its own. **An arm that stays green is the finding, not a pass.** A green
arm means no test can see that part of the change at all, and that has
turned up real coverage holes essentially every time it has been tried.

Assert the value, never mere presence. `"x" in call.args` can pass with the
real argument deleted, because a stub's own default happens to supply the
same key. A count assertion whose only possible outcomes are "the expected
count" and "zero" is not an assertion; if the broken version produces zero
matches for the thing being counted, `<= 1` is satisfied by a total absence
just as easily as by a correct single match.

Every scanner needs a vacuity check: if it walks files or matches patterns,
assert it found a plausible number of them. A scanner that silently matches
nothing reports a clean tree forever, and that is worse than reporting
nothing at all, because it is trusted.

An isolated repro built to skip a slow end-to-end path needs the mirror
image of a mutation check: a positive control. Prove it reproduces a result
you already know is correct before trusting a negative result from it, for
the same reason a mutation arm that stays green is not a pass: a repro that
cannot reproduce a known-good case is not exercising the path you think.

## 5. Narrow the cause

Only now go looking for the mechanism. Useful moves:

- Search history for when a specific literal or constant changed.
- Compare the failing input against the nearest input that passes.
- Check the pair, not each half separately: two independently correct
  values can still disagree with each other at the seam between them.
- Run the real path and inspect the real artifact it produces, instead of
  reading the code and reasoning about what it should produce; careful
  reading has repeatedly produced confident, wrong leads. Where the path
  produces an artifact, read it back with a real reader for its format,
  alongside any warning the code emitted, since some defects only show
  when both are read together.

A link-by-link trace of the call graph is not proof of anything. Every edge
in a chain can be individually present while the chain as a whole forms a
cycle that never actually fires end to end. Trace a fresh run, not a list
of links.

## 6. Fix it

Fix the cause you narrowed to, not the symptom. If the report proposes a
specific fix, verify the diagnosis yourself before trusting it: a reported
fix is regularly wrong, and treating it as ground truth wastes the steps
above.

Label the mechanism: `MEASURED:` plus what you actually observed, or
`THEORY (unverified):` if you have not confirmed it.

### If an existing test goes red against your fix, the test may be the bug

When a test's assertion **is** the reported symptom, the test itself is the
defect. This happens when a test was written to lock in a behavior that was
never actually correct. Replace the test in place and say so in the commit,
rather than shaping your fix to keep a wrong assertion green.

### Before writing a new helper, check these in order

This guards against one specific, expensive pattern: one concept
implemented twice, where one copy is wrong. It is not an argument against
building tooling; a purpose-built script often pays for itself repeatedly.

1. Grep for the concept's vocabulary, not the function name you were about
   to type: does it already exist somewhere in the codebase?
2. Is there an existing module or layer that already owns this
   responsibility, or a dependency already installed that does this?
3. Only then write it, and if you deliberately wrote a second
   implementation, say why in a comment next to it, so the next reader
   reads the pair as intentional rather than drift.

When you find the existing implementation, check that the two agree before
switching to it. The costly failure is never "we wrote it twice", it is
"we wrote it twice and they disagree by one edge case."

## 7. Revert-check

Undo the fix, run the new tests, confirm they fail, then restore. Do this
with the actual files, never with a stash: a stash is shared across every
worktree of a repository, and more than one agent doing a revert-check in
overlapping worktrees at the same time has swapped their working sets.

```
git diff > .scratch/fix.patch          # keep the fix
git checkout -- <the source files>     # revert ONLY the source, keep the tests
# run the targeted tests; they must go RED
git apply .scratch/fix.patch           # restore
git diff --stat                        # prove the restore is byte-exact
```

Report honestly which assertions failed and which passed anyway. An
assertion that passes both with and without the fix is a property
invariant, not a regression guard, and treating it as one is how a suite
quietly drifts into decoration.

If the test does not go red, the correct conclusion is not "the fix was
unnecessary" but "this assertion cannot see the difference; find one that
can." A component that repairs its own state on the next read (a stale
schema healed by a later migration, a self-correcting cache) reaches the
same end state whether or not the fix is present, because the self-heal
erases the evidence first. That needs a source-level assertion (the
production code no longer contains the removed pattern) instead of, or
alongside, a runtime-state one.

## 8. Green, plus the guard set, then the observable

Run the tests you touched, plus whatever fast structural guards the repo
has (import-boundary checks, size ratchets, doc-drift checks). Structural
gates go red at merge time as readily for a deletion as an addition. Never
raise a baseline just to make a gate pass.

Before you say it is done, name the one observable that would differ if
your change were wired to nothing, and go check it. Not a trace. Not "the
test passes." A thing you can actually see.

## Red flags: stop and go back a step

| Thought | What it actually means |
| --- | --- |
| "The test passes, so it works" | A check you never watched go red is a claim about the harness, not the bug. |
| "I traced every call site" | That is not the check; trace a real run instead. |
| "The suite is green" | A green suite has hidden this exact bug class before, repeatedly. |
| "Every mutation arm passed, so the fix is solid" | A green arm is a coverage hole, not a pass. |
| "An existing test contradicts my fix, so my fix must be wrong" | The test is sometimes the bug. |
| "I read the code carefully" | Reading produces confident, wrong leads; running a real input finds real bugs faster. |
| "I will write the test after the fix" | You will then test the fix, not the bug. |
| "The report says the cause is X" | Verify it; reported causes are regularly wrong. |
| "It is a one-line change" | A one-line change can land inside a comment and pass every existing test. |
| "I regenerated the baseline" | A ratchet you regenerate to silence it is not a ratchet. |

