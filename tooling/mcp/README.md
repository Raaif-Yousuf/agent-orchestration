# tooling/mcp

An example `.mcp.json` with three servers configured generically: a
filesystem server, a code-intelligence server (Serena), and GitHub. Copy the
file to your project root, drop the servers you don't need, and fill in
whatever environment variables the ones you keep expect.

## What MCP is

MCP, the Model Context Protocol, is an open specification for connecting an
AI application to external tools and data sources: think of it as a
standardized way to plug a data source, a tool, or a workflow into any
client that speaks the protocol, instead of writing a one-off integration
per pair of (client, tool). It's maintained by Anthropic; the spec and wider
docs are at <https://modelcontextprotocol.io>. Support is broad on both
sides: Claude, ChatGPT, VS Code, Cursor, and others all speak it as clients,
and servers exist for most things worth connecting to.

## The three transports

Confirmed against the current MCP reference
(<https://docs.claude.com/en/docs/claude-code/mcp>, which currently redirects
to <https://code.claude.com/docs/en/mcp>):

- **stdio**: the server runs as a local process on your machine, and the
  client talks to it over its stdin/stdout. This is what you want for a
  server that needs direct filesystem or local-tool access, and it's what
  both `filesystem` and `serena` use below.
- **HTTP (streamable HTTP)**: a remote server you talk to over ordinary
  HTTP. This is the recommended shape for a hosted service, and it's what
  `github` uses below.
- **SSE (Server-Sent Events)**: an older remote transport, now deprecated in
  favor of streamable HTTP but still supported for servers that haven't
  moved off it yet.

## Project vs. user scope

A server can be configured at project scope, in `.mcp.json` at the project
root (this file, meant to be committed so a team shares the same servers),
or at user scope, which applies across every project on your machine and is
not something you check into a repo. Use project scope for anything the
whole team needs (a shared GitHub server, a project-specific database tool);
use user scope for something personal to your own workflow.

## Server config is executable configuration, not a settings file

Adding an MCP server is not like adding a linter config. A stdio server is
an arbitrary local process you're granting the ability to run, with
whatever filesystem and network access that process has; an HTTP server is
a remote endpoint you're granting the ability to see whatever context the
client sends it. Whatever tools a server exposes, your agent can call, and
whatever data a server can reach, your agent can read and hand to that
server. Before adding a server you don't maintain yourself:

- Read what it actually does, not just its name. A "GitHub" server and a
  "filesystem" server can both, in principle, read far more than the one
  thing you added them for.
- Check what it exposes before trusting it: most MCP-aware clients have a
  way to list a connected server's tools and their descriptions (in Claude
  Code, `claude mcp list` and the `/mcp` command); read that list once
  before you rely on the server for anything sensitive.
- Prefer a server whose source you can read over a closed one, especially
  for anything that touches credentials.

## Never put a real token in this file

Use `${ENV_VAR}` references, as in the `github` entry below, and set the
real value in your shell environment, not in the file. A committed
`.mcp.json` is read by everyone who clones the repo; a token in it is a
leaked token. Note that a few credential-shaped variable names (your Claude
API key among them) are deliberately never expanded into a remote server's
URL or headers, precisely so a project's `.mcp.json` can't be used to
exfiltrate your own client credentials to a server you just added; give a
custom variable name to anything you actually want passed through.

## The example servers

- **`filesystem`**: the reference filesystem server, run via `npx`. Scope it
  to the project directory (as shown) rather than a home directory or drive
  root.
- **`serena`**: symbol-level code navigation over an actual language server,
  instead of grep-and-read. See `tooling/cli-tools.md` for what it gives you
  and what it costs. This entry assumes `serena` is installed and on `PATH`;
  its own setup docs also document a `claude mcp add` command that writes
  this same configuration for you.
- **`github`**: GitHub's hosted MCP server over streamable HTTP, using a
  personal access token from an environment variable. Scope the token to
  only what the server actually needs.
