# GIT-01.01 Objects

## Generators

- Every object is named by the hash of its content.
- A commit names one tree and its parent commits.

## Tags

- 2.46

## Subsections

- [GIT-01.01.01 Content-addressed objects — blobs, trees, commits and the naïve view of a snapshot](GIT-01.01.01-content-addressed-objects-blobs-trees-commits-and-the-naive.md): A commit pins a whole project state, because it names a tree whose hash covers every file below it.
- [GIT-01.01.02 Refs](GIT-01.01.02-refs.md): A branch is a movable name for a commit, so moving it rewrites no object.
