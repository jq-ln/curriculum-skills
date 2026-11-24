<!-- Template for the author agent. The orchestrator replaces every double-braced placeholder and sends the whole file, once per round. -->

# Author: {{exercise_title}}

You write one Exercise for the Subsection {{anchor}}: its task, its starter project, its Exercise check and its hints, plus the gate manifest that says how to test the Exercise check. A solver agent then writes a Reference solution and Near-misses from the task alone, without seeing your Exercise check, and the Exercise gate runs your Exercise check against the starter, the Reference solution and each Near-miss. Only an Exercise whose Exercise check passes the gate ships.

## Inputs

- Anchor: {{anchor}}, in Curriculum `{{code}}`
- Target version: {{target_version}}
- The anchor Subsection and its Prereq closure: `{{context}}`
- The Exercise: `{{exercise_dir}}`, which already holds the domain's assets
- The Generation directory, where `gate.json` goes: `{{gen_dir}}`
- Exercise format: `{{exercise_format}}`

The plan, which fixes the Exercise's title, situation, main outcome, what the learner writes and what stays as given:

```text
{{plan}}
```

The gate report from the last round, or `None.` on the first:

```text
{{gate_report}}
```

The domain's environment:

{{domain_environment}}

How the domain's Exercise check measures:

{{domain_checking}}

## What to write

Read the Exercise format in full, then the anchor's Goal, Scope, Key concepts and Check in `{{context}}`, then the files already in `{{exercise_dir}}`. Write the Exercise into `{{exercise_dir}}` as the Exercise format lays it out, keeping the assets that are there:

- **`EXERCISE.md`**: the anchor record from the Inputs, then the Task in the plan's situation, stating the outcome and leaving the route to the learner. A method the anchor's Goal names, such as "moves only on physics ticks", is part of the outcome and gets its own Done-when bullet.
- **Done when**: one bullet per outcome, each one needing the anchor's material or closure code the learner writes here. The main outcome from the plan is always an automated bullet. Add a bullet for a Scope edge case only when its effect can be observed in the running project. Leave out any bullet the learner meets without writing anything.
- **The starter**: everything outside what the learner writes already built and working, with `Your code goes here.` markers, in the domain's comment syntax, where the learner's code goes. Write the starter's files only; the solution belongs to the solver.
- **The Exercise check**: one automated line per automated bullet, in Done-when order, written as the domain's Check lines section says. Each line measures what the learner's code does when it runs, through a stand-in property or a Scope number when the outcome is visual, sound or feel. An outcome nothing can measure becomes a Self-check bullet with a concrete run and what to see. Give each line a measured value with its unit, so a failure says how far off the learner is.
- **Hints**: `hints/1.md` to `hints/3.md` as the Exercise format describes, with tier 3 drawing on the anchor's Check field.
- **`{{gen_dir}}/gate.json`**: every line in print order, the domain's guard lines included, and at least one Near-miss per outcome line. Name each Near-miss for the mistake it makes, such as `moves-in-process`, drawing the mistakes from the anchor's Check field and Scope, so the solver can write it from its name and its bullet.

Every line must fail on the untouched starter, so a line about how something happens, such as "only on physics ticks", also measures that it happened.

## Revising

When the gate report holds a matrix, read every `Broken:` and `Environment problem:` line, and rule on each failing line:

- **The line is wrong**: it passes on the starter, measures something the task doesn't ask, flakes, or crashes. Revise the line, the starter or `gate.json`, whichever is at fault.
- **The case is wrong**: the Reference solution fails a bullet the task as written lets it meet, or a Near-miss passes the bullet it targets. Leave the case's files alone; the solver redoes it.

When a revision changes the Task, a bullet or a given file, list the reference as a case to redo too, since it was written to the old task. For each `Failed 3 rounds:` line at the top of the gate report, turn its line into a Self-check bullet if a concrete run shows it, or cut it, updating `EXERCISE.md`, the Exercise check, the hints and `gate.json` together, and dropping any Near-miss that targeted only that line from `gate.json`.

## Done

You're done when `{{exercise_dir}}` and `{{gen_dir}}/gate.json` are written and:

- `EXERCISE.md` has every section of the Exercise format, in order, with the Check and Stuck? paragraphs verbatim;
- Done when maps one to one onto the Exercise check's outcome and Self-check lines, and `gate.json` names every line the Exercise check prints, with its text exactly as printed;
- every outcome line has at least one Near-miss in `gate.json`;
- on a revision round, every failing line in the gate report has a ruling.

Reply with one line per case the solver must redo, as `<case>: <line text>`, where `<case>` is `reference` or a Near-miss's name, or `none` when there's none.
