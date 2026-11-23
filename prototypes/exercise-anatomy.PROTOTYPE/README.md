# PROTOTYPE: Exercise anatomy on real Godot Subsections

Throwaway. Answers [#77](https://github.com/jq-ln/curriculum-skills/issues/77): does the working anatomy of an Exercise (instruction doc, setup, runnable check, tiered hints) hold up on real Subsections of the Godot Curriculum at `~/Documents/curricula/godot`?

## What's here

- `practice/GD/` is a Practice workspace laid out as [#80](https://github.com/jq-ln/curriculum-skills/issues/80#issuecomment-7112189773) decided, with one Godot project per Exercise:
  - `GD-01.08.02-01-walk-to-the-well/`: a practical unit. The learner makes a CharacterBody3D fall, walk at 3 m/s, climb a 30° ramp and stop at a 60° slope.
  - `GD-06.03.01-01-save-the-colony/`: a unit that leans on its Prereq closure (groups, Dictionaries, FileAccess, JSON, PackedScene). The learner writes the manual's save system for a colony of villagers and fields.
- `reference/` holds a reference solution and near-misses for each Exercise. The near-misses are the mistakes the Subsection's Check question names, plus one that ignores a limit its Scope states.
- `tools/` holds `gen_well.gd`, which built the well level's `main.tscn`, `closure.py`, which prints a Subsection's Prereq closure, and `try.sh`, which runs a check with reference files swapped into a temporary copy.

Try one: `practice/GD/GD-01.08.02-01-walk-to-the-well/check.sh` fails on the starter. `tools/try.sh practice/GD/GD-01.08.02-01-walk-to-the-well villager.gd=reference/GD-01.08.02-01/villager.gd` passes.

## GD-01.02.01 Nodes and the scene tree: no Exercise

What the skill would print:

> GD-01.02.01 Nodes and the scene tree gets no Exercise. Its Goal is a model fact: what a node is, and that a node takes part in the game only while it's in the SceneTree. Acting on that fact in code needs `add_child()` and a script, and both are outside its Prereq closure (GD-01.01.01 to GD-01.01.03, the editor only). An editor-only task, such as building a node tree in the Scene dock, would practise GD-01.01.03 and GD-01.02.02, not this unit. Its fact gets practised in the Exercises of the units that build on it, such as GD-01.04.03 Creating and freeing nodes at run time.

The call needed the Goal, the Scope and the closure together, and the format held enough to make it.

## Anatomy as built

- **Instruction doc** `EXERCISE.md`: the anchor record first (Curriculum code, anchor ID, anchor title, Target version), which settles #80's open "which file holds the record". Then Task, a "Done when" list, what stays as given, how to run the check, and where the hints are. "Done when" maps one to one onto the check's lines, so a failing line points at a bullet.
- **Setup**: a committed starter project, not a script that builds one. Stub files carry a `# Your code goes here.` marker. Given helpers carry everything outside the closure: `heading()` in the well, and `populate()`, `scramble()` and the F2/F5/F9 keys in the colony. Building the well's level with rotated slabs still needed an authoring-time script (`tools/gen_well.gd`), so the skill will write some scenes through Godot rather than as hand-typed `.tscn`.
- **Check**: `check.sh` warns on a Godot version mismatch, imports, then runs `godot --headless [--fixed-fps 60] --path . -s check/check.gd`, as [#76](https://github.com/jq-ln/curriculum-skills/issues/76#issuecomment-7111968304) found. `check.gd` lives inside the project, keeping each Exercise self-contained, and a `.gdignore` keeps it out of the import and the FileSystem dock. Each line prints PASS or FAIL with the measured value, and a `Logger` catches runtime errors. Outcome lines fail on the untouched starter. Guard lines, such as "no script errors" and "the rocks were left alone", may pass on it.
- **Hints**: `hints/1.md` to `3.md`, hidden by convention only, and out of the editor's FileSystem dock through `.gdignore`. Tier 1 asks a question that points at the concept, tier 2 gives the recipe, and tier 3 names the likely failures, by symptom, and their fixes.

## Findings

- **A check needs a reference solution and near-misses to be trusted.** Twice, a check's lines passed on the untouched starter. First, "climbed onto the plateau at y = 2" passed for a villager that never moved from y = 2. Later review found lines that hold vacuously, such as "moves only on physics ticks" for a villager that never moves and "inventory counts are ints" when nothing was loaded. The first colony check also failed one mistake on 3 lines. The fix is a generation step: run the check on the starter, where every outcome line must fail; on a reference, where all must pass; and on each near-miss, which must fail its own line. The reference has to exist at generation time even if it never ships. A property line, such as "only on physics ticks", needs the thing it qualifies to have happened.
- **The Subsection's Check field supplies the near-misses.** GD-01.08.02's Check names `* delta` and `_process()`. GD-06.03.01's names the skipped free that duplicates the colony. Each became a check line and a tier 3 hint.
- **Scope supplies the numbers a headless check needs.** `floor_max_angle` at 45° by default set the ramp at 30° and the slope at 60°. "Every number comes back as a float" became the inventory check.
- **Strict Prereq closures are narrow, and the Goal can outrun them.**
  - GD-01.08.02's closure has 11 units and no GD-01.03.02 Variables, functions and control flow, and no input. The Exercise works by giving `heading()` and needing no `if`: gravity goes in unconditionally, and `move_and_slide()` cancels it on the floor.
  - GD-06.03.01's closure lacks GD-01.04.03 Creating and freeing nodes at run time and GD-01.02.05 Finding nodes by path, yet its Goal is "free, then re-instance". Its Scope teaches those calls as steps of the pattern, so the Exercise treats an API the Scope names as in bounds. Either rule "the closure plus what the anchor's Scope names" or treat this as a missing Prereq in the Curriculum.
- **Typed properties hide the float limit.** `set("hunger", 3.0)` on an `int` property converts silently, so the limit shows only in untyped containers. The skill has to check that a Scope edge case is observable before it makes a check line out of it.
- **A "how" in the Goal becomes a target.** "Moves only on physics ticks" is in GD-01.08.02's Goal, so it's a "Done when" bullet. The check catches movement between `process_frame` and the next `physics_frame`.
- **Environment facts belong to the domain reference.** Jolt is set in `project.godot` because the Curriculum says a new 4.7 project uses it. The minimal `project.godot` from #76 doesn't say which engine it gets. `--fixed-fps 60` only matters for physics Exercises.
- **Possible flake**: once, right after `villager.gd` was swapped, a run reported a script error whose text was filtered out of the output. It didn't come back in 4 more runs.

## Subsection Fields used

| Field | Used for |
| --- | --- |
| Goal | The target, and "no Exercise" for GD-01.02.01 |
| Scope | Concrete targets, numbers, edge cases and limits; in-bounds APIs |
| Prereqs, through the closure | The scaffold line: what's given and what the learner writes |
| Check | Near-misses, a check line each, and tier 3 hints |
| Key concepts | A loose checklist. The Exercises skip some terms: `is_on_ceiling()` and `up_direction` in the well, and nested persistent nodes and skipping lines `JSON.parse()` rejects in the colony |
| Context | Curriculum code and Target version for the anchor record and the version warning |
| Title (H1) | The anchor record and the directory slug |
| Sources, Tags, Generators, Foundations, Section Generators | Not used. Running Godot verified behaviour, not the sources. |

**Missing from the format**: nothing these three needed. The old format's per-unit Build field wasn't missed: Goal plus Scope decided practical or not, and suggested a task. The one gap, GD-06.03.01's Goal using calls its closure lacks, is a Prereq question about the Curriculum, not a missing Field.

## Open questions for the human

1. Scaffold line: the strict closure, the closure plus what the anchor's Scope names, or everything before the anchor in teaching order?
2. Should the reference solution ship, such as behind a fourth hint tier, or stay generation-only?
3. Are hint files hidden only by convention enough?
4. Is the "no Exercise" verdict for GD-01.02.01 right, and is its wording what the skill should print?
5. The colony's "Done when" says each line names its scene file and parent, which is the manual's method, not only the outcome. It mirrors the Subsection's Goal. Should a Goal that names a method set the target, or only the outcome it achieves?
6. Should an Exercise cover every Key concept, or only those its task naturally needs?
