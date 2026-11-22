# GIT-01.01.01 Content-addressed objects — blobs, trees, commits and the naïve view of a snapshot

## Foundations

- A cryptographic hash gives different content different names in practice.

## Scope

Blobs, trees and commits, how each names the next, and why changing one file changes the commit's hash. Stops before tags and packfiles.

## Key concepts

object ID; blob; tree; commit

## Check

Why does editing one file in a subdirectory change the hash of the commit that records it?

## Sources

- [man git-cat-file](https://git-scm.com/docs/git-cat-file)

# GIT-01.01.02 Refs

## Scope

Branches and tags as files under `refs/`, and what moving one changes. Stops before history, which GIT-02.01.01 covers.

## Key concepts

ref; branch; HEAD

## Check

Why does resetting a branch to an older commit leave the newer commit's objects in place?

## Sources

- [man git-update-ref](https://git-scm.com/docs/git-update-ref)

# GIT-01.02.01 The index as a staging snapshot

## Scope

The index file, how `git add` updates it, and how `git commit` writes a tree from it.

## Key concepts

index; staging; tree

## Check

Why does a file edited after `git add` commit in its earlier state?

## Sources

- [man git-add](https://git-scm.com/docs/git-add)
