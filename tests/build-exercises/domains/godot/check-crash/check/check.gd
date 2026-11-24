extends "res://check/harness.gd"


func run() -> void:
	var mover: Node2D = load("res://mover.gd").new()
	root.add_child(mover)
	await ticks(60)
	expect(absf(mover.position.x - 60.0) < 0.5, "It moves 60 pixels in one second.", "%.2f px" % mover.position.x)
	var missing: Node2D = null
	expect(missing.position.x > 0.0, "A line the Exercise check never reaches.", "")
