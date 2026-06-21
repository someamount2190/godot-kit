# SOP-04 — Verify Godot / first run / install elsewhere

## This machine (verified 2026-06-21)
- Godot 4.4 .NET console exe pinned in `godotkit/env.py`.
- Python 3.10 host at `%LOCALAPPDATA%\Programs\Python\Python310\python.exe`.
- .NET 8 SDK (per-user) at `%LOCALAPPDATA%\Microsoft\dotnet` (for C#).
- A verified smoke-test fixture lives at `examples/proof_project` (GDScript) and
  `examples/cs_project` (C#).

## Gate 1 — locate + version
```python
from godotkit import env
print(env.find_godot())     # absolute path to the console exe
print(env.version())        # e.g. 4.4.stable.mono.official...
```
If it raises: set `GODOT=<full path to Godot_*_console.exe>` (the CONSOLE build
on Windows, or you get no stdout).

## Gate 2 — smoke test the loop
Run the bundled proof: capture the toolkit's own passive test scene and VIEW it.
```python
from godotkit import run
r = run.capture(PROOF_PROJECT, "res://world.tscn", OUT_PNG)
# then Read OUT_PNG — you should see a green bg + 5-box color gradient + label.
```
A correct PNG proves: exe found, Vulkan window renders, capture + save_png work,
and you can view the result. If the PNG is blank → you're likely on `--headless`
or missing a camera; if empty stdout → you're on the non-console exe.

## Installing on another box
1. Download the matching build: `Godot_v<ver>-stable_mono_<plat>.zip` (use the
   plain build if no C# needed). Extract somewhere stable.
2. Point `GODOT` at the console exe (Windows) / the binary (Linux/macOS).
3. For C#: install the .NET 8 SDK; `dotnet --list-sdks` must show 8.x.
4. Re-run Gate 1 + Gate 2.
