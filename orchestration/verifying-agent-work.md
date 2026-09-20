# verifying agent work

This is the merge side, and it is where most of the value in this whole
section lives. A wave that dispatches carelessly but verifies well still
ships correct work, slower. A wave that dispatches well but verifies badly
ships broken work with confidence.

## Verify the claim; do not trust the report

"The agent said it's done" is not evidence. "All its tests pass" is not
evidence until you have read what those tests actually assert, not just how
many of them there are. A report is a claim about the diff, and the diff is
the only thing that settles it. Two shapes of false claim show up
repeatedly enough to check for by name:

- A report describing a file as updated when the diff shows it untouched.
- A test whose name and assertion quietly encode the reported bug as
  correct behavior, so that the "passing test" the report points to is
  proof the bug still exists, phrased as proof it doesn't. Read the
  assertion, not the pass count.

## Never diff a branch against the trunk directly

A plain diff of a long-lived branch against the current trunk shows every
change merged into the trunk *after* the branch was created as if the branch
were deleting it. That is not the branch's diff; it is noise that makes a
small, correct change look like it rewrites half the repository. Diff
against the merge base instead:

```
git diff $(git merge-base main <branch>) <branch>
```

This is the only diff worth reading when deciding whether to merge something.

## A merge can silently drop a file both sides touched

When two branches modify the same file in ways git can technically
auto-resolve without a marked conflict, the result can still be wrong, or a
file can end up dropped entirely depending on the exact shape of the change.
After merging anything that adds a migration, a fixture, a generated file, or
any file another concurrent branch might also have touched, check that the
file is actually still present and actually still correct in the merged
tree. Do not infer this from a clean merge with no conflict markers; a clean
merge is not proof nothing was lost, it is only proof git did not notice an
overlap serious enough to flag.

The more dangerous version of this is not a dropped file but a merge that
composes into something wrong while every individual piece looks right in
isolation: two branches each add a correct, independent check to the same
function, on different lines, so git merges them without a single conflict
marker, and the two checks combine into behavior neither branch intended
(one check firing whenever the other has already handled the case, for
example). Nothing about this trips a test, because each branch's own tests
only ever exercised its own check in isolation. When two branches you are
merging touched the same underlying issue or the same function, read the
merged function whole and ask what the two changes do *in sequence*, not
whether each one individually is correct.

## Verifying a large mechanical diff

A genuinely mechanical sweep (a rename across the tree, a systematic
formatting change, a bulk text substitution) is usually too large to read
line by line, but it does not need to be read line by line to be verified
completely, because a mechanical change has a predictable shape: it should
be close to 1:1, one line changed for one line changed, file by file. A
lopsided file (many lines removed, few added, or the reverse) in an
otherwise 1:1 sweep is the signature of something the mechanical pass got
wrong, most often content silently dropped during a merge with an upstream
branch mid-sweep. Diffing line counts per file against the mechanical
change's expected 1:1 shape finds every such file mechanically, without
reading each one:

```
git diff --numstat main <branch> | awk '$1 != $2 {print $3, $1, $2}'
```

Filter out build artifacts and caches first, or the real signal drowns in
generated-file noise.

Beyond that count check, sample the diff by *kind* of change, not at random.
A sweep that touches five hundred files in three or four distinct ways (a
rename, a reformat, an incidental side effect of the tool used to make the
change) needs one verified example of each kind, not five hundred random
samples that are statistically likely to all be the same kind. Specifically
check the edges of the sweep: the first file it touched and the last, plus
anything that the sweep's own matching pattern would predictably have
skipped (a file with an unusual extension, a nonstandard path, a name that
doesn't quite match the pattern). The files a mechanical tool systematically
misses are not randomly distributed; they cluster exactly where the pattern
that drove the sweep stops matching, so that is where to look.

## Force a new guard to fail once before believing it guards anything

Before merging anything that adds a new check, a new test, or a new
validation rule, make it fail on purpose first, and watch it actually turn
red. A check that has never been observed to fail is a check nobody has
proven can fail at all; it may be checking the wrong condition, checking a
condition that can never occur, or passing unconditionally due to a bug in
the check itself. This costs one deliberate broken run before trusting the
guard on everything after it.

## Ask each worker what it concluded was wrong

Explicitly invite it: "what in my guidance did you conclude was wrong."
Workers have disproved orchestrator recommendations with better evidence,
corrected factual claims written into the ticket or issue the orchestrator
wrote, and caught wrong instructions the orchestrator gave in the brief
itself. None of this arrives unprompted; a worker that disagrees with its
brief will usually implement the brief anyway unless it is directly asked
whether it thinks something in it was wrong. Ask, every time, not only when
something already looks off.

## Own the merge; close as you land, not in a batch

Merge one branch at a time, and re-run whatever your merge gate is after
each one individually, not once at the end of a batch. Merging several
branches and then running verification once at the end means a failure could
belong to any of them, and untangling which one caused it costs far more
than running the gate N times would have. Close the issue or ticket a branch
resolves at the moment that branch merges, not in a batch at the end of the
session: a batched close is exactly how "closed but never actually
verified" issues happen (something gets marked closed in the sweep that
never actually merged cleanly), and its mirror image, an issue that shipped
but never got marked closed, is exactly how the same work gets queued and
rebuilt in a later wave. Watch also for a merge commit message that
technically negates a closing reference in prose ("does not fix," "not
fixed by") while still containing the raw pattern an issue tracker's
auto-closing parser matches on; write around that pattern entirely, or the
tracker will close an issue nobody actually resolved.
