# Where everything in this repo came from

I keep this file because a reader has no way to tell, from the rest of the
repo alone, which parts are an established convention I'm passing along and
which parts I made up out of my own recorded failures. Both are useful, and
conflating them is dishonest in both directions: presenting my own habit as
an industry standard, or presenting a real standard as something I invented.
This page draws the line, file by file. Every URL below is one I fetched and
read while writing this repo's docs, not one I recalled from memory.

## 1. Adopted conventions, with citations

These are published specs or documented platform behavior. I didn't design
any of them; I generalized my own files to follow them and cite the source
in the section that uses it.

- **Agent Skills and the `SKILL.md` format.** A directory
  (`skills/<name>/SKILL.md`) with YAML frontmatter (`name`, `description`,
  plus a small set of optional keys) followed by Markdown instructions,
  loaded into an existing conversation when the description matches the
  situation. Anthropic's spec and the reference skill set:
  <https://docs.claude.com/en/docs/claude-code/skills> and
  <https://github.com/anthropics/skills>, with the design rationale in
  <https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills>.
  Used by every file in `skills/*/SKILL.md`; `skills/README.md` documents
  exactly where this repo's validator is stricter than the published spec.

- **Claude Code subagents.** A separate, isolated-context worker defined as
  `agents/<name>.md`, YAML frontmatter plus a system prompt, with its own
  tool grant and optional model choice.
  <https://docs.claude.com/en/docs/claude-code/sub-agents> (current location
  <https://code.claude.com/docs/en/sub-agents>). Used by every file in
  `agents/*.md`; `agents/README.md` lists the frontmatter fields this repo's
  validator accepts, which is a narrower set than the full spec.

