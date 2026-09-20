# Lessons

This is the knowledge base behind the rest of the repo: operational lessons I
pulled from real work, stripped of anything that names a project, a client, a
date, or a ticket number. Each entry follows the shape in
`templates/knowledge-base-note.md`: what I observed, the rule that follows,
and how the rule is actually enforced, because a rule with no enforcement is
a hope, not a rule. I grouped them the way they actually cluster in practice.

## False green and dead gates

### A verifier that shares logic with the thing it verifies will agree with its own mistake

**Observation.** A grounding check and the code it was checking both called
the same helper to decide whether a value was "already accounted for". When
the helper was wrong, the production code produced a bad answer and the
verifier confirmed it, with full confidence, because it asked the same wrong
question. The same helper had already caused one incident and was still live
in a second call site by the time this was found.

**The rule.** A check and the thing it checks must not share a primitive that
could be wrong in the same way. If a verifier imports its "is this correct"
logic from the same module as the thing being verified, it isn't independent.

**Enforcement.** Not mechanically checkable in general; caught by asking, for
every guard, "what would this look like if it were blind", then deliberately
planting that exact defect and confirming the guard goes red. Two guards in
one project were found blind exactly that way.

### A guard can be written, merged, green, and run by nothing at all

**Observation.** A new regression test was merged after two earlier incidents
in its exact class. A handoff said in writing to also register it in the
project's merge-time guard list, in the same change. Nobody did. The
guard-count total agreed with itself in project docs, because the count was
derived from the runner, and a guard missing from the runner is missing from
the count too. It sat on the main branch running nowhere for a day.

**The rule.** The observable for "I added a guard" is never "the guard
passes." It is the total guard count going up, or the guard's name appearing
in the runner's own listing. Verify that on the merged tree, not the branch.

**Enforcement.** A test that asserts the guard-runner's own listing count,
checked after any change described as "add a guard," is the only thing that
catches this; a passing test file on its own does not.

### A guard that stops seeing its corpus does not go red, it reports success

**Observation.** A frontend regression test scanned source text with a
line-based regex ending in a wildcard-to-end-of-line pattern. The checked-out
tree used Windows line endings, and the regex's wildcard does not match a
carriage return, so it silently stopped at the first line boundary. The
scanner saw about six percent of the real occurrences and reported the rest
as fixed. Its own summary read exactly like a backlog someone had cleaned up:
lowering the threshold to match would have made the guard permanently green
and permanently blind.

**The rule.** Every scanner must assert that it found a plausible amount of
material before it asserts anything about what it found: a floor, a minimum
corpus size, anything. A ratchet has to fail in both directions, so a number
dropping gets looked at rather than obeyed.

**Enforcement.** A vacuity assertion (`assert found_count > some_floor`)
inside the guard itself; without one, this class of failure is invisible from
outside the guard's own passing output.

### A hand-maintained list standing in for a real population is where blind guards come from

**Observation.** Auditing a set of merge-time guards by planting a violation
of each guard's actual concept, not its literal pattern, found that guards
checking "every X is registered" routinely passed with the thing they were
meant to catch fully removed, because their notion of "every X" was a
human-maintained list rather than a scan of the real population. A guard
using `git ls-files` as its corpus missed anything untracked. A guard reading
a docstring mention as evidence of a real call passed on prose alone.

**The rule.** When a guard checks "every X is registered or covered," find
where its list of X comes from. If a person maintains that list, the guard
cannot see the X nobody added, which is exactly the X most likely to be
wrong. Prefer a whole-tree census derived from a property (an AST walk, a
real scan) over a roster anyone edits by hand.

**Enforcement.** Code review discipline plus, where it matters enough, a
guard that derives its own roster from the tree and asserts the hand-kept
list matches it exactly.

### A test double or a mutation check that doesn't move with a refactor stops testing anything

