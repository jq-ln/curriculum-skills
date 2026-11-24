extends "res://check/harness.gd"

signal never


func _init() -> void:
	time_limit = 1.0


func run() -> void:
	var mover: Node2D = load("res://mover.gd").new()
	root.add_child(mover)
	await never
	expect(true, "A line the Exercise check never reaches.", "")
