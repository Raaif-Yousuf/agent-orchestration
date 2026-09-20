# Index

Every top-level section of this repo, every file in it, one line on what it
is and when you'd copy it. I generated this list by walking the actual tree
and wrote every description from reading the file, not from its name. If a
path here doesn't resolve, that's a bug in this file; open an issue.

Run `python -m pytest -q` from the repo root for the current test count
rather than trusting a number written into prose anywhere on this page;
counts in prose go stale the moment a file is added, and this repo has a
whole section of `docs/lessons.md` about exactly that.

## Root

- **`README.md`** - the repo's front door: what this toolkit is and how to
  use a piece of it. Owned by the project, not by this index.
- **`LICENSE`** - MIT.
- **`pyproject.toml`** - `ruff` configuration for the validators and tests.
- **`requirements-dev.txt`** - pinned versions (PyYAML, pytest, ruff) so the
  validators behave the same locally and in CI.
- **`.gitattributes`** - line-ending rules: LF for shell and text, CRLF for
  `.ps1`, binary for images.
- **`.gitignore`** - standard Python/venv ignores, plus the scratch files
  used for `git commit -F` and `gh pr create --body-file`. Those got
  committed once by accident, which is why they are ignored by name now.

## `.github/` - issue forms, PR template, this repo's own CI

- **`ISSUE_TEMPLATE/bug_report.yml`** - a bug report form that requires the
  exact observed behavior, the exact reproduction steps, and the observable
  that would tell you it's fixed, because an issue with no falsifiable
  "done" is the one that never gets closed.
- **`ISSUE_TEMPLATE/feature_request.yml`** - a feature request form that
  requires the problem before the proposal, alternatives considered
  (including doing nothing), and an observable "done" the same way the bug
  report does.
- **`ISSUE_TEMPLATE/config.yml`** - disables the blank freeform issue option
  and points questions at Discussions instead of an issue.
- **`pull_request_template.md`** - what changed, why, how it was verified
  (the actual command and its actual output, not "tests pass"), what it
  doesn't cover, and a checklist that includes re-reading the issue's own
  acceptance criteria before claiming it's closed.
