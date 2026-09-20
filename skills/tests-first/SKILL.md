---
name: tests-first
description: Use before writing any feature or bug fix, before adding a guard or ratchet, and whenever a fix "should work" but nothing proves it yet. Also use when you catch yourself about to write code before a test exists for it.
---

# Tests first

Write the failing test before the code, every time. This is not a style
preference. A test written after the fix tends to assert what the fix does;
a test written from the reported symptom asserts what the system is supposed
to do. Not knowing the cause yet is an advantage: you cannot accidentally
write a test that only exercises your own theory of the bug.

## The loop, in order

1. **Name the observable.** One sentence: what would a user or a log line
   show if this were working, that it does not show now? That sentence is
   your first assertion. If you cannot state it, you do not understand the
   change well enough to test it, let alone build it.
2. **Write the failing test(s)**, at the symptom level, not the
   implementation level. State it as something a user would recognize:
   "the export contains the missing column", not "`_build_rows` returns a
   longer list".
3. **Run it. Read the failure message, do not just note the exit code.**
   `ImportError` or `KeyError` on your own fixture is not evidence of
   anything except a broken test. The message has to describe the real
   defect before you move on.
4. **Write the neighbouring tests.** Same shape, adjacent input: the empty
   case, the one-item case, the largest realistic case, the value that is
   `None` rather than absent. One reproduction is an anecdote; a small
   matrix is a rule. This step has caught defects a single targeted test
   missed, repeatedly, on real work.
5. **Write the code.** The smallest change that turns the new tests green.
   Do not refactor unrelated code in the same pass.
6. **Run the targeted tests again and confirm green.** Then run whatever
   fast structural checks your repo has (linters, import guards, doc-drift
   checks). Do not run the full suite from a worker lane; that is the
   integrator's job, once, alone.
7. **Report both outputs**, the red one and the green one, not just the
   final state. A report that only shows green is a report you cannot check.

## Non-negotiables

- No production code exists before you have watched a test fail for the
  right reason.
- "I will add tests after" is the exact failure mode this skill exists to
  stop. Tests written after tend to encode the bug as intended behavior.
- A new guard, ratchet, or allowlist needs two tests: one that plants the
  violation and proves the guard catches it, and one vacuity check proving
  the guard actually scans something (a scanner that silently matches
  nothing reports a clean tree forever). See `verifying-a-green-gate`.
- **Assert the value, never mere presence.** `"x" in call.args` can pass
  with the real argument deleted, if a stub's own default happens to supply
  the same key. Check what was actually passed.
- A green mutation arm (revert part of the fix, tests stay green) is a
  coverage hole, not confirmation the code was fine. See `fixing-a-bug` for
  the full revert-check recipe.
- Label every causal claim as `MEASURED:` (you watched it happen) or
  `THEORY (unverified):`. Do not write a theory as if it were a measurement.

## Why this is worth the friction

The alternative loop, code first and test after, produces tests that pass on
the first run with no surprises and that go on passing when the code is
later broken. A test that has never been watched to fail is a claim about
your harness, not about your code.