**Observation.** Two production functions each gained a new required
parameter. Test doubles that stood in for them kept the old parameter list,
so the real call sites broke, but because the double's own wrapper absorbed
the exception, the error surfaced somewhere unrelated: one inside a generic
error handler that renamed a signature drift into "the backend is
unreachable," the other at the real call site with a traceback that pointed
at production code instead of the stale test. Separately, a helper moved
during a refactor left a test's patch target resolving to a name nothing
called anymore; that one at least failed loudly with an attribute error, which
is the lucky version of the same defect. The unlucky version resolves fine
and quietly stops covering anything.

**The rule.** Any refactor that moves or changes a function's signature has
to grep for every test double and every by-name patch of that function in the
same change. A double that still resolves after a move is not evidence it
still works.

**Enforcement.** A dedicated check that walks every mocked call in the test
tree, resolves the target through the test file's own imports, and compares
the double's declared parameters against the real function's signature.
Cheap enough to run on every merge once scoped to the project's own modules.

### The exit code you read may belong to the wrong step

**Observation.** A compound shell command (`run something > log 2>&1; echo
exit=$?`) reports the status of whatever ran last, which is often a trailing
`tail` or `echo` that always succeeds, not the command you actually cared
about. Separately, a long-running gate that gets silently backgrounded by the
harness reports its status through a task notification, and that relayed
exit code came back "0" more than once while the script's own printed output
showed real failures underneath it.

**The rule.** Never conclude a step passed from a relayed or compound exit
code alone. Put the status check immediately after the command with nothing
following it, invoke long scripts by absolute path (a shell's working
directory persists and drifts between calls), and read the tool's own last
line of output, or a dedicated verdict flag, instead of trusting a
notification's number.

**Enforcement.** Prose discipline in the runbook plus, for the one gate that
matters most, a verdict file the gate writes with the commit it was measured
against, checked instead of any exit code.

### A green gate and a green main are different claims

**Observation.** A fast merge-time gate reported "all checks passed" while the
project's own full test suite, run once by hand afterward, found more than a
dozen real failures on the same commit, none of them in files the fast gate
ever opened. Three separate versions of this were measured over time as the
guard set grew: a fixed short list of test files run after every merge, while
the actual regression-prone tests kept landing outside that list. One
instance persisted through several consecutive green gate runs before anyone
ran a single named failing test directly and confirmed it.

**The rule.** A gate's own green output is a claim about the files that gate
opens, never a claim about the whole tree. When you hand off a known
pre-existing failure to someone running the gate, say explicitly "this is not
in the gate, so the gate will pass regardless of it," not just "this is
pre-existing" — the second phrasing invites the wrong inference.

**Enforcement.** A once-a-session full-suite run on a frozen tree, whose
result is recorded with the commit it was measured against, is the only
thing that actually answers "is main green." A short list of guard files is
a floor, not a fence; deriving the guard set from a property of the tests
(which ones touch files the branch never opened) instead of a hand-picked
list closes the gap that keeps reopening it.

## Agent dispatch and parallel waves

### A forked subagent is not isolated

**Observation.** A worker dispatched a "fork" of itself for what its own
prompt described as read-only research. A fork inherits the parent's full
context and runs in the same worktree with the same git identity. It wrote
real source, added a test, and committed all of it onto the dispatching
agent's own branch. The work happened to be correct, which is the only
reason anyone noticed at all: the failure was that a commit appeared on a
branch from an actor nobody was supervising, and nothing mechanical would
have flagged a wrong version of the same thing landing the same way.

**The rule.** A worker executing a lane must not dispatch subagents of any
kind, including a fork of itself, unless the orchestrator explicitly asked
for that. "Read-only" in an agent type's own description is a description of
intent, not a permission boundary; a general-purpose worker with shell access
can commit code regardless of what its brief says it's there to do.

**Enforcement.** A pre-tool-use hook that blocks agent dispatch from inside a
worktree, plus the rule stated directly in every lane brief. Prose alone was
tried first and was not sufficient.

### A shared scratch path is not private to the agent using it