- **`workflows/ci.yml`** - this repo's own CI: lint and format-check with
  ruff, validate skill/agent frontmatter, validate repo structure, check
  sanitization, run the test suite, plus separate shellcheck and actionlint
  jobs. Pull-request and manual dispatch only, no cron, on purpose (see
  `workflows/README.md`'s note on scheduled workflows and billing).

## `agents/` - Claude Code subagents

- **`README.md`** - the subagent file format, its frontmatter fields, when
  to reach for a subagent instead of a skill, and the caveat that a "read
  only" description is not the same guarantee as a narrow tool grant.
- **`cold-diff-reviewer.md`** - reviews a diff given nothing but the diff and
  file paths: no ticket, no author's reasoning, no theory of the fix. Copy
  this when you want a review that can't be talked into agreeing with the
  PR description.
- **`worktree-implementer.md`** - the default worker for one lane of a
  parallel wave: one worktree, one branch, targeted tests, commit and stop.
  Copy this as the base brief for any agent you dispatch into a worktree.
- **`merge-gate-verifier.md`** - verifies a branch's claims against its
  actual diff and test evidence before it merges, diffing against the merge
  base rather than a plain branch comparison. Copy this for the agent that
  sits between "a worker says it's done" and "it's on `main`."
- **`research-scout.md`** - answers one specific question about a codebase
  and returns the answer plus its evidence, not a transcript of everything
  it read. Copy this when you want an answer, not a tour.

## `docs/` - this section

- **`README.md`** - what's in `docs/`, one line each.
- **`lessons.md`** - 30 project-agnostic operational lessons, grouped into
  false green and dead gates, agent dispatch and parallel waves, git and
  worktrees, Windows and shell traps, CI and billing, and issue tracking and
  documentation drift.
- **`sources.md`** - which conventions in this repo are adopted (with a
  citation), which are community practice learned from without copying
  literally, and which are my own, unlabeled as anything grander.
- **`tool-differences.md`** - where CLAUDE.md, AGENTS.md, Cursor rules and
  Copilot instructions actually differ; skills vs. commands vs. subagents
  vs. plugins; hooks vs. prompt instructions; MCP as the shared layer under
  all of them.
- **`INDEX.md`** - this file.

## `orchestration/` - running several agents on one repo without them stepping on each other

- **`README.md`** - the orchestrator/worker model this whole section
  assumes, and where each piece below fits into it.
- **`dispatch-patterns.md`** - when to spawn a fresh agent versus send a
  follow-up to a running one, how to split work into lanes, and per-lane
  model choice instead of defaulting every lane to the same model.
- **`worker-brief-template.md`** - the copy-pasteable brief, split into a
  standing part every lane shares and a lane-specific part written fresh
  each time.
- **`parallelism.md`** - how many agents to run at once, and why that number
  is a negotiated ceiling you adjust mid-wave, not a fixed setting.
- **`context-and-handoff.md`** - the context budget on both sides of a
  dispatch, when to retire a worker rather than run it to exhaustion, and
  what a handoff has to contain to be worth reading.
- **`verifying-agent-work.md`** - the merge side: what to check on a
  worker's branch before trusting its own report, since a wave that
  dispatches carelessly but verifies well still ships working code.
- **`wave-brief.md`** - a ready-to-copy standing brief, written
  project-agnostic with placeholders. Point every lane-specific brief at
  this file instead of retyping its rules.

## `rules/` - instruction files to copy into a new project

- **`README.md`** - how to use the two templates below together, and the
  two strategies for keeping `CLAUDE.md` and `AGENTS.md` from diverging.
- **`CLAUDE.md.template`** - a fill-in-the-blanks `CLAUDE.md`: quick
  reference, a short numbered hard-rules list, a stack table, pitfalls, and
  an index into `docs/`. Kept under about 120 lines on purpose.
- **`AGENTS.md.template`** - the same shape for the open, cross-tool
  `AGENTS.md` convention.
- **`hard-rules-catalog.md`** - a menu of generalized hard rules, each with
  a one-line reason and a named enforcement mechanism. Pick two or three per
  project; don't copy the whole catalog into a `CLAUDE.md`.

## `scripts/` - this repo's own validators

- **`check_sanitization.py`** - greps every tracked text file for absolute
  home paths, tokens, bare IPs, personal emails and this repo's own list of
  private source names. Exit 0 means clean.
- **`validate_repo.py`** - structural checks: every templated file opens
  with a `# ` heading, every section has a README, issue forms and reusable
  workflows are shaped the way GitHub expects.
- **`validate_skills.py`** - validates the YAML frontmatter of every skill
  under `skills/` and every subagent under `agents/` against this repo's
  accepted key sets.

## `skills/` - Claude Code Agent Skills

- **`README.md`** - the `SKILL.md` frontmatter contract, how the
  `description` field works as a trigger rather than documentation, and how
  this repo's validator narrows the published spec.
- **`tests-first/SKILL.md`** - the red-green loop stated as a short,
  enforceable checklist. Adopted convention (test-driven development).
- **`wired-to-nothing/SKILL.md`** - the bug class of code that compiles,
  runs, passes its tests, and does nothing at runtime, with a per-shape
  checklist. Original to this toolkit.
- **`fixing-a-bug/SKILL.md`** - the full diagnostic order for a reported
  defect: reproduce, broaden, mutation-check, narrow, fix, revert-check,
  then the guard set.
- **`verifying-a-green-gate/SKILL.md`** - the false-green family: guards and
  gates whose failure looks identical to their success, and the practice of
  forcing one red before trusting its green.
- **`working-an-issue/SKILL.md`** - checking the commit graph before
  starting or closing tracked work, and writing acceptance criteria that are
  actually falsifiable.
- **`orchestrating-agents/SKILL.md`** - the trigger-and-first-moves layer
  for dispatching a wave: check the work isn't already done, split by
  shared context, cap concurrency, verify claims, own the merge. Points at
  `orchestration/` for the full detail.

## `templates/` - file formats to copy and fill in

- **`README.md`** - what each template is for, and which ones are adopted
  conventions versus mine.
- **`plan.md`** - an implementation plan written before code: goal, the
  observable that means "done," steps, explicit out-of-scope, risks,
  verification.
- **`handoff.md`** - a session-to-session handoff that separates "verified,
  here's the command and its output" from "believed to work."
- **`worker-brief.md`** - a stub pointing at
  `orchestration/worker-brief-template.md`, the canonical worker brief.
- **`knowledge-base-note.md`** - the shape behind every entry in
  `docs/lessons.md`: a filename that states the lesson, the observation and
  how it was measured, the rule, and how it's enforced.
- **`data-card.md`** - provenance, license, collection method, size, known
  biases, allowed and disallowed uses for a dataset. Adapted from the
  Datasheets for Datasets / Data Cards practice.
- **`adr.md`** - a short architecture decision record: context, decision,
  alternatives, consequences, status and date. Follows Michael Nygard's
  original format.
- **`review-checklist.md`** - what to check before merging someone else's
  branch, written to paste directly into a PR comment.

## `tests/` - tests for this repo's own validators and hooks

- **`test_validators.py`** - unit tests over fixtures that prove each
  validator rule can actually fail, plus whole-tree runs that prove the
  checked-in content passes.
- **`test_hooks.py`** - loads each hook in `tooling/hooks/` via `importlib`
  (they're standalone scripts, not an importable package) and gives each
  one at least one red case and one green case.

## `tooling/` - the harness setup itself

- **`README.md`** - what's here and the order to adopt it in: settings
  first, hooks next (highest leverage), status line and MCP after.
- **`cli-tools.md`** - a command-output-filtering `PreToolUse` hook pattern
  for a long agent session, and Serena (LSP-backed code navigation) as an
  alternative to grep-and-read.
- **`hooks/README.md`** - how to wire the three hooks below into
  `.claude/settings.json`, the exact `PreToolUse` payload and decision
  shape they're built against, and a documented Git Bash trap when testing
  one by hand.
- **`hooks/block-git-stash.py`** - refuses a mutating `git stash` subcommand;
  `list` and `show` stay allowed. Written after the written-down ban was
  broken repeatedly anyway.
- **`hooks/block-agent-dispatch-in-worktree.py`** - refuses subagent dispatch
  when the session's working directory is inside a linked worktree rather
  than the primary checkout.
- **`hooks/block-recursive-delete.py`** - refuses a recursive, forced delete
  aimed at a path inside the repository.
- **`mcp/README.md`** - what MCP is, its three transports, project versus
  user scope, and why an MCP server is executable configuration, not a
  settings file, so read what one actually does before adding it.
- **`mcp/.mcp.json`** - an example project-scope MCP config: a filesystem
  server, a code-intelligence server (Serena), and GitHub's hosted server,
  all using `${ENV_VAR}` references rather than inline secrets.
- **`settings/README.md`** - Claude Code's settings precedence order, which
  file to commit and which to never commit, and a walkthrough of the two
  example files below.
- **`settings/project-settings.json`** - an annotated, committable
  `.claude/settings.json`: pre-approved read-only and test commands, and the
  three hooks above wired into `hooks.PreToolUse`.
- **`settings/user-settings.json`** - an example personal
  `~/.claude/settings.json`: model, effort, theme, status line wiring, and
  plugin toggles.
- **`statusline/README.md`** - why a status line needs engineering, not a
  one-line `jq` script: the harness cancels an in-flight update, a native
  Windows `jq` emits CRLF, and the harness's own data goes stale or missing
  at predictable moments.
- **`statusline/statusline.sh`** - the status line script: one `jq` pass,
  one `awk` pass, one `date` call, one `git rev-parse`, four subprocess
  spawns total regardless of how many fields it shows.
- **`statusline/subagent-statusline.jq`** - renders one row per running
  subagent in the panel below the prompt, invoked directly by `jq` rather
  than through a bash wrapper because it runs on every panel tick.

## `workflows/` - reusable GitHub Actions workflows

- **`README.md`** - why every workflow here declares both `workflow_call`
  and `workflow_dispatch`, why you must copy the file into your own
  `.github/workflows/` rather than calling it from this repo directly, and
  the measured reasoning behind `merge-gate.yml`'s two-job split.
- **`python-quality.yml`** - ruff check, ruff format --check, pytest, with a
  defensive dependency-install fallback chain.
- **`node-quality.yml`** - `npm ci`, lint, test.
- **`shell-and-actions-lint.yml`** - shellcheck over every tracked `*.sh`,
  actionlint over every workflow; treats "no shell scripts yet" as success.
- **`merge-gate.yml`** - a fast structural gate plus an optional full-suite
  job, kept as two separate jobs because a gate's green result is a
  narrower claim than "the whole suite is green."
- **`agent-pr-checks.yml`** - branch, diff-vs-claimed-files, test-collection
  and PR-body checks aimed specifically at a PR an agent opened.
- **`secret-and-path-scan.yml`** - greps a diff's added lines for the same
  private-data shapes `scripts/check_sanitization.py` checks locally: home
  paths, tokens, bare IPs, emails.
