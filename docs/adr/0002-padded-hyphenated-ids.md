# 0002: Padded, hyphenated IDs

Status: Accepted

Evidence: [Link and path conventions](https://github.com/jq-ln/curriculum-skills/issues/8#issuecomment-7014855610), building on [Wiki-link tooling for plain Markdown in LazyVim](https://github.com/jq-ln/curriculum-skills/issues/4) and [Pipeline from research to doc set](https://github.com/jq-ln/curriculum-skills/issues/9#issuecomment-7017961994). The link marker's end anchor was amended in review, [first](https://github.com/jq-ln/curriculum-skills/pull/25#discussion_r4635417208) and [again](https://github.com/jq-ln/curriculum-skills/pull/25#discussion_r4635495783), and [limited to prose](https://github.com/jq-ln/curriculum-skills/pull/25#discussion_r4635495787), [skipping code and raw HTML](https://github.com/jq-ln/curriculum-skills/pull/25#discussion_r4635566133) and [the links `derive` wrote](https://github.com/jq-ln/curriculum-skills/pull/25#discussion_r4635565767). Review also [scoped ID stability to renumbering](https://github.com/jq-ln/curriculum-skills/pull/25#discussion_r4635565433) and [`ls` order to the C locale](https://github.com/jq-ln/curriculum-skills/pull/25#discussion_r4635565286).

## Context

An ID is stable once its Curriculum exists, and it appears everywhere: in prose, H1s, filenames, the Context Field, Prereqs and references from other Curriculums. Agents find a Subsection by globbing its ID, and humans read a Curriculum in `ls` order. Whatever form an ID takes is fixed for every Curriculum built.

The earlier form, `GIT 7.2.3`, differed between prose and filenames. Unpadded numbers sort wrongly in `ls` (`GIT-10` before `GIT-2`), and once one level passes 9 they give mixed forms such as `GIT-1.09.3`.

## Decision

An ID is `<CODE>-PP.SS.UU`, such as `GIT-07.02.03`: the Curriculum's code, a hyphen, then each level as exactly two digits. A Part's ID is `GIT-07` and a Section's is `GIT-07.02`. The same form is used everywhere, with no translation between prose, H1s and filenames.

- A Subsection's ID always has three levels. A flat subject gains Sections.
- Numbers are padded even when a level has fewer than ten entries: `GIT-05`, never `GIT-5`.
- `check` rejects unpadded numbers and any number above 99. Reaching 99 at any level means splitting the Part or Section, never widening to three digits.
- An ID changes only when units are renumbered: a split at 99, or a Subsection inserted mid-Section, renumbers the units after it.
- A filename is the ID plus a title slug, such as `GIT-07.02.03-conflicts-stages-markers-and-styles.md`. The ID part changes only with the ID; the slug follows the title, so nothing may depend on it, and an agent finds a Subsection with the glob `GIT-07.02.03-*`.

## Consequences

- `ls` lists a Curriculum in teaching order only under byte-order collation, `LC_COLLATE=C`, such as `LC_ALL=C ls`. Locales such as `en_US.UTF-8` ignore `-` and `.`, so they list `GIT-07.02.01` before `GIT-07.02` and `GIT-07.01` before `GIT-07`. A filename starts with its ID verbatim.
- Each level holds at most 99 entries. Widening later would change every ID and filename in every existing Curriculum, so it's ruled out.
- A renumber renames the moved units' files. An old ID that no longer exists fails `check` as an unknown ID, but one the renumber reassigns to another unit still passes, so a renumber has to rewrite every reference to the units it moves. A reference from another Curriculum is plain text that `check` can't see, so it goes stale.
- The link marker the build script recognizes in authored Fields, `\b[A-Z][A-Z0-9]*-[0-9]{2}(\.[0-9]{2}){0,2}(?![.-]?\w)`, depends on this form. It uses `[0-9]` rather than `\d`, which matches any Unicode digit in most regex engines. A match with the Curriculum's own code becomes a link, and an unknown one is a `check` error; a match with another code stays plain text.
- The end anchor stops a malformed ID from matching as its valid prefix, so `GIT-07.2`, `GIT-07.02.031`, `GIT-07-02` and `GIT-07.02a` don't link to `GIT-07` or `GIT-07.02`. It still matches an ID that ends a sentence. `check` reports any token with the Curriculum's own code that looks like an ID but doesn't match the marker.
- The marker and that report apply only to prose: the text of the parsed CommonMark document outside code spans, fenced and indented code blocks, raw HTML, autolinks and link destinations. Anything else is never linked or checked, so an author writes an ID-shaped token literally by putting it in backticks, such as `SQL-92` or the glob `GIT-07.02.03-*`.
- `derive` recognizes the links it wrote on an earlier run, such as `[GIT-07.02.03 Conflicts](GIT-07.02.03-conflicts.md)`, and refreshes each as a whole instead of matching the ID inside it, so a re-run never nests a link.
- A reference into another Curriculum uses the same form as plain text, such as `MATH-12.01.04`, never a link: Curriculums share no root directory, so a path such as `../MATH/…` would break whenever they aren't siblings.
