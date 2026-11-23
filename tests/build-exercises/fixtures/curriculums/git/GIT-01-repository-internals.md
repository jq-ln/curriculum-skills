# GIT-01 Repository internals

## Intro

What a repository holds on disk, before any command that changes it.

## Appendices

- [Appendix: Manual coverage](GIT-appendix-manual-coverage.md): Which manual pages each Part draws on, to check coverage against the Target version. It cross-checks sources and teaches nothing, so no unit holds it.

## Sections

- [GIT-01.01 Objects](GIT-01.01-objects.md)
  - Every object is named by the hash of its content.
  - A commit names one tree and its parent commits.
- [GIT-01.02 The index](GIT-01.02-the-index.md)
  - The index records the tree the next commit will hold.
