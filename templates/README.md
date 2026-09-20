# templates

File formats I reach for again and again: a plan before code, a handoff
between sessions, a knowledge-base note, a data card, an architecture
decision record, and a review checklist. Each one is a Markdown file you
copy and fill in. Every file here opens with a `# ` heading (the repo
validator enforces this) and carries a short "how to use this" line at the
top, with placeholders in `<angle brackets>`.

## What is in here

| File | What it is for |
| --- | --- |
| `plan.md` | An implementation plan written before code: goal, the observable that means "done", steps, explicit out-of-scope, risks, verification. |
| `handoff.md` | A session-to-session handoff. Separates "verified, here is the command and its output" from "believed to work" - that separation is the whole point of the file. |
| `worker-brief.md` | A stub pointing at `orchestration/worker-brief-template.md`, which is the canonical brief for dispatching an agent worker. Kept here only so `templates/` has an entry point for it. |
| `knowledge-base-note.md` | The format I use for a memory note: a filename that states the lesson, a one-line description, the observation and how it was measured, the rule that follows, and how it is enforced. |
| `data-card.md` | For a dataset used in a project: provenance, licence, collection method, size, known biases, preprocessing, allowed and disallowed uses, how to regenerate it. Adapted from the Datasheets for Datasets / Data Cards practice; see sources below. |
| `adr.md` | A short architecture decision record: context, decision, alternatives, consequences, status and date. Follows Michael Nygard's original ADR format; see sources below. |
| `review-checklist.md` | What to check before merging someone else's branch, written so it can be pasted directly into a PR comment. |

## How to use a piece of this in a new project

Copy the file you need to wherever your project keeps that kind of
document (a `docs/adr/` directory for ADRs, a `docs/` or root location for
a handoff, next to the dataset for a data card) and fill in the
placeholders. None of these need the whole toolkit installed; each file is
self-contained and says how to use itself at the top.

## Which parts are adopted conventions, versus mine

- `adr.md` and its status/context/decision/consequences structure is
  Michael Nygard's convention, not something I designed. I did not add
  extra sections beyond his original four plus a title and date, on
  purpose: the format's value is that it stays short.
- `data-card.md` follows the shape of the Datasheets for Datasets and Data
  Cards documentation practice from the ML community, not an invention of
  mine. I picked the section list to match what I actually need to know
  before trusting a dataset in a project, which is a subset of what the
  full academic practice covers.
- `plan.md`, `handoff.md`, `knowledge-base-note.md`, `worker-brief.md` and
  `review-checklist.md` are my own formats, shaped by what has actually
  gone wrong when a plan, a handoff or a review skipped a step. The
  handoff template's central rule (separate verified from believed) came
  directly from tracking down claims in my own session notes that turned
  out not to have been checked.
- `.github/ISSUE_TEMPLATE/*.yml` and `.github/pull_request_template.md`
  (in the repo root's `.github/` directory, not under `templates/`, but
  the same "format to copy and fill in" idea) follow GitHub's own issue
  forms schema; see sources below.

## Sources cited

- [Datasheets for Datasets (Gebru et al.)](https://arxiv.org/abs/1803.09010)
  - the paper `data-card.md` is adapted from; cited here and in the
    template's own header comment.
- [Architecture Decision Records - Michael Nygard's original template](https://github.com/joelparkerhenderson/architecture-decision-record/blob/main/locales/en/templates/decision-record-template-by-michael-nygard/index.md)
  - the format `adr.md` follows: Title, Status, Context, Decision,
    Consequences, from Nygard's 2011 essay "Documenting Architecture
    Decisions."
- [Syntax for issue forms - GitHub Docs](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms)
  - the schema `.github/ISSUE_TEMPLATE/bug_report.yml` and
    `feature_request.yml` follow: top-level `name`/`description`/`body`,
    and body element types `markdown`, `input`, `textarea`, `dropdown`,
    `checkboxes`.
