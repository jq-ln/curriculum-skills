# 0004: A single integer Format version with exact-match `check`

Status: Accepted

Evidence: [Format versioning](https://github.com/jq-ln/curriculum-skills/issues/13#issuecomment-7021363322), building on [Packaging and local install for shipped skills](https://github.com/jq-ln/curriculum-skills/issues/10).

## Context

The format doc, `docs/curriculum-format.md`, is synced into each shipped skill's `references/`, and a Curriculum outlives the skill run that built it. Producers, readers and doc sets can therefore disagree about which revision of the format they follow, and a later skill that updates or migrates a Curriculum needs to know which one it started from.

A `MAJOR.MINOR` scheme would almost never have a minor bump: an unknown H2 is a `check` error ([ADR 0003](0003-fields-parsed-by-contract.md)), so even an added optional Field breaks an older checker. Reusing the repo's release version would make prompt-only releases look like format changes.

## Decision

The Format version is one integer, starting at `1`, owned by the format doc and independent of the repo's release version.

- It's bumped only by a change to what `check` accepts or to how the Parsing section reads a doc. Wording fixes and clarifications don't bump it.
- Every bump is a breaking release of the repo; a breaking release need not bump it.
- Changes made before the first release that ships the skill edit version `1` in place.
- The format doc states it under its H1 (`Format version: 1`) and ends with a Version history section. The build script holds a `FORMAT_VERSION` constant, and CI fails when the two differ, so the script never parses its `references/` copy at runtime.
- A Curriculum records it only in `index.md`, as the derived `## Format version` Field holding just the integer, because a doc set is only checked as a whole.
- `derive` writes the Field when it's absent, leaves it when it matches, and stops with an error when it differs.
- `check` fails when the Field is missing or differs from `FORMAT_VERSION`, naming both numbers. It never reads older formats.

## Consequences

- A re-run of `derive` never relabels an old doc set as current.
- After a bump, every existing Curriculum fails `check` under the new script until it's migrated. Migration is a later skill, which starts from the recorded version.
- Contributors have to judge whether a format doc change affects `check` or parsing, and bump and mark the release breaking when it does.