**Observation.** Two agents working in the same wave each wrote a commit
message to the identical scratch file path, and one of them committed with
the other agent's message attached to its own, correct file tree. It surfaced
only because that agent happened to check its own commit afterward; nothing
else would have caught it, since the commit succeeded, the diff was right,
and the message read as plausible prose about a different piece of work.

**The rule.** Any file a worker writes to coordinate its own actions (a
commit message body, a scratch note) belongs inside that worker's own
worktree, never in a shared temp or scratch directory that other concurrent
workers can also reach.

**Enforcement.** Stated directly in the shared brief, plus a habit of
checking the actual committed message (`git log -1 --format=%s`) right after
committing, before moving on.

### A redirect mid-wave is a fresh dispatch and needs the same check as the first one

**Observation.** A precheck tool correctly said a given task was safe to
start because nothing in the commit history had touched it yet. That answer
only means "nobody has already built this," and it was read as "this is
worth doing now," missing that the task was on an explicit do-not-build list
recorded elsewhere. Later the same session, five lanes were redirected onto
new targets without re-running the same precheck on any of them, and two of
the five turned out to be already finished.

**The rule.** A precheck tool that reads only the commit graph answers only
the question it was built to answer. Run it again, for every new target,
every time a lane's assignment changes, not only at first dispatch. Then also
check anything the tool cannot see: a status field, a list of explicitly
deferred work, a hold recorded in a comment thread.

**Enforcement.** A batched precheck call before every dispatch and every
redirect, named as a required step in the orchestration workflow rather than
left as a habit.

### A handoff document is a snapshot; the live tracker is the state

**Observation.** A worker was dispatched against a priority noted in a
handover document. The item had already been fixed, merged, and closed hours
earlier in an update the handover predated. A quick check of the live issue
list, which had already been run minutes before for an unrelated reason,
would have shown the item was gone.

**The rule.** Read a handover file for shape (which areas are weak, what the
known traps are), never for current state. Anything that claims a status
(open, blocked, assigned) needs a live check against the actual tracker
before it goes into a dispatch brief.

**Enforcement.** A one-line habit stated in the dispatch workflow: check the
live tracker for every item number before it goes into a brief. Cheap enough
that skipping it has no excuse.

### Killing a process by image name kills every other agent's copy on the machine

**Observation.** An orphaned background job left running by one finished
agent was competing with a foreground gate run for machine resources. The fix
for the orphan is to find its specific process id and stop that one process.
Stopping every process sharing an executable's name also stops every other
concurrent agent's unrelated work, and a wave running several agents at once
makes that an near-certain collision rather than a remote one.

**The rule.** Never stop a process by executable or image name in a shared
environment. Find the specific process id tied to the specific worktree or
task, and stop only that one.

**Enforcement.** Stated as an explicit ban with the reason attached, in every
orchestration brief; a ban with no reason attached gets worked around by
habit the first time it's inconvenient.

## Git and worktrees

### A clean merge can silently drop one side's insertion

**Observation.** Two branches each inserted a new entry into the same
ordered file, at hunks adjacent to each other but not overlapping. A
three-way merge resolved it by keeping one side's insertion and discarding
the other's, with no conflict marker, no warning, and a result that reads as
completely coherent on its own. It was caught only by a guard checking a
structural invariant on the merged file (a numbering sequence with a gap in
it), not by reading the merge output itself, and not by the merge tool
reporting anything unusual.

**The rule.** After merging two branches that both touched a shared ordered
or registry-like file, verify the invariant that should hold on the result
(every entry present, sequence contiguous, count correct) rather than
trusting that an absence of conflict markers means nothing was lost. Diffing
each branch against the merge base and comparing the two diffs to each other
finds a dropped insertion that reading the merged file cannot.

**Enforcement.** A guard asserting the structural invariant on the merged
file, run as part of the merge-time gate; reading the merge result by eye is
not a substitute; it looks fine either way.

### Two branches that each pick "the next free" identifier will collide

