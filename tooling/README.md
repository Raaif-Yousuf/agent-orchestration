# tooling

This is how I set up the harness itself: the settings files, the hooks that
enforce rules an agent's own judgment has broken before, the status line I
actually read during a session, MCP server configuration, and the CLI setup
that makes a long agent session cheaper to run. Everything here is meant to
be copied into a project that isn't mine and to work there with a few paths
changed, not read as a description of my own machine.

## What is here

- [`settings/`](settings/README.md): example `.claude/settings.json` files,
  one for a project (commit it) and one for a personal `~/.claude/settings.json`
  (never commit it), plus the precedence order between every settings file
  Claude Code reads and which one a given kind of setting belongs in.
- [`hooks/`](hooks/README.md): three `PreToolUse` hooks that block a mutating
  `git stash`, block sub-agent dispatch from inside a worktree, and block a
  recursive force-delete inside the repo. Each one exists because the rule it
  enforces was already written down in prose and broken anyway.
- [`statusline/`](statusline/README.md): a status line script built around
  three things that are not obvious until you hit them: the harness cancels
  an in-flight status line script the moment the next update fires, a native
  Windows `jq` writes CRLF into values a POSIX script doesn't expect, and the
  harness zeroes or omits fields at moments that make a naive script flash a
  wrong number.
- [`mcp/`](mcp/README.md): an example `.mcp.json` with a filesystem server, a
  code-intelligence server, and a GitHub server configured generically, plus
  what MCP is, the three transports, and how to check what a server you add
  can actually reach before you trust it.
- [`cli-tools.md`](cli-tools.md): short notes on the parts of a CLI setup
  that make a long agent session cheaper: a command-output-filtering proxy in
  front of the shell tool, and a language-server-backed code navigation tool
  used instead of grep-and-read.

## How to use this section

Start with `settings/`: get the project file committed and your personal
file set up, since almost everything else here is wired through one of
those two. Add the hooks next, they are the highest-leverage single piece of
this section because they turn a rule an agent can talk itself out of
following into one it cannot. The status line and MCP config are worth
having but are comfort and capability, not safety; add them when you want
them, not before the hooks.
