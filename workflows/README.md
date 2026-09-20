# workflows

Reusable GitHub Actions workflows I copy into a new repo's `.github/workflows/`
and tune with inputs, instead of writing CI from scratch each time.

Every file here declares `on: workflow_call:` so another workflow can call it
with `uses:`, and also `on: workflow_dispatch:` with the same inputs so you can
run it by hand from the Actions tab while you're setting it up. Every tunable
(Python or Node version, working directory, the actual test command, whether
to run the full suite) is an input with a default, not something hardcoded.

**GitHub requires a reusable workflow file to live in `.github/workflows/`, no
subdirectories.** That means none of the files in this `workflows/` directory
can be called directly with `uses: Raaif-Yousuf/agent-orchestration/workflows/python-quality.yml@main`;
GitHub will not find it there. Copy the file you want into your own repo's
`.github/workflows/` first, then either run it as its own workflow or `uses:`
it from another workflow in that same repo. (Source: [Reuse workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows).)

## What's here

| File | What it runs | Key inputs |
| --- | --- | --- |
| `python-quality.yml` | ruff check, ruff format --check, pytest | `python-version`, `working-directory`, `lint-paths`, `test-command` |
| `node-quality.yml` | npm ci, lint, test | `node-version`, `working-directory`, `lint-command`, `test-command` |
| `shell-and-actions-lint.yml` | shellcheck over tracked `*.sh`, actionlint over every workflow | `shellcheck-severity`, `working-directory` |
| `merge-gate.yml` | a fast structural gate plus an optional full-suite job, kept as two jobs on purpose (see below) | `gate-command`, `full-suite-command`, `run-full-suite` |
| `agent-pr-checks.yml` | branch, diff-vs-claimed-files, test-collection and PR-body checks aimed at a PR an agent opened | `protected-branch`, `test-collect-command`, `verification-heading` |
| `secret-and-path-scan.yml` | greps a diff's added lines for private-data shapes (home paths, tokens, IPs, emails) | `extra-patterns` |

`python-quality.yml` and `node-quality.yml` install dependencies defensively:
the Python one tries `requirements-dev.txt`, then `requirements.txt`, then a
`pyproject.toml` `dev` extra, then falls back to installing ruff and pytest
bare, so a repo that has none of those still gets a working run instead of a
failure on "no dependency file found".

`shell-and-actions-lint.yml` treats "no shell scripts tracked yet" as success,
not failure. A fresh repo has none, and the first thing that happens to a
check that errors on "nothing to do" is that someone deletes it.

## Pinning actions

Every action here is pinned to a major version tag (`actions/checkout@v4`),
which is what GitHub itself recommends as the minimum. A tag can be moved by
whoever owns the action, so it is not immutable; pinning to a full commit SHA
(`actions/checkout@11bd719...`) is stricter because a SHA cannot be
repointed, at the cost of needing to update the SHA yourself on every bump
instead of picking up patch releases automatically. I use major-version tags
here because this is a library meant to be copied and read, and a wall of
SHAs is harder for a stranger to sanity-check at a glance; tighten to SHA
pinning yourself if your threat model calls for it.

## Permissions

