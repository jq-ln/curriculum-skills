# GIT Overview

## Methodology

Primary sources are the Git manual pages and the Git source tree at the Target version, which was read from the release tag on kernel.org.

## Ordering rationale

The object model comes first, because every later command reads or writes objects. [GIT-02 History](./GIT-02-history.md) builds history on top of [GIT-01 Repository internals](GIT-01-repository-internals.md).
