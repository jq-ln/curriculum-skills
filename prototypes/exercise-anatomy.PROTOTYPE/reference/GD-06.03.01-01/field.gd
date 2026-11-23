extends Node3D

## What grows here, such as "wheat".
var crop := ""
## How far the crop has grown, from 0.0 (sown) to 1.0 (ready).
var growth := 0.0


# Your code goes here.

func _ready() -> void:
	add_to_group("Persist")


func save() -> Dictionary:
	return {
		"filename": get_scene_file_path(),
		"parent": get_parent().get_path(),
		"pos_x": position.x,
		"pos_y": position.y,
		"pos_z": position.z,
		"crop": crop,
		"growth": growth,
	}


func load_state(data: Dictionary) -> void:
	position = Vector3(data["pos_x"], data["pos_y"], data["pos_z"])
	crop = data["crop"]
	growth = data["growth"]
