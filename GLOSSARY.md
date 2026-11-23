# Glossary

Terms used in this repo. Add project terms above `## Workflow`, as [`domain.md`](docs/workflow/domain.md#glossary) describes.

## Curriculums

**Curriculum**:
The whole doc set for one subject: a flat directory of Markdown docs with an `index.md` entry point. It has an uppercase code, such as `GIT`, that never changes once the Curriculum exists.
_Avoid_: Session Map

**Part**:
A top-level portion of a Curriculum. Its doc lists its Sections.

**Section**:
A portion of a Part. Its doc holds its Generators and lists its Subsections.

**Subsection**:
A portion of a Section, and the teachable unit. Its doc carries everything an agent needs to teach it, so it can be loaded alone.
_Avoid_: Session, Topic, Chapter

**ID**:
The stable identifier of a Part, Section or Subsection, such as `GIT-07`, `GIT-07.02` or `GIT-07.02.03`: the code, a hyphen, then each level padded to two digits. It changes only when a split or a mid-Section insertion renumbers units. It takes the same form in prose, H1s, filenames, the Context Field and references from another Curriculum. A Subsection's ID always has three levels, so a flat subject gains Sections.

**Field**:
An H2 heading whose text matches a Field name the format doc defines, such as Goal or Sources, with its content up to the next H2. An authored Field is written by an agent or a human, apart from the links the build script's `derive` writes around IDs and tag markers in its prose. A derived Field is written by `derive`. A mixed Field, such as Prereqs or Tags, has authored IDs or tag names that `derive` links and copies facts beside. The Format version Field is none of these: only the build script's `split` writes it.

**Generators**:
The Field holding the few base facts a Section's Subsections collapse into. A Subsection may add Generators specific to itself.
_Avoid_: Click

**Context**:
The derived Field that copies a Subsection's surrounding facts into it: the Curriculum's name and code, Target version, Snapshot, Part, Section and the Section's Generators.

**Needs**:
The derived Part Field listing the other Parts of the Curriculum its Subsections' Prereqs land in. The index's Parts table repeats it as a column.
_Avoid_: Part Prereqs

**Appendix**:
An optional, repeatable doc of non-teaching reference material, named `<CODE>-appendix-<description>.md`. It never holds Subsections: teaching material that would go in an appendix becomes a Part tagged Optional.

**Doc type**:
One kind of doc in a Curriculum, with its own filename rule and Field set: `index.md`, the overview, tags, sources and notes docs, Part, Section, Subsection and Appendix.

**Outline**:
The human-approved skeleton of a Curriculum that fill agents work from: IDs, titles, Goals, Prereqs, Generators and tags.

**Draft**:
The throwaway, authored-only Markdown that the build script splits into the doc set; deleted once the doc set passes `check`.

**Brief**:
The optional free text that scopes a Curriculum, such as "on Arch Linux", passed verbatim into every stage prompt.
_Avoid_: Scope notes

**Format version**:
The integer that identifies a revision of the curriculum format. A Curriculum records the one it follows in `index.md`.

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
