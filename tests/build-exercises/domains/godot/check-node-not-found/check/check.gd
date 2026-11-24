extends "res://check/harness.gd"


func run() -> void:
	var mover: Node2D = load("res://mover.gd").new()
	mover.name = "Mover"
	root.add_child(mover)
	await ticks(60)
	var typo: Node2D = root.get_node("Movr")
	expect(typo.position.x > 0.0, "A line the Exercise check never reaches.", "")
