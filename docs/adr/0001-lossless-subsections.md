# 0001: Lossless Subsections with script-derived copies

Status: Accepted

Evidence: [Field set for each doc type](https://github.com/jq-ln/curriculum-skills/issues/6#issuecomment-7011388517), building on [Doc set and file granularity](https://github.com/jq-ln/curriculum-skills/issues/5).

## Context

A Subsection becomes the teaching prompt for a tool that sees no other doc from its Curriculum, only a record of the Subsections the learner has already taken. To teach it, that tool needs the Subsection's surrounding facts: which Curriculum and release it belongs to, its Section's Generators, what each prereq established and what each tag means. Linking to those facts would make the agent load the Section, Part, prereq and tags docs, which defeats one file per Subsection (about 470 tokens instead of a whole Section or Part).

Copying the facts into every Subsection fixes that, but a fact copied by hand into hundreds of docs drifts from its source as soon as one copy is edited.

## Decision

Every Subsection is lossless: loaded alone, it carries everything needed to teach it.

- The derived Context Field copies in the Curriculum's name and code, Target version, Snapshot, Part, Section and the Section's Generators.
- Each Prereq bullet copies in the prereq's title and Goal.
- The Tags Field copies in each tag's one-line meaning, including tags copied down from the Part and Section.

Each fact is authored in one source doc. Agents and humans write only authored Fields. The build script's `derive` writes every copy, count, nav line and link from that source, and `check` re-derives the doc set and fails on any word-for-word difference.

## Consequences

- A copy is changed by editing its source and re-running `derive`. A hand edit to derived content fails `check`.
- A valid doc set can't be produced or maintained without the script, so `derive` runs in place and is idempotent, and a human can edit authored Fields and re-derive.
- An edit to one source fans out: changing a Section's Generators rewrites the Context of every Subsection under it.
- Subsections are longer than a linked design would make them, in exchange for never needing a second doc.
