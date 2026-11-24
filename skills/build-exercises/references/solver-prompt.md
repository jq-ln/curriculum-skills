<!-- Template for the solver agent. The orchestrator replaces every double-braced placeholder and sends the whole file. -->

# Solve: {{exercise_title}}

You solve an Exercise the way a learner would, twice over: once correctly, as its Reference solution, and once per Near-miss, making one mistake a learner plausibly makes. Another agent wrote the Exercise and its Exercise check. You work from the task alone, so your Reference solution shows the task can be solved as written, and the Exercise check is then tested against it.

## Inputs

- The Exercise, as the learner gets it, without its Exercise check or hints: `{{solver_view}}`
- The anchor Subsection and its Prereq closure: `{{context}}`
- Write the Reference solution to: `{{gen_dir}}/reference/`
- Write each Near-miss to: `{{gen_dir}}/near-misses/<name>/`
- Exercise format: `{{exercise_format}}`

The Near-misses to write, one per line as `<name>: <the Done-when bullet it fails>`:

```text
{{near_misses}}
```

Redo only these cases, each with the Exercise check's measured value, or `None.` on a first run:

```text
{{redo}}
```

The domain's environment, which says how to run its tool and how a project in it is laid out:

{{domain_environment}}

## What to write

Read `EXERCISE.md` in `{{solver_view}}`, then the starter project beside it, then the anchor's Goal, Scope and Check in `{{context}}`. Read the Exercise format's "What the gate reads" section for how the cases are laid out.

- **Reference solution**: solve the Task so every Done-when bullet holds, writing only in the places `EXERCISE.md` says the learner writes, with only what the anchor and its Prereq closure teach. Put each file you change or add in `reference/`, at its path in the Exercise, holding the whole file as the learner would leave it. Leave every given file as it is.
- **Near-miss**: for each line of the list above, start from your Reference solution and make the one mistake its `<name>` describes, so that bullet fails and the rest still hold where they can. Draw the mistake from the anchor's Check field and Scope when they name one, since those are the mistakes learners make. Lay its files out as `reference/`'s are, under `near-misses/<name>/`.

Run the starter's project with your files laid over it, using the domain's tool as its environment describes, to see each case does what you meant. Write in the files above only; `{{solver_view}}` stays as it is.

On a redo, rewrite only the cases listed: a Reference solution whose bullet measured as failing gets fixed so the bullet holds, and a Near-miss whose bullet measured as passing gets a mistake that breaks it.

## Done

You're done when `reference/` and a directory for every Near-miss in the list exist, each holding only files at their paths in the Exercise, and:

- the Reference solution meets every Done-when bullet, by what you saw when you ran it;
- each Near-miss fails its own bullet through a mistake a learner could make, and differs from the Reference solution only in that mistake.

Reply `done` and nothing else.
