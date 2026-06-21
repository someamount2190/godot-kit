# SOP-01 — The screenshot loop (show → view → understand → decide → delete)

The core capability. You CANNOT see a running Godot game; this loop gives you
eyes. It is a discrete polling loop (seconds per frame, driven by your tool
round-trips), NOT a real-time video feed. You observe snapshots and act between
them. Every gate is mandatory.

## Gate 0 — preflight (never skip)
```python
# from scripts/ :  python -m godotkit.<...>  OR import in a host script
from godotkit import preflight
g = preflight.check(PROJECT_DIR, "res://target.tscn")
assert g["ok"], g["errors"]   # broken refs / parse errors -> FIX before capturing
```
A blank or error frame wastes a full window boot. Pure stage is microseconds.

## Gate 1 — capture the REAL running scene
```python
from godotkit import run
res = run.capture(
    PROJECT_DIR,
    "res://target.tscn",            # the scene to look at (any scene, not just main)
    OUT_PNG_ABS,                     # e.g. r"C:\...\_tmp\shot.png"
    settle=6,                        # frames to let it settle before the grab
    shots=1, interval=30,            # shots>1 -> OUT used as dir/prefix, _NNN.png
)
assert res["shots"], res["log"]      # list of PNG abs paths written
```
`capture()` is **non-invasive**: it copies the gdkit harness into the project,
runs the target in a Vulkan window, screenshots the viewport, then deletes the
harness. It does NOT touch the project's `main_scene`.

## Gate 2 — VIEW (both eyes)
1. **Read each PNG** with your image tool. Actually look. Is anything on screen?
   Right colors? Right position? Sprite missing (white box)? UI overlapping?
2. **Read the node tree** — `run.scene_report(PROJECT_DIR, "res://target.tscn")`
   returns `{nodes:[{name,class,script,transform,visible,...}]}`. This catches
   what a screenshot can't: a node that exists but is invisible/off-screen, a
   missing script, a wrong class.

You may NOT judge the scene from `scene_report` alone, nor from the PNG alone —
a node can be present in the tree yet draw nothing, and a PNG can look right
while the tree is wrong. Use both.

## Gate 3 — DECIDE & act
Compare to intent. Typical fixes:
- **Black/blank frame** → no Camera2D/3D, node off-screen, or you captured under
  `--headless` (don't). Check transforms in scene_report.
- **White rectangle** → missing texture (`res://` path broken — inspect_core
  will have flagged it).
- **Wrong position/scale** → fix the node transform in the `.tscn` or script.
- **Nothing happens over time** (multi-shot identical) → `_process`/physics not
  running, or you needed input.

To drive the game (stepped, not real-time), inject input or set state, then
recapture. Minimal input-injection pattern (extend the harness):
```gdscript
Input.action_press("ui_right")
await get_tree().process_frame
# ... capture ...
Input.action_release("ui_right")
```

## Gate 4 — DELETE & repeat
Delete the frame(s) you've judged (each viewed PNG costs context tokens — do
NOT spam hundreds). Re-run from Gate 1 until it visually holds.

## Gate 5 — report
Report ONLY after a PNG you VIEWED matches intent. Cite it. If you could not view
a render, STOP and say so — never claim it "looks right" blind.
