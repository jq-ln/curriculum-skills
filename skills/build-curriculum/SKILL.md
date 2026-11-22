---
name: build-curriculum
description: Research a subject and write it as a Curriculum, a flat directory of linked Markdown docs. Use when the user wants a curriculum built for a subject.
---

# Build a Curriculum

You orchestrate: agents research and write the Draft, and the build script turns it into a doc set that follows [the curriculum format](references/curriculum-format.md). Paths below are relative to this skill's directory; give subagents absolute paths.

## 1. Inputs

Take from the user's request:

- **Subject** (required): what the Curriculum teaches, as free text.
- **Target version** (optional): the release of the subject to teach.
- **Brief** (optional): free text that scopes the Curriculum, such as "on Arch Linux" or "through the undergraduate core". Keep it verbatim.
- **Output directory** (optional): default `./<slug>/`, where `<slug>` is the Subject under the format doc's [slug rule](references/curriculum-format.md#filenames).

Propose a **Code**: a short abbreviation of the Subject in the [code form](references/curriculum-format.md#doc-set), such as `GIT` or `PG`.

If the request names no Subject, ask for it first, since the Code is proposed from it. Then ask the user once, in one message, to confirm or correct the Code, the Target version (or that the outline agent will establish it) and the output directory. Say the Code never changes once the Curriculum exists. Take their answer as final.

The Snapshot is today's date as `YYYY-MM-DD`. The Draft directory is `<output>.draft/`, beside the output directory.

If `<output>.draft/outline.md` already exists, an earlier run wrote it, and its values win: take the Code from its index H1 and the Target version from its index's Target version Field (`none given` when the Field is absent), and tell the user when either differs from what they confirmed. Then skip the outline agent, but still run step 2's `split` check before step 3, because an agent that stopped part-way leaves an Outline that never passed it.

The step is done when the Subject, Code, Target version (or `none given`), Brief (or `None.`), Snapshot, output directory and Draft directory are fixed.

## 2. Outline

Fill [`references/outline-prompt.md`](references/outline-prompt.md): replace each `{{placeholder}}` with its input, `{{draft_dir}}` with the Draft directory's absolute path, and `{{draft_format}}` and `{{curriculum_format}}` with the absolute paths of [`references/draft-format.md`](references/draft-format.md) and [`references/curriculum-format.md`](references/curriculum-format.md). Create the Draft directory, then hand the filled prompt to one subagent. Where you can't start subagents, follow the prompt yourself.

Then check that `split` reads the Outline, into a new empty temporary directory:

```sh
python3 <skill-dir>/scripts/build.py split <draft-dir> <temp-dir>
```

Pass all three as absolute paths, since the script and the Draft sit under different directories. A non-zero exit prints the problem: fix `outline.md` and run it again. Delete the temporary directory once `split` exits 0. The step is done when it has.

## 3. Checkpoint

Show the user:

- the number of Parts, Sections and Subsections, counted from the H1s in `outline.md` whose ID has one, two and three levels;
- each Part's ID and title, with its Sections' IDs and titles nested under it;
- the path to `outline.md`, which they can edit directly;
- when there are more than about 400 Subsections, a warning that the fill will be large, and that a narrower Brief would shrink it.

Ask the user to edit `outline.md` or tell you what to change, and to say go when it's right. Make each change they ask for in `outline.md`, renumbering as [IDs](references/curriculum-format.md#ids) says, run the `split` check of step 2 again, and show the checkpoint again. Wait for go.

## 4. After go

The fill stage isn't built yet. Tell the user the Outline is approved and kept in the Draft directory, and stop.
