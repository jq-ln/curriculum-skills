# GIT Notes

## Judgement calls

None so far.

## Scope decisions

Porcelain commands are taught only where they expose the object model.

## Ordering and granularity choices

The three object types share one unit, [GIT-01.01.01 Content-addressed objects — blobs, trees, commits and the naïve view of a snapshot](GIT-01.01.01-content-addressed-objects-blobs-trees-commits-and-the-naive.md), because none is teachable without the others.

## Build notes

Built from the manual pages of the Target version. Release names such as `GIT-2.47` are written in code spans, so they aren't read as IDs.
