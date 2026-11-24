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
- **Steer** (optional): free text on what the learner wants from this Exercise, such as "easier" or "focus on `is_on_wall()`". Step 5 applies it.

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

## 3. Renumber check

Every run checks all of the Curriculum's Exercises before it writes anything, since a renumber in the Curriculum can leave an Exercise naming an old ID:

```sh
exercises.py renumber <CODE> --curriculums <dir> --practice <dir>
```

A non-zero exit prints why: tell the learner and stop. Otherwise act on each Exercise's line:

- **`valid`**: nothing to do.
- **`moved: <old ID> → <new ID>`**: tell the learner the Exercise moved, as that line, and offer to point it at the new ID. Rename it only once the learner confirms that move:

  ```sh
  exercises.py rename <Practice workspace>/<CODE>/<name> <new ID> --curriculums <dir>
  ```

  Tell the learner the `renamed:` line it prints. When they decline, leave the Exercise as it is.
- **`broken`**: tell the learner the Exercise's reference is broken, with the reason and each `candidate:` line, so they can settle it. When they name a candidate as its anchor, rename the Exercise to it as above. A missing or unreadable record is theirs to fix by hand.

The step is done when every moved or broken Exercise has been reported and every rename the learner confirmed has printed `renamed:`.

## 4. Context and existing Exercises

```sh
exercises.py context <ID> --curriculums <dir>
exercises.py existing <ID> --curriculums <dir> --practice <dir>
```

A non-zero exit prints why, such as an ID that names no Subsection or a Format version that differs from `build-curriculum`'s: tell the learner and stop. Keep `context`'s output: the anchor's Fields, then its Prereq closure. A closure unit printed as `Unresolved:` is treated as given, never expected of the learner. `existing` prints the anchor's Exercises, each followed by what it covered as its files show it: its title, its Done when and Given sections, and the `<path>:<line>` of each `Your code goes here.` marker left in its starter. Then it prints `Next: <NN>`. A learner who has worked an Exercise may have replaced its markers, so `Markers: none` means only that none are left; Given still says what stayed as given.

The step is done when both have exited 0.

## 5. Plan, or no Exercise

Decide from the anchor's Goal, Scope, Key concepts and Check, and its Prereq closure.

**No Exercise.** Give one, and write nothing, when either holds:

- The anchor's material has no practical use on its own: acting on it in the tool needs units outside its Prereq closure, and a task that avoids them practises other units instead.
- The Goal's main outcome can't be measured by an Exercise check, even through a stand-in from the domain's Stand-ins section.

Tell the learner the anchor gets no Exercise and why, naming what's missing, and where its material gets practised instead, such as a dependant that uses it. For example: "GD-01.02.01 Nodes and the scene tree gets no Exercise. Its Goal is a model fact: what a node is, and that a node takes part in the game only while it's in the SceneTree. Acting on that fact in code needs `add_child()` and a script, and both are outside its Prereq closure. An editor-only task would practise GD-01.01.03 and GD-01.02.02, not this unit." Then stop.

**Plan.** Otherwise plan the next rung of the ramp. Hold every plan to these rules, which a steer can't change:

- **Scaffold line**: the learner writes only what uses the anchor's material. They may be expected to use anything in its Prereq closure and any API the anchor's own Scope names. Everything else is given, already built.
- **The Goal sets the target**, including a method it names, such as "moves only on physics ticks". The route beyond it is the learner's.
- **Minimum to ship**: at least one automated outcome, with the Goal's main outcome among them. A Scope edge case becomes an outcome only when it's observable, and every outcome needs the anchor's material or closure code the learner writes in this Exercise, so the Exercise gate can hold each one to its rules.

