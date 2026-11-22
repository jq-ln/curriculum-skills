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

Propose a **Code**: a short uppercase abbreviation of the Subject, starting with a letter, then letters or digits, such as `GIT` or `PG`.

Ask the user once, in one message, to confirm or correct the Code, the Target version (or that the outline agent will establish it) and the output directory, and to name a Subject if the request had none. Say the Code never changes once the Curriculum exists. Take their answer as final.

The Snapshot is today's date as `YYYY-MM-DD`. The Draft directory is `<output>.draft/`, beside the output directory.

The step is done when the Subject, Code, Target version (or `none given`), Brief (or `None.`), Snapshot, output directory and Draft directory are fixed. If `<output>.draft/outline.md` already exists, ask the user whether to go to the checkpoint with it or write a new one.

## 2. Outline

Fill [`references/outline-prompt.md`](references/outline-prompt.md): replace each `{{placeholder}}` with its input, `{{draft_dir}}` with the Draft directory's absolute path, and `{{draft_format}}` and `{{curriculum_format}}` with the absolute paths of [`references/draft-format.md`](references/draft-format.md) and [`references/curriculum-format.md`](references/curriculum-format.md). Create the Draft directory, then hand the filled prompt to one subagent. Where you can't start subagents, follow the prompt yourself.

Then check that `split` reads the Outline, into a new empty temporary directory:

```sh
python3 scripts/build.py split <draft-dir> <temp-dir>
```

A non-zero exit prints the problem: fix `outline.md` and run it again. The step is done when `split` exits 0. Delete the temporary directory.

## 3. Checkpoint

Show the user:

- the number of Parts, Sections and Subsections;
- each Part's ID and title, with its Sections' IDs and titles nested under it;
- the path to `outline.md`, which they can edit directly;
- when there are more than about 400 Subsections, a warning that the fill will be large, and that a narrower Brief would shrink it.

Ask the user to edit `outline.md` or tell you what to change, and to say go when it's right. Make each change they ask for in `outline.md`, keeping IDs sequential, run the `split` check of step 2 again, and show the checkpoint again. Wait for go.

## 4. After go

The fill stage isn't built yet. Tell the user the Outline is approved and kept in the Draft directory, and stop.
