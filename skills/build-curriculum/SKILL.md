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

If the Draft directory already exists, an earlier run stopped part-way: resume it as [Resuming](#resuming) says. Otherwise the output directory must be missing or empty, since `split` writes into it; if it isn't, ask the user for another one.

The step is done when the Subject, Code, Target version (or `none given`), Brief (or `None.`), Snapshot, output directory and Draft directory are fixed.

## 2. Outline

Fill [`references/outline-prompt.md`](references/outline-prompt.md): replace each `{{placeholder}}` with its input, `{{draft_dir}}` with the Draft directory's absolute path, and `{{draft_format}}` and `{{curriculum_format}}` with the absolute paths of [`references/draft-format.md`](references/draft-format.md) and [`references/curriculum-format.md`](references/curriculum-format.md). Create the Draft directory and write the Brief to `brief.txt` in it, verbatim, or `None.` when there is none, so a resumed run fills the part files with the same Brief. Then hand the filled prompt to one subagent. Where you can't start subagents, follow the prompt yourself. If the agent returns and `outline.md` doesn't exist, it stopped part-way: delete `outline.md.partial` and run it again.

Then check that `split` reads the Outline, into a new empty temporary directory:

```sh
python3 <skill-dir>/scripts/build.py split <draft-dir> <temp-dir>
```

Pass all three as absolute paths, since the script and the Draft sit under different directories. A non-zero exit prints the problem: fix `outline.md` and run it again. Delete the temporary directory once `split` exits 0. The step is done when it has.

## 3. Checkpoint

Show the user:

- the capability target sentence, quoted from the overview's Ordering rationale in `outline.md`;
- the number of Parts, Sections and Subsections, counted from the H1s in `outline.md` whose ID has one, two and three levels;
- each Part's ID and title, with its Sections' IDs and titles nested under it, and the first Part labelled as the core;
- the Parts that open straight after the core, as Ordering rationale names them;
- the path to `outline.md`, which they can edit directly;
- when there are more than about 400 Subsections, a warning that the fill will be large, and that a narrower Brief would shrink it.

Ask the user whether the core should hold more or less, or aim at a different capability. Ask them to edit `outline.md` or tell you what to change, and to say go when it's right. Make each change they ask for in `outline.md`, renumbering as [IDs](references/curriculum-format.md#ids) says, run the `split` check of step 2 again, and show the checkpoint again. Wait for go.

On go, create an empty file `.approved` in the Draft directory, so a resumed run doesn't ask again. The step is done when it exists.

## 4. Fill

Plan the part files from `outline.md`. A Part of up to 30 Subsections is one part file, `part-NN.md`. A larger Part is split into batches of whole Sections: walk its Sections in ID order and start a new batch whenever the next Section would take the current one past 30 Subsections, so each batch holds at least one Section. Name the batches `part-NN.md`, `part-NN-b.md`, `part-NN-c.md` and so on, as the [Draft format](references/draft-format.md#layout) says.

Fill [`references/fill-prompt.md`](references/fill-prompt.md) once per part file: `{{subject}}`, `{{code}}`, `{{target_version}}` and `{{brief}}` as in step 2; `{{part}}` with the Part's ID and title, such as `GIT-03 Plumbing`; `{{sections}}` with the batch's Section IDs, such as `GIT-03.01, GIT-03.02, GIT-03.03`; and with absolute paths, `{{outline}}` with `outline.md`, `{{part_file}}` with the part file in the Draft directory, and `{{draft_format}}` and `{{curriculum_format}}` as in step 2.

Start one subagent per part file, all at once, so they run in parallel. Where the host caps how many run together, start another as each returns. Where you can't start subagents, follow each prompt yourself, one part file at a time. When an agent returns and its part file doesn't exist, it stopped part-way: delete its `.partial` file and run it again.

The step is done when every planned part file exists.

## 5. Build

Run the script on the Draft, with absolute paths:

```sh
python3 <skill-dir>/scripts/build.py split <draft-dir> <output-dir>
python3 <skill-dir>/scripts/build.py derive <output-dir>
python3 <skill-dir>/scripts/build.py check <output-dir>
```

A non-zero `split` names the Draft file and doc at fault: fix it in the Draft and run `split` again, since a failed `split` writes nothing. After 3 failed runs, show the user the last error and stop, keeping the Draft. `split` checks only the Draft's shape, so a mistake in a part file's content surfaces later, in `check`.

When `derive` or `check` exits non-zero, run a fix round:

1. Read every error line. Each names a doc in the output directory.
2. Fix the authored content behind each error in that doc, such as a Prereq that points forward, a Sources bullet that isn't a link or a tag the tags doc lacks. Derived content follows from authored content, so fix its source and let `derive` rewrite it. When a fix changes a Goal, Prereq or tag the user approved, add a bullet saying what and why to the notes doc's Build notes.
3. Run `derive`, then `check`, again.

Run at most 3 fix rounds. If `check` still fails after the third, show the user its remaining error lines, say the Draft and the doc set are kept so a later run resumes from them, and stop.

The step is done when `check` exits 0.

## 6. Clean up

Delete the Draft directory, since the doc set now holds everything it did. Tell the user where the Curriculum is, with its Parts, Sections and Subsections counts from `index.md`, and point them at the notes doc's Open questions Field when it exists. The step is done when the Draft directory is gone and the user has the path.

## Resuming

Each stage leaves a mark in the Draft directory or the output directory, so a new run picks up at the first stage that hasn't finished.

The Draft's values win over what the user gave or confirmed in step 1: take the Brief from `brief.txt`, and when `outline.md` exists, the Code from its index H1 and the Target version from its index's Target version Field (`none given` when the Field is absent). Tell the user when any of them differs from what they gave.

Then check these in order and start at the first that applies:

1. **No `outline.md`**: the outline agent didn't finish. Delete any `outline.md.partial` and start at step 2.
2. **No `.approved`**: the user hasn't said go. Run step 2's `split` check, since the user may have edited `outline.md`, then show the checkpoint.
3. **No `.marksman.toml` in the output directory**: the fill or `split` didn't finish, since `split` writes `.marksman.toml` last. Delete every `*.partial` file in the Draft directory, and `index.md` and every `<CODE>-*.md` file in the output directory, which is all an unfinished `split` leaves there. If the output directory holds anything else, ask the user before deleting it. Then run step 4 for the planned part files that don't exist yet, and step 5.
4. **`.marksman.toml` in the output directory**: `split` finished, and the build or its fix rounds stopped. Start step 5 at `derive`, with 3 fresh fix rounds, keeping the fixes already in the doc set.
