# Curriculum format

Format version: 1

This doc defines the curriculum format: the docs a Curriculum holds, the Fields in each, how IDs, filenames and links are formed, and how to parse a doc. It's the single source of truth: read and write a Curriculum from this doc alone. It defines every term it uses.

A Curriculum is written for two readers. An agent loads one Subsection, and nothing else from the Curriculum, as the material to teach. A human browses the doc set in an editor or on GitHub and follows links.

## Authored and derived content

Every piece of a doc is one of these:

- **Authored** content is written by an agent or a human: the facts the Curriculum teaches and the decisions behind it.
- **Derived** content is computed from authored content in its one source doc: every copy, count, nav line and link between docs. A Subsection is lossless: loaded alone, it carries everything needed to teach it, so derived content copies facts such as the Section's Generators and each prereq's Goal into it.
- A **mixed** Field, such as Prereqs or Tags, holds authored IDs or tag names with derived links and copies beside them.
- The index's **Format version** Field is written once, when the doc set is first built, and is neither authored nor derived.

To change a copy, edit its source and derive again. A doc set is invalid when any derived content differs, word for word, from what deriving it from its sources gives.

Deriving is idempotent and runs in place over the doc set. It rewrites only derived content, renames a file when its title changes, and keeps everything authored as it is.

## Doc set

A Curriculum is one flat directory holding exactly the docs below and an empty `.marksman.toml`, which makes marksman treat the directory as one workspace. Any other file, and any subdirectory, makes the doc set invalid.

| Doc type | Filename | Count |
| --- | --- | --- |
| Index | `index.md` | exactly 1 |
| Overview | `<CODE>-overview.md` | exactly 1 |
| Tags doc | `<CODE>-tags.md` | exactly 1 |
| Sources doc | `<CODE>-sources.md` | exactly 1 |
| Notes doc | `<CODE>-notes.md` | exactly 1 |
| Part | `<CODE>-PP-<slug>.md` | 1 or more |
| Section | `<CODE>-PP.SS-<slug>.md` | 1 or more per Part |
| Subsection | `<CODE>-PP.SS.UU-<slug>.md` | 1 or more per Section |
| Appendix | `<CODE>-appendix-<description>.md` | 0 or more |

A reader tells a doc's type from its filename. A Curriculum has no other Doc types: material outside these goes in an Appendix or stays out.

`<CODE>` is the Curriculum's code: an uppercase letter followed by uppercase letters or digits, such as `GIT` or `PG`. It never changes once the Curriculum exists.

