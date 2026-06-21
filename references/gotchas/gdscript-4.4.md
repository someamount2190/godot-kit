# GDScript on Godot 4.4 — verified traps

Every item here was HIT and verified during this skill's own build (2026-06-21,
Godot 4.4.stable.mono). These are not theory.

## 1. Inferred/untyped vars can be a PARSE ERROR (not a warning)
This environment surfaces `INFERRED_DECLARATION` as an error
("Warning treated as error"). So:
```gdscript
var warns := node.get_configuration_warnings()   # FAILS to parse (Variant infer)
var scr   := node.get_script()                    # FAILS (Variant)
var res   := load(p) if p != "" else null         # FAILS (ternary -> Variant)
```
Fix — type explicitly when the RHS is Variant/untyped:
```gdscript
var warns: PackedStringArray = node.get_configuration_warnings()
var scr: Variant = node.get_script()
var res: Variant = load(p) if p != "" else null
```
`var r := load(p)` alone is FINE — `load()` is typed `Resource`. The trap is
only Variant/untyped RHS. When in doubt, annotate the type.

## 2. Editor-only methods do not exist at runtime
`get_configuration_warnings()`, `_validate_property()`, `_get_property_list()`
for editor display, and anything you guard with `Engine.is_editor_hint()` are
EDITOR-ONLY. Calling them in a running scene throws
`Invalid call. Nonexistent function '...'` and aborts the current function
(everything after it in that call silently doesn't run). Don't call them at
runtime.

## 3. Windows: use the `*_console.exe` or stdout is empty
The plain `Godot_*.exe` detaches from the console (GUI subsystem). Subprocess
capture comes back EMPTY — you are blind to every error and `print()`. Always
launch `Godot_*_console.exe`. `godotkit.env` pins it.

## 4. `--headless` renders nothing
The headless display server doesn't draw. A screenshot under `--headless` is
blank and `get_viewport().get_texture().get_image()` may be null. Use headless
for logic/error scans (`run.check`, `run.scene_report`); use a real window for
pixels (`run.capture`).

## 5. Capturing the viewport — the working recipe (4.x)
```gdscript
for i in settle_frames:                  # let layout + a few frames settle
    await get_tree().process_frame
await RenderingServer.frame_post_draw    # wait until the frame is actually drawn
var img: Image = get_viewport().get_texture().get_image()
var err := img.save_png(abs_path)        # err == OK on success
```
Missing the `frame_post_draw` await is the usual cause of a black/partial grab.

## 6. A scene that fails to load makes headless Godot HANG
If the main/target scene's script has a parse error, `godot --headless` does not
exit on its own. Always pass a `--quit-after <frames>` backstop (the toolkit
does) so a broken target times out fast instead of hanging the run.

## 7b. Don't name a method after a Node virtual (signature clash)
Defining `func _input() -> void:` (or `_process`, `_ready`, `_draw`,
`_unhandled_input`, `_physics_process`...) with the WRONG signature collides with
the engine's virtual of that name → parse error: "The function signature doesn't
match the parent. Parent signature is '_input(InputEvent) -> void'." Rename your
helper (`_handle_input()`), or match the real virtual signature. Hit building the
dating sim's DateScene.

## 7. A self-quitting target races a harness
If a scene calls `get_tree().quit()` in `_ready`, instancing it under a capture
harness will quit the WHOLE tree before the harness captures. Capture targets
should be passive (real game scenes are). The harness owns the quit.
