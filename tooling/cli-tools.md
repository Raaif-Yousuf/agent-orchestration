# tooling/cli-tools.md

Short notes on the parts of a CLI setup that make a long agent session
cheaper to run. Not a shopping list, just what's actually paid for itself.

## A command-output-filtering proxy in front of the shell tool

The pattern: put a `PreToolUse` hook on the `Bash` matcher that rewrites the
command before it runs, routing it through a wrapper that filters or
truncates the output before it ever reaches the model's context. A `git
status` on a large repo, a build log, a verbose test run: most of what
those print is noise the model doesn't need to see in full to act on, and
context spent on it is context not available later in the same session.

The hook shape is the same one used in `tooling/hooks/`: read the
`PreToolUse` payload on stdin, and instead of an `allow`/`deny` decision,
return an `updatedInput` that replaces the tool's `command` with the same
command run through the proxy. The matcher is `Bash` (or `Bash|PowerShell`
if you want it on both shells); confirm the exact `updatedInput` field
against the current hooks reference
(<https://docs.claude.com/en/docs/claude-code/hooks>, which currently
redirects to <https://code.claude.com/docs/en/hooks>) since hook payload and
decision shapes have changed before and will again.

I use `rtk` for this, a Rust CLI built for exactly this purpose. Naming it
here as one implementation, not the only one: the pattern (filter before it
reaches context, not after) is what's worth copying, and any tool that can
sit in front of a command and cut its output down is a fit. Whatever
percentage a tool like this claims to save is that tool's own number, not
something measured in this repo; take it as a claim to verify against your
own usage, not a fact.

## Serena, for symbol-level code navigation

Grep-and-read works, but it's blind to what a symbol actually is: a `grep`
for a function name returns every string match, including comments and
unrelated symbols with the same name, and finding every caller of a method
means grepping for the method name and manually filtering false positives.
Serena runs an actual language server underneath and gives an agent
LSP-backed operations instead: find a symbol's definition, find its
references, get a file's symbol outline, rename a symbol project-wide. That
turns "find everywhere this function is called" from a grep-and-guess into
one accurate call.

What it costs: a language server per language in the project, which needs
installing and can be slow to index on first run for a large codebase; and
another MCP server's worth of tools and context in the session, which is
worth it for a codebase-heavy task and dead weight for a task that's mostly
writing new content. See `tooling/mcp/README.md` for how to wire it in, and
<https://github.com/oraios/serena> for the project itself.

## Everything else, one line each

- **A worktree per parallel agent** rather than one shared working directory:
  see `orchestration/README.md`; it's a process pattern, not a CLI tool, but
  it belongs in the same "makes a long multi-agent session survive contact
  with a real machine" category as everything else here.
- **`jq`**: worth having on `PATH` regardless of the status line in
  `tooling/statusline/`; most hook payloads and a lot of tool output are
  JSON, and shelling out to a small Python one-liner every time is slower
  and noisier than one `jq` call.
