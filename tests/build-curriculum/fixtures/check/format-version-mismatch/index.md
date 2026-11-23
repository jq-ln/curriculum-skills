# Git (GIT)

## Intro

How Git stores a project's history, from the object database up.

## Snapshot

2026-11-19

## Target version

2.47.1

## Format version

1

## Counts

- Parts: 3
- Sections: 4
- Subsections: 5
- Synthesis: 1
- Optional: 1

## Docs

- [Overview](GIT-overview.md)
- [Tags](GIT-tags.md)
- [Sources](GIT-sources.md)
- [Notes](GIT-notes.md)
- [Appendix: Manual coverage](GIT-appendix-manual-coverage.md): Which manual pages each Part draws on, to check coverage against the Target version. It cross-checks sources and teaches nothing, so no unit holds it.

## Parts

| Part | Title | Sections | Subsections | Needs |
| --- | --- | --- | --- | --- |
| [GIT-01](GIT-01-repository-internals.md) | Repository internals | 2 | 3 | |
| [GIT-02](GIT-02-history.md) | History | 1 | 1 | [GIT-01](GIT-01-repository-internals.md) |
| [GIT-03](GIT-03-plumbing.md) | Plumbing | 1 | 1 | [GIT-01](GIT-01-repository-internals.md) |
