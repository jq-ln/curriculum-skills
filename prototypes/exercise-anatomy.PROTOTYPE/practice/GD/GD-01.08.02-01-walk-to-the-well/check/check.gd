extends SceneTree
## Check for GD-01.08.02-01 Walk to the well.
## Run through ../check.sh, which runs:
##   godot --headless --fixed-fps 60 --path <exercise> -s check/check.gd


class ErrorCatcher extends Logger:
	var errors: Array[String] = []

	func _log_error(_function: String, file: String, line: int, code: String, rationale: String, _editor_notify: bool, _error_type: int, _script_backtrace: Array[ScriptBacktrace]) -> void:
		errors.append("%s:%d %s" % [file, line, rationale if rationale != "" else code])

	func _log_message(_message: String, _error: bool) -> void:
		pass


var catcher := ErrorCatcher.new()
var failures: Array[String] = []
var villager: CharacterBody3D
var moved_in_process := false
var _pos_at_process := Vector3.INF


func _initialize() -> void:
	OS.add_logger(catcher)
	_run()


func expect(ok: bool, what: String) -> void:
	print(("  PASS  " if ok else "  FAIL  ") + what)
	if not ok:
		failures.append(what)


func ticks(n: int) -> void:
	for i in n:
		await physics_frame


func flat(v: Vector3) -> Vector3:
	return Vector3(v.x, 0.0, v.z)


func _on_process_frame() -> void:
	_pos_at_process = villager.global_position


func _on_physics_frame() -> void:
	# Between process_frame and the next physics_frame only _process runs.
	if _pos_at_process != Vector3.INF and villager.global_position != _pos_at_process:
		moved_in_process = true


func _run() -> void:
	var main: Node = (load("res://main.tscn") as PackedScene).instantiate()
	root.add_child(main)
	villager = main.get_node("Villager")
	await process_frame
	process_frame.connect(_on_process_frame)
	physics_frame.connect(_on_physics_frame)
	var start := villager.global_position

	print("Falling (1.5 s)")
	await ticks(90)
	expect(villager.is_on_floor(), "the villager is on the floor after falling")
	expect(absf(villager.global_position.y) < 0.05, "it landed on the ground at y = 0 (y = %.2f)" % villager.global_position.y)
	expect(villager.global_position.z < start.z - 3.0, "it walked toward the well while falling and landing (%.2f m)" % (start.z - villager.global_position.z))

	print("Walking on flat ground (0.5 s)")
	var a := villager.global_position
	await ticks(30)
	var walked := flat(villager.global_position - a).length() / 0.5
	expect(absf(walked - 3.0) < 0.15, "it walks at speed, 3 m/s (measured %.2f m/s)" % walked)
	expect(villager.is_on_floor(), "it stays on the floor while walking")

	print("Climbing and meeting the steep slope (10 s)")
	var highest := -INF
	for i in 600:
		await physics_frame
		highest = maxf(highest, villager.global_position.y)
	var p := villager.global_position
	expect(p.z < -4.0, "it crossed the plateau (z = %.2f)" % p.z)
	expect(absf(p.y - 2.0) < 0.1, "it climbed the 30-degree ramp onto the plateau at y = 2 (y = %.2f)" % p.y)
	expect(highest < 2.5, "it never climbed the 60-degree slope (highest y = %.2f)" % highest)
	expect(p.z < -7.0 and p.z > -8.5, "it stopped at the foot of the 60-degree slope (z = %.2f)" % p.z)
	expect(villager.is_on_wall(), "it reports is_on_wall() against the 60-degree slope")
	expect(villager.is_on_floor(), "it still reports is_on_floor() on the plateau")
	expect(flat(villager.velocity).length() < 0.5, "its velocity lost the part going into the slope (horizontal %.2f m/s)" % flat(villager.velocity).length())

	expect(not moved_in_process, "it moves only on physics ticks")
	expect(catcher.errors.is_empty(), "no script errors%s" % ("" if catcher.errors.is_empty() else ":\n        " + "\n        ".join(catcher.errors)))

	print("")
	if failures.is_empty():
		print("All checks passed.")
		quit(0)
	else:
		print("%d check(s) failed." % failures.size())
		quit(1)
