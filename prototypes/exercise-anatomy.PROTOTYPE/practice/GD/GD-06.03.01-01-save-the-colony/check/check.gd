extends SceneTree
## Check for GD-06.03.01-01 Save the colony.
## Run through ../check.sh, which runs:
##   godot --headless --path <exercise> -s check/check.gd

const SAVE_PATH := "user://savegame.save"


class ErrorCatcher extends Logger:
	var errors: Array[String] = []

	func _log_error(_function: String, file: String, line: int, code: String, rationale: String, _editor_notify: bool, _error_type: int, _script_backtrace: Array[ScriptBacktrace]) -> void:
		errors.append("%s:%d %s" % [file, line, rationale if rationale != "" else code])

	func _log_message(_message: String, _error: bool) -> void:
		pass


var catcher := ErrorCatcher.new()
var failures: Array[String] = []
var main: Node


func _initialize() -> void:
	OS.add_logger(catcher)
	_run()


func expect(ok: bool, what: String) -> bool:
	print(("  PASS  " if ok else "  FAIL  ") + what)
	if not ok:
		failures.append(what)
	return ok


func frames(n: int) -> void:
	for i in n:
		await process_frame


## The colony's state, keyed so two snapshots compare with ==. Numbers are
## compared as floats here; whether they came back as ints is its own check.
func snapshot() -> Dictionary:
	var villagers := {}
	for v in main.get_node("World/Villagers").get_children():
		var inventory := {}
		for item in v.inventory:
			inventory[item] = float(v.inventory[item])
		villagers[v.display_name] = {
			"position": v.position.snapped(Vector3.ONE * 0.0001),
			"hunger": float(v.hunger),
			"inventory": inventory,
		}
	var fields := []
	for f in main.get_node("World/Fields").get_children():
		fields.append([f.crop, snappedf(f.growth, 0.0001), f.position.snapped(Vector3.ONE * 0.0001)])
	fields.sort()
	return {"villagers": villagers, "fields": fields, "villager_nodes": main.get_node("World/Villagers").get_child_count()}


func inventory_types_ok() -> bool:
	for v in main.get_node("World/Villagers").get_children():
		for item in v.inventory:
			if typeof(v.inventory[item]) != TYPE_INT:
				return false
	return true


func _run() -> void:
	DirAccess.remove_absolute(ProjectSettings.globalize_path(SAVE_PATH))
	main = (load("res://main.tscn") as PackedScene).instantiate()
	root.add_child(main)
	await frames(1)
	var before := snapshot()
	var rocks: int = main.get_node("World/Decor").get_child_count()

	print("Saving")
	main.save_game()
	var lines := []
	var file := FileAccess.open(SAVE_PATH, FileAccess.READ)
	if expect(file != null, "save_game() wrote %s" % SAVE_PATH):
		while file.get_position() < file.get_length():
			lines.append(file.get_line())
		file.close()
	var expected_lines: int = before.villagers.size() + before.fields.size()
	expect(lines.size() == expected_lines, "it holds one line per villager and field, %d (found %d)" % [expected_lines, lines.size()])
	var all_parse := true
	for line in lines:
		var parsed = JSON.parse_string(line)
		if not (parsed is Dictionary and parsed.has("filename") and parsed.has("parent")):
			all_parse = false
	expect(lines.size() > 0 and all_parse, "each line is a JSON object naming the node's scene file and parent")

	main.scramble()
	await frames(1)
	var scrambled := snapshot()
	expect(scrambled != before, "(scrambling the colony changed it)")

	print("Loading")
	main.load_game()
	await frames(2)
	var after := snapshot()
	expect(after.villager_nodes == before.villager_nodes and after.villagers.keys().all(func(k): return before.villagers.has(k)),
		"the same villagers are back, no more and no fewer (%d: %s)" % [after.villager_nodes, ", ".join(after.villagers.keys())])
	expect(after.fields.size() == before.fields.size(), "the same number of fields is back (%d)" % after.fields.size())
	expect(after == before, "every villager's position, hunger and inventory, and every field's crop, growth and position, are as saved")
	expect(after != scrambled and inventory_types_ok(), "inventory counts came back as whole numbers (int), as they were saved")
	expect(main.get_node("World/Decor").get_child_count() == rocks, "the rocks, which aren't saved, were left alone")

	print("Loading again")
	main.load_game()
	await frames(2)
	expect(snapshot() == before, "loading twice in a row still gives the saved colony, with nothing duplicated")

	expect(catcher.errors.is_empty(), "no script errors%s" % ("" if catcher.errors.is_empty() else ":\n        " + "\n        ".join(catcher.errors)))
	print("")
	if failures.is_empty():
		print("All checks passed.")
		quit(0)
	else:
		print("%d check(s) failed." % failures.size())
		quit(1)
