# godot-kit

A [Claude Code](https://docs.claude.com/en/docs/claude-code) **Agent Skill** for reliable [Godot 4](https://godotengine.org) game work from the command line. It wraps a language model's weak spots when building games — *it can't see the running game, it tends to claim GDScript "works" without ever running it, and it confuses Godot 3 vs 4 APIs* — inside deterministic tooling and a strict **preflight → run → screenshot → inspect** loop.

> Built for, and verified on, **Godot 4.4 (.NET)** with both **GDScript and C#**.

## Why

When an agent writes a Godot scene it places nodes by raw coordinates it cannot see, skims past broken `res://` references in a large `.tscn`, and reaches for renamed Godot-3 APIs. godot-kit removes those failure modes with code and procedure: it captures a real frame of the running game and makes the agent *look at it* before claiming anything works.

## The mandatory loop

```
PREFLIGHT   pure .tscn/project validation, then a headless boot that scans
            stdout for parse/runtime errors — before spending a window
RUN+CAPTURE run the real scene in a window and screenshot the viewport to PNG,
            non-invasively (never edits the project's main scene)
INSPECT     view the PNG + dump the live node tree (types, scripts, transforms)
FIX → REPEAT  until it visually holds — then report, citing the frame
```

A scene is never called "working" or "looking right" from code alone.

## The toolkit

**Host-side Python** (`scripts/godotkit/`):

| Module | What it does |
|--------|--------------|
| `env` | locate the Godot CLI (pins the console build on Windows) + version |
| `run` | `run_scene` / `check` (headless) / `capture` (screenshots, single + multi-shot) / `scene_report` (headless node-tree dump) / `import_project` (mtime-aware) |
| `inspect_core` | pure-Python `.tscn` / `project.godot` validator (broken refs, missing main scene, duplicate nodes) |
| `preflight` | the pre-capture gate (static checks + headless boot) |
| `debug` | classify a run log → probable cause + mapped fix |

**Engine-side GDScript** (`scripts/gdkit/`): tiny harnesses copied into the target project at runtime (and deleted after) to capture the viewport and emit a JSON scene report.

## Requirements

- **Godot 4.4** (the `.NET`/Mono build if you want C#). On Windows, use the `*_console.exe` so stdout is captured.
- **Python 3.10+** for the host toolkit.
- **.NET 8 SDK** only if building C# scripts.

Point the `GODOT` environment variable at your Godot executable, or let `env.py` auto-detect it.

## Usage

As a Claude Code skill it activates automatically for Godot tasks. You can also drive the toolkit directly:

```bash
cd scripts
python -m godotkit.preflight  /path/to/Project  res://main.tscn
python -m godotkit.env         # prints the resolved Godot binary + version
```

`examples/` contains verified smoke-test projects for GDScript and C#.

## Layout

```
SKILL.md              the skill contract + routing
scripts/godotkit/     host-side Python toolkit
scripts/gdkit/        engine-side GDScript capture/report harnesses
sops/                 step-by-step procedures (new project, screenshot loop, debug, C#, …)
references/gotchas/   Godot 3→4 rename catalog + verified GDScript-4.4 traps
LEARNINGS.md          append-only, verified-only fix log
examples/             GDScript + C# smoke fixtures
```

## Support

If godot-kit saved you some time, tips are welcome at this EVM address (ETH, USDC, etc. on Ethereum, Base, Arbitrum, Optimism or Polygon):

`0xD3b3d18C871e7dd36489915A6dd83a32eFD7829f`

## License

[MIT](LICENSE) © 2026 Christian Correa
