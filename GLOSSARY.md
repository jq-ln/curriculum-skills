# Glossary

Terms used in this repo. Add project terms above `## Workflow`, as [`domain.md`](docs/workflow/domain.md#glossary) describes.

## Workflow

**Accelerator**:
An optional agent skill that automates part of this repo's workflow by reading its conventions; never the source of a convention.
_Avoid_: Required skill, plugin dependency

**Spec**:
A parent issue describing a change too big for one PR; its Tickets are its sub-issues.
_Avoid_: Epic, PRD

**Ticket**:
A sub-issue of a Spec: one unit of work an agent or human can pick up. Standalone issues with no parent are just issues.
_Avoid_: Story, subtask

**Follow-up**:
An issue filed for out-of-scope work discovered while working another issue. It is linked from that issue or its PR by a comment and joined to it by a blocking edge, never as a sub-issue.
_Avoid_: TODO issue, spin-off

**Review round**:
One agent review of a PR plus the author's response pass that answers it.
_Avoid_: Review cycle, iteration

**Issue branch**:
The one short-lived branch an issue's work happens on. That work reaches `main` only through the issue's PR, as a squash merge.
_Avoid_: Feature branch, topic branch

**Release PR**:
The one standing PR, kept up to date by the release tool, whose merge cuts a release; it skips Review rounds and agents never touch it.
_Avoid_: Release branch, version bump PR