**What earlier Exercises covered** comes from `existing`'s output only: each one's Done when says which outcomes, Key concepts and Scope edge cases it reached, and its Given and markers say how much of the Prereq closure it gave. A Key concept or edge case counts as reached when a bullet's outcome needs it, not only when the bullet names it, such as `move_and_slide()` behind "the character walks to the well". Pass state stays out of it: the ramp reads only those files, never an earlier Exercise's Exercise check result or the learner's account of how one went. An Exercise printed with `no EXERCISE.md` or `EXERCISE.md can't be read` counts as covering nothing; still pick a situation other than its name's.

**The ramp.** Each Exercise turns one knob at most one notch from the latest Exercise, the one with the highest `<NN>`, and keeps the Goal's main outcome in a fresh situation: a scenario none of the earlier Exercises used, not a re-skin of one. Each covers only the Key concepts its task needs. Take the first rung that applies:

1. **First**: with no earlier Exercise, the Goal's main outcome in the plainest situation that shows it, with the most of the Prereq closure given.
2. **Coverage**: while a Key concept or observable Scope edge case is one no earlier Exercise reached, reach one of them, giving as much of the closure as the latest Exercise did.
3. **Composition**: once coverage is done, give one closure unit's code less than the latest Exercise gave, so the learner writes it alongside the anchor's material. The scaffold line is the ceiling: only closure code moves from given to written.
4. **Past the top rung**: once coverage is done and the latest Exercise gave none of the Prereq closure its task used, write the next Exercise in a fresh situation with no knob turned, the learner again writing all the closure code its task uses. Tell the learner that coverage and composition are exhausted, unless the latest Exercise was itself past the top rung, as it was when the Exercises before it had already exhausted both; that keeps the note to the first run past the top.

**The steer**, when the learner gave one, replaces the default pick of knob, direction and focus: "easier" turns a knob back a notch or picks a plainer situation, and "focus on `is_on_wall()`" makes that API the Key concept in play. When the steer would break the scaffold line or Minimum to ship, the rule wins: plan the closest Exercise within it, and tell the learner which rule the steer lost to and why, such as "Floor snapping is GD-12.01.02, outside GD-01.08.02's Prereq closure and Scope, so the scaffold line keeps `apply_floor_snap()` out of what you write". Go on without asking.

Write the plan as a few lines:

```text
Title: <a short title naming the situation, such as Walk to the well>
Situation: <the scene or program the learner finds, in the domain's tool>
Rung: <first, coverage: what it reaches, composition: the closure unit the learner now writes, or past the top rung>
Main outcome: <the Goal's main outcome, in this situation>
Learner writes: <where, and what it must do, as outcomes>
Given: <everything else the learner uses: files, scenes, helpers>
Key concepts in play: <only those the task needs>
```

The Exercise name is `<ID>-<NN>-<slug>`, with `<NN>` from `existing`'s `Next:` and `<slug>` made from the title as the Exercise format's [slug rule](references/exercise-format.md#where-an-exercise-lives) says.

The step is done when the plan and the Exercise name are fixed, and the learner has been told any rule their steer lost to and any past-the-top-rung note, or when the learner has the reason for no Exercise.

## 6. Generation directory

Make a fresh temporary directory, the Generation directory, and fill the domain's assets into the Exercise inside it:

```sh
exercises.py assets <domain> <gen-dir>/<name> --exercise-name <name> --curriculums <dir>
```

Write `context`'s output to `<gen-dir>/context.md`. The Exercise is built in `<gen-dir>/<name>/`, with `gate.json`, `reference/` and `near-misses/` beside it in `<gen-dir>`, as the Exercise format's [What the gate reads](references/exercise-format.md#what-the-gate-reads) lays out.

From here until step 10, a stop is a failed run: tell the learner why, and give them the paths of the Generation directory and, once step 8 has made it, the solver's directory, kept for inspection; nothing is in the Practice workspace, so they can run the skill again.

## 7. Author

Fill [`references/author-prompt.md`](references/author-prompt.md): `{{exercise_title}}` with the plan's title, `{{anchor}}` with the ID, `{{code}}` with the code, `{{target_version}}` with the Target version or `none`, `{{plan}}` with the plan, `{{gate_report}}` with `None.`, and with absolute paths, `{{context}}` with `<gen-dir>/context.md`, `{{exercise_dir}}` with `<gen-dir>/<name>`, `{{gen_dir}}` with the Generation directory and `{{exercise_format}}` with [`references/exercise-format.md`](references/exercise-format.md). Fill `{{domain_environment}}` with the text of `domain.md` from `## Environment` up to `## Checking`, and `{{domain_checking}}` with the text from `## Checking` to the end. Hand the filled prompt to one subagent.

The step is done when `<gen-dir>/<name>/EXERCISE.md` and `<gen-dir>/gate.json` exist.

## 8. Solver

Make a second fresh temporary directory, the solver's directory, outside the Generation directory: the Generation directory holds `check/`, so a solver given any path in it could read the Exercise check and tune the Reference solution to it. Copy the Exercise to `<solver-dir>/exercise/`, leaving out `check.sh`, `check/` and `hints/`, and copy `<gen-dir>/context.md` to `<solver-dir>/context.md`.