**Observation.** Two agents working in the same wave each independently
added the next sequential migration version number, picking the same one,
because each only checked its own branch. Both branches were internally
green. The collision surfaced only as a merge conflict, not from any test.
The same shape recurred with a shared guard-count total: two branches each
added a distinct new guard and each computed the new total by adding one to
what they'd seen before, and both totals were wrong once combined, because a
third guard had also landed in between.

**The rule.** Any identifier drawn from a shared, incrementing sequence
(a version number, a running total, an index into a shared table) cannot be
safely picked by each branch independently. Either assign it explicitly per
task before dispatch, or re-derive the true next value from the merged tree
rather than computing it from each branch's own view.

**Enforcement.** Assigning the number in the dispatch brief where the
resource is contended; otherwise, a guard that asserts sequence integrity on
the merged result (see above) catches the fallout even when the assignment
step was skipped.

### A ratchet constant that two branches each lowered independently cannot be reconciled by arithmetic

**Observation.** A shrinking-allowlist ratchet constant was lowered by
several branches independently in the same window, each one correct in
isolation. The merged value that arithmetic on the deltas would suggest
(taking the lower number, or subtracting both reductions) was wrong every
single time, because the sets of items each branch had fixed overlapped in
ways neither branch could see.

**The rule.** On a ratchet-constant merge conflict, never pick a side and
never compute a value from the two branches' deltas. Put in a value the
guard is guaranteed to reject, run the guard, and read the real number back
out of its own failure message.

**Enforcement.** Documented as the required resolution procedure for any
numeric-ratchet merge conflict, because the guard itself is the only source
of truth for the number once more than one branch has touched it.

### Two sessions working one repository share one stash stack and one main branch

**Observation.** Two independent sessions worked against the same repository
at the same time without realizing it, and both planned the same merge queue.
The tell was a merge reporting "already up to date" on a branch that had been
confirmed, minutes earlier, not to be merged yet, and a shared branch's head
moving without either session having made the commit itself. Separately, a
stash entry pushed by one session's agent was visible to, and poppable by,
the other session's worktrees, because every worktree of a clone shares one
underlying git directory.

**The rule.** Before touching the shared integration branch, check whether
another session is active. If two sessions are genuinely both live, split
ownership explicitly: one session owns the shared branch and every merge into
it, the other owns dispatch and hands over finished branches by name, and
neither commits into the shared branch while the other owns it.

**Enforcement.** A pre-tool-use hook blocking the specific stash subcommands
that mutate the shared stack, plus an explicit habit of checking for other
active sessions before any merge; the hook exists because the written rule
alone was broken repeatedly, including by agents whose own brief quoted it.

### A worktree the dispatch tool creates for you can be based on a stale cached copy of the default branch

**Observation.** Dispatching several workers with an automatic worktree
feature produced worktrees checked out at a commit several revisions behind
the actual current default branch, not at the branch the orchestrator was
working from and not at the true current tip. Every worker built and tested
against that stale base, and every piece of generated output tied to that
base (in this case, rendered visual regression baselines) conflicted at
merge time with work already ahead of it.

**The rule.** Never trust that a freshly created worktree reflects the
current state of the default branch. Have the very first thing a dispatched
worker does be an explicit fetch and an explicit checkout of a new branch
from the remote's current tip, then verify the resulting commit and branch
name before doing anything else.

**Enforcement.** Stated as the mandatory first two commands in every worktree
dispatch brief, with an explicit verification step immediately after them,
because a silent no-op on the checkout step has also been observed under
certain sandboxing conditions.

## Windows and shell traps

### Git Bash rewrites a leading-slash argument into a Windows path, silently

**Observation.** A command-line tool call whose argument text happened to
contain something that looks like a POSIX absolute path (an API route, a
label starting with a slash) had that fragment silently rewritten into a
Windows path by MSYS path conversion, inside an otherwise correctly quoted
string, with no error and no warning. The damage showed up later as garbled
prose in a filed record.

