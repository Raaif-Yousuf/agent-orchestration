fix: accept every model value the subagent spec allows

The skill validator rejected two things that are legal: a subagent `model`
given as a full model id rather than a short alias, and skill frontmatter
keys that the host adds on top of the published spec (`model`, `context`,
`agent`).

A validator that rejects a legal value is worse than no validator, because
the first thing anyone does with it is delete it. Both cases now pass, and
both have tests on each side of the line.
