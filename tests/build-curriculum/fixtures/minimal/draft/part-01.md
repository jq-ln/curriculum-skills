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
