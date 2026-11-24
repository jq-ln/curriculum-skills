# Exercise format

This doc defines what an Exercise ships, where it lives, and what the Exercise gate reads while the Exercise is built. It is the single source of truth for that shape: the author writes an Exercise from it, `exercises.py` reads Exercises by it, and a domain reference fills in only what it leaves to the domain.

An Exercise is a practice item anchored to one Subsection, done in the subject's real environment, whose completion needs that Subsection's material. The Subsection is its **anchor**.

## Where an Exercise lives

Each Exercise is one directory:

```text
<Practice workspace>/<CODE>/<ID>-<NN>-<slug>/
```

- **Practice workspace**: the directory outside any doc set where a learner's Exercises live. It defaults to `practice/` in the Curriculums directory, and the learner can give another.
- **`<CODE>`**: the anchor's Curriculum code. Exercises of different Curriculums never share a directory.
- **`<ID>`**: the anchor's Subsection ID, such as `GD-01.08.02`, so `<ID>-*` finds a Subsection's Exercises and `LC_ALL=C ls` lists them in teaching order.
- **`<NN>`**: the anchor's Exercise number, two digits or more, starting at `01`. A new Exercise takes the highest number among the anchor's existing Exercises plus one, as `exercises.py existing <ID>` prints it. A number is never reused, so a gap left by a deleted Exercise stays a gap.
- **`<slug>`**: written once from the Exercise's title: lowercase it, turn each run of characters other than `a`-`z` and `0`-`9` into one `-`, and drop a leading or trailing `-`. When nothing is left, such as for a title in Japanese, the slug is `exercise`. `Walk to the well` gives `walk-to-the-well`. The slug stays when the anchor is renumbered and the directory is renamed.

Each Exercise is self-contained: it runs on its own, and nothing in one Exercise reaches into another.

### When the Curriculum renumbers

A renumber can give an Exercise's anchor a new ID, so the Exercise is traced by its [anchor record](#exercisemd), not its directory name. `exercises.py renumber <CODE>` reads every directory in `<Practice workspace>/<CODE>/` named `<ID>-<NN>-<slug>` with an ID of that code, and reports each as one of:

- **valid**: the recorded anchor ID, and the ID the directory name starts with, still name a Subsection with the recorded title.
- **moved**: exactly one Subsection has the recorded title, and the recorded ID or the directory name's ID differs from it. The line gives the old ID and the new one.
- **broken**: none or several Subsections have the recorded title, or the record is missing or unreadable. Its candidates follow: each Subsection with the recorded title, or, when none has it, the Subsection still at the recorded ID. A retitled anchor is therefore broken, never moved, because a title match is the only evidence of a move.

`renumber` writes nothing. Once the learner confirms a move, or picks the anchor of a broken Exercise whose record can be read, `exercises.py rename <dir> <new ID>` rewrites the record's Anchor and Anchor title from the new anchor, then renames the directory to `<new ID>-<NN>-<slug>`, keeping the slug and taking the next free `<NN>` under the new ID. When the ID is unchanged, as when settling a retitle, only the record changes. A missing or unreadable record is fixed by hand.

## What an Exercise ships

```text
<ID>-<NN>-<slug>/
  EXERCISE.md
  check.sh
  check/           the Exercise check's other files, when it has any
  hints/1.md
  hints/2.md
  hints/3.md
  ...              the starter project
```

### `EXERCISE.md`

Its sections, in this order:

````markdown
# <Exercise title>

- Curriculum: <CODE>
- Anchor: <ID>
- Anchor title: <anchor title>
- Target version: <version>

## Task

<The situation, then the outcome to reach. Names the files the learner writes in.>

## Done when

- <outcome>
- <Self-check outcome, as a concrete run and what to see> **(check by eye)**

## Given

<What stays as given: the files, scenes and helpers the learner uses but doesn't change.>

## Check

Run `./check.sh` from this folder. Leave `check/` as it is: the Exercise check relies on its files being the ones it shipped with.

Each PASS means that bullet's outcome held when measured, as the line prints. You're done when every automated line passes and you've seen each CHECK YOURSELF bullet hold. The check doesn't judge your route, style or code quality, and it doesn't record that you've finished.

## Stuck?

`hints/` holds three hints, each more direct than the last. Open `hints/1.md` first, and the next only if you're still stuck.
````

