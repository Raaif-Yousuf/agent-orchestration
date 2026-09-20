# tooling/settings

Example Claude Code settings files: one for a project's shared
`.claude/settings.json`, one for a personal `~/.claude/settings.json`. Copy
whichever applies, drop the keys you don't want, and fill in the paths.

## Which file to put a setting in

Claude Code reads settings from several files and combines them with a fixed
precedence. Confirmed against the current settings reference
(<https://docs.claude.com/en/docs/claude-code/settings>, which currently
redirects to <https://code.claude.com/docs/en/settings>), highest precedence
first:

1. **Managed settings** (`managed-settings.json`, MDM, or an organization's
   claude.ai console policy). Nothing you set in your own files overrides
   these. Only relevant if you're deploying Claude Code to an organization.
2. **Command line** (`claude --settings '...'`), for one session only.
3. **Project local** (`.claude/settings.local.json`): your personal
   overrides for one project. Claude Code keeps this out of git for you.
4. **Shared project** (`.claude/settings.json`): the team's file, committed
   to the repo. This is `project-settings.json` in this directory.
5. **User** (`~/.claude/settings.json`): your personal defaults for every
   project on your machine. This is `user-settings.json` in this directory.

List-valued keys, `permissions.allow` in particular, merge across every file
instead of the higher one replacing the lower one, so a project file's allow
rules and your own local additions both apply.

## Which file to commit, and which never to

- **Commit** `.claude/settings.json` (`project-settings.json` here). It is
  team configuration: permissions everyone needs, the hooks that enforce
  repo-wide rules, plugin choices. Nobody's personal preference belongs here.
- **Never commit** `.claude/settings.local.json`. Claude Code creates this
  file itself the first time you give a standing "yes, don't ask again"
  approval, and it adds the file to your global git excludes automatically,
  so you usually don't have to think about it. If you create it by hand,
  gitignore it yourself. Put personal overrides for one project here:
  a wider permission you're comfortable with but don't want to impose on
  teammates, a model override, anything you wouldn't want reviewed in a PR.
- **Never commit anything secret-adjacent** in either file. Neither
  `settings.json` nor `settings.local.json` is a good place for an actual
  token or key; use `${ENV_VAR}` references (see `tooling/mcp/README.md` for
  the same pattern applied to MCP server config) and put the real value in
  your shell environment or a local, gitignored `.env` file instead.
- `user-settings.json` here is `~/.claude/settings.json`: it lives outside
  any repository, is never committed, and applies to every project on your
  machine. It is the right place for personal taste (model, theme, status
  line) and for anything you want everywhere, not just one project.

## project-settings.json

An annotated shared project file. The interesting parts:

- `$schema` points at the published JSON schema
  (<https://json.schemastore.org/claude-code-settings.json>), which gives you
  autocomplete and inline validation in editors that support JSON schema.
- `permissions.allow` pre-approves read-only and test commands so an agent
  session doesn't stop for a permission prompt on things that can't hurt
  anything: running the test suite, running a linter, reading files. Adjust
  the actual command names to your project's stack; the shape (allow the
  read-only and test commands, leave everything mutating to ask) is the part
  worth keeping.
- The Windows/PowerShell read-only entries (`Get-ChildItem`, `Select-String`,
  `Test-Path`, and so on) are worth calling out specifically: they're
  genuinely useful on a Windows box and not something most examples online
  bother to write down, because most Claude Code documentation and examples
  assume a POSIX shell.
- `hooks.PreToolUse` wires up the three guard hooks in `tooling/hooks/`. See
  that directory's README for what each one does and the exact payload and
  decision shape a `PreToolUse` hook receives and returns.

## user-settings.json

An example personal file. `model`, `effortLevel`, and `theme` are ordinary
preferences. `statusLine` and `subagentStatusLine` point at the scripts in
`tooling/statusline/`; replace the placeholder paths with wherever you put
your copy of `bash.exe`, `jq.exe`, and the scripts themselves.
`enabledPlugins` is a plain map of plugin name to on/off; the ones listed are
examples, not a recommendation to install exactly these.
