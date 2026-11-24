---
name: build-exercises
description: Write a gated practice Exercise for one Subsection of a Curriculum, in the subject's real tool. Use when the learner wants an exercise or practice for a Subsection ID.
---

# Build an Exercise

You orchestrate: `exercises.py` reads the Curriculum, fills the domain's assets and runs the Exercise gate, an author agent writes the Exercise, a solver agent solves it blind, and the Exercise gate tests the Exercise check against both before anything ships. An Exercise has the shape [the Exercise format](references/exercise-format.md) defines. Paths below are relative to this skill's directory; give subagents absolute paths. `exercises.py` below is `python3 <skill-dir>/scripts/exercises.py`, run with absolute paths.

## 1. Inputs and domain

Take from the learner's request:

- **Subsection ID** (required), such as `GD-01.08.02`. Its code is the Curriculum's.
- **Curriculums directory** (optional): default the working directory.
- **Practice workspace** (optional): default `<Curriculums directory>/practice/`.

Pass both directories to every `exercises.py` call as `--curriculums` and, where it takes one, `--practice`.

Find the Curriculum: the one directory in the Curriculums directory whose `index.md` H1 ends `(<CODE>)`. Its H1 names the subject, its Intro Field describes the scope the Brief set, and its Target version Field, when present, is the Target version.

Pick the domain: read the `Applies to:` line of each `references/domains/*/domain.md`, and match it against the subject and Intro. With no match, tell the learner no Domain reference applies to the Curriculum, name the domains there are, and stop. With more than one, ask the learner which applies, and take their answer.

The step is done when the ID, both directories, the Curriculum and one domain are fixed.

## 2. Tool check

Follow the chosen `domain.md`'s Environment, Tool section, before anything else runs:

- When the tool isn't on PATH, tell the learner which tool is missing and how its Tool section says to check for it, and stop.
- When the installed version doesn't match the Target version as the Tool section compares them, warn the learner, naming both versions, and go on.
- When the Curriculum has no Target version, say once that the version check is skipped, and go on.

The step is done when the tool is found.

## 3. Context and existing Exercises

```sh
exercises.py context <ID> --curriculums <dir>
exercises.py existing <ID> --curriculums <dir> --practice <dir>
```

A non-zero exit prints why, such as an ID that names no Subsection or a Format version that differs from `build-curriculum`'s: tell the learner and stop. Keep `context`'s output: the anchor's Fields, then its Prereq closure. A closure unit printed as `Unresolved:` is treated as given, never expected of the learner. `existing` prints the anchor's Exercises and `Next: <NN>`.

The step is done when both have exited 0.

## 4. Plan, or no Exercise

Decide from the anchor's Goal, Scope, Key concepts and Check, and its Prereq closure.

**No Exercise.** Give one, and write nothing, when either holds:

- The anchor's material has no practical use on its own: acting on it in the tool needs units outside its Prereq closure, and a task that avoids them practises other units instead.
- The Goal's main outcome can't be measured by an Exercise check, even through a stand-in from the domain's Stand-ins section.

Tell the learner the anchor gets no Exercise and why, naming what's missing, and where its material gets practised instead, such as a dependant that uses it. For example: "GD-01.02.01 Nodes and the scene tree gets no Exercise. Its Goal is a model fact: what a node is, and that a node takes part in the game only while it's in the SceneTree. Acting on that fact in code needs `add_child()` and a script, and both are outside its Prereq closure. An editor-only task would practise GD-01.01.03 and GD-01.02.02, not this unit." Then stop.

**Plan.** Otherwise plan the first rung of the ramp: the Goal's main outcome, in the plainest situation that shows it, with the most of the Prereq closure given. When `existing` lists Exercises, pick a situation none of them used. Hold the plan to these rules:

- **Scaffold line**: the learner writes only what uses the anchor's material. They may be expected to use anything in its Prereq closure and any API the anchor's own Scope names. Everything else is given, already built.
- **The Goal sets the target**, including a method it names, such as "moves only on physics ticks". The route beyond it is the learner's.
- **Minimum to ship**: at least one automated outcome, and the Goal's main outcome among them.

Write the plan as a few lines:

```text
Title: <a short title naming the situation, such as Walk to the well>
Situation: <the scene or program the learner finds, in the domain's tool>
Main outcome: <the Goal's main outcome, in this situation>
Learner writes: <where, and what it must do, as outcomes>
Given: <everything else the learner uses: files, scenes, helpers>
Key concepts in play: <only those the task needs>
```

