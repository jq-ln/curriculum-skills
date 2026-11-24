extends "res://check/harness.gd"


func run() -> void:
	var main: Node = (load("res://main.tscn") as PackedScene).instantiate()
	root.add_child(main)
	var mover: Node2D = main.get_node_or_null("Mover")
	if mover == null:
		expect(false, "It moves 60 pixels in one second.", "no node named Mover")
		return
	await ticks(60)
	expect(absf(mover.position.x - 60.0) < 0.5, "It moves 60 pixels in one second.", "%.2f px" % mover.position.x)
