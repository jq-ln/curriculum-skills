extends SceneTree
# Builds main.tscn for GD-01.08.02-01. Run with --path <exercise>.

func _slab(root: Node, name: String, size: Vector3, xform: Transform3D, color: Color) -> void:
	var body := StaticBody3D.new()
	body.name = name
	body.transform = xform
	root.add_child(body)
	body.owner = root
	var cs := CollisionShape3D.new()
	cs.name = "CollisionShape3D"
	var box := BoxShape3D.new()
	box.size = size
	cs.shape = box
	body.add_child(cs)
	cs.owner = root
	var mi := MeshInstance3D.new()
	mi.name = "MeshInstance3D"
	var mesh := BoxMesh.new()
	mesh.size = size
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mesh.material = mat
	mi.mesh = mesh
	body.add_child(mi)
	mi.owner = root

# A slab of the given length and thickness whose top face rises at `deg`
# toward -Z, starting at the point (0, y0, z0) on its top surface.
func _ramp_xform(deg: float, length: float, thick: float, y0: float, z0: float) -> Transform3D:
	var a := deg_to_rad(deg)
	var basis := Basis(Vector3.RIGHT, a)
	var top_mid := Vector3(0, y0 + sin(a) * length / 2.0, z0 - cos(a) * length / 2.0)
	var normal := basis.y
	return Transform3D(basis, top_mid - normal * thick / 2.0)

func _initialize() -> void:
	var root := Node3D.new()
	root.name = "Main"
	var grass := Color(0.35, 0.55, 0.3)
	var stone := Color(0.55, 0.55, 0.55)
	# Ground: top at y = 0.
	_slab(root, "Ground", Vector3(12, 1, 60), Transform3D(Basis(), Vector3(0, -0.5, -10)), grass)
	# Gentle ramp, 30 degrees, from z = 0 up to the plateau at y = 2.
	_slab(root, "GentleRamp", Vector3(4, 0.5, 4), _ramp_xform(30, 4, 0.5, 0, 0), grass)
	var ramp_end := -2.0 / tan(deg_to_rad(30))
	# Plateau: top at y = 2, from the ramp's top to z = -8.
	var plateau_len := 8.0 + ramp_end
	_slab(root, "Plateau", Vector3(4, 2, plateau_len), Transform3D(Basis(), Vector3(0, 1, ramp_end - plateau_len / 2.0)), grass)
	# Steep slope, 60 degrees, rising from the plateau's far edge.
	_slab(root, "SteepSlope", Vector3(4, 0.5, 6), _ramp_xform(60, 6, 0.5, 2, -8), stone)
	var well := Marker3D.new()
	well.name = "Well"
	well.position = Vector3(0, 6, -16)
	root.add_child(well)
	well.owner = root
	var villager: Node3D = (load("res://villager.tscn") as PackedScene).instantiate()
	villager.position = Vector3(0, 2, 8)
	root.add_child(villager)
	villager.owner = root
	villager.set("target", well)
	var sun := DirectionalLight3D.new()
	sun.name = "Sun"
	sun.transform = Transform3D(Basis.from_euler(Vector3(deg_to_rad(-50), deg_to_rad(30), 0)), Vector3(0, 10, 0))
	root.add_child(sun)
	sun.owner = root
	var cam := Camera3D.new()
	cam.name = "Camera3D"
	cam.transform = Transform3D(Basis.from_euler(Vector3(deg_to_rad(-20), deg_to_rad(90), 0)), Vector3(16, 6, -2))
	root.add_child(cam)
	cam.owner = root
	var packed := PackedScene.new()
	packed.pack(root)
	print(ResourceSaver.save(packed, "res://main.tscn"))
	quit()
