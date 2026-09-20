# Knowledge base note: <the lesson, as a phrase>

How to use this: copy this file's shape (it does not have to stay a
separate template file forever, most tools that use this format want it as
a single markdown note per lesson) and fill in every section the day you
learn the thing, not later from memory. Name the file after the lesson, not
the topic.

**On naming.** Title the file with the LESSON, phrased as a short claim, not
the general subject. `a-guard-can-go-blind-and-still-look-green.md` tells
you what you will find inside months later, before you open it.
`notes-3.md` or `database-issue.md` does not, and a pile of those becomes
unsearchable the moment you have more than a dozen. If you can state the
lesson as a sentence, the filename is that sentence with the spaces turned
to hyphens.

## Description

<!-- One line: what this note is about, written so it also works as a
search result. This is the line a listing or a search tool shows before
anyone opens the file. -->

<one-line description>

## Observation

<!-- What happened, and how you know. Include how it was measured or
reproduced: a command, a log line, a specific failure. "It seemed slow"
is not an observation; "this took 40 seconds against an expected 2" is. -->

<what was observed, and the measurement or reproduction behind it>

## The rule that follows

<!-- The generalisable instruction this observation implies. Not "fix the
one broken thing", but the shape of the rule that would have prevented it
or would catch the next instance. -->

<the rule, stated so it applies beyond this one instance>

## How it is enforced

<!-- What actually makes this rule stick: a test, a lint rule, a hook, a
line in a brief that gets read every time, or "nothing yet, this is why it
needs one." A rule with no enforcement is a hope. -->

<test / lint rule / CI check / hook / "not yet enforced, and here is what should">

## Related

<!-- Links to other notes this connects to, if any. Optional. -->

- <related note or file>
