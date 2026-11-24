# Domain reference contract

What a domain author writes so `build-exercises` can build Exercises in a new subject's environment. A [Domain reference](../GLOSSARY.md#exercises) is the only part of the skill that knows a subject's tool; the rest of the skill, `exercises.py` and the prompts, stays domain-neutral, so adding a domain touches no other code. Godot is the worked example throughout, and its [`domain.md`](../skills/build-exercises/references/domains/godot/domain.md) and [`assets/`](../skills/build-exercises/references/domains/godot/assets/) are the full one.

There's no contract version. Every domain ships with the rest of the skill in one plugin, so a PR that changes this contract updates every Domain reference with it.

## Layout

A Domain reference is one directory in the skill, named for the domain in kebab-case:

```text
skills/build-exercises/references/domains/<domain>/
├── domain.md
└── assets/
    └── check.sh.tmpl
```

- `domain.md` is prose that only the model reads, under the fixed headings in [domain.md](#domainmd).
- `assets/` is copied into each Exercise, as [assets/](#assets) describes.

## domain.md

`domain.md` opens with an H1 naming the domain, then an `Applies to:` line. The rest is these headings, in this order, each present even when its answer is short; a section with nothing to say holds `None.`:

```markdown
# <Domain>

Applies to: <which Curriculums this domain serves>

## Environment

### Tool
### Self-contained
### Project layout
### Building the starter

## Checking

### Harness
### Check lines
### Stand-ins
```

H4 headings may follow inside any section. A test in `tests/build-exercises/test_exercises.py` checks every `domain.md` in the skill against this order.

### Applies to

The orchestrator matches each `Applies to:` line against the Curriculum's subject and Brief to pick the domain. A doc set doesn't keep its Brief verbatim, so the orchestrator reads the subject from the H1 of `index.md` and the scope the Brief set from its Intro Field. No match stops the run; more than one asks the learner. Name the subject and the tool, so a near-miss subject doesn't match:

```markdown
# Godot

Applies to: a Curriculum teaching the Godot game engine and GDScript, 4.x.
```

### Environment

What it takes to run the subject's tool and lay out a project in it. Both subagents get this section, so it says how the environment works, never how the Exercise check measures.

- **Tool**: what must be on PATH, how to check it's there, the version command, and how to compare its output with the Curriculum's Target version. Godot: `godot` on PATH; `godot --version` prints `4.7.2.stable.arch_linux`, which matches a Target version that is a dotted prefix of it, such as `4.7.2` or `4.7`.
- **Self-contained**: what one Exercise is in the tool, so that nothing in one Exercise can break another. Godot: one Godot project per Exercise, because `class_name` globals, autoloads and the input map are project-wide.
- **Project layout**: the file types, where given code and learner code go, and the `Your code goes here.` marker's comment syntax for each file type. Godot: scenes are `.tscn` and scripts `.gd` at the project root; the marker is `# Your code goes here.` in `.gd` files.
- **Building the starter**: ways to produce starter files that are hard to write as text, or `None.` Only their output ships. Godot: authoring-time scripts run with `godot --headless -s` in the Generation directory, such as one that builds rotated level geometry and saves it as a `.tscn`.

### Checking

How the Exercise check measures. Only the author subagent gets this section, so the solver's Reference solution can't be shaped by it.

- **Harness**: what the shared harness in `assets/` does and how `check.sh` runs it. Godot: `check.sh` runs `godot --headless --no-header --path <project> --import` so `class_name` globals exist, then `godot --headless --no-header --fixed-fps 60 --path <project> -s check/check.gd`; `check/harness.gd` registers a `Logger` with `OS.add_logger` to turn learner runtime errors into failed guard lines, and holds `expect()`, the `CHECK YOURSELF` section, the summary and the exit codes.
- **Check lines**: which file the author writes that Exercise's lines in, and their form. Godot: `check/check.gd`, which extends the harness and calls `expect()` once per "Done when" bullet.
- **Stand-ins**: the measurable properties behind visual, sound or feel outcomes, so the author can automate them. Godot: `modulate` or `visible` for a color or visibility, `AudioStreamPlayer.playing` and its `stream` for a sound, and a Scope number such as time to apex for feel.

### Who reads which section

| Reader | Gets |
| --- | --- |
| Orchestrator | `Applies to:`, to pick the domain; Environment's Tool, for the tool check before anything runs |
| Author subagent | Environment as `{{domain_environment}}` and Checking as `{{domain_checking}}` |
| Solver subagent | Environment only, as `{{domain_environment}}` |

## assets/

`exercises.py assets <domain> <gen-dir> --exercise-name <ID>-<NN>-<slug>` copies `assets/` into a fresh [Generation directory](../GLOSSARY.md#exercises), mirroring its paths, hidden files and empty directories included:

- A file whose name ends `.tmpl` is a template. It's read as UTF-8, filled, and written without the suffix, keeping its line endings and file mode, so `check.sh.tmpl` becomes an executable `check.sh`.
- Every other file is copied byte for byte, so binaries, and text that happens to hold `{{`, are safe.

A template may use exactly two placeholders:

| Placeholder | Filled with |
| --- | --- |
| `{{target_version}}` | The Curriculum's Target version, or empty when its index has none |
| `{{exercise_name}}` | The Exercise's directory name, `<ID>-<NN>-<slug>` |

Any other `{{...}}` in a template is an error naming the file and line, and `assets` writes nothing, so a typo fails before the author starts.

`check.sh.tmpl` is the only required asset. It becomes the Exercise check's one command. Before an Exercise ships, `exercises.py gate` runs that command on the starter, the Reference solution and each Near-miss, relying only on this contract, so it works for every domain unchanged:

- On a version mismatch with `{{target_version}}`, it warns and still runs.
- Each automated line prints `PASS` or `FAIL`, the bullet and the measured value.
- Self-check bullets print last, under `CHECK YOURSELF`, and don't affect the exit code.
- It exits 0 when every automated line passes, 1 when one fails, and 2 for an environment problem such as a missing tool. A runtime error in learner code fails a guard line rather than exiting 2.

The Godot domain's `assets/`:

```text
assets/
├── check.sh.tmpl        # imports, then runs check/check.gd headless; compares {{target_version}}
├── project.godot.tmpl   # sets config/name to {{exercise_name}} and the physics engine to Jolt
├── check/
│   ├── .gdignore        # hides check/ from the editor's FileSystem dock
│   └── harness.gd       # the Logger catcher, expect(), CHECK YOURSELF, the summary and exit codes
└── hints/
    └── .gdignore        # hides hints/ from the editor's FileSystem dock
```

A fix to a shared asset, such as `harness.gd`, reaches only Exercises written after it.

## Testing a domain

A domain's tests are fixture cases, run by [`test_domain_checks.py`](../tests/build-exercises/test_domain_checks.py), so a domain author writes no test code. Each case is the part of an Exercise its assets don't give, and the runner checks what the filled `check.sh` prints and exits with:

```text
tests/build-exercises/domains/<domain>/
├── requires                one line: the tool check.sh runs, such as godot
└── <case>/
    ├── expected            exit <code>, then every line check.sh prints
    ├── target-version      optional: the case's Target version
    └── ...                 the project files and check lines, laid over the filled assets
```

For each case, the runner copies a fixture Curriculum, gives its index the case's `target-version` or none, fills the domain's assets into a fresh Exercise directory with `exercises.py assets`, lays the case's other files over them, and runs `./check.sh` there. It passes when the exit code is the one on `expected`'s first line and the output, stdout and stderr together, matches the remaining lines one for one:

- A `*` in a line matches any run of characters, such as a tool version that differs between machines.
- A line that is just `...` matches any number of lines, such as the tool's own error output.

A case named `env-error` runs with the tool removed from PATH. When the tool isn't on PATH at all, the domain's cases are skipped, so a contributor without it can still run the suite; its CI job sets `REQUIRE_DOMAINS=<domain>` to fail instead.

Every domain covers these cases, each named for what it shows:

| Case | Shows |
| --- | --- |
| `pass` | Every line passes: exit 0. |
| `fail` | An outcome line fails, with its measured value: exit 1. |
| `runtime-error` | A runtime error in the learner's code fails a guard line: exit 1, not 2. |
| `self-check-last` | Self-check bullets print last, under `CHECK YOURSELF`, outside the exit code. |
| `version-mismatch` | A Target version the tool doesn't match: a warning, then the run. |
| `no-target-version` | No Target version: nothing about versions. |
| `env-error` | The tool is missing: exit 2. |

A domain adds cases for its own ways to fail, such as Godot's `import-error`, `check-crash`, `check-node-not-found`, `check-timeout`, `parse-error`, `missing-scene` and `broken-scene`.

Each domain gets its own CI job in [`ci.yml`](../.github/workflows/ci.yml) that installs its tool, pinned by sha256, and runs the cases; see [`ci.md`](workflow/ci.md#adding-a-job).
