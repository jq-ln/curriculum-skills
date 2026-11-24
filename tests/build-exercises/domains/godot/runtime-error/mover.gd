extends Node2D

## Speed in pixels per second.
@export var speed := 60.0

var trail: Array


func _physics_process(delta: float) -> void:
	position.x += speed * delta
	trail.back().queue_free()
