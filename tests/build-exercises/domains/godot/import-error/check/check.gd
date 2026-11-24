extends "res://check/harness.gd"


func run() -> void:
	var mover: Node2D = load("res://mover.gd").new()
	root.add_child(mover)
	await ticks(30)
	await ticks(30)
	expect(absf(mover.position.x - 60.0) < 0.5, "It moves 60 pixels in one second.", "%.2f px" % mover.position.x)
