# Headless checks for Godot 4.7 Exercises

Research for [#76](https://github.com/jq-ln/curriculum-skills/issues/76), under the map [#74](https://github.com/jq-ln/curriculum-skills/issues/74). Sources checked 2026-11-23. Engine claims marked **verified** were run against the local `godot 4.7.2.stable.arch_linux` in a scratch project; the scripts are summarized in [Local verification](#local-verification).

## Answer

A plain GDScript check run as `godot --headless --fixed-fps 60 --path <project> -s <check.gd>` does everything an Exercise check needs, with no addon. The check extends `SceneTree`, loads the learner's scene into `root`, feeds input with `Input.parse_input_event` or `Input.action_press`, steps frames by awaiting `physics_frame` or `process_frame`, reads node properties and signals, records the learner's runtime errors through a `Logger`, and ends with `quit(code)`. All of this was verified headless on 4.7.2, including key events reaching `is_action_just_pressed` and `_input`, a held action moving a node, a mouse click pressing a `Button`, `CharacterBody2D` landing on a floor, an `Area2D` firing `body_entered`, and a tween finishing.

The check script doesn't have to be inside the project: `-s` takes an absolute filesystem path, and that script can `load()` helpers by absolute path too (verified). So one Godot install serves every Exercise and nothing is copied into `addons/`.

GUT and gdUnit4 add asserts, reports and an editor panel, but both hard-code `res://addons/<name>/` paths, so each Godot project needs its own copy (about 260 to 270 files). Each also has a headless trap: GUT's CLI exits 0 without running anything when its classes aren't in the global class cache yet, and gdUnit4's CLI refuses to run headless (exit 103) unless passed `--ignoreHeadlessMode`.

One Godot project per Part, with each Exercise as a subdirectory, runs fine, and checks can target one Exercise's scene. Its costs are a single `class_name` namespace (two Exercises declaring `class_name Player` collide silently: the cache keeps one path, with no warning in `--import` output, verified), autoloads that run during every Exercise, and one shared input map and set of project settings. Since the plain-script check needs no addon, the addon-duplication reason for sharing a project goes away; a project per Exercise costs a 92-byte `project.godot` and a 2.4 s first import (verified).

## Options

### `godot --headless --script` with a `SceneTree` script

**Invocation.** `--headless` is "`--display-driver headless --audio-driver Dummy`. Useful for servers and with `--script`" ([command line tutorial](https://docs.godotengine.org/en/4.7/tutorials/editor/command_line_tutorial.html)). `--script` takes "a resource path relative to the project ... or an absolute filesystem path", and "The script must inherit from `SceneTree` or `MainLoop`" (same page). `--path` names the project directory. `--fixed-fps <fps>` "Force[s] a fixed number of frames per second. This setting disables real-time synchronization" (same page).

**Install footprint.** None beyond the Godot binary. The check can live outside the project (verified with an absolute `-s` path), or inside it in a folder holding a `.gdignore` file, which hides the folder from the editor's FileSystem dock ([project organization](https://docs.godotengine.org/en/4.7/tutorials/best_practices/project_organization.html)). That page says ignored resources "can't be loaded anymore using the `load()` and `preload()` methods"; on 4.7.2 a `.gd` check in a `.gdignore` folder still ran with `-s` and still loaded a sibling `.gd` helper (verified), so this holds for scripts but shouldn't be relied on for imported assets such as textures.

**One install, several Exercises.** Yes: the same binary runs any check against any project via `--path`.

**Exit codes.** `SceneTree.quit(exit_code)` "Quits the application at the end of the current iteration, with the given `exit_code`", and "For portability reasons, it should be between `0` and `125`" ([SceneTree](https://docs.godotengine.org/en/4.7/classes/class_scenetree.html)). The docs give no other exit codes. Verified on 4.7.2:

- `quit(7)` exits 7.
- A parse error in the check script itself exits 1.
- Runtime errors in the learner's code don't change the exit code: running a scene that errors every physics frame with `--quit-after 30` exits 0. The check has to catch them itself, with a `Logger` (below).
- A parse error in a learner script makes `load()` log `Failed to load script ... with error "Parse error"` and return a script whose `can_instantiate()` is false; the process carries on. `godot --headless --path <project> --check-only -s res://<file>.gd` exits 1 on that file and 0 on a valid one, so it doubles as a syntax check for any learner script.

**Loading and driving a scene.** `load("res://ex1/main.tscn").instantiate()` then `root.add_child(scene)`, or `change_scene_to_file`, which takes effect at the end of the frame ([SceneTree](https://docs.godotengine.org/en/4.7/classes/class_scenetree.html)). The project's autoloads are present under `-s` (verified: `root.has_node("Game")` is true); the project's main scene is not loaded, because the check script is the main loop. Methods and properties on the learner's nodes can be called and read directly.

**Input.** `Input.parse_input_event` "Feeds an InputEvent to the game. Can be used to artificially trigger input events from code"; `Input.action_press` "will simulate pressing the specified action" but "will not cause any `Node._input()` calls" ([Input](https://docs.godotengine.org/en/4.7/classes/class_input.html)). Verified headless: an `InputEventKey` for physical Space, mapped to `jump` in the project's input map, made `is_action_just_pressed("jump")` true for one physics frame and reached `_input`; `action_press("move_right")` held for 60 physics frames moved a node at 100 px/s by 99.99 px; an `InputEventMouseButton` press and release over a `Button` emitted `pressed`, both through `Input.parse_input_event` and through `root.push_input`.

**Stepping frames.** `await physics_frame` and `await process_frame` advance one frame each; the signals fire "immediately before" `_physics_process` and `_process` ([SceneTree](https://docs.godotengine.org/en/4.7/classes/class_scenetree.html)). Without `--fixed-fps`, frames run at real time (the 60-frame check took 1.3 s wall clock); with `--fixed-fps 60` each frame gets a fixed 1/60 s delta and the same check took 0.2 s (verified). `--fixed-fps` also makes timing-based results repeatable.

**Catching learner errors.** `Logger` is a "Custom logger to receive messages from the internal error/warning stream", registered with `OS.add_logger()`; `_log_error` receives the `file`, `line`, `code` and `rationale`, and "will be called from threads other than the main thread", so a real check should guard its list with a `Mutex` ([Logger](https://docs.godotengine.org/en/4.7/classes/class_logger.html)). Verified: a `Logger` subclass in the check captured `res://ex2/player.gd:5 Invalid call. Nonexistent function 'foo' in base 'Nil'.`, and the check turned it into a nonzero exit.

**What else works headless (verified).** `CharacterBody2D.move_and_slide` with gravity landed on a `StaticBody2D` (`is_on_floor()` true), an `Area2D` emitted `body_entered`, and a `Tween` reached its final value. The headless root viewport is 64 x 64 px, so GUI layout that depends on window size (anchors, containers) lays out at that size unless the check sets `root.size`.

**Global class cache.** `class_name` globals come from `.godot/global_script_class_cache.cfg`, which only the editor writes. In a project that has never been opened or imported, `ProjectSettings.get_global_class_list()` is empty under `-s` (verified), so code that names a learner class, or a learner script that names another, fails. `godot --headless --path <project> --import` builds the cache and exits 0 (2.4 s for an empty project, verified). A learner who has opened the project in the editor already has it; a check runner can run `--import` first to be safe.

### A `MainLoop` script

`-s` also accepts a script that extends `MainLoop` directly, and `--main-loop <name>` runs "a MainLoop specified by its global class name" ([command line tutorial](https://docs.godotengine.org/en/4.7/tutorials/editor/command_line_tutorial.html)). A bare `MainLoop` has no scene tree, so it can't load or run a learner's scene; `--main-loop` also needs the global class cache. `SceneTree` is a `MainLoop` subclass and is the one to use.

### GUT 9.7.1

**Version.** GUT 9.7.1, on the `godot_4_7` branch, is the release for Godot 4.7.x; `main` and 9.6.1 target 4.6.x ([README](https://github.com/bitwes/Gut), [9.7.1 release](https://github.com/bitwes/Gut/releases/tag/v9.7.1)).

**Install footprint.** "Put the `addons/gut` directory into your project" and enable the plugin, then relaunch Godot (README; [Install](https://gut.readthedocs.io/en/v9.7.1/Install.html)). The `addons/gut` tree at v9.7.1 is 259 files, 2.5 MB. The CLI entry point loads `res://addons/gut/version_conversion.gd` and `res://addons/gut/cli/gut_cli.gd` by `res://` path ([`gut_cmdln.gd`](https://github.com/bitwes/Gut/blob/godot_4_7/addons/gut/gut_cmdln.gd)), so it must live at that path in each project. A symlinked directory under `res://addons/` resolved for a hand-written script on 4.7.2 (verified), so one shared copy symlinked into each project may work; GUT itself was not run, per this ticket's rule against running downloaded code.

**One install, several Exercises.** One copy per Godot project. Within a project, `-gdir`, `-gtest` and `-gselect` pick which test scripts run ([Command line](https://gut.readthedocs.io/en/v9.7.1/Command-Line.html)), so one copy serves every Exercise in that project.

**Exit codes.** "0 will be returned if all tests pass and 1 will be returned if any fail" ([Command line](https://gut.readthedocs.io/en/v9.7.1/Command-Line.html)). Gotcha in the source: if GUT's `class_name`s aren't in the global class cache, `gut_cmdln.gd` pushes "Some GUT class_names have not been imported. Please restart the Editor or run godot --headless --import" and calls `quit(0)`; it also calls `quit(0)` if the main loop doesn't start in time ([`gut_cmdln.gd`](https://github.com/bitwes/Gut/blob/godot_4_7/addons/gut/gut_cmdln.gd), [`version_conversion.gd`](https://github.com/bitwes/Gut/blob/godot_4_7/addons/gut/version_conversion.gd)). A fresh copy run before an import reports success without running a test.

**Invocation.** `godot -d -s --path "$PWD" addons/gut/gut_cmdln.gd`, with `-gexit` to quit when done; options can also come from `res://.gutconfig.json` ([Command line](https://gut.readthedocs.io/en/v9.7.1/Command-Line.html)). The docs don't mention `--headless`.

**Driving a scene and input.** Tests extend `GutTest` and add nodes themselves (`add_child_autofree`). `GutInputSender` sends events either to an object's `_input`, `_gui_input` and `_unhandled_input`, or to `Input`, in which case "`Input` will treat all the events it gets exactly the same as if the events were triggered from hardware. This means all the `is_action_just_pressed` and similar functions will work the same"; calls chain with `wait`, `wait_frames` and `hold_for`, and the sender emits `idle` when the sequence ends ([Mocking Input](https://github.com/bitwes/Gut/blob/godot_4_7/documentation/docs/Mocking-Input.md)).

**Stepping frames.** `wait_idle_frames` (alias `wait_process_frames`), `wait_physics_frames`, `wait_seconds`, `wait_for_signal` and `wait_until` ([Awaiting](https://gut.readthedocs.io/en/v9.7.1/Awaiting.html)). `simulate(obj, times, delta)` calls `_process` and `_physics_process` recursively but is not a real frame: "timers, for example, will not fire since the main loop of the game is not actually running" ([Simulate](https://gut.readthedocs.io/en/v9.7.1/Simulate.html)).

### gdUnit4 6.2.3

**Version.** v6.2.x supports Godot 4.5 to 4.7.1; master (v7.0.0) targets 4.7, 4.7.1 and 4.8.dev7 ([README](https://github.com/godot-gdunit-labs/gdUnit4)). 4.7.2 isn't listed; v6.2.3 fixes "font size error on a fresh Godot 4.7 editor" and the "scene runner delivering input events twice" ([v6.2.3 release](https://github.com/godot-gdunit-labs/gdUnit4/releases/tag/v6.2.3)).

**Install footprint.** "Extract the downloaded package to the `addons` folder", enable it under Project Settings, Plugins, and "restart the Godot Editor after the plugin installation" ([Install](https://godot-gdunit-labs.github.io/gdUnit4/latest/first_steps/install/)). The `addons/gdUnit4` tree at v6.2.3, excluding its own `test/` folder, is 273 files, 1.2 MB, and its runner loads `res://addons/gdUnit4/bin/GdUnitCmdTool.gd` ([`runtest.sh`](https://github.com/godot-gdunit-labs/gdUnit4/blob/v6.2.3/addons/gdUnit4/runtest.sh)). One copy per project, as for GUT.

**One install, several Exercises.** One copy per project; `runtest -a <directory|suite>` picks suites, `-i` ignores some ([Command line](https://godot-gdunit-labs.github.io/gdUnit4/latest/advanced_testing/cmd/)).

**Exit codes.** Documented: 0 all passed, 100 failures, 101 warnings ([Command line](https://godot-gdunit-labs.github.io/gdUnit4/latest/advanced_testing/cmd/)). The source adds 103 headless not supported, 104 Godot version not supported, 105 script errors detected ([`GdUnitTestCIRunner.gd`](https://github.com/godot-gdunit-labs/gdUnit4/blob/v6.2.3/addons/gdUnit4/src/core/runners/GdUnitTestCIRunner.gd)).

**Headless.** `runtest.sh` needs `GODOT_BIN` or `--godot_binary`, and runs Godot with `-d` and without `--headless`, minimizing the window ([`runtest.sh`](https://github.com/godot-gdunit-labs/gdUnit4/blob/v6.2.3/addons/gdUnit4/runtest.sh), [`GdUnitCmdTool.gd`](https://github.com/godot-gdunit-labs/gdUnit4/blob/v6.2.3/addons/gdUnit4/bin/GdUnitCmdTool.gd)). Under the headless display server it exits 103 with "Headless mode is not supported! ... Godot 'InputEvents' are not transported by the Godot engine in headless mode", unless run with `--ignoreHeadlessMode` ([`GdUnitTestCIRunner.gd`](https://github.com/godot-gdunit-labs/gdUnit4/blob/v6.2.3/addons/gdUnit4/src/core/runners/GdUnitTestCIRunner.gd)). The engine-level claim doesn't hold on 4.7.2: both input paths gdUnit4's scene runner uses, `Input.parse_input_event` and `Viewport.push_input` ([`GdUnitSceneRunnerImpl.gd`](https://github.com/godot-gdunit-labs/gdUnit4/blob/v6.2.3/addons/gdUnit4/src/core/GdUnitSceneRunnerImpl.gd)), delivered events headless (verified). gdUnit4's own scene runner wasn't run.

**Driving a scene and input.** `scene_runner("res://my_scene.tscn")` loads a scene, "One Scene Runner can only manage one scene", and it is freed automatically; `simulate_frames(n, delta_ms)` processes frames "respecting time factor", and `set_time_factor` speeds the run up by scaling `Engine.time_scale` and physics ticks ([Scene runner](https://godot-gdunit-labs.github.io/gdUnit4/latest/advanced_testing/sceneRunner/)). Actions, keys, mouse and touch have `simulate_*` functions, and "you must wait at least one frame cycle after simulating inputs", with `await runner.await_input_processed()` ([Actions](https://godot-gdunit-labs.github.io/gdUnit4/latest/advanced_testing/scene_runner/actions/)).

### Anything newer

Nothing new for 4.7. The [4.7 release page](https://godotengine.org/releases/4.7/) doesn't mention testing, headless or the command line. The release build's `godot --help` has no `--test` option; the engine's own unit tests are a build-time option for engine developers, not a tool for game projects. The newest relevant engine piece is the `Logger` class above, which lets a plain check catch learner errors that would otherwise leave the exit code at 0.

## What a headless check can't observe

- **Pixels.** The headless display driver uses the dummy renderer: `root.get_texture()` returned null with `Parameter "t" is null` from `servers/rendering/dummy/storage/texture_storage.h` (verified). Colors on screen, shaders, lighting, particles' look, and whether something is visible on camera can't be checked by image; only the properties that drive them (`visible`, `modulate`, `material` parameters, camera position) can. Running the same check without `--headless` opens a window with a real renderer, at the cost of needing a display.
- **Sound.** `--headless` uses the Dummy audio driver ([command line tutorial](https://docs.godotengine.org/en/4.7/tutorials/editor/command_line_tutorial.html)); a check can read `AudioStreamPlayer.playing` and which stream is set, not what is heard.
- **Feel.** Game feel, readability, juice and difficulty are judgments. A check can pin numbers that stand in for them (jump height within a range, time to apex, coyote-time frames) only if the Exercise states those numbers as its target.
- **Editor work.** Whether the learner used an editor feature (the Inspector, a particular dock, the animation editor) isn't visible; only the saved result in `.tscn`, `.tres` or `project.godot` is, and those are text the check can parse.

## One project per Part

Mechanically it works: a check runs one Exercise with `--path <part> -s <check>` and loads `res://exN/main.tscn` (verified), and the learner runs one Exercise in the editor with Run Current Scene; `--scene res://ex1/main.tscn` does the same from the command line (verified). The costs come from everything in `project.godot` and the class cache being project-wide:

- **`class_name` collisions.** Two Exercises each declaring `class_name Player` left one entry in `global_script_class_cache.cfg`, pointing at `res://ex2/player.gd` after one import and `res://ex1/player.gd` after the next, with no warning in `--import` output (verified). Any script that says `Player` gets whichever won. Exercises would need unique class names, such as a prefix per Exercise, or no `class_name` in given code.
- **Autoloads.** Autoloads are "always loaded, no matter which scene is currently running" ([Singletons (Autoload)](https://docs.godotengine.org/en/4.7/tutorials/scripting/singletons_autoload.html)), and they load under `-s` too (verified). An autoload one Exercise adds runs during every other Exercise and its check, and an Exercise whose material is autoloads would change the environment of its siblings.
- **Input map.** Actions live in `project.godot`'s `[input]` section. Two Exercises that both want `jump` share one binding; an Exercise that teaches editing the input map edits every Exercise's map. A check can add its own actions at runtime with `InputMap`, but the learner's editor play uses the saved map.
- **Other project settings.** Main scene, window size, physics ticks, gravity, layer names and rendering settings are one set per project, so an Exercise about any of them leaks into the rest.
- **Addons.** The upside: one GUT or gdUnit4 copy per Part instead of per Exercise. With the plain-script check there's no addon to share.

A project per Exercise avoids all of the above for 92 bytes of `project.godot` and one import, at the cost of a separate entry in the Project Manager per Exercise and a given scaffold copied into each.

## Local verification

Scratch project with `project.godot` holding an autoload `Game`, input actions `jump` (physical Space) and `move_right`, and subdirectories `ex1/`, `ex2/`, `ex3/`; checks in a separate directory, run with absolute `-s` paths.

| Claim | Command shape | Result |
| --- | --- | --- |
| Key event reaches `is_action_just_pressed` and `_input` | `--headless --path part1 -s /abs/check_ex1.gd` | `jumps=1`, `inputs=1` |
| Held action over 60 physics frames | same | moved 99.9999 px at 100 px/s |
| Mouse click presses a `Button` | same, `check_ui.gd` | `pressed` emitted via `parse_input_event` and via `push_input` |
| Autoloads load under `-s` | same | `root.has_node("Game")` true |
| `--fixed-fps 60` speed | `time` both ways | 0.2 s vs 1.3 s |
| `Logger` captures learner runtime error | `check_ex2.gd` | captured `res://ex2/player.gd:5`, exit 2 |
| Class cache absent before import | `get_global_class_list()` | empty; after `--import`, one `Player` entry |
| Duplicate `class_name` | two `--import` runs | one entry, path flips, no warning |
| Learner parse error | `load()`; `--check-only -s` | `can_instantiate()` false, exit 0; `--check-only` exit 1 |
| Exit codes | `quit(7)`; broken check; erroring scene `--quit-after 30` | 7; 1; 0 |
| Physics and tweens | `check_physics.gd` | landed at y=89.99 on floor, `body_entered` once, tween at 100.0 |
| Pixels | `root.get_texture()` | null, dummy renderer |
| Symlinked `res://addons/shared` | `load("res://addons/shared/helper.gd")` | loaded |
| `.gdignore` folder | `-s res://ex1/check/check.gd` | ran, loaded sibling `.gd` |
| Empty project cost | `--import` on 92-byte `project.godot` | 2.4 s, 16 KB `.godot/` |
