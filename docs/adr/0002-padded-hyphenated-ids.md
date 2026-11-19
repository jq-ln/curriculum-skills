# 0002: Padded, hyphenated IDs

Status: Accepted

Evidence: [Link and path conventions](https://github.com/jq-ln/curriculum-skills/issues/8#issuecomment-7014855610), building on [Wiki-link tooling for plain Markdown in LazyVim](https://github.com/jq-ln/curriculum-skills/issues/4).

## Context

An ID never changes once its Curriculum exists, and it appears everywhere: in prose, H1s, filenames, the Context Field, Prereqs and references from other Curriculums. Agents find a Subsection by globbing its ID, and humans read a Curriculum in `ls` order. Whatever form an ID takes is fixed for every Curriculum built.

The earlier form, `GIT 7.2.3`, has a space, which is awkward in a filename. Unpadded numbers sort wrongly in `ls` (`GIT-10` before `GIT-2`), and once one level passes 9 they give mixed forms such as `GIT-1.09.3`.

## Decision

An ID is `<CODE>-PP.SS.UU`, such as `GIT-07.02.03`: the Curriculum's code, a hyphen, then each level as exactly two digits. A Part's ID is `GIT-07` and a Section's is `GIT-07.02`. The same form is used everywhere, with no translation between prose, H1s and filenames.

- A Subsection's ID always has three levels. A flat subject gains Sections.
- Numbers are padded even when a level has fewer than ten entries: `GIT-05`, never `GIT-5`.
- `check` rejects unpadded numbers and any number above 99. Reaching 99 at any level means splitting the Part or Section, never widening to three digits.
- A filename is the ID plus a title slug, such as `GIT-07.02.03-conflicts-stages-markers-and-styles.md`. The ID part is permanent; the slug follows the title, so nothing may depend on it, and an agent finds a unit with the glob `GIT-07.02.03-*`.

## Consequences

- A plain `ls` lists a Curriculum in teaching order, and a filename starts with its ID verbatim.
- Each level holds at most 99 entries. Widening later would change every ID and filename in every existing Curriculum, so it's ruled out.
- The link marker the build script recognizes in authored Fields, `\b[A-Z][A-Z0-9]*-\d{2}(\.\d{2}){0,2}\b`, depends on this form.
- A reference into another Curriculum uses the same form, unlinked, such as `MATH-12.01.04`, so it reads the same whether or not that Curriculum is on disk.
