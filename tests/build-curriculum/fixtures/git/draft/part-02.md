# GIT-02.01.01 Ancestry

## Scope

Reachability through parent links, the graph sense defined in MATH-03.01, and why a commit's ancestry is fixed. Stops before merge bases.

## Key concepts

ancestor; reachability; parent

## Check

Why can't a new commit change the history of an existing one?

## Sources

- [man gitrevisions](https://git-scm.com/docs/gitrevisions)
- [src revision.c](https://github.com/git/git/blob/v2.47.1/revision.c)

# GIT Sources added

## Families

- Git source tree: the C source of Git at the Target version

## Abbreviations

| Abbreviation | Expands to | Family |
| --- | --- | --- |
| src | Git source tree, version 2.47.1 | Git source tree |

# GIT Part notes

## Open questions

- GIT-02.01.01: no manual page states that reachability ignores grafts.
