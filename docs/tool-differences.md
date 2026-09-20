# Where practice differs between tools

I built this toolkit against Claude Code, but most of it is written to be
copy-pasteable into whatever a project actually uses. This page is the part
I keep having to re-check: which file a given tool reads, which mechanism is
actually enforced versus merely suggested, and where the vendors have
converged on a shared convention versus where they haven't. I verified every
claim here against the tool's own current documentation rather than
recalling it, and I say so where I'm not sure.

## Instruction files: CLAUDE.md, AGENTS.md, `.cursorrules`, Copilot instructions

**AGENTS.md** is the closest thing to a cross-tool standard that exists right
now. It's an open, plain-Markdown format, stewarded by the Agentic AI
Foundation under the Linux Foundation, built for exactly one purpose: a
predictable place to put the build steps, test commands and conventions an
agent needs, separate from the human-facing README. It came out of
collaboration between several agent vendors (OpenAI Codex, Google Jules,
Cursor, Factory and others), and by the project's own count over 60,000
open-source repositories already carry one. It has no required frontmatter;
it's just Markdown, and nested `AGENTS.md` files in subdirectories layer with
more specific ones taking precedence. `rules/AGENTS.md.template.md` in this
repo follows that shape.

**CLAUDE.md** is Claude Code's own instruction file, loaded at project, user
and (for organizations) managed-policy scope, plus an uncommitted
`CLAUDE.local.md` for personal overrides. As of the version documented at the
time I checked, Claude Code also reads `AGENTS.md` directly. The default
behavior is "`CLAUDE.md` if you have one, `AGENTS.md` otherwise": having any
`CLAUDE.md` (project, or an uncommitted `CLAUDE.local.md`) in your working
directory or above it turns off automatic `AGENTS.md` reading, and a setting
exists to load both together instead. If a project wants one shared file
that every tool reads, the documented pattern is a `CLAUDE.md` containing a
single `@AGENTS.md` import line plus any Claude-specific notes below it, which
`rules/CLAUDE.md.template` in this repo does.

**GitHub Copilot** reads three separate kinds of instruction file, layered:
a repository-wide `.github/copilot-instructions.md`, path-scoped instruction
files under `.github/instructions/*.instructions.md` that declare which
globs they apply to via an `applyTo` frontmatter field, and, separately,
whichever of `AGENTS.md`, `CLAUDE.md` or `GEMINI.md` it finds, nearest file
in the directory tree wins. Personal instructions outrank repository
instructions, which outrank organization-level ones.

**Cursor** has moved off the old single `.cursorrules` file entirely. Current
Cursor reads `.mdc` rule files under `.cursor/rules/`, each with its own
frontmatter controlling whether it always applies, attaches to files
matching a glob, or is left for the agent to decide is relevant, plus a
simpler `AGENTS.md` (no metadata) as an alternative for straightforward
cases. If you still have a `.cursorrules` file from an older project, treat
it as legacy: it isn't in Cursor's current documentation at all.

The practical upshot: write your durable, cross-tool instructions into
`AGENTS.md` first. Add a tool-specific file only for the things that tool
alone understands (Claude Code's `.claude/rules/` for path-scoped rules
outside a skill, Cursor's `alwaysApply` frontmatter, Copilot's per-path
`applyTo` files), and point it at the shared file with an import or a one-line
pointer rather than duplicating the prose.

## Skills vs. custom slash commands vs. subagents vs. plugins

These four are easy to conflate because they all live under `.claude/` and
all show up as something you can invoke, but they solve different problems.

**A skill** (`SKILL.md`, optionally with supporting files in the same
directory) runs in your **main conversation**, with full history, and can be
invoked either by you explicitly or by the model deciding the task matches
its description. It's the current, preferred format; Claude Code's own
documentation says custom slash commands have effectively been folded into
skills, kept only for backward compatibility. `skills/*/SKILL.md` in this
repo uses this format, and `rules/AGENTS.md.template` in this repo is the
plain cross-tool instruction file described above, not a skill.

**A custom slash command** is the older, single-file version of the same
idea: a Markdown file under `.claude/commands/`, no supporting-file directory,
invoked by typing its name. Anything you'd write as a new command today is
better written as a skill instead, specifically because a skill can ship
supporting files and a command cannot.

