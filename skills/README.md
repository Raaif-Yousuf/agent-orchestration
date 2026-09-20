# skills

A skill is a directory `skills/<name>/SKILL.md` with YAML frontmatter
followed by Markdown instructions. It is not a separate agent or a separate
context: it is a chunk of instructions that gets loaded into whatever
conversation Claude Code is already having, the moment the conversation
looks like the thing the skill covers. That is the whole mechanism, and it
is why the frontmatter matters more than the body.

## The frontmatter contract

```yaml
---
name: my-skill
description: Use when X happens. Also use when Y.
---
```

`name` and `description` are required. This repo's validator
(`scripts/validate_skills.py`) also enforces:

- `name` must equal the directory name, and must be lowercase-hyphenated.
- `description` must be a single line, at least 40 characters.
- Only these frontmatter keys are accepted: `name`, `description`,
  `allowed-tools`, `compatibility`, `license`, `metadata`,
  `disable-model-invocation`. Anything else is rejected.

**The description is the only thing Claude sees before the skill fires.**
It is not documentation, it is a trigger. Nothing in the body of a skill
gets read until the description convinces the model this is the moment.
So write it as a condition, not a summary: "Use when X. Also use when Y."
naming the concrete situations, not "This skill covers testing practices."
A vague description is a skill that never fires, which is functionally the
same as not having written it.

Do not invoke a skill just because its name shows up as a word in what
someone typed; several plausible skill names are also ordinary English
words. Match the actual situation the description names, not a substring.

## Installing a skill

Copy the whole directory (`SKILL.md` and anything alongside it) into
`.claude/skills/` inside a project, for a project-scoped skill that the
whole team gets when they check out the repo. Copy it into
`~/.claude/skills/` for a personal skill that follows you across every
project instead.

## Checking it

```
python scripts/validate_skills.py
```

Run this after adding or editing any skill. It also checks every subagent
definition under `agents/`, since both share one script.

## The skills here

| Skill | What it is |
| --- | --- |
| `tests-first` | The red-green loop: failing test, watch it fail, write the code, watch it pass. Adopted convention (test-driven development), stated as a short, enforceable checklist. |
| `wired-to-nothing` | Code that compiles, runs, passes its tests, and does nothing at runtime because nothing calls it. This bug-class framing and its per-shape checklist are original to this toolkit's owner. |
| `fixing-a-bug` | The full diagnostic order for a reported defect: reproduce, broaden, mutation-check, narrow, fix, revert-check, then the guard set. Combines the adopted TDD convention with the owner's own mutation-check and revert-check discipline. |
| `verifying-a-green-gate` | The "false green" family: guards, gates, and checks whose failure looks identical to their success. The checklist and the "force it red, then restore" practice are original to the owner. |
| `working-an-issue` | Checking the commit graph before starting or closing tracked work, and writing acceptance criteria that are actually falsifiable. Adopted issue-tracking discipline, sharpened by the owner's own before/after checklist. |
| `orchestrating-agents` | The trigger-and-first-moves layer for dispatching a wave of subagents: check the work isn't done, split by shared context, name skills by name, cap concurrency, verify claims, own the merge. Points at `orchestration/` for the full detail. |

## Sources

The SKILL.md format (frontmatter fields, directory-as-name convention,
description-driven triggering) is Anthropic's Agent Skills spec, not
something invented here:

- <https://docs.claude.com/en/docs/claude-code/skills>
- <https://github.com/anthropics/skills>
- <https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills>

The flat `skills/<name>/SKILL.md` layout and the practice of writing a
short, enforceable checklist rather than a long essay is shared with
community plugins built on the same convention, for example
<https://github.com/obra/superpowers>, which ships its own
test-driven-development and verification-before-completion skills in the
same shape used here.

This repo's own validator is stricter than the published spec in two ways
worth knowing about: the spec accepts several other frontmatter fields
(`when_to_use`, `model`, `context`, `agent`, and more) that this repo's
checker rejects, and the spec technically makes every field optional
(including `description`) while this repo requires both `name` and
`description` on every skill. That is a deliberate narrowing for this
toolkit, not a gap in the checker; check `scripts/validate_skills.py`
itself for the exact allowed set before adding a field that is not listed
above.
