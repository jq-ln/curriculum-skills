# How an agent loads one Subsection plus its prereqs (layout C)

Token estimate: characters / 4. "Whole files" is what an agent gets from opening each file; "extracted" is what it gets if it cuts each needed Subsection out by heading.

## GIT 7.2.3 Conflicts: stages, markers and styles `[2.56]` `[2.98-dev]`

Direct prereqs: 2. Transitive prereqs: 23.

| Load | Files opened | Lines | ~Tokens (whole files) | ~Tokens (extracted) |
| --- | --- | --- | --- | --- |
| Unit only | 1 | 249 | 7,835 | 388 |
| Unit + direct prereqs | 2 | 316 | 9,769 | 955 |
| Unit + transitive prereqs | 6 | 764 | 23,472 | 6,441 |

Files for unit + direct prereqs:

- [GIT-3-the-index.md](GIT-3-the-index.md)
- [GIT-7-branching-and-merging.md](GIT-7-branching-and-merging.md)

Steps: open the Part file (hundreds of lines), find the `### GIT 7.2.3 …` heading, read to the next `##`/`###`; prereq links are `file#anchor` into other Part files.

## GIT 19.1.1 Life of a commit `[Synthesis]`

Direct prereqs: 3. Transitive prereqs: 63.

| Load | Files opened | Lines | ~Tokens (whole files) | ~Tokens (extracted) |
| --- | --- | --- | --- | --- |
| Unit only | 1 | 44 | 1,509 | 241 |
| Unit + direct prereqs | 4 | 358 | 11,959 | 1,030 |
| Unit + transitive prereqs | 12 | 1379 | 43,803 | 18,036 |

Files for unit + direct prereqs:

- [GIT-10-remotes-and-synchronisation.md](GIT-10-remotes-and-synchronisation.md)
- [GIT-11-transfer-protocols.md](GIT-11-transfer-protocols.md)
- [GIT-15-automation-hooks-plumbing-and-metadata.md](GIT-15-automation-hooks-plumbing-and-metadata.md)
- [GIT-19-synthesis.md](GIT-19-synthesis.md)

Steps: open the Part file (hundreds of lines), find the `### GIT 19.1.1 …` heading, read to the next `##`/`###`; prereq links are `file#anchor` into other Part files.
