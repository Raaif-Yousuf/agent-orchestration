# Hard rules catalog

I keep this list next to `rules/CLAUDE.md.template` because a good hard rule
is rarer than it looks, and most of the ones worth having were paid for by
a real incident, not invented at a desk. Every rule below started as
something specific to one of my own projects. I have stripped the project
names, the numbers that were only ever true for one day, and the tool
names that only make sense inside one codebase, and kept the shape: what
to ban, why it is worth banning, and what actually enforces it once
someone stops reading the rule.

**How to use this.** Do not copy the whole list into a new project's
`CLAUDE.md`. Read a section, pick the two or three rules whose failure mode
you can already imagine happening to you, rewrite them in your project's
own vocabulary, and put only those in your Hard Rules. A CLAUDE.md with
forty rules gets skimmed; one with eight gets read. The rest of this catalog
stays here as a menu, not as something you are behind on.

**On enforcement.** A rule that only lives in prose gets broken by someone
who read it and forgot, or never read it at all. Every entry below names
what actually enforces it: a test, a lint rule, a CI check, or a hook that
blocks the action outright. If you cannot name one, that is worth noticing
before you write the rule down, not after it fails a third time. See
[`a ban broken repeatedly needs a hook, not a bolder rule`](#agent-specific-and-process)
below, which is itself in this list because it is the rule that produced
most of the others.

---

## Repo hygiene

**1. Name the one approved wrapper for each shared resource and ban the raw call.**
A database handle, an HTTP client, a path resolver, a config loader: pick one
function that owns retries, redaction, pooling or normalization, and forbid
calling the underlying primitive directly.
*Why:* every raw call is a place the wrapper's guarantees quietly do not
apply, and it costs nothing to write on the day it is added.
*Enforce:* a grep-based CI check for the raw call, or a lint rule scoped to
the module that should never import it.

**2. Ban a platform primitive by name the moment it has burned you once.**
If a specific concurrency primitive, encoding call or library function has
caused a real, reproduced failure, do not just fix the call site: name the
primitive in the rules and forbid it outright.
*Why:* a comment at the fixed call site does not stop the next person, or
the next agent, from reaching for the same primitive out of habit somewhere
else. The fix is prevention at the name, not at the instance.
*Enforce:* a grep-based lint rule for the banned identifier, checked in CI.

**3. Never commit generated, local or machine-specific state.**
Data directories, `.env` files, build caches, IDE state: list them in
`.gitignore` and treat any of them showing up in a diff as a review blocker,
not a nitpick.
*Why:* these files leak local paths, credentials and machine-specific
assumptions, and once one lands, everyone's `git status` gets noisier and
the next accidental commit is easier.
*Enforce:* `.gitignore` plus a CI or pre-commit check that fails on a diff
touching a listed path.

**4. Cap file or component size and split past it.**
Pick a line-count ceiling for the unit your language treats as "one
component" and enforce it mechanically.
*Why:* a size cap is a proxy for "does one thing", and proxies that are
never checked drift silently upward until nobody wants to touch the file.
*Enforce:* a line-count guard in CI, scoped to the files the branch touched
so it does not block on pre-existing debt.

**5. A ban with no stated alternative loses to the reflex.**
Every "never do X" needs a "do Y instead" in the same sentence, not in a
linked doc three clicks away.
*Why:* the person or agent hitting the banned pattern is mid-task and under
time pressure; they will do the familiar thing unless the replacement is
right there.
*Enforce:* a review checklist item on any new Hard Rule: does it name the
replacement move.

**6. Put a count in a test, never in prose.**
If a rule or a doc wants to say "there are N of these", derive N from the
code with a test or a script, and reference the command instead of writing
the number.
*Why:* a count in prose is honest on the day it is written and wrong the
day something changes it, and nothing tells the reader it went stale. A
stale number reads as more authoritative than an honest "run this to find
out", which makes it worse than having no number at all.
*Enforce:* a test that asserts the count via AST or a registry, or a doc
convention that any number must cite the command that produced it.

**7. A rule broken three or more times despite being written down needs a
hook, not a bolder rule.**
When the same written ban fails repeatedly against people or agents who
read it, stop rewriting the rule and build a mechanism that refuses the
action.
*Why:* writing a rule harder has never fixed a rule that was already read
and ignored. Only something that runs before the action can.
*Enforce:* a `PreToolUse`-style hook, a pre-commit hook, or a CI gate that
blocks the specific command shape, ideally one that also prints the
approved alternative in its refusal message.

**8. Never recursively force-delete a shared or tracked path without
checking who else has files there.**
A scratch or working directory shared across parallel agents or branches is
not "yours to clean up" just because your own files are in it.
*Why:* a recursive, forced delete has no way to distinguish your files from
someone else's, and it fails silently: the delete succeeds, the mistake
surfaces later as someone else's missing work.
*Enforce:* a hook that blocks a delete which is both recursive and forced
and resolves inside a shared directory, while still allowing a named file,
a non-forced recursive delete, or a delete scoped to a private path.

**9. A clean merge is not evidence that nothing was lost.**
Two branches editing adjacent lines, or making the same deletion
independently, can merge with no conflict marker and still drop content or
compose into something neither branch intended.
*Why:* git's three-way merge resolves at the line level, not at the level
of the invariant you actually care about (every entry present, versions
contiguous, no duplicate registration).
*Enforce:* after any merge, re-run the specific check for the invariant
that should hold over the merged file, not just "did the merge succeed".
For anything with an ordering or uniqueness property, diff the merge-base
against each side directly rather than only reading the merged result.

---

## Testing

**10. Prefer a whole-tree census over a hand-maintained roster.**
When a guard checks "every X is registered, covered or documented", ask
where its list of X comes from. If a human maintains that list, derive the
set from a property of the code instead (an AST pattern, an import, a
decorator) and compare the roster against the census.
*Why:* a hand-maintained list cannot see the X nobody thought to add, which
is exactly the X most likely to be wrong.
*Enforce:* a census script run on a schedule or at merge time, diffed
against the roster it is meant to replace.

**11. Every scanner or guard must assert it found something before it
asserts the violation set is empty.**
A zero-result sweep and a scanner that stopped working produce the same
output. Add a floor: "found at least N candidates" before "none of them are
violations".
*Why:* a guard that goes blind does not fail. It reports success, and a
success that used to be a real check is worse than no check, because the
next person trusts it.
*Enforce:* a vacuity assertion inside the test itself, checked every run,
not just when the guard is written.

**12. Mutation-check every new guard before trusting it.**
Plant the exact violation the guard exists to catch, confirm it goes red,
revert, confirm it goes green again, and keep a record that this happened.
*Why:* a guard that has never been shown to fail has not been shown to
work; a passing test proves nothing about whether it can catch the thing it
is named for.
*Enforce:* make the mutation check part of the guard's own commit or PR
description, not a one-time manual step that nobody repeats later.

**13. Use structural parsing, never a substring or line-based match, when a
check reasons about code.**
A comment, a docstring, or a deletion note containing the pattern you are
looking for will satisfy a grep-based check exactly as well as real code
does.
*Why:* a substring scanner cannot tell "this exists" from "this used to
exist and I wrote a comment about it", which means the corpus it appears to
guard includes its own explanatory prose.
*Enforce:* rewrite the scanner with the language's own AST or parser
instead of a regex, and add a fixture where the pattern appears only in a
comment to prove the parser-based version ignores it.

**14. A guard authored is not a guard that runs.**
Writing a check and wiring it into the thing that actually executes checks
are two different pieces of work, and only one of them has a test that
proves it happened.
*Why:* a guard can be merged, pass when run by hand, and be invoked by
nothing, and the total count of "checks that ran" cannot detect its own
omission because it is measured from the runner.
*Enforce:* treat "the runner's check count went up by one" as the
acceptance criterion for adding a guard, not "the guard passes", and verify
it on the merged tree.

**15. Assert the value, never mere presence.**
`assert "key" in result` passes whether the value behind that key is
correct, wrong, or a placeholder. Assert what the value actually is.
*Why:* a presence-only assertion protects the shape of a response and says
nothing about its correctness, so a silently wrong computation ships with a
green suite.
*Enforce:* code review convention; a lint rule that flags a bare membership
assertion on a dict access is worth writing if the pattern recurs.

**16. A census or reachability report is a candidate generator, never a
defect list.**
Any tool that flags "possibly unused", "possibly unreachable" or "possibly
uncovered" will overstate the real defect count, often by an order of
magnitude, because it cannot see rendering, indirection or intentional
design.
*Why:* reporting the raw count as a bug count trains the next reader to
either panic or, more likely, to stop trusting the tool.
*Enforce:* trace every candidate to a real consumer or a documented reason
before filing anything, and publish the traced-to-real ratio next to the
raw number wherever the number is quoted.

**17. A source-scanning test must normalize line endings and match the
syntactic unit, not the line.**
A pattern anchored on `\n` breaks silently on a CRLF checkout, and a
regex expecting two tokens on one line breaks silently the moment a
formatter puts them on two.
*Why:* both failures are invisible: the test still runs, still passes, and
now checks nothing.
*Enforce:* normalize line endings before matching, match against a joined
or parsed span rather than a single line, and pair the check with rule 11's
vacuity assertion.

---

## Concurrency and processes

**18. Only one process runs the full test suite at a time; everything else
runs a scoped subset.**
A worker, agent or contributor validating a change runs only the tests that
cover the files it touched. One owner, at the end, runs the full suite.
*Why:* several full suites running concurrently exhaust the machine's
memory and CPU, and a starved test run flakes in a way that reads exactly
like a real failure.
*Enforce:* state the rule in every worker brief, and where possible, a hook
or wrapper script that refuses a full-suite invocation without an explicit
override.

**19. Ban a parallel-execution flag on scoped runs by name.**
A test runner's built-in parallelism flag turns one "targeted, cheap" run
into many concurrent processes, which defeats rule 18 even when everyone
believes they are following it.
*Why:* the flag is easy to reach for out of habit and its cost is invisible
until the machine is already saturated.
*Enforce:* grep the command being run for the flag before executing it, or
block it with the same hook mechanism as rule 7.

**20. A freshly created worktree or parallel branch may be based on a stale
snapshot, not on the branch you asked for.**
Tooling that creates a worktree or a parallel checkout can pin it to a
cached copy of the default branch that is already behind the remote.
*Why:* work built on a stale base looks correct in isolation and fails only
at merge time, in a way that is expensive to diagnose because the branch
"clearly" started from the right place.
*Enforce:* the first step of every worker brief is an explicit fetch and
checkout from the remote's default branch, followed by printing the
resulting commit and branch name to confirm it.

**21. A shared scratch or temp path is not isolated per worker.**
If two concurrent workers can both resolve to the same temporary file path
(a shared scratchpad, a default temp directory), one can silently commit
with the other's content attached.
*Why:* the failure is invisible from either worker's own point of view: the
write succeeds, the commit succeeds, and the result is merely wrong.
*Enforce:* every worker writes its own transient files inside its own
isolated working tree, never a shared temp directory, and confirms its own
output after writing it (for example, reading back the subject line of the
commit it just made).

**22. Walk the whole process tree before deciding something is hung, and
never kill by image name.**
A parent process sitting at low CPU is not evidence its work is stuck; the
actual work may be several process levels down. Killing by executable name
kills every process with that name, including ones you do not own.
*Why:* an ancestor process legitimately shows near-zero CPU while waiting
on a child, and a name-based kill has no way to distinguish your process
from a concurrent one, or from the user's own running application.
*Enforce:* use a process-tree inspection script or command before killing
anything, and kill only a specific PID you launched yourself.

**23. Know your platform's real capacity ceiling, not just free memory.**
On some platforms, the metric that actually predicts a silent kill is not
"free RAM" but a combined figure (commit charge, cgroup limit, whatever the
OS enforces), and hitting it produces no error, just a process that stops.
*Why:* watching the wrong gauge gives false confidence right up until a
long-running job vanishes mid-run with an empty log.
*Enforce:* identify and document the platform-correct ceiling for your
environment, and check it before raising concurrency, not after a run dies.

---

## Shell and platform

**24. Never pass a message containing shell metacharacters through an
inline flag; write it to a file first.**
Backticks, `$(...)`, unescaped parentheses or quotes inside a `-m`/`--body`
style argument get interpreted by the shell before the target program ever
sees them.
*Why:* the damage is silent: the command exits zero, the message is simply
wrong, and by the time anyone notices, the artifact (a commit, a comment)
may already be public.
*Enforce:* always write the message with a file-writing tool and pass it
with the program's file-based flag (`-F`, `--body-file`); treat any inline
multi-line or punctuation-heavy string as a bug in the calling script.

**25. Know when your shell rewrites arguments that look like paths.**
Some POSIX-emulation shells on Windows silently rewrite any argument that
looks like an absolute POSIX path, including inside quoted strings, even
when the argument is really a URL fragment, a route or a regex.
*Why:* the rewrite happens with no error and no warning; the command
succeeds with mangled input.
*Enforce:* document the opt-out environment variable for your shell and use
it on any command whose arguments contain a leading-slash token that is not
a real filesystem path.

**26. Never trust the exit code of a backgrounded or piped compound
command.**
A wrapper that reports "exit code 0" for a multi-step or backgrounded
command is often reporting the status of the last thing that ran, not the
thing you launched.
*Why:* this fails in the reassuring direction: a real failure reads as
success, which is the one outcome that guarantees nobody investigates.
*Enforce:* have long-running or gating scripts write a verdict file
containing their own real result, and read that file, or the script's own
guaranteed last output line, instead of a relayed exit code.

**27. Never pipe a long-running command through a tail-like filter.**
Commands like `| tail` or a "last N lines" filter buffer their input, so
the destination log or terminal can sit empty for the command's entire
runtime.
*Why:* an empty, buffered log is indistinguishable from a hung process,
which leads to killing healthy long-running work.
*Enforce:* redirect long-running output to a file and read the file
directly, never through a tail-style filter.

**28. A collection-typed argument can silently flatten across a process
boundary.**
Invoking a script with an array or list parameter through a nested shell
call (spawning a new interpreter process) can serialize the collection
across `argv` and misassign its later elements to the wrong parameter,
with no error at the call site.
*Why:* the script still runs, still exits zero, and the wrong data lands
somewhere plausible-looking instead of where you sent it.
*Enforce:* invoke in-process (source or dot the script, or call it directly
in the same interpreter) rather than through a child shell when passing a
collection argument, and have the script echo back what it parsed before
it acts, especially in a dry-run mode.

---

## Documentation and changelogs

**29. Replace a hand-written count with the command that derives it.**
Anywhere a doc or a rule states "there are N of these", either pin N with a
test or replace the number with the command that prints it live.
*Why:* this is rule 6 restated for documentation specifically, because it
is the single most common way a doc goes stale without anyone noticing:
the sentence still reads fine, it is just wrong.
*Enforce:* a doc-linting convention, or the same stale-count test pattern
as rule 6.

**30. Never use a doc's enumerated list as an audit's scope without
re-deriving it from the code first.**
A doc that says "there are three kinds of X" makes a sweep against those
three kinds look complete, even when the code has grown a fourth.
*Why:* a stale checklist is worse than no checklist, because it produces
false confidence that the surface was fully covered.
*Enforce:* before scoping any audit or sweep from a doc-recorded list,
re-derive the same list from the code (a grep, an AST walk, a dispatch
table) and reconcile any difference before starting.

**31. File the issue in the same commit as the deferral.**
A scope cut, a budget bound, or a "left as a follow-up" decided mid-
implementation must produce a tracked issue immediately, not just a code
comment.
*Why:* a `TODO`-shaped comment is invisible to whatever tool lists open
work, so the decision sits unbuilt until someone happens to read that file.
*Enforce:* a review convention that flags follow-up language ("for now",
"not yet", "left for later") in a diff and asks for the linked issue
number.

**32. Label a causal or performance claim as measured or as a theory, and
never leave the two looking the same.**
Any statement of the form "X causes Y" or "this is Z times faster" needs a
tag: measured, with how, or an explicit unverified theory.
*Why:* an unlabelled claim reads with the same confidence whether it was
checked or guessed, and a wrong guess that reads as fact gets built on.
*Enforce:* a writing convention enforced in review; when a theory is
disproven, replace the original claim in place rather than appending a
correction elsewhere that a later reader may never reach.

---

## Issue tracking

**33. All issue tracking lives in one named system, with no comment-shaped
exception.**
Pick the tracker (GitHub Issues or otherwise) and treat a TODO comment or a
docstring aside about future work as a tracking failure, not a lighter-
weight alternative.
*Why:* a comment does not show up in a backlog query, a milestone view, or
anything else that decides what to work on next.
*Enforce:* the same review convention as rule 31.

**34. Close an issue against its written acceptance criteria, never
against a one-line summary of the fix.**
The mechanism that was fixed and the observable the issue actually asked
for are not always the same claim; a fix can make the named code path stop
firing while the user-visible symptom persists through a different path.
*Why:* closing from a compressed summary is how a half-finished issue
disappears from view while still being open in every way a user would
notice.
*Enforce:* re-read the issue's own "done when" text against the diff before
closing it, every time, and prefer reopening with a comment over leaving a
wrong close standing.

**35. A merge commit's closing keyword only closes anything once that
commit reaches the tracker's remote.**
If your local default branch runs ahead of the remote the tracker watches,
writing a closing keyword in a commit message closes nothing until that
commit is pushed.
*Why:* everything about the commit looks correct, so nothing surfaces the
gap except manually checking the tracker.
*Enforce:* close explicitly through the tracker's own API or CLI at merge
time, and treat the commit message's closing keyword as documentation, not
as the mechanism.

**36. Sweep for "fixed but never marked closed", not only the reverse.**
It is easy to build a check for "closed but not really fixed" and forget
that a merged fix can just as easily leave its issue sitting open forever.
*Why:* nothing fails when this happens: the code is right, the tests pass,
and the only symptom is a backlog that looks larger than the real amount of
open work.
*Enforce:* a script that compares the commit graph against open-issue
state and flags issues whose linked commits already merged, run at the
start of a work session, not only at the end.

---

## Agent-specific and process

**37. State the model per task rather than leaving every dispatch on one
default.**
A mechanical, low-judgment task (a re-measurement, a repetitive scan) and a
task requiring real judgment (a design decision, a cross-cutting diagnosis)
do not need the same model.
*Why:* a single default either overspends on easy work or underpowers hard
work, and the difference compounds across a large fan-out.
*Enforce:* pass the model explicitly on every dispatch call, chosen by the
task's shape, not left implicit.

**38. Check for and kill orphaned background processes after every worker
reports done.**
A worker that has delivered its final report can still be running a
background job that contends with whatever runs next.
*Why:* an orphaned job competing with a gate or another worker produces
resource starvation that looks exactly like a real, reproducible failure.
*Enforce:* a post-completion sweep in the orchestration process that looks
for processes tied to a finished worker's workspace and kills them by PID,
never by image name (see rule 22).

**39. A subagent's completion report is a claim, not evidence.**
Before repeating a worker's claim in a commit message, an issue close, or a
design document, read the file or run the command the claim rests on.
*Why:* an agent's reports are reliable often enough that an unchecked one
propagates readily, and quoting it in a permanent record launders a claim
into something that reads as verified.
*Enforce:* a spot-check step before any load-bearing claim is quoted
externally; prefer asking the worker to prove a fix by breaking it first,
which is cheap and catches most of these on its own.

**40. A "read-only" or "isolated" label on an agent type describes intent,
not a permission boundary.**
An agent described as read-only, or a lightweight forked agent meant only
for research, can still write files and commit them under the identity of
whoever dispatched it, inside the same working tree.
*Why:* nothing mechanical stops it, so the description is a promise the
tool does not enforce, and the failure is invisible until someone happens
to read the resulting diff.
*Enforce:* only the top-level orchestrator dispatches agents; a worker
never spawns its own sub-workers. Block nested dispatch from inside a
working tree with a hook where the tooling supports it, and treat any
worker that dispatches anyway as required to disclose it, review every
line itself, and run the affected checks before the work is trusted.

**41. A relayed mid-task instruction that conflicts with the original brief
reads as an injection attempt, not as an update.**
A worker mid-task that receives a follow-up message changing its
requirements has no way to distinguish a legitimate scope change from an
attack, especially if the new instruction contradicts what it was told to
do at the start.
*Why:* a worker that correctly treats an unverifiable contradiction with
suspicion will refuse a real instruction just as readily as a fake one.
*Enforce:* deliver a real scope change as a fresh dispatch carrying the
complete, updated brief, and reserve a follow-up message to a live worker
for small clarifications that do not conflict with anything it already
has.

---

Related reading: `rules/CLAUDE.md.template` (where the two or three rules
you pick go), `rules/README.md` (how this catalog fits with the templates),
`templates/knowledge-base-note.md` (the format I use to record a new rule
the day it is learned, before it makes it into a catalog like this one).