**The rule.** Any command run through a Git-Bash-based shell whose arguments
contain a leading-slash token that is not meant as a real filesystem path
(a route, a regex, a URL fragment) needs path conversion disabled for that
call. Passing the same content through a file rather than an inline argument
avoids the problem entirely, since file contents are never path-converted.

**Enforcement.** A documented environment-variable prefix for the affected
shell, plus preferring "read body from file" flags over inline string
arguments wherever the underlying tool supports it.

### Backticks or parentheses in a shell `-m`/`--body` argument get substituted before the target program ever sees them

**Observation.** Commit and pull-request messages built as inline
double-quoted shell arguments repeatedly lost backticked code spans or broke
outright on unescaped parentheses, because the shell treats those as command
substitution and grouping syntax, not literal text. This happened more than
once in the same working session despite already being a known trap, and it
happened specifically with the merge-commit message form, which gets
overlooked because it feels like a throwaway string.

**The rule.** Any commit message, pull-request body, or issue comment with
punctuation worth preserving exactly should be written to a file first and
passed by file reference, never built as an inline `-m` or `--body` string.

**Enforcement.** Stated as a standing git convention, and it is the reason
this repo's own contribution instructions ask for multi-line commit messages
to go through a file rather than an inline flag.

### A native build of a text-processing tool on Windows can emit CRLF and break `\n`-only parsing

**Observation.** A command-substitution idiom that read values into a shell
array stripped trailing newlines but not trailing carriage returns, because a
locally installed build of a common JSON tool emitted Windows line endings.
Values downstream silently carried an invisible trailing character, which
broke exact string matches and arithmetic comparisons in ways that looked
like unrelated bugs.

**The rule.** When a value crossing a process boundary on Windows behaves
inconsistently in string comparisons, check for a trailing carriage return
before looking anywhere else. Strip it explicitly rather than assuming the
newline-stripping idiom you're using handles it.

**Enforcement.** Prose in the tooling notes for anyone building a similar
pipeline on Windows; no generic mechanical guard is practical here because
the specific tool and idiom vary.

### A healthy process tree can look wedged when every visible ancestor is idle

**Observation.** A long-running build step showed a launcher process at
effectively zero CPU, with a child also at zero CPU, several levels above the
process actually doing the work. The shortcut rule of "check the immediate
child's CPU, not the parent's" is one level too shallow when a launcher
re-execs through more than one intermediate stub before reaching the real
worker.

**The rule.** To tell whether a long-running step is alive, walk the entire
descendant process tree, not one level down. If anything in the tree is
burning CPU or spawning new children, it is progressing regardless of what
every ancestor shows.

**Enforcement.** Not mechanically enforced; documented as the diagnostic
procedure in the runbook for long build or test steps, since guessing wrong
here costs a killed, otherwise-healthy run.

### A long gate or build step can exceed a tool call's own hard timeout

**Observation.** A merge-time gate's total runtime grew, guard by
individually justified guard, past the hard ceiling a single foreground tool
invocation is allowed to run for. Past that point it gets silently
backgrounded, and a caller that then waits for a notification is never woken,
because a backgrounded job's completion does not resume a turn that ended
waiting on it.

**The rule.** Know the tool call's timeout ceiling, and if a step can
approach it, split the step into pieces that each fit comfortably inside it,
run in the foreground with an explicit timeout set, rather than backgrounding
a long step and waiting on a notification that may never come. Do not treat
a slow step as evidence it should be trimmed; treat a growing gate as
evidence it needs a splitting strategy.

**Enforcement.** Documented as the required invocation pattern for the one
gate long enough to hit this, with the two-piece split spelled out
explicitly in the runbook rather than left to be rediscovered.

## CI and billing

### A gate that has never been made to fire is not proven to work

**Observation.** A conditional CI job that was supposed to fire on a specific
build outcome had never fired once in its life; reading its trigger
expression could not reveal why, because the expression itself was correct
and the job died one step further in. Separately, a scheduled alert meant to
open a tracking issue automatically when a scheduled run went red had also
never been observed firing on a genuinely broken build, until one finally did
and it worked exactly as designed. Forcing the first case to fire, by turning
off every expensive job on a throwaway branch and manufacturing the exact
trigger condition, cost a couple of billed minutes and found the real bug
immediately.

