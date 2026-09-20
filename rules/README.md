# rules

Agent instruction files I copy into a new project, plus a catalog of hard
rules to draw from when writing my own. Everything here targets Claude Code
first because that is the tool I use, and the cross-tool file (`AGENTS.md`)
second because most other agentic coding tools read that instead.

## What is in here

- **`CLAUDE.md.template`** - a fill-in-the-blanks `CLAUDE.md` for a new
  project: a quick-reference card, a short numbered Hard Rules list, a
  stack table, a pitfalls section, and an index pointing at `docs/` for
  anything longer. Kept under about 120 lines on purpose; the whole point
  of a CLAUDE.md is that it is short enough that it stays true.
- **`AGENTS.md.template`** - the same idea for the open, tool-agnostic
  `AGENTS.md` convention.
- **`hard-rules-catalog.md`** - a menu of generalised, project-agnostic
  hard rules, each with a one-line reason and a named enforcement
  mechanism (a test, a lint rule, a CI check, or a hook). Pick two or three
  per project, do not copy the whole thing into a CLAUDE.md.

## How to use a piece of this in a new project

1. Copy `rules/CLAUDE.md.template` to `<new project>/CLAUDE.md` and replace
   every `<placeholder>`. Read `rules/hard-rules-catalog.md` first and pick
   the two or three rules that match a real failure mode you can already
   imagine happening in that project; write those into the Hard Rules
   section in the new project's own vocabulary.
2. If the project needs to work with agentic tools other than Claude Code,
   copy `rules/AGENTS.md.template` to `<new project>/AGENTS.md` and fill it
   in the same way. See "CLAUDE.md and AGENTS.md" below for how the two
   should relate.
3. Keep both files under version control from the start. They are read by
   the whole team (and every agent session), not personal notes.

## CLAUDE.md and AGENTS.md

`AGENTS.md` is an open, plain-Markdown convention with no required schema:
[agents.md](https://agents.md/) documents it as "a simple, open format for
guiding coding agents," read by a broad set of tools (OpenAI's Codex,
Google's Jules, Cursor, GitHub Copilot's coding agent, and dozens of
others, by that page's own count). In a monorepo, the `AGENTS.md` nearest
to the file being edited wins. Claude Code has first-class support for it:
per [Claude Code's memory docs](https://code.claude.com/docs/en/memory), it
reads a project's `AGENTS.md` automatically when there is no `CLAUDE.md` in
the working directory or above it, and a `CLAUDE.md` can pull `AGENTS.md`
in explicitly with an `@AGENTS.md` import, after which both load together.

There are two common strategies once a project wants both:

- **(a) `AGENTS.md` as the single source**, with `CLAUDE.md` reduced to an
  `@AGENTS.md` import (plus anything Claude-Code-specific, like a hook
  reference, that would not mean anything to another tool reading the
  file).
- **(b) Keep both and accept the duplication**, useful when the two files
  genuinely need to diverge.

I have historically only written `CLAUDE.md`, because Claude Code has been
my only agent. For any project going forward that I expect other tools to
touch, I use strategy (a): one file to keep true, imported rather than
copied. That is a decision for this toolkit, not an industry standard;
treat the rest of `AGENTS.md.template`'s section on this as a convention to
adapt, not a rule to follow blindly.

## `hard-rules-catalog.md` is not gospel

Every rule in the catalog was generalised from something that actually
broke on one of my own projects, with the project-specific names and
numbers stripped out. Read the "why" and the "enforce" line for each one
you consider adopting: a rule with no realistic enforcement mechanism in
your project is not worth writing down yet.

## Sources cited

- [agents.md](https://agents.md/) - the `AGENTS.md` convention, cited in
  `AGENTS.md.template` and above.
- [Claude Code: How Claude remembers your project](https://code.claude.com/docs/en/memory)
  - CLAUDE.md file locations, precedence, the `@path` import syntax, and
  the `AGENTS.md` interop behaviour described above.
