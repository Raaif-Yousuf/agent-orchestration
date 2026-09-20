---
name: working-an-issue
description: Use before starting or closing any tracked issue. Also use when an issue cannot be closed because nobody wrote down what "done" means, when triaging a stale backlog item, or when an issue reads as an epic or container rather than a single task.
---

# Working an issue

Work has been rebuilt from scratch after it had already shipped, because
nobody checked before starting. Issues have also been closed as done when
no commit actually did the work, and disproven on the next real check. Both
are the same missing step: nobody asked the repository what it already
knew. The repository always knows; the issue tracker is a second, separate
system that can silently fall out of sync with it in either direction.

## 1. Before you start: ask the commit graph, not the issue body

Search the commit history for the issue's number and for its distinctive
keywords before reading the issue body itself:

```
git log --all --oneline --grep="<issue-number>"
git log --all --oneline -S"<a distinctive literal from the report>"
```

If commits naming the issue already touched the relevant source files, read
every one of those commits before writing a line of code. The issue body
describes what someone wanted when they filed it; the commit log describes
what actually happened, and when the two disagree, the log is right.

Two ways this step still misses, both worth checking explicitly:

- **A multi-item issue gets one verdict for the whole issue.** An item deep
  in a checklist can already be shipped while the issue as a whole still
  reads as open, because the summary check only looked at the issue as a
  unit. If the issue has a checklist, check each item's own subject against
  the log, not just the issue number.
- **The comment thread, not just the body, carries the answer.** Read the
  full comment history, newest first, before starting. A thread has
  repeatedly superseded its own issue body with a different scope or a
  different architecture entirely; building to the stale body produces the
  wrong thing and then closes the issue on it.

If related work happens across more than one repository, check the other
repository's branches too. An issue can read as completely untouched here
while its fix sits on an unmerged, unpushed branch next door.

## 2. Does the issue say what "done" means?

Most stale issues are not hard, they are unclosable: nobody can tell
whether they are finished, so nobody picks them up and nobody closes them.
If the issue has no acceptance criteria, writing them is the first piece of
real work, and doing so often reveals the issue is already satisfied.

A criterion only counts if it is falsifiable: someone can run one command
or look at one screen and answer yes or no.

| Not a criterion | A criterion |
| --- | --- |
| "This feature is reliable" | A named script or check reports zero failures over a fixed, named input set, on three consecutive runs |
| "It feels faster" | A named metric stays under a named threshold, measured from a real run, not a synthetic one |
| "Fewer oversized modules" | One command prints a count against a fixed ceiling, and the ceiling may only be lowered, never raised to pass |
| "Better traceability" | Every reported number links back to the exact query or computation that produced it, and following that link reproduces the same value |

For a container, epic, or "lead" issue: enumerate what it actually contains,
check each piece against the code, and either split it into concrete
children and close the container pointing at them, or rescope the body down
to whatever single piece remains. A rescoped issue must come out smaller
and sharper than it went in, not vaguer.

For a conditional issue ("revisit once X happens"), the deliverable is the
trigger itself: one mechanical check that answers whether X has happened
yet.

An issue left permanently undecided is the failure state. "Declined,
because ..." is a successful outcome; silence is not.

## 3. Before you close: name the observable

Closing an issue records a belief that the code is done. Never close on "the
diff looks right." State three things in the closing comment:

1. The commit(s) that did the work.
2. The acceptance criteria you are closing against.
3. The one observable that would differ if the change were wired to
   nothing, and confirm you actually checked it. See `wired-to-nothing` for
   the per-shape checklist. This is not a formality: this exact bug class,
   code that runs and passes tests while doing nothing at runtime, is the
   most expensive one on real work, and no test alone has ever caught an
   instance of it.

Watch the exact wording of a commit or comment that closes an issue.
Closing-keyword parsers match on the issue number regardless of surrounding
negation: a comment that says "not fixed: #123, out of scope here" can
still close #123, because the parser matches "fixed: #123" and ignores the
leading "not." If a sentence needs to say an issue is *not* resolved, phrase
it so the closing keyword and the number never appear adjacent, or leave
the number out of that sentence entirely.

## 4. If the behavior is unproven on a real target, say so explicitly

Closing the issue and proving the behavior on a real target (a packaged
build, real hardware, a live external dependency) are different statements,
and conflating them is how "closed" comes to mean "probably fine." Keep a
running list of exactly what a human still needs to verify by hand and what
passing looks like, separate from the issue tracker. Delete an entry only
once someone actually verifies it; if verification fails, reopen the
original issue with the measured evidence rather than filing a fresh one
that loses the history.

## 5. Recording a cause

A causal claim about why something was broken carries its own evidence:
`MEASURED:` plus what you actually observed, or `THEORY (unverified):` if
you have not confirmed it. When a theory is later disproven, replace it
where it was written rather than appending a correction somewhere else;
otherwise the next reader finds the wrong answer first.

## Red flags

| Thought | What it actually means |
| --- | --- |
| "This looks like nobody started it" | Check the commit graph before assuming. Work has repeatedly turned out to already be done. |
| "The diff is obviously right, close it" | Issues have been closed exactly this way and disproven the next day on a real run. |
| "I'll write the criteria after I build it" | Then neither you nor anyone else can tell whether you are finished. |
| "It's an epic, I'll just work top to bottom" | Check every child's current state first; epics outlive their children and drift. |
| "The tests pass, so it works" | No test alone has ever caught a wired-to-nothing instance. Name the observable and check it. |
| "I'll close it and remember to verify the build separately" | Write it down where it will not be forgotten, not just in your own memory of the session. |
