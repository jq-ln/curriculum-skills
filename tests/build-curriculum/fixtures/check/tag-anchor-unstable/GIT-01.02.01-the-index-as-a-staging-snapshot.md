# GIT-01.02.01 The index as a staging snapshot

[Index](index.md) · [GIT-01](GIT-01-repository-internals.md) · [GIT-01.02](GIT-01.02-the-index.md) · Prev [GIT-01.01.02](GIT-01.01.02-refs.md) · Next [GIT-02.01.01](GIT-02.01.01-ancestry.md)

## Context

- Curriculum: Git (GIT)
- Target version: 2.47.1
- Snapshot: 2026-11-19
- Part: [GIT-01 Repository internals](GIT-01-repository-internals.md)
- Section: [GIT-01.02 The index](GIT-01.02-the-index.md)
- Section Generators:
  - The index records the tree the next commit will hold.

## Tags

- [2.43](GIT-tags.md#243): Checked against the release notes of Git 2.43.

## Goal

The next commit's tree is built from the index, not from the working tree.

## Scope

The index file, how `git add` updates it, and how `git commit` writes a tree from it.

## Key concepts

index; staging; tree

## Prereqs

- [GIT-01.01.01 Content-addressed objects — blobs, trees, commits and the naïve view of a snapshot](GIT-01.01.01-content-addressed-objects-blobs-trees-commits-and-the-naive.md): A commit pins a whole project state, because it names a tree whose hash covers every file below it.

## Check

Why does a file edited after `git add` commit in its earlier state?

## Sources

- [man git-add](https://git-scm.com/docs/git-add)
