<!-- Template for the outline agent. The orchestrator replaces every {{placeholder}} and sends the whole file. -->

# Outline: {{subject}}

Write a structured, progressive topic list for learning {{subject}} in depth: the table of contents of an exhaustive textbook on the subject. Cover the subject as fully as that textbook would, within the Brief; there's no target number of units.

You write the Outline, the skeleton of a Curriculum that later agents fill in, one Part each and in parallel. They can't change what you fix here: the units, their IDs, titles, Goals and Prereqs, and the tags.

## Inputs

- Subject: {{subject}}
- Code: `{{code}}`
- Snapshot: {{snapshot}}
- Target version: {{target_version}}
- Write to: `{{draft_dir}}/outline.md`
- Draft format: `{{draft_format}}`
- Curriculum format: `{{curriculum_format}}`

The Brief, verbatim from the user. It scopes the Curriculum, and it wins over anything below:

```text
{{brief}}
```

## What to write

Read the Draft format, then the Curriculum format's sections for the docs and Fields it names. Write `outline.md` exactly as the Draft format's `outline.md` section lays it out, with each Field's meaning and form as the Curriculum format gives it. The index H1 is `# {{subject}} ({{code}})`, unless a shorter, plainer name for the subject reads better as a title.

## Sources

<!-- The primary-source rules below are adapted from the research skill in mattpocock/skills (https://github.com/mattpocock/skills), Copyright (c) 2026 Matt Pocock, used under the MIT licence. -->

Every claim the Curriculum makes is traced to the source that owns it:

- Work from **primary sources**: official docs, source code, specs and standards, first-party APIs, and for an academic subject the canonical texts and original papers. Use a secondary write-up only to find the primary source behind it.
- Decide what "primary source" means for {{subject}}, and record that standard in the overview's Methodology. Every later Sources Field is judged by it.
- List the source families you used in the Sources doc's Families, and give each source you'll cite a short abbreviation in its Abbreviations.
- A claim you can't trace to its source goes in the notes doc's Open questions, not in a Goal.

## Versions

- If the Target version above is given, the Curriculum teaches that release.
- If it's `none given`, establish the subject's current stable release from its primary sources, write it in the index's Target version, and say in Methodology how you established it. A subject with no releases, such as a branch of mathematics, has no Target version: leave the Field out.
- If the subject is software installed on this machine, run its version command and record the installed versions in Methodology, with any difference from the Target version that matters to a learner.

## Units

- Size each Subsection to about 5–15 reasoning steps: the chain a learner follows from what they already hold to its Goal. Split a topic that needs more into several Subsections. Merge a topic too thin to carry its own Goal into its neighbour.
- Write each Goal as one proposition the unit installs, a fact that feels obviously true once taught.
- Give each Section the few Generators its Subsections collapse into.
- Add a Synthesis Subsection where loose facts collapse into a structure, such as at the end of a Section, and tag it `Synthesis`.
- Teaching material a textbook would put in an appendix becomes a Part tagged `Optional`, which no unit outside it lists as a Prereq. Reference material that teaches nothing, such as a coverage table, stays out of the Outline.
- Prereqs list only direct prerequisites, each an earlier Subsection's ID; transitive ones are implied. A unit with none has `None`.
- Number every level from `01` in teaching order. A level that would reach 100 is split instead.
- Fix the tag vocabulary now: the standard tags you use, copied from the Curriculum format, then the Curriculum's own. Fill agents can't add tags.

## Notes

Write the first notes in the notes doc:

- Scope decisions: what the Curriculum covers and leaves out, and why, including how you read the Brief.
- Ordering and granularity choices: the units you merged, split or placed against the obvious order, and why.
- Judgement calls and Build notes: what you have so far, or `None so far.`

## Done

You're done when `outline.md` is written and:

- every Part has at least one Section and every Section at least one Subsection;
- every Subsection has a Goal and a Prereqs Field, and every Prereq is an earlier Subsection's ID or another Curriculum's three-level ID;
- every tag used is defined in the tags doc;
- the overview's Methodology states the primary-source standard and how the Target version was established.

Reply with the number of Parts, Sections and Subsections, and nothing else.
