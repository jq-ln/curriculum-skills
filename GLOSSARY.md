# Glossary

Terms used in this repo. Add project terms above `## Workflow`, as [`domain.md`](docs/workflow/domain.md#glossary) describes.

## Curriculums

**Curriculum**:
The whole doc set for one subject: a flat directory of Markdown docs with an `index.md` entry point. It has an uppercase code, such as `GIT`, that never changes once the Curriculum exists.
_Avoid_: Session Map

**Part**:
A top-level portion of a Curriculum. Its doc lists its Sections.

**Core**:
The first Part of a Curriculum, holding what day-to-day practice of the subject needs; every later Part builds on it. It's marked only by its position, and it's drawn to a capability target that the overview's Ordering rationale states.
_Avoid_: Tier, foundation Part

**Section**:
A portion of a Part. Its doc holds its Generators and lists its Subsections.

**Subsection**:
A portion of a Section, and the teachable unit. Its doc carries everything an agent needs to teach it, so it can be loaded alone.
_Avoid_: Session, Topic, Chapter

**Capstone**:
A Subsection that traces one scenario end to end through several Parts, such as the life of a commit in git, and lists every unit the scenario passes through in its Prereqs. A capstone that passes through an Optional unit is Optional itself. A Curriculum's capstones sit together in one Part, after every Part they need.
_Avoid_: Final project

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

**Dependant**:
A Subsection that lists another directly in its Prereqs. The build script's `dependants` lists a Subsection's dependants.
_Avoid_: Dependent, successor

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

**Prereq closure**:
Every Subsection a Subsection's Prereqs reach: its Prereqs, their Prereqs and so on, in any Curriculum. It's what the learner already holds when they take the Subsection.
_Avoid_: Prereq tree, transitive Prereqs

## Exercises

**Exercise**:
A practice item anchored to one Subsection, done in the subject's real environment, whose completion needs that Subsection's material. It is never a multiple-choice question or an explanation of a concept.
_Avoid_: Practice problem, project

**Practice workspace**:
The directory outside any doc set where a learner's practice items live, one subdirectory per Curriculum code. It sits beside the Curriculums by default.
_Avoid_: Exercise directory, sandbox

**Exercise check**:
The runnable command in an Exercise that measures its Done-when outcomes headless, one line per outcome, and exits 0 only when all of them pass. Prose says "Exercise check", never a bare "check", which already names a Subsection Field and `build.py check`.
_Avoid_: Test, grader, autograder

**Self-check bullet**:
A Done-when bullet the learner confirms by running the scene, used only where an Exercise check can't measure the outcome.
_Avoid_: Manual check, rubric item

**Reference solution**:
A finished Exercise that the solver writes from its task and starter without seeing its Exercise check, so the check can be shown to pass on a real solution. It never ships with the Exercise.
_Avoid_: Answer key, model solution

**Near-miss**:
A solution the solver writes to fail one Done-when outcome the way a learner plausibly would, so the Exercise check's line for that outcome can be shown to fail. It never ships with the Exercise.
_Avoid_: Mutant, wrong answer

**Domain reference**:
The swappable part of `build-exercises` for one subject's environment: a `domain.md` the prompts read and an `assets/` tree copied into each Exercise, chosen by its Applies-to line.
_Avoid_: Plugin, adapter, backend

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
