# SOP-02 — Modify / debug an existing scene or script

## Gate 1 — SEE it first (baseline)
Before changing anything, capture the current state (SOP-01) and run
`scene_report` so you know the actual tree + how it looks NOW. Do not edit blind.

## Gate 2 — locate the real target
`scene_report` gives node names/classes/scripts/transforms. Match the on-screen
problem to a node. A `.tscn` is text — read it, but trust the report for the
runtime tree (instanced sub-scenes won't be obvious from the parent `.tscn`).

## Gate 3 — make the smallest change, TYPED
Edit the `.gd`/`.tscn`. Keep GDScript typed. If porting old code, check
gotchas/godot3-to-4.md FIRST.

## Gate 4 — preflight + re-capture (compare)
`preflight.check` then `capture` again to the SAME size. View before/after.
Confirm the change did what you intended AND didn't break something else (re-read
scene_report for new errors/missing nodes).

## Gate 5 — on failure
`debug.report(res["log"])` → mapped fix. Bounded retries (max 2). Then minimal
repro + STOP. Record a verified fix in LEARNINGS.md.
