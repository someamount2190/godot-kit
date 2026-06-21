"""debug.py — classify a Godot run log -> probable cause + mapped fix.
PURE PYTHON (no engine); runs on any captured log.

Protocol (sops/03-debug-failure.md):
  1. Read the captured log (run.py writes one per run to logs/).
  2. consult LEARNINGS.md + references/gotchas/ FIRST for the signature.
  3. classify() against the built-in signatures below.
  4. Apply the mapped fix, retry (bounded, max 2). On continued failure, build a
     minimal repro + STOP. Never fake success.

Every signature here was either hit-and-verified during this skill's own build,
or is a well-known Godot 3->4 / runtime breaker.
"""

import re
import sys

# (name, compiled regex, probable_cause, fix)
_SIGNATURES = [
    (
        "inferred_variant_parse_error",
        re.compile(r"Cannot infer the type of .* variable|inferred from a Variant"
                   r"|Warning treated as error", re.I),
        "A `var x := <expr>` where <expr> is Variant/untyped (e.g. load() in a "
        "ternary, get_script(), a Dictionary lookup). This project treats the "
        "INFERRED/UNTYPED warning as an ERROR, so the script fails to PARSE.",
        "Type the variable EXPLICITLY: `var x: Variant = ...`, "
        "`var s: PackedStringArray = ...`. Never use := when the RHS is Variant.",
    ),
    (
        "editor_only_method_at_runtime",
        re.compile(r"Nonexistent function '(get_configuration_warnings|_get"
                   r"_configuration_warnings|_validate_property)'", re.I),
        "Called an EDITOR-ONLY method at game runtime. get_configuration_"
        "warnings() and friends exist only inside the editor.",
        "Do not call editor-only methods in a running scene. For config-warning "
        "scans run an editor import pass instead (preflight.check_scripts).",
    ),
    (
        "no_stdout_windows",
        re.compile(r"^\s*$"),  # only used via the heuristic in classify()
        "On Windows the plain Godot_*.exe detaches from the console -> NO stdout, "
        "so GDScript errors are invisible.",
        "Always launch the *_console.exe on Windows (env.py already pins it).",
    ),
    (
        "class_name_not_registered",
        re.compile(r"Could not find type \"?\w+\"? in the current scope"
                   r"|Identifier \"?\w+\"? not declared in the current scope", re.I),
        "A `class_name` global (the project's own classes) isn't registered yet. "
        "On a FRESH project (no .godot cache) the global class list is empty until "
        "an import scan runs, so `Player`/`Wall`/etc. don't resolve.",
        "Run an import pass once: `godot --headless --path <proj> --import` (or "
        "godotkit.run.import_project / just call preflight.check, which auto-heals). "
        "Then class_name types resolve. NOT a typo in your code.",
    ),
    (
        "gdscript_parse_error",
        re.compile(r"SCRIPT ERROR: Parse Error|Parse Error:", re.I),
        "GDScript failed to compile (syntax, unknown identifier, bad type).",
        "Read the exact 'at: ...:<line>'; fix the line. Common 4.x: typed arrays "
        "`Array[Node]`, `@onready`, `@export`, `await` (not `yield`), `signal x()`.",
    ),
    (
        "nil_instance_access",
        re.compile(r"Attempt to call .* on a null instance|Invalid get index .* on "
                   r"base: 'Nil'|null instance", re.I),
        "Accessed a node/var before it existed — usually $NodePath in _ready "
        "before the child is in tree, or a node renamed/moved in the .tscn.",
        "Guard with `@onready var x = $Path`, verify the path via scene_report(); "
        "use `is_instance_valid(x)` / `if x:` before use.",
    ),
    (
        "godot3_to_4_api",
        re.compile(r"Nonexistent function '(move_and_slide_with_snap|instance|"
                   r"empty|get_node_or_null2)'|KinematicBody|YieldInstruction|"
                   r"'instance'.*PackedScene", re.I),
        "Godot 3 API used on Godot 4. Many renames: instance()->instantiate(), "
        "KinematicBody->CharacterBody2D/3D, yield->await, .empty()->.is_empty(), "
        "Spatial->Node3D, OS.get_ticks_msec->Time.get_ticks_msec.",
        "Port the call to its Godot 4 name (references/gotchas/godot3-to-4.md).",
    ),
    (
        "resource_load_failed",
        re.compile(r"Failed loading resource|Cannot open file|ext_resource.*not "
                   r"found|Can't open file", re.I),
        "A res:// path in a .tscn/.tres points at a file that does not exist "
        "(moved/renamed/typo).",
        "Run inspect_core.validate_scene() — it lists broken ext_resource paths "
        "statically. Fix the path or restore the file.",
    ),
    (
        "headless_no_render",
        re.compile(r"headless.*(viewport|texture)|get_image\(\).*null", re.I),
        "Tried to screenshot while running --headless. The headless display "
        "server does not render, so the viewport texture is empty/null.",
        "Capture with a WINDOW (no --headless). run.capture() already does this; "
        "only run.check()/scene_report() use --headless (logic only).",
    ),
]


def classify(log_text):
    """Return a list of {signature, cause, fix} matches, most specific first."""
    hits = []
    for name, rx, cause, fix in _SIGNATURES:
        if name == "no_stdout_windows":
            continue  # heuristic-only, see below
        if rx.search(log_text):
            hits.append({"signature": name, "cause": cause, "fix": fix})
    # heuristic: a run that produced essentially nothing on stdout on Windows
    if not hits and len(log_text.strip().splitlines()) <= 3:
        n, _, c, f = _SIGNATURES[2][0], None, _SIGNATURES[2][2], _SIGNATURES[2][3]
        hits.append({"signature": n, "cause": c, "fix": f})
    return hits


def report(log_path):
    with open(log_path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    hits = classify(text)
    if not hits:
        return "No known signature matched. Read the log + consult LEARNINGS.md."
    out = ["%d signature(s) matched %s:" % (len(hits), log_path)]
    for h in hits:
        out.append("\n[%s]\n  cause: %s\n  fix:   %s"
                   % (h["signature"], h["cause"], h["fix"]))
    return "\n".join(out)


if __name__ == "__main__":
    print(report(sys.argv[1]))
