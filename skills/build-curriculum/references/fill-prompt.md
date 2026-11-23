<!-- Template for a fill agent. The orchestrator replaces every double-braced placeholder and sends the whole file, once per part file. -->

# Fill: {{part}}, {{subject}}

You fill in the Subsections of {{part}} in Sections {{sections}} of a Curriculum on {{subject}}: for each one, the Fields that teach it. Other agents fill the other part files at the same time, from the same Outline.

The Outline is fixed. Its IDs, titles, Goals, Prereqs and tags were approved by the user, and every agent relies on them, so you write around them: each unit you fill teaches exactly its Goal, to a learner who holds exactly its Prereqs.

Every unit you fill is true but incomplete: its claims stay true under every unit that builds on it, so a learner who goes deeper adds detail and never unlearns. Scope and Key concepts say what a thing is and does, and leave how it's represented or implemented to the unit whose Goal is about that.

## Inputs

- Subject: {{subject}}
- Code: `{{code}}`
- Target version: {{target_version}}
- Fill: Sections {{sections}} of {{part}}
- Outline: `{{outline}}`
- Write to: `{{part_file}}.partial`, renamed to `{{part_file}}` when you're done
- Draft format: `{{draft_format}}`
- Curriculum format: `{{curriculum_format}}`

The Brief, verbatim from the user. It sets the Curriculum's scope, environment and learner, and on those it wins over anything below:

```text
{{brief}}
```

## What to write

Read the whole Outline first: the overview's Methodology sets the source standard, the tags doc the tag vocabulary, the sources doc the abbreviations, and the other Parts show what each unit can leave to its neighbours. Then read the Draft format, and the Curriculum format's Subsection, Sources doc, Notes doc and Markers sections.

Write the part file as the Draft format's Part files section lays it out. For each Subsection in your Sections, in ID order:

- Copy its H1 from the Outline character for character, since `split` merges your Fields into the Outline's by H1.
- Write the Fields the Draft format gives a part file, each with the meaning and form the Curriculum format gives it.
- Build Scope toward the Goal from what the Prereqs' Goals already give the learner. A fact the unit needs that a Prereq doesn't give is a Foundation or part of Scope; a unit the Goal can't be reached in is a Judgement call in your Part notes, naming its ID.
- Read the Goals of the Outline units that list this unit directly in Prereqs, and keep its Scope and Key concepts true under each of them. Where Scope deliberately stops short of detail one of those units teaches, name that unit by ID in Scope as a preview, such as "how refs are stored is GIT-09.02.01" in a git Curriculum.
- A general rule is the claim those units' Goals most easily break: a closed list of kinds, or a claim that something always, only or never happens. A Goal that teaches a new kind, case or exception of what the rule covers breaks it, even when the Goal doesn't state the rule, so qualify the rule to the cases it holds for and preview that unit as the exception, such as "changes to lines of a text file that unchanged lines separate merge cleanly; files git can't merge by lines need a custom merge driver, GIT-06.02.03".
- When a Prereq's Goal is false at this unit's depth, keep this unit true and record a Judgement call in your Part notes naming both IDs.
- Write the Check so that only a learner holding the Goal can answer it.
- Name another unit by its bare ID and a tag as `{name}`, using only tags the Outline's tags doc defines. The tag vocabulary is closed: a unit that seems to need a new tag gets a Judgement call in your Part notes instead.

End the file with the Draft format's two merge blocks. They are your only route into the shared sources and notes docs, since other agents write beside you.

## Sources

<!-- The primary-source rules below are adapted from the research skill in mattpocock/skills (https://github.com/mattpocock/skills), Copyright (c) 2026 Matt Pocock, used under the MIT licence. -->

Every claim a unit makes is traced to the source that owns it, and cited:

- Work from **primary sources** as the overview's Methodology defines them for {{subject}}, at the Target version. Use a secondary write-up only to find the primary source behind it.
- Cite each unit's sources in its Sources Field, one full link per bullet, at the most specific page or anchor that holds the claim. Open each link and confirm it states what the unit says.
- Write link text with the sources doc's abbreviations. A source no abbreviation covers gets a new one, listed in Sources added with its family, chosen so it doesn't clash with any abbreviation in the Outline.
- A claim you can't trace to its source stays out of the unit and goes in Part notes' Open questions, naming the unit's ID. So does a citation you couldn't open or confirm.
- Record how you verified citations, and sources you tried but didn't use, in Part notes' Build notes.

## Done

You're done when `{{part_file}}.partial` is written and:

- it holds every Subsection of Sections {{sections}}, and nothing else before the merge blocks;
- every one has Scope, Key concepts, Check and Sources, and its H1 matches the Outline's;
- no claim in a unit's Scope or Key concepts is contradicted by the Goal of an Outline unit that lists it in Prereqs;
- every general rule in a unit that such a Goal makes an exception to is qualified and names that unit;
- every Sources bullet is a full link you opened, with link text using an abbreviation from the sources doc or your Sources added;
- every `{name}` is a tag in the tags doc, and every bare ID with code `{{code}}` names a unit in the Outline;
- the file ends with both merge blocks.

Then, as your last step, rename `{{part_file}}.partial` to `{{part_file}}`. The renamed file tells the orchestrator you finished, so rename it only once every item above holds.

Reply `done` and nothing else.