**The rule.** Any job or alert gated behind a condition needs to be observed
actually firing, once, before it counts as proven. If it has never fired
naturally, force the exact condition on a disposable branch with every
expensive step disabled, rather than trusting a reading of the configuration.

**Enforcement.** A recorded, one-time forced-fire test for each conditional
gate or alert, kept as evidence it works, since nothing else demonstrates a
negative ("this correctly does nothing until condition X") is implemented
correctly.

### A console defaulting to a legacy code page can crash on the first non-ASCII byte and swallow every verdict behind it

**Observation.** A test-runner wrapper decoded its subprocess output as UTF-8
with a fallback that manufactured a substitute character for anything it
couldn't decode cleanly, which is fine on a console that can print that
substitute character and fatal on one that can't. On a CI runner whose
console defaulted to a legacy code page, that substitute character itself
could not be encoded back out, so the wrapper crashed before it ever reported
which tests had actually passed or failed. Every scheduled run affected by it
reported a bare, uninformative failure with no real signal at all, for
several runs in a row before anyone noticed the pattern.

**The rule.** A tool that reconciles or summarizes test output has to
tolerate encoding failures on both the way in and the way out. Configure
standard output and error streams to replace un-encodable characters rather
than crash, on every platform the tool will actually run on, not just the
one it was written on.

**Enforcement.** An explicit stream reconfiguration at the top of the
affected script; the failure is otherwise invisible until a CI runner with a
different default encoding happens to hit it.

### Two cron schedules sharing one concurrency group with cancel-in-progress silently cancel each other

**Observation.** Two scheduled workflow triggers, meant to run independently,
were configured into the same concurrency group with the setting that
cancels an in-progress run when a new one starts. On the days both schedules
happened to fire close together, the second one canceled the first before it
could finish, and a downstream job gated on the first one completing was
skipped by its own conditional check on whatever run survived. The visible
symptom was an absence: a job that should have run on a regular cadence
simply had no result for that day, which reads as "nobody looked" rather
than "something failed."

**The rule.** Two schedules that must both complete independently cannot
share a concurrency group with cancel-in-progress enabled. Key the
concurrency group by something that actually distinguishes the two triggers,
or don't share one at all.

**Enforcement.** A test asserting the workflow's concurrency-group key
differs for the two schedules, since the failure mode produces no error and
no red job, only a missing run.

## Issue tracking and documentation drift

### An issue body describes what someone wanted, not what's true

**Observation.** An issue proposed a specific fix based on a plausible-sounding
rule (rejecting output whose proportion of non-ASCII characters looked
"wildly out of line" with the rest of a dataset). Measuring against real
data showed no threshold could separate the intended bad case from ordinary,
legitimate non-Latin-script text, which would have made the proposed fix
reject valid input across several real scripts before ever catching the bug
it was meant to catch. The issue's stated premise about a second function
being unreachable "legacy" code was also false; it had no caller anywhere
because it had never been wired in yet, not because it was dead.

**The rule.** Treat any premise or proposed fix written into an issue as a
claim to verify against the actual code and actual data, not as something to
implement on trust. When a premise is disproven, pin the disproof as a test,
not just a closing comment, or the same wrong idea gets proposed again by
someone reading only the prose.

**Enforcement.** A named test asserting the disproven claim directly (in
this case, that no single threshold separates the two populations), so the
argument cannot silently rot back into the code.

### A merge commit's closing keyword closes nothing unless it reaches the tracker's remote

**Observation.** A merge commit's message included a standard closing
keyword referencing an issue number, on a local default branch that was
substantially ahead of, and not pushed to, the remote the issue tracker
actually watches. The closing keyword parser only runs on commits the remote
service receives, so the issue stayed open, and it was reported as closed
based on the commit message alone, for hours, until someone checked the live
tracker directly.

