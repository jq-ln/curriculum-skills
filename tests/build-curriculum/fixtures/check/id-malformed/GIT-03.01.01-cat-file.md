# GIT-03.01.01 cat-file

[Index](index.md) · [GIT-03](GIT-03-plumbing.md) · [GIT-03.01](GIT-03.01-reading-objects.md) · Prev [GIT-02.01.01](GIT-02.01.01-ancestry.md)

## Context

- Curriculum: Git (GIT)
- Target version: 2.47.1
- Snapshot: 2026-11-19
- Part: [GIT-03 Plumbing](GIT-03-plumbing.md)
- Section: [GIT-03.01 Reading objects](GIT-03.01-reading-objects.md)
- Section Generators:
  - Plumbing commands print objects as Git stores them.

## Tags

- [Optional](GIT-tags.md#optional): No unit outside it depends on it, so a learner may skip it. (from GIT-03)
- [2.46](GIT-tags.md#246): Checked against the release notes of Git 2.46. (inline)

## Goal

`git cat-file -p` prints any object by its ID, as checked against [2.46](#tags).

## Scope

Printing an object's type, size and content with `git cat-file`. Stops before `git ls-tree`.

## Key concepts

cat-file; object type; pretty-print

## Prereqs

- [GIT-01.01.01 Content-addressed objects — blobs, trees, commits and the naïve view of a snapshot](GIT-01.01.01-content-addressed-objects-blobs-trees-commits-and-the-naive.md): A commit pins a whole project state, because it names a tree whose hash covers every file below it.

## Check

What does `git cat-file -p` print for a tree?

## Sources

- [man git-cat-file](https://git-scm.com/docs/git-cat-file)
