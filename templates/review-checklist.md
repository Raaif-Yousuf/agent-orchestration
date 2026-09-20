# Review checklist

How to use this: paste the checklist section below into a PR comment when
reviewing someone else's branch (including your own agent's), then check
off or strike out what does not apply. It is written as questions you can
answer by looking, not as a form to fill in from memory.

## Before merging

- [ ] I read the diff, not just the description. A large or mechanical diff
      gets `git diff --numstat <base> <branch>` checked for lopsided files
      (a rewrite should be roughly 1:1 line-for-line; a file with far more
      removed than added may have silently lost content).
- [ ] Every new check, guard or test asserts something that can actually be
      false. If it is a scanner or census, it asserts it found a non-empty
      candidate set before asserting no violations.
- [ ] Anything the diff claims is fixed has a test or a reproduction step
      that fails without the fix and passes with it, not just a passing
      suite that never exercised the change.
- [ ] The branch's own tests pass, run by me, not only reported as passing
      by whoever wrote the branch.
- [ ] No committed secrets, tokens, absolute personal paths, or generated
      artefacts that belong in `.gitignore`.
- [ ] Any new hard rule, ban, or convention names its replacement move and
      its enforcement mechanism, not just the ban.
- [ ] Any count or number in a doc or comment is either derived by a test
      or clearly marked as a one-time measurement with its date.
- [ ] If this closes an issue, I re-read the issue's own "done when" text
      against the diff, not just the PR description's summary of it.
- [ ] If this touches a shared or generated file (a registry, a baseline,
      a migration list), I re-derived the invariant that should hold after
      the change rather than trusting that the diff looks right.
- [ ] Commit messages and the PR description describe why, not just what,
      and match this repo's commit convention.

## Questions worth asking out loud

- What would make this look done but actually be wired to nothing?
- What did the author get wrong, if anything, and did they say so?
- What is explicitly out of scope here, and is that stated anywhere?
