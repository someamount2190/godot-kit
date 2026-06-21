# SOP-06 — Design a scene / level before coding it

For anything beyond a trivial prop scene (a level, a UI screen, a character with
behavior), commit a short plan BEFORE writing nodes/scripts. You place things by
coordinates and can't see the result — a plan makes the screenshot loop converge
instead of flailing.

## The plan (write it to `_tmp/<slug>_plan.md`)
1. **GOAL** — what the player sees/does in this scene, in one sentence.
2. **NODE TREE** — the intended hierarchy (root type + key children + their
   classes). e.g. `CharacterBody2D Player / Sprite2D / CollisionShape2D / Camera2D`.
   Choosing the right root class is half the battle (CharacterBody2D vs Area2D vs
   RigidBody2D have completely different behavior).
3. **LAYOUT** — approximate positions/sizes in the viewport (use the project's
   `viewport_width/height`). Anchor UI; place world nodes by logic, not vibes.
4. **BEHAVIOR** — per script: inputs consumed, signals emitted/connected, the
   `_process` vs `_physics_process` split.
5. **FAILURE MODES** — what usually breaks this kind of scene (e.g. platformer:
   forgot `move_and_slide()`, no gravity, collision layer mismatch, camera not
   following). Note the guard for each.

## Then build → SOP-01
Build to the plan, then run the screenshot loop. Compare the captured frame to
the LAYOUT you wrote. Divergence is your fix list.

## Verify, then record
Once a capture matches the plan, record durable genre learnings (the node setup,
the failure mode + guard) under `references/objects/<genre>.md` — verified only.