Every workflow sets `permissions:` explicitly, at `contents: read` or less,
because the default `GITHUB_TOKEN` permissions for a repository can be as
broad as read/write on everything, and a workflow that never declares
`permissions:` inherits whatever that repository's default is. Declaring it
per workflow means the workflow's own file tells you what it can do, instead
of that living in a repo setting nobody thinks to check.
(Source: [Automatic token authentication](https://docs.github.com/en/actions/security-guides/automatic-token-authentication).)

## Concurrency

`python-quality.yml` and `node-quality.yml` set `concurrency` with
`cancel-in-progress: true`, keyed on `${{ github.workflow }}-${{ github.ref }}`,
so a new push to the same branch cancels the still-running check for the
previous push instead of both finishing.
(Source: [Control the concurrency of workflows and jobs](https://docs.github.com/en/actions/using-jobs/using-concurrency).)

I did not add `concurrency` to `merge-gate.yml`, `agent-pr-checks.yml` or
`secret-and-path-scan.yml`: cancelling a merge-gate run because another one
started is the wrong default, since the whole point is to know which merge
broke something, and a cancelled run tells you nothing.

Where concurrency groups bite: two different scheduled cadences (say, an
hourly job and a nightly job) that happen to land in the same hour share a
concurrency group if you key it loosely, and one of them gets silently
cancelled. It looks exactly like a normal cancellation in the log, not like a
scheduling collision, which is what makes it slow to notice. This has cost
real runs of the one job that was supposed to run the heavy suite. Key your
concurrency group narrowly enough that two things you actually want to both
run can't land in the same group.

## Scheduled workflows and billing

One more thing worth writing down plainly: a cadence the account cannot pay
for is not a cadence. On a personal GitHub account, Actions minutes are
finite, and when they run out, a scheduled (`cron`) run fails in about two
seconds with a billing-related error, which in a job summary looks exactly
like several unrelated failures at once rather than "you're out of minutes".
Price a cron cadence against your plan before you set it, and on a personal
account prefer `pull_request` and `workflow_dispatch` triggers over `schedule`
for anything that isn't cheap. This repo's own `.github/workflows/ci.yml`
follows that rule: pull request and manual dispatch only, no cron.

## merge-gate.yml: why it's two jobs

This is the one built from real, repeated measurement rather than from
general advice, so it gets its own section.

**A wave of branches can each be green alone and turn `main` red the moment
they combine.** Anything that compares against a frozen baseline, a
structure-drift check, a file-count ratchet, a lint-violation ratchet, a
migration version, a changelog fold, is a property of the *combination* of
everything currently merged, not of any single branch. This has happened
repeatedly on real waves of merges, including one where several branches
each added a component or two and no single branch, taken alone, could
possibly have tripped the count; only the combination did. The fix is in the
workflow's shape: run the `gate` job after **every** merge, not after a batch
of them lands. If you only check at the end, you know something broke but not
which merge did it. And when a drift check goes red, the right move is
usually to document the new thing the check is now correctly flagging, not to
raise the baseline to make it pass; a bigger baseline just gives the next
five things permission to drift back up to it unexamined.

**The gate being green is not the same claim as `main` being green.** On one
real day, eleven branches were merged one after another, the gate ran after
every single one and was green every time, and `main` was red on eighteen
backend tests, not one of which lived anywhere in the gate's file list. The
gate had done its job; its job was just narrower than "everything works".
So: write down, next to wherever you configure `gate-command`, exactly what
it does **not** cover, and run `full-suite-command` (`run-full-suite: true`)
once, alone, after the wave, specifically because the gate being a subset
means it can't tell you the suite is clean.

**Proving a red is pre-existing, not something you just broke:** create a
detached worktree at the commit SHA your session started from
(`git worktree add ../checkpoint <sha>`), run the same failing test there, and
compare the result. This works because a virtual environment is just an
interpreter plus a site-packages directory; the primary checkout's
interpreter can run perfectly well against another worktree's source, so you
don't need to rebuild an environment to check whether a failure predates your
change.

## actionlint and shellcheck

`shell-and-actions-lint.yml` runs both. actionlint statically checks workflow
YAML: trigger and job syntax, `${{ }}` expression types, reusable-workflow
input and secret usage, and it also hands `run:` steps to shellcheck and
`pyflakes` where applicable, so most of what would otherwise only show up as
a red run shows up before you push.
(Source: [rhysd/actionlint](https://github.com/rhysd/actionlint).) I run it
locally the same way CI does:

```
bash <(curl -fsSL https://raw.githubusercontent.com/rhysd/actionlint/main/scripts/download-actionlint.bash)
./actionlint -color
```

shellcheck lints the shell script bodies themselves; install it from your
package manager (`apt-get install shellcheck`, `brew install shellcheck`) to
run it locally against tracked `*.sh` files the same way the workflow does.