**A subagent** (`.claude/agents/*.md`) is a different mechanism entirely: a
separate, isolated context window with its own system prompt, its own tool
allowlist or denylist, and optionally its own model. It does not inherit your
conversation history (a plain dispatch doesn't; a `fork` does, and a fork
shares the parent's worktree and git identity too, which is worth knowing
before you use one for anything you want isolated). Use a subagent when you
want to keep a large, noisy exploration out of your main context and get back
only a summary, or when you want to force a narrower tool grant than your
main session has. `agents/*.md` in this repo are subagents.

**A plugin** is a distribution unit, not a new capability: a directory
carrying any combination of skills, subagents, hooks, MCP server
configuration and settings, with a manifest that namespaces its skills
(`/plugin-name:skill-name`) so two plugins can't collide. The decision is
really "standalone `.claude/` versus plugin," and it's about sharing, not
functionality: keep something in `.claude/` while you're iterating on it
alone, package it as a plugin once you want to hand it to a team or publish
it with versioning.

## Hooks vs. prompt instructions

This is the one distinction worth internalizing before anything else on this
list, because it explains why half of this toolkit's `rules/` catalog exists
as prose and the other half is going to end up as a hook once `tooling/`
lands: **a prompt instruction is a suggestion, and a hook is enforcement.**

CLAUDE.md, AGENTS.md and any equivalent instruction file are context. The
model reads them and, per Claude Code's own documentation, "might comply, but
isn't forced to." A hook is a shell command, an HTTP call, an MCP tool call or
a subagent that the harness itself runs at a specific point in the agent's
lifecycle (before a tool call, after one, at session start, on a user prompt,
and several other points), and a `PreToolUse` hook can return an exit code
that **deterministically blocks the action**, with no dependence on whether
the model decided to listen. The worked example in Claude Code's docs is a
hook that blocks a destructive shell command outright, regardless of what any
instruction file says about not running it.

The rule of thumb I use: if a ban has been written into an instruction file
and broken more than once by an agent that had it in its own brief, that's
the signal it needs a hook, not a stronger sentence. See `docs/lessons.md`
for the two cases in this repo's own history where that was true.

## MCP: the cross-vendor tool-server layer

The Model Context Protocol is an open standard, originally published by
Anthropic, for connecting an AI application to external tools, data sources
and prompts through one common interface, rather than every vendor building
its own bespoke integration to every data source. The protocol's own framing
is the right one: it's a standard connector, not a specific tool. An MCP
server can expose a database, a search index, a file store or a whole
workflow as a set of callable tools and resources, and any MCP-aware client,
which now includes Claude, ChatGPT, VS Code, Cursor and others, can use it
without custom glue code per pairing. Build the server once, and every client
that speaks the protocol can use it.

Don't confuse an MCP server with a skill or a subagent: MCP is how a tool
call *reaches* an external system, while a skill or a subagent is how the
agent decides *when* and *how* to use whatever tools it already has,
including MCP-provided ones.

## Summary table

| Mechanism | Enforced or suggested | Scope | Cross-tool? |
| --- | --- | --- | --- |
| `AGENTS.md` | Suggested (context) | Whole repo, or a subdirectory | Yes, by design; read natively by many agents and tools |
| `CLAUDE.md` | Suggested (context) | Project, user, or org-managed | Claude Code only, though it can import `AGENTS.md` |
| `.cursor/rules/*.mdc` | Suggested (context) | Project, glob-scoped, or manual | Cursor only |
| `.github/copilot-instructions.md` | Suggested (context) | Repo-wide, or path-scoped via a separate file | Copilot only |
| Skill (`SKILL.md`) | Suggested (context), model-invoked | Main conversation | Claude Code only as a format; the underlying idea (a packaged, discoverable prompt) has rough equivalents elsewhere |
| Slash command | Suggested (context), user- or model-invoked | Main conversation | Claude Code only |
| Subagent | Suggested (context) inside an isolated run | Its own context window and tool grant | Claude Code only as a format |
| Hook | Enforced (can block deterministically) | Whatever lifecycle event it binds to | Claude Code only as a format; the concept (a pre-commit hook, a CI gate) is universal |
| MCP server | Neither; it's a transport | Any tool call routed through it | Yes, by design; the point of the protocol |

I'm confident in the file-precedence and enforcement claims above because I
checked them against each vendor's current documentation while writing this
page. Where a vendor's docs were silent or ambiguous (for example, whether
`.cursorrules` still works at all versus simply being undocumented), I said
so rather than guessing. See `docs/sources.md` for the exact pages.
