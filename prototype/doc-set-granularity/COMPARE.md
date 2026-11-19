# Layout comparison (PROTOTYPE, throwaway)

Source: `/home/jqln/Documents/curriculum/git.md`. 19 Parts, 52 Sections, 192 Subsections.

Every layout is flat (one directory) and shares the same non-unit docs: `index.md`, `GIT-overview.md`, `GIT-fields-and-tags.md`, `GIT-sources.md`, `GIT-notes.md`, `.marksman.toml`. Only the unit granularity differs. Open each layout's `index.md` and `LOADING.md`.

Example unit: GIT 7.2.3 Conflicts (was 17.3).

| Layout | Grain | Dir | .md files | Median unit-file lines | Max unit-file lines | ~Tokens to read GIT 7.2.3 | ~Tokens with transitive prereqs (whole files) | Files for that |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | per Subsection | [A-per-subsection](A-per-subsection/index.md) | 268 | 10 | 54 | 471 | 8,166 | 24 |
| B | per Section | [B-per-section](B-per-section/index.md) | 76 | 32 | 86 | 3,084 | 16,574 | 11 |
| C | per Part | [C-per-part](C-per-part/index.md) | 24 | 97 | 249 | 7,835 | 23,472 | 6 |

Known prototype gaps:

- Only Prereqs lines are rewritten to new IDs and links. Old numbers in prose (Scope, Check, Notes) are left as-is.
- In layouts B and C, version tags sit in headings, so anchors carry them (`#git-723-conflicts-stages-markers-and-styles-256-298-dev`).
