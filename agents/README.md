# agents

A subagent is `agents/<name>.md`: YAML frontmatter plus a Markdown system
prompt, defining a separate agent Claude Code can dispatch work to. The
file goes in `.claude/agents/` inside a project for a team-shared subagent,
or `~/.claude/agents/` for a personal one that follows you across projects,
the same split as skills.

## Skill vs. subagent

A skill is instructions loaded into the conversation you are already
having. It shares your context, your history, and whatever you have
already read. A subagent is a separate conversation, with its own context
window, its own tool grant, and optionally its own model. Dispatching to a
subagent costs a cold start (it has none of your context unless you hand it
over explicitly), but buys isolation: a subagent cannot see the framing
you would otherwise bring to a review, and a subagent's mistake does not
pollute your own context with a wrong path you then have to mentally
discard.

Use a skill when the task benefits from what you already know. Use a
subagent when the task benefits from NOT knowing what you know, or when
you want the work to happen without spending your own context on it.

## The frontmatter fields

```yaml
---
name: my-agent
description: Use when X.
tools: Read, Grep, Glob
model: sonnet
---
```

`name` must equal the filename stem, and `description` is required. This
repo's validator (`scripts/validate_skills.py`, which checks both skills
and agents) accepts these optional keys: `tools`, `disallowedTools`,
`model`, `permissionMode`, `mcpServers`, `hooks`, `maxTurns`, `skills`.
`model`, if set, must be one of `sonnet`, `opus`, `haiku`, `inherit`.

`tools` is the actual capability grant. Everything after the frontmatter is
the subagent's system prompt: what it is told about its job, before it
sees anything else.

## The agents here

| Agent | Tools | What it is for |
| --- | --- | --- |
| `cold-diff-reviewer` | Read, Grep, Glob | Reviews a diff having been given nothing but the diff and the file paths: no ticket, no author reasoning, no theory of the fix. The framing removal is deliberate; a reviewer primed with the intended diagnosis tends to agree with it even when it is wrong. |
| `worktree-implementer` | inherited (sonnet) | The default worker for one lane of a parallel wave: one worktree, one branch, targeted tests only, commit and stop. Never merges, never closes a tracked issue, never stashes, never kills a process by image name. |
| `merge-gate-verifier` | Read, Grep, Glob, Bash | Verifies a branch's claims against its actual diff and test evidence before it merges, rather than trusting the report. Diffs against the merge base, never against a plain comparison with the target branch. |
| `research-scout` | Read, Grep, Glob | Answers a specific question about a codebase and returns the answer plus its evidence, not a transcript of everything read along the way. |

`cold-diff-reviewer` generalizes a reviewer originally written for one
specific stack; the framing-removal idea is the part worth keeping, and it
has no dependency on any particular language or framework.

## The caveat worth writing down

A subagent's `tools` list is a real permission boundary: if you do not
grant `Bash`, the subagent cannot run shell commands, full stop. But a
**description** that says "read-only" is not the same guarantee. A
built-in agent type can be documented as read-only while still holding a
general-purpose shell tool with no narrower allowlist under the hood,
which means nothing mechanically stops it from running a mutating command
if it decided to. `merge-gate-verifier` above is a case in point: it needs
`Bash` to run `git diff` and read test output, so its read-only behavior is
enforced by its instructions, not by its tool grant. Treat the tool grant
as the actual boundary, and read what a "read-only" agent's tool list
contains before relying on the label alone.

## Sources

The subagent file format, frontmatter fields, and project-vs-personal
storage locations are Anthropic's Claude Code convention, not invented
here: <https://docs.claude.com/en/docs/claude-code/sub-agents>. This repo's
validator accepts a narrower set of frontmatter keys than the full Claude
Code spec (missing, among others, `memory`, `background`, `omitClaudeMd`,
`effort`, `isolation`, `color`, and `experimental`, and it restricts
`model` to `sonnet`, `opus`, `haiku`, `inherit` where Claude Code itself
also accepts `fable` and a full model ID). That narrowing is deliberate for
this toolkit; check `scripts/validate_skills.py` for the exact accepted
set before adding a field not listed above.
