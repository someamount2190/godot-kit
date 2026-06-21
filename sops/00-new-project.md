# SOP-00 — New project / scene from scratch

## Gate 1 — minimal valid project
A Godot 4.4 project needs a `project.godot` (config_version=5) and a main scene.
Minimal:
```
; project.godot
config_version=5
[application]
config/name="my-game"
run/main_scene="res://main.tscn"
[display]
window/size/viewport_width=640
window/size/viewport_height=360
```
A `.tscn` referencing a script:
```
[gd_scene load_steps=2 format=3 uid="uid://someuid"]
[ext_resource type="Script" path="res://main.gd" id="1"]
[node name="Main" type="Node2D"]
script = ExtResource("1")
```
(Or generate scenes from the editor — but for headless/agent work, authoring the
text directly is fine and reviewable.)

## Gate 2 — write GDScript, TYPED
Type everything (see gotchas/gdscript-4.4.md — untyped Variant inference is a
parse error here). Use `@onready`, `@export`, `await` (not `yield`), Callable
signals (`btn.pressed.connect(_on_press)`).

## Gate 3 — preflight before you trust it
`preflight.check(PROJECT_DIR, "res://main.tscn")` — static refs + headless boot.
Fix every error before moving on.

## Gate 4 — run the loop (SOP-01)
Capture → view → fix. Do not declare the scene done from code. A new scene is
"working" only when you've seen a correct PNG.

## Gate 5 — record
If you discovered a non-obvious build fact (a node setup, an import quirk),
append it to LEARNINGS.md AFTER a capture verified it.
