# Draft format

A Draft is the authored content of a Curriculum, before the build script's `split` turns it into the doc set. It lives in `<output>.draft/`, beside the output directory, and is deleted once the doc set passes `check`. Every Field's meaning and form is in [the curriculum format](curriculum-format.md); this doc says only which file each piece goes in and how the files are laid out.

## Layout

- `brief.txt`: the Brief, verbatim, or `None.`, written by the orchestrator before the outline agent starts, so a resumed run gives the fill agents the same Brief. It isn't `.md`, so `split` doesn't read it.
- `outline.md`: the Outline, written by the outline agent and edited by the human at the checkpoint. The agent writes it as `outline.md.partial` and renames it when done, so `split`, which reads only `outline.md`, never sees an unfinished Outline.
- `part-NN.md`, one per Part, such as `part-03.md` for `<CODE>-03`: the rest of that Part's Subsection Fields, written by its fill agent. A Part filled in batches of whole Sections has `part-NN.md`, then `part-NN-b.md`, `part-NN-c.md` and so on, each holding whole Sections in Section order. `split` reads them in that order and stops on a unit from another Part, a Section in more than one file, or a Section before one in an earlier file.
- `appendix-<description>.md`, one per Appendix, such as `appendix-manual-coverage.md`: the whole Appendix, with `<description>` as the [Filenames](curriculum-format.md#filenames) section gives it. `split` writes it as `<CODE>-appendix-<description>.md`. An Appendix goes in no other file.

`split` stops on any other `.md` file in the Draft, so a misnamed file isn't skipped.

Every file holds a run of docs. Each doc is an H1 followed by its Fields as H2s:

- The H1 is the doc's H1 as the format doc gives it, such as `# GIT-01.01.01 Content-addressed objects` or `# GIT Sources`.
- Its Fields follow in the order the format doc lists them for its Doc type, each at most once. The doc has no content between the H1 and its first Field.
- A doc split across files, such as a Subsection with its Goal in `outline.md` and its Scope in a part file, has the identical H1 in each, and each Field in exactly one of them. `split` merges the docs by H1.
- Units come in global ID order, each Part followed by its Sections, each Section followed by its Subsections.
- The Draft holds authored content only. Derived Fields, nav lines, links between docs, the Tags doc's Uses lines and the index's Format version are written by the script, so leave them out. Mark a unit with its bare ID and a tag with `{name}` in prose, as [Markers](curriculum-format.md#markers) says.

## `outline.md`

`outline.md` fixes everything the fill agents work from: the IDs, titles, Goals, Prereqs and tags, and the docs about the Curriculum as a whole. It holds these docs, in this order:

| Doc | Fields in `outline.md` |
| --- | --- |
| Index, `# <Subject> (<CODE>)` | Intro, Snapshot, Target version (left out for a subject with no releases) |
| Overview | Methodology, Ordering rationale |
| Tags doc | one `## <tag>` per tag, with its Meaning and Where bullets |
| Sources doc | Families, Abbreviations |
| Notes doc | Judgement calls, Scope decisions, Ordering and granularity choices, Build notes, Open questions (optional) |
| Each Part | Intro, Tags (optional) |
| Each Section | Generators, Tags (optional) |
| Each Subsection | Tags (optional), Goal, Prereqs |

A Notes doc Field with nothing to say yet holds `None so far.`, because every Field but Open questions is required.

## Part files

A part file holds that Part's Subsections, each with its remaining Fields: Generators (optional), Foundations (optional), Scope, Key concepts, Check and Sources. It holds only Subsections that `outline.md` holds, and none of their Tags, Goal or Prereqs Fields, so a fill agent never changes an ID, title, Goal, Prereq or tag. `split` stops on any other doc, or a Tags, Goal or Prereqs Field.

The file ends with two merge blocks, in this order, so parallel fill agents never edit a shared doc. `split` adds their entries to the shared docs.

### Sources added

The sources this part file's Sources Fields use that the Sources doc doesn't list yet:

```markdown
# GIT Sources added

## Families

- Git source tree: the C source of Git at the Target version

## Abbreviations

| Abbreviation | Expands to | Family |
| --- | --- | --- |
| src | Git source tree, version 2.47.1 | Git source tree |
```

Both Fields take the Sources doc's form and are left out when empty. `split` adds each family bullet and table row the Sources doc doesn't hold yet, so two part files may add the same source. An abbreviation the Sources doc already defines with the same expansion isn't repeated; one defined with a different expansion is a `check` error.

### Part notes

The notes this Part's fill produced:

```markdown
# GIT Part notes

## Judgement calls

- GIT-01.01.02: the manual and the source disagree on ...

## Build notes

- Verified every Sources link against the Target version's manual pages.

## Open questions

- GIT-01.02.01: no primary source states ...
```

Each Field is optional and its entries are added to the Notes doc's Field of the same name. They replace a Field that holds only `None so far.`, and an Open questions Field the Notes doc lacks is added. A part file with nothing to add still ends with both H1s, each with no Fields.