Fill [`references/solver-prompt.md`](references/solver-prompt.md): `{{exercise_title}}` as in step 7; `{{near_misses}}` with one line per entry of `gate.json`'s `near_misses`, as `<name>: <line text>`; `{{redo}}` with `None.`; `{{domain_environment}}` as in step 7, and only that section of `domain.md`; and with absolute paths, `{{solver_view}}` with `<solver-dir>/exercise`, `{{context}}` with `<solver-dir>/context.md`, `{{solver_dir}}` with the solver's directory and `{{exercise_format}}`. Hand it to one subagent.

Then sync the cases: replace `<gen-dir>/reference/` and `<gen-dir>/near-misses/` with copies of the solver's, leaving out any Near-miss directory that `gate.json`'s `near_misses` doesn't name.

The step is done when `<gen-dir>/reference/` and a directory under `<gen-dir>/near-misses/` for every Near-miss exist.

## 9. Gate

```sh
exercises.py gate <gen-dir>/<name> <gen-dir>
```

It prints a matrix of each automated line against the starter, the Reference solution and each Near-miss, then a verdict. Exit 0 is a pass: go to step 10. Otherwise run a revision round:

1. Fill the author prompt as in step 7, with `{{gate_report}}` set to the gate's whole output, and hand it to a new author subagent. It revises the Exercise and replies with the cases the solver must redo, as `<case>: <line text>`, or `none`.
2. For each case to redo, take the line's measured value: copy `<gen-dir>/<name>` to a new temporary directory, lay the case's files from `reference/` or `near-misses/<case>/` over it, run `./check.sh` there, and take that line's text in parentheses. Delete the temporary directory.
3. When there's a case to redo, refresh `<solver-dir>/exercise/` from the revised Exercise as in step 8, and fill the solver prompt again with `{{near_misses}}` from the revised `gate.json` and `{{redo}}` with one line per case, as `<case>: <line text> (measured: <value>)`. The solver gets only the line's text and its measured value, never the rest of the gate report. A Near-miss that's new in `gate.json` goes in `{{redo}}` too, with no measured value. Hand it to a new solver subagent.
4. Sync the cases as in step 8, so a Near-miss the author dropped from `gate.json` leaves `near-misses/` too, and run the gate again.

An `Environment problem:` line, exit 2, means a case couldn't run at all, such as a starter that fails to import; it goes to the author like any other failing round.

After 3 revision rounds, when the gate still fails:

- If it reports only `Environment problem:` lines, and no line of the Exercise check, stop as a failed run, showing the learner the gate's last output.
- If the Goal's main outcome line is among the lines it reports, the Exercise can't ship. Give a reasoned no Exercise as step 5 does, naming that line and why it couldn't be measured, and give the learner the paths of the Generation directory and the solver's directory, kept for inspection. Stop.
- Otherwise run one last revision round, steps 1 to 4, with `Failed 3 rounds: <line text>` at the top of `{{gate_report}}` for each line the gate reports. The author turns each into a Self-check bullet or cuts it. When that leaves no automated outcome line, or the gate still doesn't exit 0, stop as a failed run, showing the learner the gate's last output.

The step is done when the gate exits 0.

## 10. Ship

Check that `<Practice workspace>/<CODE>/` has no `<ID>-<NN>-*` directory, whatever its slug; if it has one, another run took the number, so stop as a failed run. Then remove from `<gen-dir>/<name>/` anything that isn't `EXERCISE.md`, `check.sh`, `check/`, `hints/` or a file of the starter, such as a cache the domain's tool wrote while an authoring-time script ran. Move `<gen-dir>/<name>/` there, creating `<Practice workspace>/<CODE>/` when it's missing. Only the Exercise moves: `gate.json`, `reference/`, `near-misses/` and `context.md` stay behind. Delete the Generation directory and the solver's directory.

Tell the learner the Exercise's path and title, the Done-when bullets, and to start from `EXERCISE.md`. When the gate turned a line the steer asked for into a Self-check bullet or cut it, tell the learner the steer lost to the Exercise gate there, naming the line. When the gate cut the line for what a coverage rung reaches, tell the learner that target is still unreached, so a later run may pick it again, and that a steer naming another Key concept or edge case moves past it. The step is done when the Exercise is in the Practice workspace and both temporary directories are gone.

## Without subagents

Where you can't start subagents, follow each filled prompt yourself, in the step that hands it off. When you follow the solver prompt, work from the solver's directory and the prompt alone, and solve the Task as `EXERCISE.md` states it, not as the Exercise check you wrote measures it.
