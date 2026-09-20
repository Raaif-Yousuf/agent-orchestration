# Data card: <dataset name>

How to use this: copy this file next to the dataset it describes (or into
`docs/` with a matching filename) and fill in every section before anyone
else builds on this data. This follows the shape of the Datasheets for
Datasets and Data Cards practice from the ML documentation literature, not
something I invented; see `templates/README.md` for the sources. Delete a
section only if it is genuinely not applicable, and say so rather than
leaving it blank.

## What this is

<One or two sentences: what the dataset contains and why it exists.>

## Provenance and licence

<!-- Where the data came from, who collected it, and under what licence
you may use, redistribute or publish derivatives of it. If you are not
sure of the licence, say that explicitly rather than guessing. -->

- Source: <where this came from>
- Licence: <licence name, or "unknown, do not redistribute until confirmed">
- Collected by: <who or what>

## Collection method

<!-- How the data was gathered: a scrape, a survey, a sensor log, a
synthetic generation process. Include the time window it covers. -->

<method, and the date range it covers>

## Size and shape

<!-- Row/record count, column or field list if tabular, file count and
total size if not. Prefer a command that prints this over a hand-typed
number that will go stale; see rules/hard-rules-catalog.md rule 6. -->

- Records: <count, or the command that prints it>
- Shape: <columns/fields, or format description>
- Size on disk: <size>

## Known biases and gaps

<!-- What the data does NOT represent well, missing populations, time
periods, or categories, and any known collection artefacts. Silence here
is read as "none", so write "not yet assessed" if that is the truth. -->

<known gaps, or "not yet assessed">

## Preprocessing applied

<!-- What transformations already happened before this version: cleaning,
deduplication, anonymisation, resampling. Link the script if there is one. -->

<preprocessing steps, or "none, this is raw">

## What it may and may not be used for

<!-- The intended use, and the uses the collection method or licence make
inappropriate. Be specific: "not suitable for X because Y", not a blanket
disclaimer. -->

- May be used for: <intended use>
- Must not be used for: <excluded use, and why>

## How to regenerate it

<!-- The exact command or pipeline that produces this dataset from its
source, so it is not a one-off artefact nobody can reproduce. -->

```
<regeneration command or pipeline reference>
```
