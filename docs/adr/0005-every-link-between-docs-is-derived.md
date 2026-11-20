# 0005: Every link between docs is derived, and prose excludes all link text

Status: Accepted. Supersedes two bullets of [ADR 0002](0002-padded-hyphenated-ids.md): what counts as prose, and how `derive` recognizes the links it wrote.

Evidence: [an authored link nested by `derive`](https://github.com/jq-ln/curriculum-skills/pull/27#discussion_r4635782303), then [links whose text names no unit or tag](https://github.com/jq-ln/curriculum-skills/pull/27#discussion_r4635867057) and [editing an accepted ADR](https://github.com/jq-ln/curriculum-skills/pull/27#discussion_r4635867105).

## Context

ADR 0002 excluded link destinations from prose but not link text, and had `derive` refresh "the links it wrote". An authored link out of the Curriculum, such as `[GIT-07.02 discussion](https://example.com)` in Scope, still had an own-code marker in its text, so `derive` wrapped a link inside a link, which CommonMark doesn't render and which a re-run would nest again. Telling the links `derive` wrote from authored ones needs a rule a second implementation can reproduce.

## Decision

- Prose is the text of the parsed CommonMark document outside code spans, fenced and indented code blocks, raw HTML, autolinks and links, both their text and their destinations. Markers are matched and own-code tokens checked only in prose.
- Every link between docs of a Curriculum is derived; only a link out of the Curriculum, to an absolute URL, is authored.
- In an authored Field or free content, `derive` identifies a link between docs from its text: a tag when the whole text is a tag name in the tags doc, otherwise a unit when the first word is an own-code ID naming a unit. It refreshes the link as a whole from that tag or unit.
- A link between docs whose text names neither is invalid, and `derive` leaves it unchanged.

## Consequences

- An ID in an authored link's text is neither linked nor checked, as in a code span.
- An author can't hand-write a link between docs, such as `[the overview](GIT-overview.md)` in the notes doc: it's invalid. They write a marker instead, or name the doc in plain text.
- A derived link whose unit a renumber removed is invalid until it's rewritten, since its ID is in link text and so isn't checked as prose.
