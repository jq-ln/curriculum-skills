# 0007: Learner progress lives outside the doc set, keyed by ID

Status: Accepted

Evidence: [Marking units complete in a Curriculum](https://github.com/jq-ln/curriculum-skills/issues/52), raised while resolving [Making the branch graph visible in the doc set](https://github.com/jq-ln/curriculum-skills/issues/41).

## Context

A Curriculum with a core and Parts taken in the order a learner needs ([ADR 0006](0006-part-level-needs-and-within-part-reading-order.md)) gives no single linear position to remember, so a learner needs some record of which Parts, Sections and Subsections they've finished. The obvious place is the doc set itself, such as a task-list item, `- [x]`, on each unit in its parent's child list or the index's Parts table. [ADR 0001](0001-lossless-subsections.md) already assumes the other place: the teaching tool sees a Subsection and "a record of the Subsections the learner has already taken", which isn't part of the Curriculum.

That state is neither authored nor derived. It isn't a fact the Curriculum teaches or a decision behind it, and it can't be computed from one. Every piece of a doc set is currently one or the other, with two exceptions: the Format version Field, which only `split` and migration change ([ADR 0004](0004-integer-format-version.md)), and front matter a human adds, which `derive` keeps and `check` sets aside ([ADR 0003](0003-fields-parsed-by-contract.md)). Neither sits inside a Field.

## Decision

A doc set holds no learner state. Completion, and any other per-learner progress, is kept by the tool that consumes the Curriculum, outside the doc set, keyed by unit ID. The curriculum format defines no Field, marker or list syntax for it, and the build script neither writes nor reads it.

Alternative rejected: **completion in the doc set**, as a task-list item on each unit in its parent's child list or the index's Parts table, or a Field on each unit.

- Child lists and the Parts table are derived, so a ticked item differs word for word from what `derive` gives and fails `check`. Keeping it would need content that `derive` preserves and `check` ignores, like front matter but inside a derived Field.
- A doc set is shared, such as through a git repo, so it would carry one learner's progress to every other learner, and a rebuild with `split` from a Draft would have to carry it across.
- An agent loading one Subsection to teach would pay for state that says nothing about the subject.

## Consequences

- No Format version change: `check` already fails on a task-list marker in a derived list, and this decision keeps that.
- A progress tool must handle renumbering, the one case where an ID changes, as when a Subsection is inserted mid-Section or a level splits at 99 ([ADR 0002](0002-padded-hyphenated-ids.md)). The format records no map from old IDs to new ones, so that tool has to match moved units itself, such as by title.
- Progress tracking is out of scope for this repo until a skill that consumes Curriculums needs it.
