extends "res://check/harness.gd"


func run() -> void:
	var mover: Node2D = load("res://mover.gd").new()
	root.add_child(mover)
	self_check("Run the scene: the mover glides to the right.")
	await ticks(60)
	expect(absf(mover.position.x - 60.0) < 0.5, "It moves 60 pixels in one second.", "%.2f px" % mover.position.x)
	self_check("Run the scene and watch it for a second: it never stutters.")
	expect(mover.position.y == 0.0, "It stays on its row.", "y = %.2f" % mover.position.y)
