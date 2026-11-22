# GIT-01.01.01 Content-addressed objects — blobs, trees, commits and the naïve view of a snapshot

## Context

- Curriculum: Git (GIT)
- Target version: 2.47.1
- Snapshot: 2026-11-19
- Part: [GIT-01 Repository internals](GIT-01-repository-internals.md)
- Section: [GIT-01.01 Objects](GIT-01.01-objects.md)
- Section Generators:
  - Every object is named by the hash of its content.
  - A commit names one tree and its parent commits.

## Foundations

- A cryptographic hash gives different content different names in practice.

## Scope

Blobs, trees and commits, how each names the next, and why changing one file changes the commit's hash. Stops before tags and packfiles.

## Key concepts

object ID; blob; tree; commit

## Prereqs

None

## Check

Why does editing one file in a subdirectory change the hash of the commit that records it?

## Sources

- [man git-cat-file](https://git-scm.com/docs/git-cat-file)
