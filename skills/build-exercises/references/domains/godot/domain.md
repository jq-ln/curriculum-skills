# Godot

Applies to: a Curriculum teaching the Godot game engine and GDScript, 4.x.

## Environment

### Tool

`godot` must be on PATH; `command -v godot` finds it. `godot --version` prints the installed version, such as `4.7.2.stable.arch_linux.ed1daf0bf` or `4.7.2.stable.official.<hash>`. A Target version matches when it's a dotted prefix of that output: `4.7.2` and `4.7` match `4.7.2.stable.arch_linux`, and `4.7.1` and `4.70` don't. A mismatch is a warning, never a reason to stop.

### Self-contained

One Godot project per Exercise: the Exercise's directory is the project, with its own `project.godot`. `class_name` globals, autoloads, the input map and every project setting are project-wide, so a project per Exercise keeps one Exercise's `class_name Player` or `jump` action out of every other. `assets/project.godot.tmpl` sets `config/name` to the Exercise's directory name and the 3D physics engine to Jolt; add any other setting the Exercise needs, such as an input action or the main scene, to the filled `project.godot`.

### Project layout

- Scenes are `.tscn` and scripts `.gd`, at the project root unless the Exercise has enough files to need folders. Refer to them by `res://` paths.
- Given code and learner code share a script when the learner writes one function of a node; the learner's part sits where the marker is. A script the learner writes whole holds only `extends` and the marker.
- The marker is `# Your code goes here.` in `.gd` files. A `.tscn` file holds no marker: when the learner builds a scene, the Task names the scene and the nodes it needs.
- `check/` and `hints/` each hold an empty `.gdignore`, from `assets/`, which hides them from the editor's FileSystem dock, so the learner's project shows only the starter.

### Building the starter

Write scenes as `.tscn` text when the nodes and their properties are easy to state. For geometry that's hard to type, such as ramps at an angle or a tiled level, write an authoring-time script that builds the scene in code and saves it with `ResourceSaver.save()`, and run it in the Generation directory:

```sh
godot --headless --path <exercise> -s <authoring-script>.gd
```

The script extends `SceneTree`, builds the nodes, sets each one's `owner` to the scene root so it's saved, packs the root into a `PackedScene`, saves it to a `res://` path and calls `quit()`. Only the saved `.tscn` ships; keep the authoring script outside the Exercise directory.

## Checking

### Harness

`check.sh` imports the project, then runs the Exercise's lines headless at a fixed frame rate:

```sh
godot --headless --no-header --path . --import
godot --headless --no-header --fixed-fps 60 --path . -s check/check.gd
```

- Importing first builds the global class cache, so `class_name` globals resolve even when the learner never opened the project in the editor. A project that fails to import, such as a broken `project.godot`, exits 2.
- `--fixed-fps 60` gives every frame a 1/60 s delta, so a run is repeatable and runs faster than real time. Each process frame comes with one physics tick.
- `check/harness.gd`, copied verbatim into every Exercise, is the `SceneTree` the lines run in. It registers a `Logger` with `OS.add_logger` that collects every error the engine reports. An error raised in a file under `res://check/` is the Exercise check's own, and so is an engine error whose innermost GDScript frame is there, such as `get_node()` on a missing node, unless its text names a `res://` path outside `res://check/`, such as the Exercise check's `load()` of a missing `main.tscn`. Every other error counts against the learner's code.
- After `run()` returns, the harness prints the guard line `No script errors.`, which fails on any of the learner's errors and measures them, then the summary, then the Self-check bullets under `CHECK YOURSELF`. A runtime error in the learner's code carries on: the function that raised it returns, and the lines still run.
- When the Exercise check's own code raises an error, it stops. If the learner's code had already raised one, that error is the likely cause, such as a script that didn't parse, so the guard line fails and the Exercise check exits 1. Otherwise it crashed and exits 2, as it does when `run()` takes longer than `time_limit` seconds of game time, 60 by default.

### Check lines

Write them in `check/check.gd`, which extends the harness and overrides `run()`. `run()` loads the learner's scene, drives it, and calls `expect()` once per automated "Done when" bullet and `self_check()` once per Self-check bullet, in the order "Done when" lists them:

```gdscript
extends "res://check/harness.gd"


func run() -> void:
	var main: Node = (load("res://main.tscn") as PackedScene).instantiate()
	root.add_child(main)
	var villager: CharacterBody3D = main.get_node_or_null("Villager")
	if villager == null:
		expect(false, "It walks toward the well at `speed`, 3 meters per second.", "no node named Villager")
		return
	var start := villager.global_position
	await ticks(60)
	var walked := Vector2(villager.global_position.x - start.x, villager.global_position.z - start.z).length()
	expect(absf(walked - 3.0) < 0.15, "It walks toward the well at `speed`, 3 meters per second.", "%.2f m/s" % walked)
	self_check("Run `main.tscn`: the villager's feet stay on the ramp as it climbs.")
```

What the harness gives `run()`:

- `expect(ok: bool, text: String, measured: String) -> bool` prints `PASS` or `FAIL`, the text, and the measured value in parentheses. `text` is the bullet exactly as "Done when" has it, without **(check by eye)**. `measured` says what was measured, with its unit, so a failure tells the learner how far off they are. It returns `ok`, so a later line can depend on an earlier one.
- `self_check(text: String)` records a Self-check bullet. Every one prints last, under `CHECK YOURSELF`, wherever `run()` calls it.
- `await ticks(n)` returns once `n` more physics ticks have run every `_physics_process`; `await frames(n)` waits `n` process frames. Use these to wait, rather than awaiting a signal the learner's code may never emit.
- `time_limit`: set it in `_init()` when `run()` needs more than 60 s of game time.
- Signals connected to the harness, such as `physics_frame.connect(...)` and `process_frame.connect(...)`, observe between ticks. To check "moves only on physics ticks", record the position at each `process_frame` and compare it at the next `physics_frame`: only `_process` runs between the two.

`gate.json` lists the harness's guard line last among the automated lines, as `{ "text": "No script errors.", "kind": "guard" }`.

Read the learner's nodes defensively, with `get_node_or_null()`: a node the learner renamed comes back null, so check it for null before reading its properties and fail the line with what's missing as its measured value, as the example does. `get_node()` on a missing node also logs `Node not found`, which the harness counts as the Exercise check's own error, so it exits 2. Use `Input.parse_input_event()` to press keys or click, so `_input` and `is_action_just_pressed` see the event; `Input.action_press()` holds an action but reaches no `_input`. The headless root viewport is 64 by 64 pixels, so set `root.size` before checking a layout that depends on window size.

### Stand-ins

Headless Godot draws nothing and plays nothing, so measure the property that drives a visual, sound or feel outcome:

- A color or tint: `modulate`, `self_modulate`, or a material's `albedo_color`, such as `modulate == Color.RED`.
- Visibility: `visible` or `is_visible_in_tree()`; on camera: `Camera3D.is_position_in_frustum()` or `Camera2D.get_screen_center_position()`.
- A sound: `AudioStreamPlayer.playing` and which `stream` is set.
- An animation: `AnimationPlayer.current_animation` and `is_playing()`; a tween: the property's value once it finishes.
- Particles: `emitting` and `amount`.
- Feel: a number the anchor's Scope states, such as time to the jump's peak or how far a dash goes, measured in ticks or units.

An outcome with no property or number behind it, such as whether a motion reads as smooth, becomes a Self-check bullet with a concrete run and what to see.
