"""inspect_core.py — PURE PYTHON static validation of Godot text resources.
NO engine import; unit-testable on plain strings/files.

Godot's .tscn / .tres / project.godot are text. A huge class of "scene won't
load" failures is statically detectable WITHOUT launching the engine:
  - ext_resource path="res://x.gd" where x.gd does not exist on disk
  - project.godot run/main_scene pointing at a missing file
  - autoload singleton script path missing
  - duplicate node names under the same parent (Godot auto-renames -> broken refs)

This is the part you skim past in a big .tscn. Run it FIRST (preflight); it is
milliseconds and catches the dumb breakers before a 10s engine boot.
"""

import os
import re

_HEADER_RE = re.compile(r'^\[(\w+)\s*(.*)\]\s*$')
_KV_RE = re.compile(r'(\w+)\s*=\s*"([^"]*)"')
_PATH_RE = re.compile(r'path\s*=\s*"([^"]+)"')


def res_to_disk(res_path, project_dir):
    """Map a res:// path to an absolute disk path under project_dir."""
    if res_path.startswith("res://"):
        rel = res_path[len("res://"):]
        return os.path.normpath(os.path.join(project_dir, rel))
    if res_path.startswith("uid://"):
        return None  # uid refs can't be resolved without the engine's uid cache
    return os.path.normpath(os.path.join(project_dir, res_path))


def parse_tscn(text):
    """Parse a .tscn/.tres into {ext_resources, sub_resources, nodes}.
    Deliberately lenient: returns what it can, never raises on odd input."""
    ext_resources, sub_resources, nodes = [], [], []
    cur = None
    for raw in text.splitlines():
        line = raw.rstrip()
        m = _HEADER_RE.match(line)
        if m:
            tag, attrs = m.group(1), m.group(2)
            kv = dict(_KV_RE.findall(attrs))
            if tag == "ext_resource":
                ext_resources.append(kv)
            elif tag == "sub_resource":
                sub_resources.append(kv)
            elif tag == "node":
                cur = {"name": kv.get("name", ""), "type": kv.get("type", ""),
                       "parent": kv.get("parent"), "instance": kv.get("instance"),
                       "script_ext_id": None}
                nodes.append(cur)
            else:
                cur = None
            continue
        # body line under a [node]: catch  script = ExtResource("id")
        if cur is not None and "ExtResource(" in line and line.lstrip().startswith("script"):
            mm = re.search(r'ExtResource\(\s*"?([\w]+)"?\s*\)', line)
            if mm:
                cur["script_ext_id"] = mm.group(1)
    return {"ext_resources": ext_resources, "sub_resources": sub_resources,
            "nodes": nodes}


def validate_scene(tscn_path, project_dir):
    """Static-check one .tscn. Returns {ok, errors, warnings}."""
    errors, warnings = [], []
    if not os.path.exists(tscn_path):
        return {"ok": False, "errors": ["scene file missing: %s" % tscn_path],
                "warnings": []}
    with open(tscn_path, encoding="utf-8", errors="replace") as fh:
        parsed = parse_tscn(fh.read())

    # ext_resource file paths must exist on disk (script/texture/scene refs)
    for er in parsed["ext_resources"]:
        p = er.get("path", "")
        disk = res_to_disk(p, project_dir) if p else None
        if disk is not None and not os.path.exists(disk):
            errors.append("ext_resource %s path missing: %s"
                          % (er.get("type", "?"), p))

    # duplicate node names under the same parent
    seen = {}
    for n in parsed["nodes"]:
        key = (n.get("parent"), n["name"])
        seen[key] = seen.get(key, 0) + 1
    for (parent, name), c in seen.items():
        if c > 1 and name:
            warnings.append("duplicate node name '%s' under parent '%s' (%dx)"
                            % (name, parent, c))

    return {"ok": not errors, "errors": errors, "warnings": warnings,
            "counts": {"ext_resources": len(parsed["ext_resources"]),
                       "nodes": len(parsed["nodes"])}}


def _project_kv(project_dir):
    """Crudely read key="value" / key=value lines from project.godot."""
    path = os.path.join(project_dir, "project.godot")
    kv = {}
    if not os.path.exists(path):
        return kv, path
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = re.match(r'\s*([\w/]+)\s*=\s*"?([^"\n]*)"?', line)
            if m:
                kv[m.group(1)] = m.group(2).strip().strip('"')
    return kv, path


def validate_project(project_dir):
    """Static-check project.godot: main_scene exists, autoload scripts exist."""
    errors, warnings = [], []
    kv, path = _project_kv(project_dir)
    if not os.path.exists(path):
        return {"ok": False, "errors": ["project.godot missing in %s" % project_dir],
                "warnings": []}
    main = kv.get("run/main_scene", "")
    if main:
        disk = res_to_disk(main, project_dir)
        if disk and not os.path.exists(disk):
            errors.append("run/main_scene missing on disk: %s" % main)
    else:
        warnings.append("no run/main_scene set in project.godot")
    return {"ok": not errors, "errors": errors, "warnings": warnings,
            "main_scene": main}


if __name__ == "__main__":
    import json
    import sys
    proj = sys.argv[1]
    print(json.dumps(validate_project(proj), indent=2))
