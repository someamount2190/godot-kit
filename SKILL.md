---
name: godot-kit
description: >-
  Reliable Godot 4 game work via the CLI. Use whenever a task involves Godot,
  GDScript or C#, .tscn/.tres scenes, the node tree, running a game/scene, or
  verifying how something looks or behaves on screen. Wraps the model's weak
  spots (can't see the running game, claims code "works" without running it,
  confuses Godot 3 vs 4 APIs) in deterministic code + a preflight->run->
  screenshot->inspect loop + a debugging and learning system.
---

# godot-kit

You cannot see a running Godot game. You tend to claim GDScript "works" without
ever running it, you confuse Godot 3 and Godot 4 APIs (instance->instantiate,
yield->await, KinematicBody->CharacterBody), and you skim past broken `res://`
refs in a big `.tscn`. This skill removes those failure modes with code and
procedure. **Follow the loop. Do not trust your mental model of the scene — run
it, screenshot it, and look.**

## Environment (this machine — verified 2026-06-21)
- Godot **4.4 .NET (Mono)** at
  `%LOCALAPPDATA%\Programs\Godot\Godot_v4.4-stable_mono_win64\Godot_v4.4-stable_mono_win64_console.exe`.
- **Always use the `*_console.exe` on Windows** — the plain `.exe` detaches from
  the console and you get NO stdout (you'd be blind to GDScript errors). `env.py`
  pins it; override with the `GODOT` env var.
- Renders via **Vulkan / Forward+** on the RTX 2050. `--headless` disables
  rendering → use it for logic/error checks ONLY, never for screenshots.
- C# needs the **.NET 8 SDK** — installed per-user at
  `%LOCALAPPDATA%\Microsoft\dotnet` (8.0.422; `Program Files\dotnet` has runtime
  only). Build with `dotnet build` (NOT `godot --build-solutions`) + a
  `nuget.config` pointing at Godot's bundled nupkgs. GDScript needs nothing extra.
  Full verified steps: `sops/05-csharp-setup.md`.
- This box treats GDScript **inferred/untyped warnings as ERRORS** — `var x := `
  on a Variant RHS fails to PARSE. Type explicitly. (See gotchas.)
- Host toolkit is Python 3.10 at `%LOCALAPPDATA%\Programs\Python\Python310`.
- Run a host module from `scripts/`:  `python -m godotkit.<mod> ...` (relative
  imports — don't run the file by path).

## THE MANDATORY LOOP (never report "done" until all of it has run)
```
PREFLIGHT  — godotkit.preflight.check(project, scene)
   STAGE 1 pure: inspect_core validates project.godot + the .tscn (broken
           res:// refs, missing main_scene) in microseconds.
   STAGE 2 boot: --headless --quit-after; scan stdout for SCRIPT ERROR / parse
           errors. MUST pass (no errors) before you spend a window on it.
RUN + CAPTURE — godotkit.run.capture(project, target, out [,shots,interval])
   runs the REAL scene in a window, writes PNG(s). Non-invasive (does not edit
   the project's main_scene).
VIEW — Read each PNG with your image tool AND read run.scene_report(project,
   target) (the node tree: types, scripts, transforms you are blind to).
DECIDE — compare to intent: blank screen? wrong node? off-position? missing
   sprite? overlapping UI? Fix the .tscn/.gd. DELETE the frame.
REPEAT until it visually holds, THEN report, citing the screenshot you looked at.
```
You may not call a scene "working" or "looking right" from code alone. "Looks
good" requires a PNG you actually viewed. If you cannot view the render, STOP
and say so.

## Hard rules
1. **Run it. Screenshot it. Look.** Never claim a scene works/looks right without
   a `capture()` PNG you VIEWED. This is the whole point of the skill.
2. **Preflight before every capture.** `preflight.check()` is microseconds-to-
   seconds and catches the dumb breakers (broken refs, parse errors) before a
   10-second window boot.
3. **Type GDScript variables explicitly when the RHS is Variant.** `var x:
   Variant = load(...)`, `var a: Array[Node] = ...`. Never `:=` off a Variant —
   it fails to parse here. (gotchas/gdscript-4.4.md)
4. **No editor-only calls at runtime** (`get_configuration_warnings`,
   `_validate_property`, anything behind `Engine.is_editor_hint()`). They throw.
5. **Windows: the `*_console.exe`, or you get no stdout.** `--headless` for logic
   only; screenshots need a window.
6. **Porting Godot 3 code? Assume the API was renamed.** Check
   `references/gotchas/godot3-to-4.md` BEFORE running — don't discover it by
   crash.
7. **On any failure: consult `LEARNINGS.md` + `references/gotchas/` FIRST,** then
   `godotkit.debug.report(logfile)`. Bounded retries (max 2) with the mapped fix,
   then minimal repro + STOP. Never fake success.
8. **Record a new fix in `LEARNINGS.md` only after a run/capture PASSES**
   (`verified_by` = which log/screenshot). An unverified "fix" poisons the catalog.

## Routing — pick the SOP, follow its numbered gates
| Task | SOP |
|------|-----|
| **The core: show→view→decide→delete on a running scene** | `sops/01-screenshot-loop.md` |
| Make a new project / scene from scratch | `sops/00-new-project.md` |
| Modify / debug an existing scene or script | `sops/02-modify-scene.md` |
| A run/parse failed — classify & fix | `sops/03-debug-failure.md` |
| Verify Godot / first run / install elsewhere | `sops/04-env-verify.md` |
| Set up or build C# (.NET) game scripts | `sops/05-csharp-setup.md` |
| Design a scene/level before coding it | `sops/06-design-first.md` |

## The toolkit
**Host-side Python (`scripts/godotkit/`, run as `python -m godotkit.<mod>`):**
- `env`         locate the Godot CLI (pins the console exe) + `version()`.
- `run`         `run_scene` / `check` (headless boot) / `capture` (screenshot,
                single + multi-shot, non-invasive) / `scene_report` (headless
                node-tree dump). **All four verified on Godot 4.4 / RTX 2050.**
- `inspect_core` PURE python `.tscn` / `project.godot` validator (broken
                ext_resource paths, missing main_scene, duplicate node names).
- `preflight`   `check(project, scene)` — the pre-capture gate (static + boot).
- `debug`       `report(log)` — classify a run log → cause + mapped fix.

**Engine-side GDScript (`scripts/gdkit/`, copied into the target at runtime):**
- `_godotkit_harness.{gd,tscn}` — instances a target scene, settles, captures
  the viewport to PNG(s), quits. Drives the screenshot loop.
- `_godotkit_report.{gd,tscn}`  — instances a target, walks the tree, emits JSON.

## References & learning loop
- `references/gotchas/godot3-to-4.md` — the Godot 3→4 API rename catalog. Check
  BEFORE porting old code.
- `references/gotchas/gdscript-4.4.md` — verified GDScript-on-4.4 traps (typed
  vars as parse errors, editor-only methods, headless renders nothing, console
  exe for stdout).
- `LEARNINGS.md` — append-only, keyed by `error_signature`. Record only AFTER a
  run/capture PASSES. Promote durable lessons into `references/gotchas/`.
- `references/objects/` — per-genre scene/build learnings (seed as you go).
