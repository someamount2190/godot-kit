# Godot 3 → 4 API rename catalog

Reference knowledge — check BEFORE running ported code, not after it crashes.
Godot 4 renamed a large fraction of the 3.x API. The classifier signature
`godot3_to_4_api` flags many of these from a log, but prevention beats cure.

## The high-frequency breakers
| Godot 3 | Godot 4 |
|---------|---------|
| `PackedScene.instance()` | `instantiate()` |
| `yield(obj, "sig")` | `await obj.sig` |
| `KinematicBody2D` / `KinematicBody` | `CharacterBody2D` / `CharacterBody3D` |
| `move_and_slide(vel)` (returns vel) | set `velocity`, call `move_and_slide()` (void) |
| `move_and_slide_with_snap(...)` | `velocity` + `floor_snap_length` + `move_and_slide()` |
| `Spatial` | `Node3D` |
| `Reference` | `RefCounted` |
| `Array.empty()` / `String.empty()` | `is_empty()` |
| `OS.get_ticks_msec()` | `Time.get_ticks_msec()` |
| `OS.window_size` / fullscreen | `DisplayServer.window_*` |
| `get_tree().set_input_as_handled()` | `get_viewport().set_input_as_handled()` |
| `connect("sig", self, "method")` | `sig.connect(method)` (Callable) |
| `emit_signal("sig", a)` | `sig.emit(a)` (or still `emit_signal`) |
| `export var x` | `@export var x` |
| `onready var x` | `@onready var x` |
| `tool` (top of file) | `@tool` |
| `setget set, get` | `set`/`get` accessors on the var |
| `rad2deg` / `deg2rad` | `rad_to_deg` / `deg_to_rad` |
| `PoolByteArray` etc. | `PackedByteArray` etc. |
| `Tween` node + `interpolate_property` | `create_tween()` + `tween_property` |
| `texture.get_data()` | `texture.get_image()` |
| `.instance()` on AnimatedSprite | `AnimatedSprite2D` / `AnimatedSprite3D` |

## Signals are Callables now
```gdscript
# 3.x
button.connect("pressed", self, "_on_pressed")
# 4.x
button.pressed.connect(_on_pressed)
button.pressed.connect(_on_pressed.bind(extra_arg))
```

## Physics: CharacterBody pattern (4.x)
```gdscript
extends CharacterBody2D
func _physics_process(delta: float) -> void:
    velocity.y += gravity * delta
    velocity.x = direction * speed
    move_and_slide()            # uses & writes `velocity`; returns void
    if is_on_floor(): ...
```

## When unsure
The fastest ground-truth is the running engine: `run.check(project)` boots
headless and prints the exact `Nonexistent function '<name>'` — then map it here.
