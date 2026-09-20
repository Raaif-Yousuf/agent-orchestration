chore: scaffold the toolkit repo with validators and PR-triggered CI

Sets up the skeleton every later section fills in: the eight content
directories, an MIT licence, pinned dev dependencies, and the three
validators that keep the repo copy-pasteable.

- validate_skills.py checks SKILL.md and agent frontmatter against the
  Agent Skills spec and the Claude Code subagent schema, including that a
  skill's name matches its directory and its description is long enough
  to actually trigger.
- validate_repo.py checks issue forms, workflow shape, section READMEs,
  and that this repo's own CI never grows a push or schedule trigger.
- check_sanitization.py greps the tracked tree for absolute home paths,
  tokens, bare IPs, personal emails and the private project names this
  toolkit was generalised from.

Every rule has a red test as well as a green one.
