extends Node3D
## Given: builds a small colony and lets you play with it.
## F5 saves, F9 loads, F2 scrambles the colony so you can see a load undo it.

const VILLAGER := preload("res://villager.tscn")
const FIELD := preload("res://field.tscn")
const ROCK := preload("res://rock.tscn")
const NAMES := ["Ada", "Bram", "Cora", "Dov", "Edda", "Finn", "Greta", "Hal"]
const CROPS := ["wheat", "barley", "turnips"]

var rng := RandomNumberGenerator.new()


func _ready() -> void:
	rng.seed = 77
	populate()


## Given: fills World with villagers, fields and rocks.
func populate() -> void:
	for i in 4:
		var field := FIELD.instantiate()
		field.crop = CROPS[i % CROPS.size()]
		field.growth = snappedf(rng.randf(), 0.01)
		field.position = Vector3(-6.0 + i * 4.0, 0, -6)
		$World/Fields.add_child(field)
	for i in 6:
		var villager := VILLAGER.instantiate()
		villager.display_name = NAMES[i]
		villager.hunger = rng.randi_range(0, 10)
		villager.inventory = {"wheat": rng.randi_range(0, 5), "wood": rng.randi_range(0, 3)}
		villager.position = Vector3(rng.randf_range(-6, 6), 0, rng.randf_range(-3, 4))
		$World/Villagers.add_child(villager)
	for i in 3:
		var rock := ROCK.instantiate()
		rock.position = Vector3(-7.0 + i * 7.0, 0, 7)
		$World/Decor.add_child(rock)


## Given: changes the colony so a load has something to undo. Moves and
## feeds every villager, regrows every field, removes one villager and one
## field, and adds a newcomer.
func scramble() -> void:
	for villager in $World/Villagers.get_children():
		villager.position += Vector3(rng.randf_range(-2, 2), 0, rng.randf_range(-2, 2))
		villager.hunger = (villager.hunger + 3) % 11
		villager.inventory["wheat"] = 99
	for field in $World/Fields.get_children():
		field.growth = 0.0
	$World/Villagers.get_child(0).free()
	$World/Fields.get_child(0).free()
	var newcomer := VILLAGER.instantiate()
	newcomer.display_name = "Newcomer"
	$World/Villagers.add_child(newcomer)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_F5:
				save_game()
				print("saved")
			KEY_F9:
				load_game()
				print("loaded")
			KEY_F2:
				scramble()
				print("scrambled")


## Writes the colony to user://savegame.save.
func save_game() -> void:
	var file := FileAccess.open("user://savegame.save", FileAccess.WRITE)
	for node in get_tree().get_nodes_in_group("Persist"):
		if node.scene_file_path.is_empty() or not node.has_method("save"):
			continue
		file.store_line(JSON.stringify(node.save()))


## Replaces the colony with the one in user://savegame.save.
func load_game() -> void:
	if not FileAccess.file_exists("user://savegame.save"):
		return
	var file := FileAccess.open("user://savegame.save", FileAccess.READ)
	while file.get_position() < file.get_length():
		var json := JSON.new()
		if json.parse(file.get_line()) != OK:
			continue
		var data: Dictionary = json.data
		var node: Node = load(data["filename"]).instantiate()
		get_node(data["parent"]).add_child(node)
		node.load_state(data)
