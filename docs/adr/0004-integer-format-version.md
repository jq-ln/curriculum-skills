# 0004: A single integer Format version with exact-match `check`

Status: Accepted

Evidence: [Format versioning](https://github.com/jq-ln/curriculum-skills/issues/13#issuecomment-7021363322), building on [Packaging and local install for shipped skills](https://github.com/jq-ln/curriculum-skills/issues/10). The rule for a missing Field was [amended in review](https://github.com/jq-ln/curriculum-skills/pull/25#discussion_r4635416770), and review [named where it's restored from](https://github.com/jq-ln/curriculum-skills/pull/25#discussion_r4635495797).

## Context

The format doc, `docs/curriculum-format.md`, is synced into each shipped skill's `references/`, and a Curriculum outlives the skill run that built it. Producers, readers and doc sets can therefore disagree about which revision of the format they follow, and a later skill that updates or migrates a Curriculum needs to know which one it started from.

A `MAJOR.MINOR` scheme would almost never have a minor bump: an unknown H2 is a `check` error in every Doc type but an Appendix and the notes doc ([ADR 0003](0003-fields-parsed-by-contract.md)), so even an optional Field added to any other Doc type breaks an older checker. Reusing the repo's release version would make prompt-only releases look like format changes.

## Decision

The Format version is one integer, starting at `1`, owned by the format doc and independent of the repo's release version.

- It's bumped only by a change to what `check` accepts or to how the Parsing section reads a doc. Wording fixes and clarifications don't bump it.
- Every bump is a breaking release of the repo; a breaking release need not bump it.
- Changes made before the first release that ships the skill edit version `1` in place.
- The format doc states it under its H1 (`Format version: 1`) and ends with a Version history section. The build script holds a `FORMAT_VERSION` constant, and CI fails when the two differ, so the script never parses its `references/` copy at runtime.
- A Curriculum records it only in `index.md`, as the `## Format version` Field holding just the integer, because a doc set is only checked as a whole.
- The Field is neither authored nor derived: only `split` writes it, when it builds a doc set from a Draft. On an existing doc set, `derive` leaves the Field when it matches and stops with an error when it's missing or differs.
- `check` fails when the Field is missing or differs from `FORMAT_VERSION`, naming both numbers. It never reads older formats.
- When the Field is missing, the error from `derive` and `check` says to restore it from the history of `index.md`, such as `git log -p index.md`, because nothing else in the doc set records the version.

## Consequences

- A re-run of `derive` never relabels an old doc set as current, even one whose Field was deleted by hand: the doc set stops at `derive` and `check` until someone restores the version it was built with from the history of `index.md`. A doc set kept without history has lost that record, and its version has to be judged against the format doc's Version history.
- A hand edit that changes the number isn't detected: `check` compares the Field only with `FORMAT_VERSION`, so editing an old doc set's Field to the current number relabels it and moves its failures from the version to the content. Only `split` and the migration skill change the Field.
- After a bump, every existing Curriculum fails `check` under the new script until it's migrated. Migration is a later skill, which starts from the recorded version.
- Contributors have to judge whether a format doc change affects `check` or parsing, and bump and mark the release breaking when it does.
