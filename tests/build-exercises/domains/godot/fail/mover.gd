extends Node2D

## Speed in pixels per second.
@export var speed := 30.0


func _physics_process(delta: float) -> void:
	position.x += speed * delta
