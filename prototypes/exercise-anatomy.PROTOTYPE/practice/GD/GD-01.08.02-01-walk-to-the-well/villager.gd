extends CharacterBody3D

## Walking speed in meters per second.
@export var speed := 3.0

## The node this villager walks toward. Set in main.tscn.
@export var target: Node3D


## Given: the horizontal direction from this villager toward its target,
## as a unit vector with no vertical part.
func heading() -> Vector3:
	var to_target := target.global_position - global_position
	to_target.y = 0.0
	return to_target.normalized()


# Your code goes here.

func _physics_process(delta: float) -> void:
	var walk := heading() * speed
	velocity.x = walk.x
	velocity.z = walk.z
	velocity += get_gravity() * delta
	move_and_slide()