- **Anchor record**: the four bullets under the H1, in that order, before anything else. Curriculum is the anchor's code, Anchor its ID, and Anchor title the Subsection's title, the text after the ID in its H1, as it reads when the Exercise is written. Target version is the Curriculum's Target version; leave the line out when the Curriculum has none. The record keeps the Exercise traceable after the Curriculum changes.
- **Task** states the outcome, not the steps to it: the route is the learner's. An outcome the anchor's Goal names, including a method such as "moves only on physics ticks", is the outcome the Task sets.
- **Done when** maps one to one onto the Exercise check's outcome and Self-check lines, in the order the check prints them: each automated bullet is exactly one outcome line, and each Self-check bullet is exactly one line under `CHECK YOURSELF`. A Self-check bullet ends with **(check by eye)** and names a concrete run and what to see, such as "Run `main.tscn` and press F5: the colony reappears where it was. **(check by eye)**". Guard lines, such as "no script errors", have no bullet.
- **Given** says what stays as given, so the learner spends their effort on the anchor's material.
- **Check** carries the two paragraphs above verbatim: the note to leave `check/` as it is, and the promise paragraph.
- **Stuck?** carries the paragraph above verbatim.

### The starter

The starter is a project in the domain's tool, built so everything outside the learner's part already works. Each place the learner's code goes holds a comment reading `Your code goes here.`, in the comment syntax of its file type as the domain reference gives it, such as `# Your code goes here.` in GDScript.

### Hints

- `hints/1.md` asks a pointing question.
- `hints/2.md` gives the recipe.
- `hints/3.md` names likely failures by symptom, drawing on the anchor's Check-field misconceptions, with at least one per automated outcome and per Self-check bullet.

The hints are hidden by convention: the learner opens them only when stuck.

### The Exercise check

`check.sh` is the Exercise check's one command. The learner runs it with no arguments from the folder `EXERCISE.md` is in. It runs the domain's tool headless and measures what the learner's code does, never its source text, so a valid route written differently still passes. It records nothing.

When the installed tool's version differs from the Curriculum's Target version, filled in when the Exercise is written, it prints a warning and runs anyway. With no Target version, it compares nothing.

It prints, in this order:

1. One line per automated line, outcome or guard: `PASS` or `FAIL`, a space, the line's text (an outcome line's bullet as Done when has it, or a guard line's own text as `gate.json` names it), a space, and the measured value in parentheses.

   ```text
   PASS It walks toward the well at `speed`, 3 meters per second, whatever the frame rate. (3.02 m/s)
   FAIL It walks up the 30-degree ramp onto the plateau. (highest point 0.00 m, plateau at 2.00 m)
   PASS No script errors. (0 errors)
   ```

2. When the Exercise has Self-check bullets, the line `CHECK YOURSELF`, then one line per Self-check bullet: `-`, a space, and its text as Done when has it, without **(check by eye)**.

The Self-check lines are the last lines printed. Other lines, such as section headings and a summary, may come before `CHECK YOURSELF`, as long as none starts with `PASS` or `FAIL` and a space.

Its exit code:

| Exit | Meaning |
| --- | --- |
| 0 | Every automated line passed. |
| 1 | At least one automated line failed. |
| 2 | An environment problem: the tool is missing, the project fails to import, or the Exercise check itself crashed. |

Self-check bullets never affect the exit code. A runtime error in the learner's code fails a guard line; it never gives exit 2.

## What the gate reads

The Exercise is built in a generation directory, and the Exercise gate checks its Exercise check there before anything ships. Beside the Exercise, the generation directory holds:

```text
gate.json
reference/               the Reference solution
near-misses/<name>/      one directory per Near-miss
```

`reference/` and each `near-misses/<name>/` hold only the files they replace or add, each at its path in the Exercise. `<name>` is a short kebab-case name for the mistake, such as `moves-in-process`. None of these ship.

### `gate.json`

`gate.json` names every line of the Exercise check, says what kind it is, and says which line each Near-miss targets:

```json
{
  "lines": [
    { "text": "It walks toward the well at `speed`, 3 meters per second, whatever the frame rate.", "kind": "outcome" },
    { "text": "It moves only on physics ticks.", "kind": "outcome" },
    { "text": "No script errors.", "kind": "guard" },
    { "text": "Run `main.tscn`: the villager's feet stay on the ramp as it climbs.", "kind": "self-check" }
  ],
  "near_misses": {
    "frame-rate-bound": "It walks toward the well at `speed`, 3 meters per second, whatever the frame rate.",
    "moves-in-process": "It moves only on physics ticks."
  }
}
```

- **`lines`** lists every line in the order the Exercise check prints them, each with its `text` exactly as the check prints it, without the status or the measured value. Every text is distinct.
- **`kind`** is one of:
  - `outcome`: an automated line for a Done-when bullet. The gate holds it to four rules: it fails on the starter, passes on the Reference solution, fails on each Near-miss targeting it, and gives the same result on every rerun of a case.
  - `guard`: an automated line with no bullet, which catches accidents such as a script error or a changed given file. The gate holds it to two of the four rules: it passes on the Reference solution and gives the same result on every rerun of a case.
  - `self-check`: a Self-check bullet, printed under `CHECK YOURSELF`. The gate doesn't run it.
- **`near_misses`** maps each Near-miss's `<name>` to the `text` of the one `outcome` line it targets. Every `outcome` line is targeted by at least one Near-miss. Every directory under `near-misses/` has an entry, and every entry has a directory.
