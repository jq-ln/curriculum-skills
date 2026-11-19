# Domain docs

How this repo records its domain language and its decisions. [`GLOSSARY.md`](../../GLOSSARY.md) at the repo root holds the terms, and `docs/adr/` holds the Architecture Decision Records (ADRs).

## Before you start

Read `GLOSSARY.md`, then the ADRs in `docs/adr/` that cover the area you're about to change. Until the first ADR is written, `docs/adr/` doesn't exist; carry on with the glossary alone.

## Glossary

`GLOSSARY.md` ends with a fixed `## Workflow` section, which defines the terms the `docs/workflow/` docs use. Add the project's own terms above `## Workflow`. Edit `## Workflow` only in a PR that changes a `docs/workflow/` doc, so the project's terms and the workflow terms don't mix.

Write each entry in the format of the `## Workflow` entries: the term in bold, its definition on the next line, and an `_Avoid_:` line listing the synonyms not to use.

Add or change an entry in the PR that introduces or changes the term, as a direct consequence of its issue (see [`issues.md`](issues.md#what-a-pr-may-touch)).

## ADRs

Create `docs/adr/` with the first ADR, when a decision first needs recording.

- Name each file `NNNN-<slug>.md`, numbered from `0001` in order, such as `0001-event-sourced-orders.md`.
- Record one decision per ADR: its context, the decision and its consequences.
- Leave an accepted ADR in place. When a later decision replaces it, mark it superseded and link the ADR that replaces it.

## Use the glossary's vocabulary

When your output names a domain concept, such as in an issue title, a refactor proposal, a hypothesis or a test name, use the term as `GLOSSARY.md` defines it, and not a synonym it lists under `_Avoid_`.

If the concept you need isn't in the glossary yet, either you're inventing language the project doesn't use, so reuse an existing term, or there's a real gap, so add the term in your PR if your issue introduces it, or note the gap in the issue.

## Flag ADR conflicts

When your output contradicts an existing ADR, say so explicitly, and give the reason for reopening it:

> _Contradicts ADR-0007 (event-sourced orders), but worth reopening because…_

## Accelerators (optional)

Delete this section if the repo uses no Accelerators. The conventions above win any conflict with a skill.

- mattpocock-skills `domain-modeling` creates and edits `GLOSSARY.md` entries and ADRs.