- **Claude Code hooks.** Lifecycle event handlers (`PreToolUse`,
  `PostToolUse`, and others) configured in `.claude/settings.json`, capable
  of deterministically blocking a tool call by exit code or JSON decision,
  which is the mechanism `docs/tool-differences.md`'s hooks-versus-prompts
  section is built on. <https://docs.claude.com/en/docs/claude-code/hooks>
  (current location <https://code.claude.com/docs/en/hooks>). Used by all
  three scripts in `tooling/hooks/`, documented against the exact current
  payload and decision shape in `tooling/hooks/README.md`.

- **Claude Code custom slash commands, settings, plugins.** Slash commands:
  <https://code.claude.com/docs/en/slash-commands> (the same page states
  commands are now a legacy subset of skills, kept for backward
  compatibility). Settings precedence (managed, command-line, project-local,
  shared project, user) and the merge behavior for list-valued keys:
  <https://code.claude.com/docs/en/settings>, cited and applied in
  `tooling/settings/README.md`. Plugins as a bundling and distribution
  format for skills, agents, hooks and MCP servers, namespaced to avoid
  collisions: <https://code.claude.com/docs/en/plugins>, referenced in
  `docs/tool-differences.md`. I did not find an existing use of Claude
  Code's output-style feature anywhere in this repo, so it is not covered
  beyond this line: it is a real, documented convention
  (<https://docs.claude.com/en/docs/claude-code/output-styles>) that this
  toolkit simply doesn't currently apply.

- **AGENTS.md.** An open, schema-free Markdown convention for instructing
  coding agents, stewarded by the Agentic AI Foundation under the Linux
  Foundation and read natively by a long list of tools beyond Claude Code.
  <https://agents.md/>. `rules/AGENTS.md.template` is this repo's copy of
  the convention; `rules/README.md` and `docs/tool-differences.md` cite the
  same page plus Claude Code's own interop behavior
  (<https://code.claude.com/docs/en/memory>).

- **The Model Context Protocol (MCP).** An open specification, published by
  Anthropic, for connecting an AI application to external tools, data and
  workflows through one common interface instead of a bespoke integration
  per pair of client and tool. <https://modelcontextprotocol.io>, with
  Claude Code's own client behavior (the three transports, project versus
  user scope) at <https://code.claude.com/docs/en/mcp>. Used by
  `tooling/mcp/.mcp.json` and documented in `tooling/mcp/README.md`.

- **GitHub issue forms and reusable workflows.** Issue form schema
  (top-level `name`/`description`/`body`, and body element types
  `markdown`, `input`, `textarea`, `dropdown`, `checkboxes`):
  <https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms>,
  used by `.github/ISSUE_TEMPLATE/bug_report.yml` and `feature_request.yml`.
  Reusable workflow mechanics (`workflow_call`, why a reusable workflow must
  live directly in `.github/workflows/` with no subdirectory):
  <https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows>,
  used by every file in `workflows/`. Also cited there: default
  `GITHUB_TOKEN` permissions and why every workflow declares its own
  (<https://docs.github.com/en/actions/security-guides/automatic-token-authentication>)
  and how a `concurrency` group and `cancel-in-progress` interact
  (<https://docs.github.com/en/actions/using-jobs/using-concurrency>).

- **Architecture decision records.** Michael Nygard's original format
  (Title, Status, Context, Decision, Consequences), from his 2011 essay:
  <https://github.com/joelparkerhenderson/architecture-decision-record/blob/main/locales/en/templates/decision-record-template-by-michael-nygard/index.md>.
  `templates/adr.md` follows it without adding sections beyond a title and
  date.

- **Data cards / datasheets for datasets.** The Datasheets for Datasets
  practice from the ML research community: Gebru et al.,
  <https://arxiv.org/abs/1803.09010>. `templates/data-card.md` follows its
  shape, narrowed to the section list I actually check before trusting a
  dataset in a project.

- **Test-driven development.** The red-green-refactor discipline (write a
  failing test, watch it fail, write the code, watch it pass) is a
  long-established software practice, not something originating here.
  `skills/tests-first/SKILL.md` states it as a short, enforceable checklist
  rather than citing a single canonical source, because the practice
  predates any one write-up of it.

## 2. Community practice borrowed or learned from

These shaped how this repo is organized, without being a single spec I
implemented literally.

- **`anthropics/skills`** (<https://github.com/anthropics/skills>): the
  reference implementation of the Agent Skills format. I took the directory
  layout (`<name>/SKILL.md`) and the principle that the `description` field
  is a trigger condition, not a summary, and checked this repo's validator
  against it directly rather than against a secondhand description.

- **Anthropic's "Building Effective Agents"**
  (<https://www.anthropic.com/engineering/building-effective-agents>): the
  source of the orchestrator-worker framing in `orchestration/README.md`,
  named there by name. I took the pattern (one coordinator that owns
  direction and verification, several workers that each do one bounded
  piece of work) and did not take any of its specific workflow diagrams
  literally, since this repo's dispatch model is built around git worktrees
  and Claude Code subagents specifically, which that piece doesn't cover.

- **Anthropic's "Equipping agents for the real world with Agent Skills"**
  (<https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills>):
  the design rationale behind why a skill's trigger condition matters more
  than its body, cited in `skills/README.md`.

- **`obra/superpowers`** (<https://github.com/obra/superpowers>): a public
  Claude Code plugin shipping its own skills in the same
  `<name>/SKILL.md` shape used here, including its own test-driven-development
  and verification-before-completion skills. I took the shape (a short,
  enforceable checklist rather than a long essay) and the general idea that
  parallel agent dispatch and git-worktree isolation are worth writing as
  composable skills rather than one-off scripts each time; I did not copy
  its skill bodies, since mine are built around this toolkit's own recorded
  failures.

- **OpenAI's "A practical guide to building agents"**
  (<https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf>):
  the manager pattern (a coordinator delegating through tool calls to
  specialized workers) referenced alongside Anthropic's orchestrator-worker
  writeup in `orchestration/README.md`. I took the general shape of that
  pattern as independent confirmation that this isn't a Claude-Code-specific
  idea; I did not adopt anything from its safety or guardrail sections,
  which are aimed at a different kind of deployed, user-facing agent than
  the developer-directed workers this repo dispatches.

## 3. My own practice, not dressed up as a standard

Everything below is generalized out of my own project's private
configuration and my own operational notes (mined from
`~/.claude/projects/*/memory/*.md`, read-only, never copied verbatim). None
of it is an industry standard, and I'm not claiming otherwise. See
`docs/lessons.md` for the full, sanitized set this was drawn from.

- **The wired-to-nothing bug class**, as a named review step
  (`skills/wired-to-nothing/SKILL.md`): code that compiles, runs, passes its
  tests, and does nothing at runtime because nothing calls it, or because
  the write path and the read path silently disagree. The name and the
  per-shape checklist are mine, built from repeated instances on one real
  codebase, not a term I picked up elsewhere.

- **The dead-gate checklist**: a green check that is green because it is
  dead, not because anything passed (`skills/verifying-a-green-gate/SKILL.md`,
  and the "false green and dead gates" section of `docs/lessons.md`). The
  practice of deliberately planting the exact defect a guard exists to catch
  and confirming it goes red before trusting the guard's green is mine,
  arrived at after several guards were found blind in exactly this way.

- **The standing wave-brief file, rather than a per-agent paraphrase**
  (`orchestration/wave-brief.md`): one file every lane's brief points to,
  instead of retyping the same standing rules into every dispatch prompt.
  Mine, on the theory (proven repeatedly) that a paraphrase silently drops
  whatever the person writing it didn't happen to remember while still
  reading as complete.

- **The false-pass prompt**: briefing a worker to name what an obvious check
  would still miss, rather than briefing it around what the finished feature
  looks like. Mine, and the reason `agents/cold-diff-reviewer.md` and
  `skills/fixing-a-bug/SKILL.md` are both built around "what would this look
  like if it were subtly broken" rather than a feature checklist.

- **Per-lane model choice**: picking which model runs a given lane based on
  what that lane actually has to do, instead of defaulting every lane to one
  model out of habit. Mine, referenced in `orchestration/dispatch-patterns.md`.

- **The after-every-merge structural gate, and saying explicitly what it
  doesn't cover** (`workflows/merge-gate.yml`'s two-job split, and the
  matching section in `workflows/README.md`): running a fast gate after
  every single merge rather than after a batch, because a combination of
  several individually-green branches can turn `main` red in a way no single
  branch could have tripped, plus writing down next to the gate exactly what
  it does not check, because a gate's own green result is easy to
  over-read as "everything is fine" rather than "this narrower thing is
  fine." Both are mine, built from real waves where the narrower reading
  was wrong.

- **The hooks that enforce a ban prose already failed to enforce**
  (all three scripts in `tooling/hooks/`): each one exists because the rule
  it enforces was already written down, in more than one place, and broken
  repeatedly anyway, including by agents whose own brief quoted the rule
  verbatim. The general principle, that a rule broken three or more times
  by people who read it needs a mechanism rather than firmer wording, is
  mine; the specific mechanism (a `PreToolUse` hook) is Anthropic's, cited
  above.
