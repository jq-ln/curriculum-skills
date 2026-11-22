# Git (GIT)

## Intro

How Git stores a project's history, from the object database up.

## Snapshot

2026-11-19

## Target version

2.47.1

# GIT Overview

## Methodology

Primary sources are the Git manual pages and the Git source tree at the Target version, which was read from the release tag on kernel.org.

## Ordering rationale

The object model comes first, because every later command reads or writes objects. GIT-02 builds history on top of GIT-01.

# GIT Tags

# GIT Sources

## Families

- Git manual pages: the reference documentation shipped with Git

## Abbreviations

| Abbreviation | Expands to | Family |
| --- | --- | --- |
| man | Git manual pages, version 2.47.1 | Git manual pages |

# GIT Notes

## Judgement calls

None so far.

## Scope decisions

Porcelain commands are taught only where they expose the object model.

## Ordering and granularity choices

The three object types share one unit, GIT-01.01.01, because none is teachable without the others.

## Build notes

Built from the manual pages of the Target version. Release names such as `GIT-2.47` are written in code spans, so they aren't read as IDs.

# GIT-01 Repository internals

## Intro

What a repository holds on disk, before any command that changes it.

# GIT-01.01 Objects

## Generators

- Every object is named by the hash of its content.
- A commit names one tree and its parent commits.

# GIT-01.01.01 Content-addressed objects — blobs, trees, commits and the naïve view of a snapshot

## Goal

A commit pins a whole project state, because it names a tree whose hash covers every file below it.

## Prereqs

None

# GIT-01.01.02 Refs

## Goal

A branch is a movable name for a commit, so moving it rewrites no object.

## Prereqs

- GIT-01.01.01

# GIT-01.02 The index

## Generators

- The index records the tree the next commit will hold.

# GIT-01.02.01 The index as a staging snapshot

## Goal

The next commit's tree is built from the index, not from the working tree.

## Prereqs

- GIT-01.01.01

# GIT-02 History

## Intro

How commits link into the graph that every history command walks, using the objects of GIT-01.01.

# GIT-02.01 The commit graph

## Generators

- Each commit names its parents, so history is a graph of commits.

# GIT-02.01.01 Ancestry

## Goal

A commit's history is every commit reachable from it through parent links, so it never changes once the commit is written.

## Prereqs

- GIT-01.01.02
- GIT-01.02.01
- MATH-03.01.02
