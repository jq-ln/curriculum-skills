# GIT-01.01.02 Refs

[Index](index.md) · [GIT-01](GIT-01-repository-internals.md) · [GIT-01.01](GIT-01.01-objects.md) · Prev [GIT-01.01.01](GIT-01.01.01-content-addressed-objects-blobs-trees-commits-and-the-naive.md) · Next [GIT-01.02.01](GIT-01.02.01-the-index-as-a-staging-snapshot.md)

## Context

- Curriculum: Git (GIT)
- Target version: 2.47.1
- Snapshot: 2026-11-19
- Part: [GIT-01 Repository internals](GIT-01-repository-internals.md)
- Section: [GIT-01.01 Objects](GIT-01.01-objects.md)
- Section Generators:
  - Every object is named by the hash of its content.
  - A commit names one tree and its parent commits.

## Goal

A branch is a movable name for a commit, so moving it rewrites no object.

## Scope

Branches and tags as files under `refs/`, and what moving one changes. Stops before history, a {Synthesis} step, which [GIT-02.01.01 Ancestry](GIT-02.01.01-ancestry.md) covers.

## Key concepts

ref; branch; HEAD

## Prereqs

- [GIT-01.01.01 Content-addressed objects — blobs, trees, commits and the naïve view of a snapshot](GIT-01.01.01-content-addressed-objects-blobs-trees-commits-and-the-naive.md): A commit pins a whole project state, because it names a tree whose hash covers every file below it.

## Check

Why does resetting a branch to an older commit leave the newer commit's objects in place?

## Sources

- [man git-update-ref](https://git-scm.com/docs/git-update-ref)