The Exercise name is `<ID>-<NN>-<slug>`, with `<NN>` from `existing`'s `Next:` and `<slug>` made from the title as the Exercise format's [slug rule](references/exercise-format.md#where-an-exercise-lives) says.

The step is done when the plan and the Exercise name are fixed, or the learner has the reason for no Exercise.

## 5. Generation directory

Make a fresh temporary directory, the Generation directory, and fill the domain's assets into the Exercise inside it:

```sh
exercises.py assets <domain> <gen-dir>/<name> --exercise-name <name> --curriculums <dir>
```

Write `context`'s output to `<gen-dir>/context.md`. The Exercise is built in `<gen-dir>/<name>/`, with `gate.json`, `reference/` and `near-misses/` beside it in `<gen-dir>`, as the Exercise format's [What the gate reads](references/exercise-format.md#what-the-gate-reads) lays out.

From here until step 9, a stop is a failed run: tell the learner why, and give them the paths of the Generation directory and, once step 7 has made it, the solver's directory, kept for inspection; nothing is in the Practice workspace, so they can run the skill again.

## 6. Author

Fill [`references/author-prompt.md`](references/author-prompt.md): `{{exercise_title}}` with the plan's title, `{{anchor}}` with the ID, `{{code}}` with the code, `{{target_version}}` with the Target version or `none`, `{{plan}}` with the plan, `{{gate_report}}` with `None.`, and with absolute paths, `{{context}}` with `<gen-dir>/context.md`, `{{exercise_dir}}` with `<gen-dir>/<name>`, `{{gen_dir}}` with the Generation directory and `{{exercise_format}}` with [`references/exercise-format.md`](references/exercise-format.md). Fill `{{domain_environment}}` with the text of `domain.md` from `## Environment` up to `## Checking`, and `{{domain_checking}}` with the text from `## Checking` to the end. Hand the filled prompt to one subagent.

The step is done when `<gen-dir>/<name>/EXERCISE.md` and `<gen-dir>/gate.json` exist.

## 7. Solver

Make a second fresh temporary directory, the solver's directory, outside the Generation directory: the Generation directory holds `check/`, so a solver given any path in it could read the Exercise check and tune the Reference solution to it. Copy the Exercise to `<solver-dir>/exercise/`, leaving out `check.sh`, `check/` and `hints/`, and copy `<gen-dir>/context.md` to `<solver-dir>/context.md`.

Fill [`references/solver-prompt.md`](references/solver-prompt.md): `{{exercise_title}}` as in step 6; `{{near_misses}}` with one line per entry of `gate.json`'s `near_misses`, as `<name>: <line text>`; `{{redo}}` with `None.`; `{{domain_environment}}` as in step 6, and only that section of `domain.md`; and with absolute paths, `{{solver_view}}` with `<solver-dir>/exercise`, `{{context}}` with `<solver-dir>/context.md`, `{{solver_dir}}` with the solver's directory and `{{exercise_format}}`. Hand it to one subagent.

Then sync the cases: replace `<gen-dir>/reference/` and `<gen-dir>/near-misses/` with copies of the solver's, leaving out any Near-miss directory that `gate.json`'s `near_misses` doesn't name.

The step is done when `<gen-dir>/reference/` and a directory under `<gen-dir>/near-misses/` for every Near-miss exist.

## 8. Gate

```sh
exercises.py gate <gen-dir>/<name> <gen-dir>
```

It prints a matrix of each automated line against the starter, the Reference solution and each Near-miss, then a verdict. Exit 0 is a pass: go to step 9. Otherwise run a revision round:

1. Fill the author prompt as in step 6, with `{{gate_report}}` set to the gate's whole output, and hand it to a new author subagent. It revises the Exercise and replies with the cases the solver must redo, as `<case>: <line text>`, or `none`.
2. For each case to redo, take the line's measured value: copy `<gen-dir>/<name>` to a new temporary directory, lay the case's files from `reference/` or `near-misses/<case>/` over it, run `./check.sh` there, and take that line's text in parentheses. Delete the temporary directory.
3. When there's a case to redo, refresh `<solver-dir>/exercise/` from the revised Exercise as in step 7, and fill the solver prompt again with `{{near_misses}}` from the revised `gate.json` and `{{redo}}` with one line per case, as `<case>: <line text> (measured: <value>)`. The solver gets only the line's text and its measured value, never the rest of the gate report. A Near-miss that's new in `gate.json` goes in `{{redo}}` too, with no measured value. Hand it to a new solver subagent.
4. Sync the cases as in step 7, so a Near-miss the author dropped from `gate.json` leaves `near-misses/` too, and run the gate again.

An `Environment problem:` line, exit 2, means a case couldn't run at all, such as a starter that fails to import; it goes to the author like any other failing round.

After 3 revision rounds, when the gate still fails:

- If it reports only `Environment problem:` lines, and no line of the Exercise check, stop as a failed run, showing the learner the gate's last output.
- If the Goal's main outcome line is among the lines it reports, the Exercise can't ship. Give a reasoned no Exercise as step 4 does, naming that line and why it couldn't be measured, and give the learner the paths of the Generation directory and the solver's directory, kept for inspection. Stop.
- Otherwise run one last revision round, steps 1 to 4, with `Failed 3 rounds: <line text>` at the top of `{{gate_report}}` for each line the gate reports. The author turns each into a Self-check bullet or cuts it. When that leaves no automated outcome line, or the gate still doesn't exit 0, stop as a failed run, showing the learner the gate's last output.

The step is done when the gate exits 0.

## 9. Ship

Check that `<Practice workspace>/<CODE>/` has no `<ID>-<NN>-*` directory, whatever its slug; if it has one, another run took the number, so stop as a failed run. Then remove from `<gen-dir>/<name>/` anything that isn't `EXERCISE.md`, `check.sh`, `check/`, `hints/` or a file of the starter, such as a cache the domain's tool wrote while an authoring-time script ran. Move `<gen-dir>/<name>/` there, creating `<Practice workspace>/<CODE>/` when it's missing. Only the Exercise moves: `gate.json`, `reference/`, `near-misses/` and `context.md` stay behind. Delete the Generation directory and the solver's directory.

Tell the learner the Exercise's path and title, the Done-when bullets, and to start from `EXERCISE.md`. The step is done when the Exercise is in the Practice workspace and both temporary directories are gone.

## Without subagents

Where you can't start subagents, follow each filled prompt yourself, in the step that hands it off. When you follow the solver prompt, work from the solver's directory and the prompt alone, and solve the Task as `EXERCISE.md` states it, not as the Exercise check you wrote measures it.
