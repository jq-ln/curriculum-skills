<!-- Template for the outline agent. The orchestrator replaces every double-braced placeholder and sends the whole file. -->

# Outline: {{subject}}

Write a structured, progressive topic list for learning {{subject}} in depth: the table of contents of an exhaustive textbook on the subject. Cover the subject as fully as that textbook would, within the Brief, and let the subject set the number of units. Order it the way a learner meets the subject: first a core of what day-to-day work with it needs, then each topic in the order a learner reaches for it, practical use before internals. The core and the order decide where a unit sits, never whether it's there. That textbook's later Parts cover, and so do yours:

- for software, its internals, down to the on-disk and wire formats;
- for software, its protocols and scaling;
- for software whose source is public, its own implementation: a tour of its source code and core APIs, how it's built and tested, and how to contribute to it;
- capstones that trace one scenario through several Parts.

Leave a topic out only when it lies outside {{subject}} or the Brief excludes it. A `None.` Brief excludes nothing.

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

## The core

The first Part is the core: what day-to-day practice of {{subject}} needs. Every later Part builds on it. Draw the core by this criterion:

1. **Capability target.** Write one sentence saying what the learner the Brief describes can do once they've finished the core. When the Brief describes no learner, the target is what a typical practitioner of {{subject}} does day to day. A Brief that describes an experienced learner moves the target, and the core moves with it.
2. **Frequency.** Keep the units that capability uses most often. Keep a rarely used unit too when the capability can't do without it, such as recovering a lost commit in git.
3. **Load-bearing model.** Admit a fact about how {{subject}} works internally only when a core Goal depends on it.
4. **Record the cut.** Write the capability target sentence and where the core cut falls in the overview's Ordering rationale.

Draw exactly one core Part, whatever the subject and the Brief. Grow it by Sections as the capability needs, and name it for what it holds, such as Essentials.

## Order

Order the Curriculum by what each unit needs, so a learner can stop at the depth they need:

- Within a Part, units run shallow to deep.
- A deep unit sits in the Part of the topic it deepens, not in a Part about the mechanism underneath, so no two Parts need each other.
- The Parts that need only the core come straight after it, ordered by how soon a practitioner reaches for them.
- Each later Part comes after every Part it needs.
- The overview's Ordering rationale names the Parts that open straight after the core, and says why the rest fall where they do.

## Units

Goals, Generators, Prereqs, IDs and tags follow the Curriculum format's Subsection, IDs and Standard tags sections. On top of those:

- Size each Subsection to about 5–15 reasoning steps: the chain a learner follows from what they already hold to its Goal. Split a unit that needs more into several Subsections. Merge a unit too thin to carry its own Goal, such as the thin remainder of a split topic, into its neighbour.
- When a topic has a core slice and a deeper remainder, split it into two Subsections, each titled for what it teaches and with its own Goal, the deep one listing the shallow one in Prereqs.
- State core Goals at the model level, saying what a thing is and does, never how it's represented or implemented, so no later unit has to retract them.
- Make every Goal true but incomplete: it may leave detail out, but the primary source, at the Target version if there is one, never contradicts it at the unit's depth. These claims are the most easily overstated, so check each against the primary source before writing it, and qualify it to the cases it holds for:
  - a general rule: a closed list of kinds, a claim about every or all of something, or a claim that something always, only or never happens, or can't be done;
  - a subject that stands for every case, such as a program named where only some of its commands do the thing;
  - a term the source defines, used more loosely than its definition;
  - a fixed fact where the source gives a default that configuration or a build option changes; state it as the default;
  - advice where the source gives none, or a constraint where it gives only advice, such as "read-only" for what the source says shouldn't be modified directly; state the advice the source gives, as advice.
- Add a Synthesis Subsection wherever loose facts collapse into a structure, such as at the end of a Section.
- Add a capstone Part, unless the Brief excludes it or too few Parts follow the core for a scenario to span several. Each of its Subsections traces one scenario end to end through several Parts, such as the life of a commit in git from edit to push, and its Prereqs list every unit the scenario passes through. A capstone that passes through an Optional unit is tagged `Optional` itself. A capstone isn't a Synthesis unit, since it may teach how those units' facts hand off to each other; define a tag of your own for capstones if you want them counted. Like any later Part, it comes after every Part it needs.
- Teaching material a textbook would put in an appendix becomes a Part tagged `Optional`. Reference material that teaches nothing, such as a coverage table, stays out of the Outline.
- A Prereq is a unit whose Goal this unit's Goal can't be reached without. Ask that of every Prereq you list, so each later Part opens as early as its content allows.
- Every fact a Goal relies on that another unit teaches is taught by one of its transitive Prereqs. A Goal that explains merge in terms of plumbing needs the unit that teaches merge, so list it, or a unit that has it among its transitive Prereqs. When that unit comes later in the Outline, move it earlier or this unit later. When it's Optional and this unit isn't, or neither move keeps every core unit in the core, the Order rules and every Prereq earlier than the unit that lists it, restate the Goal without the fact.
- Fix the tag vocabulary now, because fill agents can't add tags.

## Coverage

Once the units are drafted, walk the subject's primary reference end to end, such as every page of a program's manual, its documented file formats and protocols, and its source tree's top-level layout, or a field's canonical texts. Give each topic it documents a unit whose Goal reaches it, adding units where none does, so the fill agents, who can't add units, never meet a topic with no home.

## Notes

Write the first notes in the notes doc:

- Scope decisions: what the Curriculum covers and leaves out, and why, including how you read the Brief. Each topic you leave out names the Brief's words or the subject boundary that excludes it.
- Ordering and granularity choices: the units you merged, split or placed against the obvious order, and why.
- Judgement calls and Build notes: what you have so far.

## Done

You're done when `outline.md.partial` is written and:

- every Part has at least one Section and every Section at least one Subsection;
- every Subsection has a Goal and a Prereqs Field, and every Prereq is an earlier Subsection's ID or another Curriculum's three-level ID, and no unit outside an Optional Part, Section or Subsection lists a unit inside one;
- every Goal is true but incomplete, and each claim of the kinds the Units section lists holds against the primary source;
- every fact a Goal relies on that another unit teaches is taught by one of its transitive Prereqs;
- every tag used is defined in the tags doc;
- each topic the Coverage walk found has a unit whose Goal reaches it;
- there is a capstone Part, unless the Brief excludes it or too few Parts follow the core for a scenario to span several;
- the overview's Methodology states the primary-source standard and how the Target version was established;
- the overview's Ordering rationale states the capability target sentence, where the core cut falls and the Parts that open straight after the core.

Then, as your last step, rename `outline.md.partial` to `outline.md`. An `outline.md` tells the orchestrator you finished, so rename it only once every item above holds.

Reply with the number of Parts, Sections and Subsections, and nothing else.
