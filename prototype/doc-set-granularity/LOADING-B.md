# How an agent loads one Subsection plus its prereqs (layout B)

Token estimate: characters / 4. "Whole files" is what an agent gets from opening each file; "extracted" is what it gets if it cuts each needed Subsection out by heading.

## GIT 7.2.3 Conflicts: stages, markers and styles `[2.56]` `[2.98-dev]`

Direct prereqs: 2. Transitive prereqs: 23.

| Load | Files opened | Lines | ~Tokens (whole files) | ~Tokens (extracted) |
| --- | --- | --- | --- | --- |
| Unit only | 1 | 86 | 3,084 | 388 |
| Unit + direct prereqs | 2 | 128 | 4,391 | 955 |
| Unit + transitive prereqs | 11 | 511 | 16,574 | 6,441 |

Files for unit + direct prereqs:

- [GIT-3.1-the-index.md](GIT-3.1-the-index.md)
- [GIT-7.2-merging.md](GIT-7.2-merging.md)

Steps: open the Section file, find the `## GIT 7.2.3 …` heading, read to the next `## `; each prereq link is `file#anchor`, so open that file and cut at the anchor's heading.

## GIT 19.1.1 Life of a commit `[Synthesis]`

Direct prereqs: 3. Transitive prereqs: 63.

| Load | Files opened | Lines | ~Tokens (whole files) | ~Tokens (extracted) |
| --- | --- | --- | --- | --- |
| Unit only | 1 | 41 | 1,479 | 241 |
| Unit + direct prereqs | 4 | 209 | 7,015 | 1,030 |
| Unit + transitive prereqs | 25 | 1085 | 35,416 | 18,036 |

Files for unit + direct prereqs:

- [GIT-10.2-fetch-pull-and-push.md](GIT-10.2-fetch-pull-and-push.md)
- [GIT-11.1-the-wire-protocols.md](GIT-11.1-the-wire-protocols.md)
- [GIT-15.1-hooks.md](GIT-15.1-hooks.md)
- [GIT-19.1-capstones.md](GIT-19.1-capstones.md)

Steps: open the Section file, find the `## GIT 19.1.1 …` heading, read to the next `## `; each prereq link is `file#anchor`, so open that file and cut at the anchor's heading.
