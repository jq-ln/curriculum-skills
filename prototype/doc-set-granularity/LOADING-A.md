# How an agent loads one Subsection plus its prereqs (layout A)

Token estimate: characters / 4. "Whole files" is what an agent gets from opening each file; "extracted" is what it gets if it cuts each needed Subsection out by heading.

## GIT 7.2.3 Conflicts: stages, markers and styles `[2.56]` `[2.98-dev]`

Direct prereqs: 2. Transitive prereqs: 23.

| Load | Files opened | Lines | ~Tokens (whole files) | ~Tokens (extracted) |
| --- | --- | --- | --- | --- |
| Unit only | 1 | 10 | 471 | 388 |
| Unit + direct prereqs | 3 | 31 | 1,186 | 955 |
| Unit + transitive prereqs | 24 | 246 | 8,166 | 6,441 |

Files for unit + direct prereqs:

- [GIT-3.1.1-the-index-is-a-flattened-tree.md](GIT-3.1.1-the-index-is-a-flattened-tree.md)
- [GIT-7.2.2-the-three-way-merge-rule.md](GIT-7.2.2-the-three-way-merge-rule.md)
- [GIT-7.2.3-conflicts-stages-markers-and-styles.md](GIT-7.2.3-conflicts-stages-markers-and-styles.md)

Steps: glob `GIT-7.2.3-*.md` (or follow a link), read it, read each file its Prereqs line links to; recurse for transitive.

## GIT 19.1.1 Life of a commit `[Synthesis]`

Direct prereqs: 3. Transitive prereqs: 63.

| Load | Files opened | Lines | ~Tokens (whole files) | ~Tokens (extracted) |
| --- | --- | --- | --- | --- |
| Unit only | 1 | 10 | 330 | 241 |
| Unit + direct prereqs | 4 | 40 | 1,382 | 1,030 |
| Unit + transitive prereqs | 64 | 646 | 22,919 | 18,036 |

Files for unit + direct prereqs:

- [GIT-10.2.6-synthesis-fetch-and-push-are-mirror-images.md](GIT-10.2.6-synthesis-fetch-and-push-are-mirror-images.md)
- [GIT-11.1.8-synthesis-trace-a-clone.md](GIT-11.1.8-synthesis-trace-a-clone.md)
- [GIT-15.1.1-client-side-hooks.md](GIT-15.1.1-client-side-hooks.md)
- [GIT-19.1.1-life-of-a-commit.md](GIT-19.1.1-life-of-a-commit.md)

Steps: glob `GIT-19.1.1-*.md` (or follow a link), read it, read each file its Prereqs line links to; recurse for transitive.
