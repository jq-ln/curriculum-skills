# GIT-02.01.01 Ancestry

[Index](index.md) · [GIT-02](GIT-02-history.md) · [GIT-02.01](GIT-02.01-the-commit-graph.md) · Prev [GIT-01.02.01](GIT-01.02.01-the-index-as-a-staging-snapshot.md) · Next [GIT-03.01.01](GIT-03.01.01-cat-file.md)

## Context

- Curriculum: Git (GIT)
- Target version: 2.47.1
- Snapshot: 2026-11-19
- Part: [GIT-02 History](GIT-02-history.md)
- Section: [GIT-02.01 The commit graph](GIT-02.01-the-commit-graph.md)
- Section Generators:
  - Each commit names its parents, so history is a graph of commits.

## Tags

- [Synthesis](GIT-tags.md#synthesis): Derives how earlier units' facts follow from a few base facts, and adds no new facts of its own.

## Goal

A commit's history is every commit reachable from it through parent links, so it never changes once the commit is written.

## Scope

Reachability through parent links, the graph sense defined in MATH-03.01, and why a commit's ancestry is fixed. Stops before merge bases.

## Key concepts

ancestor; reachability; parent

## Prereqs

- [GIT-01.01.02 Refs](GIT-01.01.02-refs.md): A branch is a movable name for a commit, so moving it rewrites no object.
- [GIT-01.02.01 The index as a staging snapshot](GIT-01.02.01-the-index-as-a-staging-snapshot.md): The next commit's tree is built from the index, not from the working tree.
- MATH-03.01.02

And some prose.

## Check

Why can't a new commit change the history of an existing one?

## Sources

- [man gitrevisions](https://git-scm.com/docs/gitrevisions)
- [src revision.c](https://github.com/git/git/blob/v2.47.1/revision.c)
