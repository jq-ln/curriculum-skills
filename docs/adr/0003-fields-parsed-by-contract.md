# 0003: Fields are the only machine-readable copy, parsed by contract

Status: Accepted

Evidence: [Front matter on generated docs](https://github.com/jq-ln/curriculum-skills/issues/11#issuecomment-7018628248), building on [Pipeline from research to doc set](https://github.com/jq-ln/curriculum-skills/issues/9#issuecomment-7017961994). The rules for [fenced code and setext headings](https://github.com/jq-ln/curriculum-skills/pull/25#discussion_r4635495777) and for [the filename's ID](https://github.com/jq-ln/curriculum-skills/pull/25#discussion_r4635495805) were added in review.

## Context

The build script, `check` and any later skill need to read each doc's ID, Prereqs and Tags reliably. YAML front matter would make that easy, but it would be a second copy of facts the H2 Fields already hold. `derive` and `check` already read the Fields directly, so front matter is a copy that `derive` would have to maintain and `check` verify while no tool needs it. marksman ignores front matter, GitHub renders it as a table, and an agent loading one Subsection would pay for the duplicate in every doc.

Reading the Fields directly ties every reader to the Markdown layout, so that layout has to be specified rather than inferred from the script.

## Decision

No generated doc has YAML front matter. The ID lives in the H1 and the filename, and every other fact lives in an H2 Field: these are the only machine-readable copy.

The format doc gets a normative Parsing section, which every reader follows:

- A heading is a CommonMark ATX heading, such as `## Goal`, outside a fenced code block, so a heading-like line inside a fence is content. A setext heading (text over `===` or `---`) is a `check` error, so every heading a renderer shows is one the parser sees.
- A Part, Section or Subsection doc's H1 is exactly `<ID> <title>`, and `check` fails when that ID differs from the one its filename starts with. The other Doc types' H1s are set by the format doc.
- A Field is an H2 whose text exactly matches a Field name the format doc defines. Its content runs to the next H2 or the end of the file.
- Field order is fixed for each Doc type.
- H3 and deeper headings belong to the Field above them.
- In a Doc type whose whole Field set is fixed, an unknown H2 is a `check` error.

An Appendix and the notes doc start with their required Fields, and every H2 after those is free content that `check` doesn't parse as Fields. Front matter added by hand, such as Obsidian `aliases`, is kept by `derive` and ignored by `check`.

## Consequences

- A later skill reads a Curriculum through the Parsing section, without reading the build script.
- The Markdown layout is an interface: changing how the Parsing section reads a doc changes the Format version ([ADR 0004](0004-integer-format-version.md)).
- Because an unknown H2 is an error in a Doc type whose whole Field set is fixed, even an optional Field added to one breaks an older `check`.
- The Format version can't be recorded in front matter, so it's a Field in `index.md`.
