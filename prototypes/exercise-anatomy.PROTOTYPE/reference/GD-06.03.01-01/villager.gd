extends Node3D

## The villager's name, unique in the colony.
var display_name := ""
## How hungry the villager is, from 0 (full) to 10 (starving).
var hunger := 0
## What the villager carries: item name to a whole-number count.
var inventory := {}


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
		"display_name": display_name,
		"hunger": hunger,
		"inventory": inventory,
	}


func load_state(data: Dictionary) -> void:
	position = Vector3(data["pos_x"], data["pos_y"], data["pos_z"])
	display_name = data["display_name"]
	hunger = int(data["hunger"])
	inventory = {}
	for item in data["inventory"]:
		inventory[item] = int(data["inventory"][item])