Docs carry no YAML front matter. Front matter a human adds, such as Obsidian `aliases`, is kept by deriving and set aside when parsing; see [Parsing](#parsing).

## IDs

A unit is a Part, Section or Subsection. An ID names a unit: the code, a hyphen, then one number per level, each exactly two digits, separated by `.`.

| Unit | ID form | Example |
| --- | --- | --- |
| Part | `<CODE>-PP` | `GIT-07` |
| Section | `<CODE>-PP.SS` | `GIT-07.02` |
| Subsection | `<CODE>-PP.SS.UU` | `GIT-07.02.03` |

- Each level is numbered from `01` in teaching order, padded even when a level has fewer than ten entries: `GIT-05`, never `GIT-5`.
- No level exceeds `99`. A Part or Section that would need a 100th child is split instead.
- A Subsection's ID always has three levels. A subject with no natural Sections still gets them.
- An ID takes the same form everywhere: prose, H1s, filenames, the Context Field and references from another Curriculum.
- An ID changes only when units are renumbered, as when a Subsection is inserted mid-Section or a level is split at 99. Every reference to a moved unit then has to be rewritten.

**Global ID order** compares IDs level by level, numerically, with a parent before its children. It's the teaching order, and it equals byte order, so `LC_ALL=C ls` lists a Curriculum in teaching order.

## Filenames

A Part, Section or Subsection's filename is its ID, a hyphen, its slug and `.md`, such as `GIT-07.02.03-conflicts-stages-markers-and-styles.md`.

The slug is derived from the title in the doc's H1:

1. Decompose with Unicode NFKD, then drop combining marks. Step 3 turns every other non-ASCII character into a separator, so `Merging—rebasing` gives `merging-rebasing`.
2. Lowercase.
3. Replace each run of characters outside `[a-z0-9]` with one `-`, and trim `-` from both ends.
4. If the result is longer than 60 characters, take its first 61 characters and cut at the last `-` among them, dropping that `-` and everything after it. With no `-` among them, keep the first 60 characters.

A title whose slug is empty is invalid.

A title, whether a unit's, an Appendix's or the Curriculum's name in the index H1, contains no `[`, `]`, `|`, `\`, `<` or backtick. Deriving copies titles verbatim, without escaping, into link text, the Context Field and the Parts table, and these characters would break a link or a table row there.

The ID part of a filename changes only with the ID; the slug follows the title, so a title change renames the file and its inbound links are derived again. Find a unit by globbing its ID, such as `GIT-07.02.03-*`, never by its full filename.

An Appendix's `<description>` is authored: lowercase words of `[a-z0-9]` joined by single `-`, saying what kind of information it holds, such as `GIT-appendix-manual-coverage.md`.

## Fields

A Field is a top-level H2 whose text is one of its Doc type's Field names, together with its content up to the next H2. The tables below list each Doc type's Fields in their fixed order; [Parsing](#parsing) says how a reader finds them.

- **Required** Fields are always present.
- **Optional** Fields are left out when empty, never written as `None`. Prereqs is the one Field that says `None`.
- A derived Field marked **when** a condition holds is present exactly when it does.
- A list Field holds one bullet list, one entry per bullet.
- A one-paragraph Field holds a single paragraph, so it can be copied onto one line elsewhere.

## Subsection

The Subsection is the teachable unit. Its doc is:

1. The H1, `# <ID> <title>`, such as `# GIT-07.02.03 Conflicts: stages, markers and styles`.
2. The nav line (derived), as a paragraph on its own; see [Nav line](#nav-line).
3. The Fields:

| Field | Kind | Required |
| --- | --- | --- |
| Context | derived | required |
| Tags | mixed | optional |
| Goal | authored | required |
| Generators | authored | optional |
| Foundations | authored | optional |
| Scope | authored | required |
| Key concepts | authored | required |
| Prereqs | mixed | required |
| Check | authored | required |
| Sources | authored | required |

**Context** copies in the unit's surroundings, so it can be taught without opening another doc:

```markdown
## Context

- Curriculum: Git (GIT)
- Target version: 2.47.1
- Snapshot: 2026-11-19
- Part: [GIT-07 Branching and merging](GIT-07-branching-and-merging.md)
- Section: [GIT-07.02 Merging](GIT-07.02-merging.md)
- Section Generators:
  - A merge combines three trees: base, ours and theirs.
```

The Curriculum line takes the name and code from the index's H1. The Target version line is left out when the index has no Target version. The Section Generators are the Section's Generators bullets, in order.

**Tags** lists every tag the unit carries: the Part's and the Section's Tags Field entries copied down, the unit's own tags, and every tag used inline in the unit. Tags used inline in a Part or Section aren't copied down. The own tag names are authored, one per bullet; deriving adds the rest and writes each entry as its tag link and Meaning copied from the tags doc, in the tags doc's order, each tag once:

```markdown
## Tags

- [Synthesis](GIT-tags.md#synthesis): Derives how earlier units' facts follow from a few base facts, and adds no new facts of its own.
```

**Goal** is one proposition, as one paragraph: the understanding the unit installs, stated as a fact that should feel obviously true to the learner once the unit is taught. It states the fact itself, never a learner action such as "Understand…" or "Learn how…". It's the answer key for the Check.

**Generators** are base facts specific to this unit, beyond its Section's Generators, from which the unit's other facts follow. One per bullet.

**Foundations** are facts the unit needs that can't be derived from anything the learner already holds, so they're accepted as given. Each is unconditionally true, simple enough to take at face value without caveats. One fact per bullet.

**Scope** is prose saying what the unit covers, such as the facts, commands, cases and edge cases on the path to its Goal, and where it stops. It may name later units by ID as previews.

**Key concepts** is a single line of terms, each followed by a semicolon and a space except the last, such as `merge base; conflict markers; index stages`.

**Prereqs** lists the unit's direct prerequisites: the Subsections whose Goals the learner must already hold. Transitive prerequisites are implied, and the previous unit is never assumed. The IDs are authored, one per bullet, such as `- GIT-07.02.01`; deriving links each and copies in its title and Goal:

```markdown
## Prereqs

- [GIT-07.02.01 The index as a staging snapshot](GIT-07.02.01-the-index-as-a-staging-snapshot.md): <its Goal>
- MATH-12.01.04 Bayes' theorem: <its Goal>
```

- A prereq with the Curriculum's own code is a Subsection ID that comes before this unit in global ID order. One at or after the unit, or naming no Subsection, is invalid.
- A prereq with another code is a three-level ID. Nothing else about it is checked, because global ID order compares IDs of one Curriculum only.
- An entry is the ID alone, with no qualifier such as `(preview)`.
- A prereq in another Curriculum is plain text, never a link, because Curriculums share no root directory. Deriving looks for that Curriculum among the directories beside the doc set's own, sharing its parent: it's found when exactly one of them has an `index.md` whose H1 ends `(<CODE>)` with the prereq's code. When it's found, the entry is the ID, its title and its Goal, as in the example. When it isn't, deriving keeps the entry as it is and a validity check doesn't compare it, so a doc set built beside the other Curriculum stays valid on a machine without it.
- A unit with no prereqs has `None` as its whole content.

**Check** is exactly one question that the learner can answer only by holding the Goal. It has no answer key: the Goal is the answer key.

**Sources** lists the sources that own the unit's claims, one full link to a primary source per bullet. The link text uses the abbreviations from the sources doc, such as `- [ProGit §10.2 Git Objects](https://git-scm.com/book/en/v2/Git-Internals-Git-Objects)`. These links point outside the Curriculum, so they're authored.

## Section

The H1 is `# <ID> <title>`. A Section has no intro.

| Field | Kind | Required |
| --- | --- | --- |
| Generators | authored | required |
| Tags | mixed | optional |
| Appendices | derived | when an Appendix names it |
| Subsections | derived | required |

**Generators** are the few base facts the Section's Subsections collapse into: each loose fact in the Section is seen to follow from them. One per bullet.

**Tags**, as in a Subsection: the tag names are authored, and deriving writes each tag's link and Meaning. A Section's tags are copied down into each of its Subsections.

**Appendices** lists each Appendix whose Applies to names this Section; see [Appendix](#appendix).

**Subsections** lists the Section's Subsections in ID order, each linked with its Goal copied: `- [GIT-07.02.03 Conflicts: stages, markers and styles](GIT-07.02.03-conflicts-stages-markers-and-styles.md): <its Goal>`.

## Part

The H1 is `# <ID> <title>`. A Part has no Prereqs or Sources: those belong to its Subsections.

| Field | Kind | Required |
| --- | --- | --- |
| Intro | authored | required |
| Tags | mixed | optional |
| Appendices | derived | when an Appendix names it |
| Sections | derived | required |

**Intro** is prose saying what the Part covers and why it sits where it does in the Curriculum.

**Tags** and **Appendices** are as in a Section. A Part's tags are copied down into every Subsection in it.

**Sections** lists the Part's Sections in ID order, each linked with its Generators copied as nested bullets:

```markdown
## Sections

- [GIT-07.02 Merging](GIT-07.02-merging.md)
  - A merge combines three trees: base, ours and theirs.
```

## Index

`index.md` is the entry point. Its H1 is `# <name> (<CODE>)`, such as `# Git (GIT)`, where the name is the Curriculum's subject.

| Field | Kind | Required |
| --- | --- | --- |
| Intro | authored | required |
| Snapshot | authored | required |
| Target version | authored | optional |
| Format version | written once | required |
| Counts | derived | required |
| Docs | derived | required |
| Parts | derived | required |

**Intro** is one paragraph saying what the Curriculum covers and its scope.

**Snapshot** is the date the Curriculum was researched, as `YYYY-MM-DD`.

**Target version** is one line naming the release of the subject the Curriculum teaches, such as `2.47.1`, for a subject with releases. How it was established goes in the overview's Methodology.

**Format version** holds only the integer of the format the doc set was built to, such as `1`. It's written once, when the doc set is first built, and never written or changed by deriving. A doc set is invalid for a reader when this Field is missing or differs from the reader's own Format version: the reader reports both numbers, and deriving stops with an error instead of running. A missing Field is restored from the history of `index.md`, such as `git log -p index.md`, because nothing else in the doc set records it.

**Counts** gives the number of Parts, Sections and Subsections, then one line per standard tag, in [Standard tags](#standard-tags) order, giving the number of Subsections carrying it, copied-down tags included. A standard tag the Curriculum doesn't use still gets its line, as `0`:

```markdown
## Counts

- Parts: 19
- Sections: 52
- Subsections: 192
- Synthesis: 16
- Optional: 0
```

**Docs** links the overview, tags, sources and notes docs, then every Appendix in filename order, each with its Purpose copied:

```markdown
## Docs

- [Overview](GIT-overview.md)
- [Tags](GIT-tags.md)
- [Sources](GIT-sources.md)
- [Notes](GIT-notes.md)
- [Appendix: Manual coverage](GIT-appendix-manual-coverage.md): <its Purpose>
```

**Parts** is a table with one row per Part, in ID order:

```markdown
## Parts

| Part | Title | Sections | Subsections |
| --- | --- | --- | --- |
| [GIT-07](GIT-07-branching-and-merging.md) | Branching and merging | 4 | 21 |
```

The index has no reading paths: why the Curriculum is ordered as it is belongs in the overview.

## Overview

The H1 is `# <CODE> Overview`.

| Field | Kind | Required |
| --- | --- | --- |
| Methodology | authored | required |
| Ordering rationale | authored | required |

**Methodology** says how the Curriculum was researched and built: what counts as a primary source for this subject, how the Target version was established, and the locally installed versions when the subject is software on the machine it was built on.

**Ordering rationale** says why the Parts, Sections and Subsections come in the order they do.

## Tags doc

The H1 is `# <CODE> Tags`. The doc holds one `## <tag>` heading per tag the Curriculum uses, so every tag link lands on its definition. A tag family, such as one version tag per release, gets one heading per concrete tag, never one for a pattern. Under each heading:

```markdown
## Synthesis

- Meaning: Derives how earlier units' facts follow from a few base facts, and adds no new facts of its own.
- Where: doc
- Uses: 16
```

- **Meaning** (authored) is one line, the text copied into each Tags Field entry.
- **Where** (authored) says where the tag may be used: `doc` (in a Tags Field), `inline` (as a marker in prose) or `doc, inline`. A tag named in a Tags Field when its Where lacks `doc`, or used as a marker when its Where lacks `inline`, is invalid, so a stray `{Optional}` in prose can't make a unit Optional.
- **Uses** (derived) is the number of Subsections whose Tags Field lists the tag.

The standard tags the Curriculum uses come first, in the order of [Standard tags](#standard-tags), copied from there. The Curriculum's own tags follow, in authored order. A Curriculum with no tags of its own still has a tags doc.

A tag name is the heading's text. It contains no `{`, `}`, `[`, `]` or backtick. Its anchor is GitHub's heading slug: lowercase the name, drop every character that isn't a letter, digit, space, `-` or `_`, then turn each space into `-`, so `2.43` gives `243` and `Host: Node` gives `host-node`. A tag is invalid when its anchor is empty, contains `_` or `--`, starts or ends with `-`, or equals another heading's anchor in the tags doc. These rules are deliberately stricter than needed: they're a simple test that guarantees GitHub's anchor and marksman's, which drops punctuation and collapses separators, are identical.

## Standard tags

The format defines two tags. A Curriculum that uses one copies its Meaning and Where from here into its tags doc; every other tag belongs to its Curriculum.

### Synthesis

- Meaning: Derives how earlier units' facts follow from a few base facts, and adds no new facts of its own.
- Where: doc

A Synthesis unit exists for the collapse: loose facts the learner already holds are seen to follow from a structure. It goes where facts collapse, such as the end of a Section.

### Optional

- Meaning: No unit outside it depends on it, so a learner may skip it.
- Where: doc

Teaching material that would otherwise sit in an appendix becomes a Part tagged Optional, so every unit has an ID and a place in the dependency graph. An Optional Part, Section or Subsection may sit anywhere in ID order. A doc set is invalid when a unit outside an Optional Part, Section or Subsection lists a unit inside it in Prereqs.

## Sources doc

The H1 is `# <CODE> Sources`.

| Field | Kind | Required |
| --- | --- | --- |
| Families | authored | required |
| Abbreviations | authored | required |

**Families** lists the source families the Curriculum draws on, one per bullet as `- <family>: <what it is and what it's trusted for>`, such as `- Git manual pages: the reference documentation shipped with Git`.

**Abbreviations** is a table of the short names used in Sources link text:

```markdown
| Abbreviation | Expands to | Family |
| --- | --- | --- |
| ProGit | Pro Git, 2nd edition, by Scott Chacon and Ben Straub | Git book |
```

Each abbreviation appears once. Two rows with the same abbreviation make the doc set invalid.

## Notes doc

The H1 is `# <CODE> Notes`.

| Field | Kind | Required |
| --- | --- | --- |
| Judgement calls | authored | required |
| Scope decisions | authored | required |
| Ordering and granularity choices | authored | required |
| Build notes | authored | required |
| Open questions | authored | optional |

- **Judgement calls**: choices made where the sources disagreed or were silent.
- **Scope decisions**: what the Curriculum includes and leaves out, and why.
- **Ordering and granularity choices**: why units were merged, split or placed where they are.
- **Build notes**: how the Curriculum was built, how citations were verified and sources tried but not used.
- **Open questions**: claims whose originator couldn't be traced and citations that couldn't be verified.

An H2 that isn't one of these Field names is free content; see [Parsing](#parsing).

## Appendix

An Appendix holds non-teaching reference material, such as a per-Curriculum glossary or a coverage cross-check, and never holds units. Its H1 is `# <CODE> Appendix: <title>`.

| Field | Kind | Required |
| --- | --- | --- |
| Purpose | authored | required |
| Applies to | authored | optional |

**Purpose** is one paragraph saying what the Appendix holds and why it isn't in a unit or the notes doc.

**Applies to** lists the Part and Section IDs the Appendix serves, one per bullet. Each named Part or Section gets a derived Appendices Field entry, `- [Appendix: <title>](<filename>): <its Purpose>`. An Appendix with no Applies to serves the whole Curriculum and is linked from the index only.

An H2 that isn't one of these Field names is free content; see [Parsing](#parsing). An Appendix has no Tags, Prereqs or Check. An Appendix may link to units, but no Subsection links to an Appendix: content a unit needs belongs in the unit or a prereq.

## Links

Every link between docs of a Curriculum is derived. An author writes a marker, and deriving writes the link around it. Links out of the Curriculum, such as those in Sources, are authored.

### Link targets

A link target is one of:

- a bare sibling filename, such as `GIT-07.02-merging.md`;
- a sibling filename and an anchor, such as `GIT-tags.md#synthesis`;
- a same-file anchor, such as `#tags`;
- for an authored link out of the Curriculum, an absolute URL.

A target between docs never contains `/` or `./` and is never URL-encoded. Any other form, and any target naming a missing file or anchor, is invalid.

### Markers

In an authored Field's prose, and in the free content of the notes doc and Appendices:

- **A unit** is its bare ID, matched by `\b[A-Z][A-Z0-9]*-[0-9]{2}(\.[0-9]{2}){0,2}(?![.-]?\w)`. An ID with the Curriculum's own code becomes a link with text `<ID> <title>`. An ID with another code stays plain text. An own-code ID naming no unit is invalid. An own-code token is any match of `\b<CODE>-[0-9][0-9.-]*\w*`, with `<CODE>` the Curriculum's own code; one where the marker regex doesn't match at its start is invalid, such as `GIT-7`, `GIT-07.2`, `GIT-07.02a`, `GIT-07-02` or `GIT-07.02.03.04`. An ID that ends a sentence, such as `GIT-07.02.`, is valid.
- **A tag** is its name in braces, such as `{2.43}`, and becomes a link with the tag name as its text. In a Subsection it links to the unit's own `#tags` Field, where the tag's Meaning is copied; elsewhere it links to the tag's heading in the tags doc. Braces around anything that isn't a tag name defined in the tags doc stay as text.

Prose means the text of the parsed CommonMark document outside code spans, fenced and indented code blocks, raw HTML, autolinks and links, both their text and their destinations. To write an ID-shaped token or braces literally, put it in a code span, such as `` `SQL-92` ``.

A link with a target between docs, such as `[GIT-07.02.03 Conflicts](GIT-07.02.03-conflicts.md)` or `[2.43](#tags)`, is one deriving wrote: it's recognized and refreshed as a whole from the ID or tag name its text starts with, so a title change updates its text and target and a re-run never nests a link. A link out of the Curriculum is authored and kept as it is, so an ID in its text, such as `[GIT-07.02 discussion](https://example.com)`, is neither linked nor checked.

### Link text

| Where | Link text | Example |
| --- | --- | --- |
| Prereqs entry | `<ID> <title>`, followed by `: <Goal>` | `[GIT-07.02.01 The index as a staging snapshot](…): <Goal>` |
| Child lists in Part and Section docs | `<ID> <title>` | `[GIT-07.02 Merging](…)` |
| Units in prose | `<ID> <title>` | `[GIT-07.02 Merging](…)` |
| Nav line | `<ID>` | `[GIT-07.02](…)` |
| Tags | the tag name | `[Synthesis](…)` |

### Nav line

Each Subsection has one nav line, between its H1 and its first Field:

```markdown
[Index](index.md) · [GIT-07](GIT-07-branching-and-merging.md) · [GIT-07.02](GIT-07.02-merging.md) · Prev [GIT-07.02.02](GIT-07.02.02-fast-forward-merges.md) · Next [GIT-07.02.04](GIT-07.02.04-resolving-conflicts.md)
```

Prev and Next follow global ID order across Section and Part boundaries, Optional Parts included. The first Subsection has no Prev and the last has no Next; an empty slot is left out with its ` · ` separator.

## Parsing

Every reader parses a doc this way.

1. If line 1 is `---`, set aside everything up to and including the next line that is `---`. This is front matter.
2. Parse the rest as CommonMark.
3. A heading is a top-level ATX heading, such as `## Goal`: a direct child of the document. A heading-like line inside a code block, blockquote or list item is content. A top-level setext heading, text over a line of `===` or `---`, is invalid.
4. The doc starts with exactly one H1. A Part, Section or Subsection's H1 is exactly `<ID> <title>`, and its ID must equal the ID its filename starts with. Every other Doc type's H1 is the form given in its section above.
5. In a Subsection, the paragraph between the H1 and the first H2 is the nav line.
6. A Field is an H2 whose text exactly matches one of its Doc type's Field names. Its content runs to the next H2 or the end of the doc, and H3 and deeper headings belong to the Field above them.
7. Fields appear in their Doc type's order, each at most once. A missing required Field, a repeated Field or a Field out of order is invalid.
8. In the notes doc and an Appendix, an H2 that isn't one of the Doc type's Field names is free content, and every free H2 comes after the last Field present; a free H2 before a Field is invalid. An H2 titled with a Field name is always that Field, so free content can't reuse a Field name. In the tags doc, every H2 is a tag. In every other Doc type, an H2 that isn't one of its Field names is invalid.
9. In a list Field, each top-level bullet is one entry. Take the entry's text: its first link's text when the bullet starts with a link, otherwise the whole bullet. An ID is the first word of that text; a tag name is all of it. A bullet of the form `- <key>: <value>`, as in Context, Counts and the tags doc, has the key before its first colon and the value after that colon and the space following it; nested bullets belong to the bullet above them. In the Abbreviations and Parts tables, each body row is one entry.

## Version history

- **1**: Initial format.