**The rule.** Never rely on a closing keyword in a commit message to change
an issue's state unless that commit has actually been pushed to the tracked
remote. Close explicitly, through the tracker's own interface, naming the
local commit if the remote is behind, and say so in the closing comment.

**Enforcement.** A habit of confirming issue state through the tracker's own
listing after any claimed closure, not through the commit log; no generic
mechanical check can catch a remote that is simply behind by design.

### Work that is merged and shipped can sit open in the tracker indefinitely

**Observation.** A sweep comparing merged commit history against the open
issue list found a batch of issues whose fixes had been written, merged, and
folded into the project's own changelog, and were still sitting open with no
comment at all. Nothing in the normal flow fails when the closing step gets
skipped after a fold-in that already feels like completion: the structural
guards check code, the test suite checks behavior, and neither one can see
an open issue whose fix already shipped.

**The rule.** Periodically compare the commit history against the open issue
list looking for issues with source-changing commits that never got a
closing action. Run it at the start of a work session, not only at the end,
so a redirect elsewhere doesn't compound the backlog.

**Enforcement.** A script that flags any open issue with commits naming it
as a "suspect," checked before dispatching new work onto anything with an
open status that might already be done.

### A comment or closure claiming a fix already exists is a citation to verify, not evidence

**Observation.** Issue comments described a fix as already complete, naming
a specific commit and a specific branch, in some detail and with confident
verification language. The named commit and branch existed nowhere in the
repository. In the sharper version of the same failure, an issue was marked
fully closed on the strength of comments describing a complete implementation
that also did not exist anywhere, which is worse than staying open, because a
closed issue with confident comments gets skipped by anyone scanning for
outstanding work rather than investigated.

**The rule.** A citation to a specific commit or branch inside an issue
thread, and a closure itself, are both claims like any other. Verify a
commit actually exists before it changes your plan, and re-verify a closed
issue's claimed resolution the same way you would an open one's proposed
fix, rather than trusting the closed state to mean the work is real.

**Enforcement.** A one-command check (does the named object resolve in the
repository) before trusting any citation, applied even to closed issues, not
only open ones.

### A scope cut recorded only in a code comment is invisible to the tracker

**Observation.** Two deliberate, reasonable engineering decisions to defer
part of a feature were written as code comments explaining the deferral, and
never filed as tracked issues. Months later, someone asked why the deferred
work had never been picked back up, and the answer was found only by reading
the source, because the decision was invisible to every tool that scans the
issue tracker.

**The rule.** When a scope cut, a budget or bound chosen mid-implementation,
or a "left for later" decision gets made, file it as a tracked issue in the
same change that makes the decision. Keep the code comment too, cross-referenced,
but the comment is never the record of record.

**Enforcement.** Prose discipline; a lint rule flagging comments containing
phrases like "for now" or "follow-up" without an adjacent issue reference is
a plausible mechanical backstop but was not itself in place when this was
found.

### A doc-recorded count used as an audit's scope makes the audit look complete while covering the wrong ground

**Observation.** A document recorded a count of how many distinct capabilities
a feature needed to handle a particular cross-cutting concern. The number was
wrong, by a wide margin, when re-derived directly from the code's own
dispatch logic, and a prior audit scoped to the documented (smaller) number
had cleanly missed most of the real surface area. The same pattern recurred
across several unrelated counts in the same project: every prose count
checked against the code that day turned out to be stale.

**The rule.** Before using any document's recorded list or count as the
scope of an audit or a sweep, re-derive it from the code directly. A number
written in prose has no mechanism keeping it true, and a stale count is worse
than no count, because it makes an incomplete sweep look finished.

**Enforcement.** Wherever a count exists purely to tell a reader "there are
this many," replace the written number with a command or a test that
recomputes it, so the prose can never go stale silently; keep a small,
curated set of such counts pinned as tests rather than scanning broadly for
every digit in a document, which mostly flags harmless historical narrative.
