"""preflight.py — cheap gate BEFORE a windowed capture, so we never burn a
screenshot run on a project that won't even boot.

check() runs two stages, cheapest first:
  STAGE 1 (microseconds, pure): inspect_core static validation of project.godot
          + the target scene — broken ext_resource paths, missing main_scene.
  STAGE 2 (~seconds, headless): boot the project with --headless --quit-after and
          scan stdout for 'SCRIPT ERROR' / 'Failed loading' / parse errors.

Returns {ok, errors, warnings, stage}. Treat `errors` as blocking — do NOT
capture() until check() passes. Mirrors blender-kit's preflight-before-render.
"""

import re

from . import inspect_core as ic
from . import run as gk_run

_RUNTIME_ERR = re.compile(
    r"SCRIPT ERROR|Parse Error|Failed loading|Can't open file|"
    r"Nonexistent function|null instance", re.I)


def check(project, scene=None, headless_boot=True, godot=None):
    errors, warnings = [], []

    # STAGE 1 — pure static checks
    proj = ic.validate_project(project)
    errors += ["project.godot: " + e for e in proj.get("errors", [])]
    warnings += ["project.godot: " + w for w in proj.get("warnings", [])]
    if scene:
        # scene is a res:// path; resolve to disk for the static checker
        disk = ic.res_to_disk(scene, project) if scene.startswith("res://") else scene
        sc = ic.validate_scene(disk, project)
        errors += ["%s: %s" % (scene, e) for e in sc.get("errors", [])]
        warnings += ["%s: %s" % (scene, w) for w in sc.get("warnings", [])]
    if errors:
        return {"ok": False, "errors": errors, "warnings": warnings, "stage": 1}

    # STAGE 2 — headless boot, scan for runtime/parse errors
    if headless_boot:
        # Fresh project (no .godot) can't resolve `class_name` globals until an
        # import scan runs. Auto-heal once so preflight doesn't false-positive
        # on "Could not find type X" for the project's own classes.
        gk_run.import_project(project, godot=godot)
        res = gk_run.check(project, godot=godot)
        bad = [ln for ln in res["out"].splitlines() if _RUNTIME_ERR.search(ln)]
        if bad:
            errors += bad[:10]
            return {"ok": False, "errors": errors, "warnings": warnings,
                    "stage": 2, "log": res["log"]}

    return {"ok": True, "errors": errors, "warnings": warnings, "stage": 2}


if __name__ == "__main__":
    import json
    import sys
    proj = sys.argv[1]
    scene = sys.argv[2] if len(sys.argv) > 2 else None
    print(json.dumps(check(proj, scene), indent=2))
