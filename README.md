# agent-orchestration

This is the pile of things I copy into a new project when I want coding agents to
be useful on it: the skills I reuse, the rules file I start from, the templates,
the CI and merge gates, and the way I run several agents at once without them
standing on each other.

Most of it started as private configuration for a project of mine. Almost every
rule in here exists because something went wrong once and I wrote down what would
have caught it, so I kept the mechanism and stripped the project.

```
$ python scripts/validate_skills.py
checked 10 definition(s), 0 problem(s)
$ python scripts/validate_repo.py
0 problem(s)
$ python scripts/check_sanitization.py
scanned 68 file(s), 0 finding(s)
$ python -m pytest -q
74 passed
```

## How it works

- Nothing here installs or imports. You copy the piece you want into your own
  repo and change the names in it. Every file is written to survive that.
- Three validators keep it honest. One checks skill and subagent frontmatter,
  one checks the templates, the issue forms and the workflow shape, and one
  greps the tree for home paths, tokens, bare IPs, emails and the private
  project names this was generalised from.
- Every validator rule has a test that proves it can fail, not just one that
  proves it passes. A check that cannot fail is not a check.
- CI runs on pull requests only, plus shellcheck over the shell scripts and
  actionlint over the workflows.

## What's in it

| Section | What you take from it |
| --- | --- |
| `skills/` | 6 Agent Skills. `wired-to-nothing` and `verifying-a-green-gate` are the two I would keep if I kept one thing. |
| `agents/` | 4 subagent definitions, including a diff reviewer that is deliberately given no ticket and no author reasoning. |
| `rules/` | `CLAUDE.md` and `AGENTS.md` templates, plus a catalog of 41 generalised hard rules to pick from. |
| `templates/` | Plan, handoff, knowledge base note, data card, ADR, review checklist. |
| `orchestration/` | How I dispatch, brief, cap, hand off and verify parallel agents. The most original part. |
| `workflows/` | 6 reusable GitHub Actions workflows, including a merge gate that runs after every merge rather than after the batch. |
| `tooling/` | Three PreToolUse hooks, settings examples, a status line, and MCP setup. |
| `docs/` | Where everything came from, how practice differs between tools, and the lessons the rest of the repo is built on. |

Full index in [`docs/INDEX.md`](docs/INDEX.md). What is an adopted convention and
what is my own is spelled out in [`docs/sources.md`](docs/sources.md).

## Use a piece of it

```
git clone https://github.com/Raaif-Yousuf/agent-orchestration
cp -r agent-orchestration/skills/wired-to-nothing .claude/skills/
cp agent-orchestration/rules/CLAUDE.md.template CLAUDE.md
python agent-orchestration/scripts/validate_skills.py
```

## Tests

`pip install -r requirements-dev.txt && pytest -q` runs the suite over the three
validators and the hooks, and the same commands run in CI on every pull request.
Run it for the current count rather than trusting the number in the block above,
which was true the day it was pasted.

MIT licensed.
