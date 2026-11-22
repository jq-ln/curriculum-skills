<!-- Template for the outline agent. The orchestrator replaces every {{placeholder}} and sends the whole file. -->

# Outline: {{subject}}

Write a structured, progressive topic list for learning {{subject}} in depth: the table of contents of an exhaustive textbook on the subject. Cover the subject as fully as that textbook would, within the Brief, and let the subject set the number of units.

You write the Outline, the skeleton of a Curriculum that later agents fill in, one Part each and in parallel. They can't change what you fix here: the units, their IDs, titles, Goals and Prereqs, and the tags.

## Inputs

- Subject: {{subject}}
- Code: `{{code}}`
- Snapshot: {{snapshot}}
- Target version: {{target_version}}
- Write to: `{{draft_dir}}/outline.md.partial`, renamed to `outline.md` when you're done
- Draft format: `{{draft_format}}`
- Curriculum format: `{{curriculum_format}}`

The Brief, verbatim from the user. It sets the Curriculum's scope, environment and learner, and on those it wins over anything below:

```text
{{brief}}
```

## What to write

Read the Draft format, then the Curriculum format's sections for the docs and Fields it names. Write `outline.md.partial` exactly as the Draft format's `outline.md` section lays it out, with each Field's meaning and form as the Curriculum format gives it. The index H1 is `# {{subject}} ({{code}})`.

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

Goals, Generators, Prereqs, IDs and tags follow the Curriculum format's Subsection, IDs and Standard tags sections. On top of those:

- Size each Subsection to about 5–15 reasoning steps: the chain a learner follows from what they already hold to its Goal. Split a unit that needs more into several Subsections. Merge a unit too thin to carry its own Goal into its neighbour.
- Add a Synthesis Subsection wherever loose facts collapse into a structure, such as at the end of a Section.
- Teaching material a textbook would put in an appendix becomes a Part tagged `Optional`. Reference material that teaches nothing, such as a coverage table, stays out of the Outline.
- Keep Prereqs direct and backward-only, so the fill agents inherit a sound dependency graph.
- Fix the tag vocabulary now, because fill agents can't add tags.

## Notes

Write the first notes in the notes doc:

- Scope decisions: what the Curriculum covers and leaves out, and why, including how you read the Brief.
- Ordering and granularity choices: the units you merged, split or placed against the obvious order, and why.
- Judgement calls and Build notes: what you have so far.

## Done

You're done when `outline.md.partial` is written and:

- every Part has at least one Section and every Section at least one Subsection;
- every Subsection has a Goal and a Prereqs Field, and every Prereq is an earlier Subsection's ID or another Curriculum's three-level ID, and no unit outside an Optional Part, Section or Subsection lists a unit inside one;
- every tag used is defined in the tags doc;
- the overview's Methodology states the primary-source standard and how the Target version was established.

Then, as your last step, rename `outline.md.partial` to `outline.md`. An `outline.md` tells the orchestrator you finished, so rename it only once every item above holds.

Reply with the number of Parts, Sections and Subsections, and nothing else.
