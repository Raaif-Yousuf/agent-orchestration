# Handoff: <short name>

How to use this: copy this file when you stop a session with work left to
do, and fill it in before you close the terminal, not from memory the next
day. The load-bearing rule is the one in the next paragraph; everything
else in this file exists to make that rule easy to follow.

**Separate "verified, here is the command and its output" from "believed to
work".** Do not let a sentence describing what you believe happened sit
next to a checkmark that implies it was checked. If you did not run the
command, say so plainly in the "not verified" section, even if you are
fairly confident.

## Where things stand

<One or two sentences: what state the work is in right now.>

## Committed and pushed

<!-- Only what is actually on the remote. A local commit that has not been
pushed goes in the next section, not here. -->

- <branch/commit> - <what it contains>

## Committed but not pushed, or not committed at all

<!-- Be specific about which. "Uncommitted work dies with the session" is
the reason this section exists. -->

- <what, and where it currently lives>

## Verified

<!-- Every line here names the command and shows the actual result you
saw, not the result you expected. If you ran it and it failed, say that. -->

- `<command run>` -> <actual output or result>

## NOT verified

<!-- Things you believe are true, or that you did partway, but did not
confirm with a command or a direct check. This section is not a confession;
it is what makes the handoff usable by the next person. -->

- <claim or assumption> - <why it is unverified, and how to verify it>

## Open decisions that need the owner

<!-- A question only a human with context outside this repo can answer.
Not "should I use approach A or B" if you can just decide that yourself. -->

- <decision needed> - <the options, if there are clear ones>

## Exact next action

<!-- One thing. Specific enough that whoever picks this up does not have
to re-derive what "next" means. -->

<The next concrete step, stated as an instruction.>
