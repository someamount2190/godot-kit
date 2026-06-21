# LEARNINGS — persistent correction log

Append-only. One entry per solved NEW failure. **Record only AFTER a run/capture
actually PASSED** — `verified_by` names that log/screenshot. Never write a guess;
an unverified "fix" poisons the catalog. Dedupe by `error_signature` (if it's
already here or in `references/gotchas/`, refine the existing entry). Promote
durable, general lessons into `references/gotchas/`.

Entry format:
```
### <error_signature>
- date: YYYY-MM-DD
- godot_version: X.Y.Z (build)
- error_signature: <short stable key, matches debug.py>
- root_cause: <why it happened>
- fix: <exact change that resolved it>
- verified_by: <log/screenshot that PASSED proving the fix>
```

---

### inferred_variant_parse_error
- date: 2026-06-21
- godot_version: 4.4.stable.mono
- error_signature: inferred_variant_parse_error
- root_cause: `var warns := n.get_configuration_warnings()` and `var scr := n.get_script()` infer their type from a Variant/untyped value. This environment treats the INFERRED_DECLARATION warning as an ERROR ("Warning treated as error"), so the script failed to PARSE and the harness never loaded (headless Godot then hung to the run timeout).
- fix: Type these explicitly — `var scr: Variant = n.get_script()`, `var warns: PackedStringArray = n.get_configuration_warnings()`, `var res: Variant = load(p) if p != "" else null`. Never use `:=` when the RHS is Variant/untyped. (Plain `var r := load(p)` is fine because `load()` is typed `Resource`.)
- verified_by: logs/20260621_221318.log → scene_report later returned 8 nodes cleanly (report_test.py: ok=True nodes=8).

### editor_only_method_at_runtime
- date: 2026-06-21
- godot_version: 4.4.stable.mono
- error_signature: editor_only_method_at_runtime
- root_cause: The scene-report harness called `n.get_configuration_warnings()` while the scene ran as a normal game (not in the editor). That method is EDITOR-ONLY; at runtime it does not exist → "SCRIPT ERROR: Invalid call. Nonexistent function 'get_configuration_warnings'". The error aborted the node-walk *before* `report.nodes.append(entry)`, so the report came back with 0 nodes.
- fix: Do not call editor-only methods (`get_configuration_warnings`, `_validate_property`, anything behind `Engine.is_editor_hint()`) in a running scene. Removed the call; config-warning scans, if ever needed, require an editor import pass.
- verified_by: logs/20260621_221318.log (the failure) → after removal, report_test.py printed the full 8-node tree with classes/scripts/transforms.

### no_stdout_windows
- date: 2026-06-21
- godot_version: 4.4.stable.mono
- error_signature: no_stdout_windows
- root_cause: On Windows the plain `Godot_*.exe` is a GUI subsystem binary that detaches from the parent console, so `subprocess` captures EMPTY stdout — every GDScript error/print is invisible.
- fix: Always invoke the `*_console.exe` build (it keeps the console attached). `env.py` pins it as the default and the `GODOT` override should also point at a console build.
- verified_by: All capture/report runs (e.g. logs/20260621_220724.log) show full Godot banner + SHOT/print output via the console exe.

### class_name_not_registered
- date: 2026-06-21
- godot_version: 4.4.stable.mono
- error_signature: class_name_not_registered
- root_cause: Building the Classic Tank game, the first headless boot failed to PARSE Main.gd: "Could not find type 'Player' in the current scope" / "Identifier 'Wall' not declared in the current scope" for the project's OWN `class_name` globals (Player, Wall, Enemy, Tank, Bullet). On a fresh project with no `.godot` cache, the global script class registry is empty, so cross-file `class_name` references don't resolve — even though the code is correct.
- fix: Run an import scan to build `.godot/global_script_class_cache.cfg`: `godot --headless --path <proj> --import`. Added `run.import_project()` and made `preflight.check()` auto-run it before the headless boot, so this self-heals. UPDATE (verified building the ClassicRPG): the cache also goes STALE when you ADD a new `class_name` to an already-imported project (e.g. adding `Sprites.gd` → "Could not find type Sprites" even though .godot exists). So `import_project()` now re-imports when the cache is MISSING **or any .gd/.cs is newer than the cache (mtime)**, not just when it's absent. Skipping-on-cache-exists was insufficient.
- verified_by: _tmp/tank_static.png (fresh-project case); and ClassicRPG preflight went False→True after adding Sprites.gd once the mtime re-import landed (rpg_map_m_00*.png show the new class rendering).

### csharp_build_sdk_resolution
- date: 2026-06-21
- godot_version: 4.4.stable.mono / .NET SDK 8.0.422
- error_signature: csharp_build_sdk_resolution
- root_cause: `dotnet build` of a Godot C# project failed with "The SDK 'Godot.NET.Sdk/4.4.0' could not be found". Godot.NET.Sdk is a NuGet-distributed MSBuild SDK; with no NuGet source configured it can't be restored. Separately, `godot --headless --build-solutions` failed with "Could not load file or assembly 'Microsoft.Build.Framework, Version=15.1.0.0'" (GodotTools' bundled MSBuild path is broken on this box). Also: winget install of the SDK HUNG (silent UAC elevation prompt, non-interactive); and `dotnet --list-sdks` exits 0 with EMPTY output when no SDK is present (false "ready").
- fix: (1) Install the SDK per-user without admin via dot.net/v1/dotnet-install.ps1 to %LOCALAPPDATA%\Microsoft\dotnet. (2) Add a nuget.config next to the .csproj pointing at `<GODOT_DIR>\GodotSharp\Tools\nupkgs` + nuget.org. (3) Build with `dotnet build <csproj>` (NOT godot --build-solutions), with DOTNET_ROOT/PATH set to the per-user dotnet. (4) Verify SDK by parsing `--list-sdks` OUTPUT, not its exit code.
- verified_by: _tmp/cs_scene.png — a C# Main:Node2D._Ready() built a purple bg + cyan box + label, captured through the GDScript harness and viewed. dotnet build RC=0, csproof.dll produced.

### headless_renders_nothing
- date: 2026-06-21
- godot_version: 4.4.stable.mono
- error_signature: headless_no_render
- root_cause: `--headless` uses the dummy display/rendering server. The window viewport's texture is not drawn, so a screenshot taken under `--headless` is blank (and `get_image()` may be null). Headless is for logic + error scanning, not pixels.
- fix: `run.capture()` runs WITHOUT `--headless` (real Vulkan window) and is the only path that produces a usable PNG. `run.check()` / `run.scene_report()` use `--headless` deliberately (no pixels needed). Proven: a windowed capture produced a correct 640x360 PNG I could view.
- verified_by: _tmp/world_single.png (windowed capture, correct content) vs. headless boot in logs producing no image.
