"""run.py — host-side driver around the Godot CLI. PURE PYTHON.

Wraps the THREE verified primitives (all proven on Godot 4.4 .NET, RTX 2050):
  1. run_scene()  — run a project/scene, capture stdout+stderr+rc to logs/.
  2. capture()    — non-invasively screenshot ANY target scene (copies the
                    gdkit harness into the project, runs it by positional path,
                    deletes it again). This is the show->view->decide->delete loop.
  3. check()      — fast script/scene parse check (no window), for preflight.

Everything routes stdout to logs/<ts>.log so a failure is never silent. On
Windows we ALWAYS use the *_console.exe (see env.py) or stdout is empty.
"""

import json
import os
import shutil
import subprocess
import time

from . import env as gk_env

_HERE = os.path.dirname(os.path.abspath(__file__))
_SKILL_ROOT = os.path.normpath(os.path.join(_HERE, "..", ".."))
_GDKIT = os.path.join(_SKILL_ROOT, "scripts", "gdkit")
_LOGDIR = os.path.join(_SKILL_ROOT, "logs")

_HARNESS_FILES = ["_godotkit_harness.gd", "_godotkit_harness.tscn"]
_REPORT_FILES = ["_godotkit_report.gd", "_godotkit_report.tscn"]


def _copy_in(project, files):
    copied = []
    for f in files:
        dst = os.path.join(project, f)
        shutil.copyfile(os.path.join(_GDKIT, f), dst)
        copied.append(dst)
    return copied


def _clean(copied):
    for dst in copied:
        try:
            os.remove(dst)
        except OSError:
            pass


def _log_path():
    os.makedirs(_LOGDIR, exist_ok=True)
    return os.path.join(_LOGDIR, time.strftime("%Y%m%d_%H%M%S") + ".log")


def _run(argv, timeout, log=None):
    """Run argv, tee combined output to `log`, return {rc, out, log}."""
    log = log or _log_path()
    with open(log, "w", encoding="utf-8", errors="replace") as fh:
        fh.write("# godot-kit run %s\n# argv: %s\n%s\n"
                 % (time.strftime("%Y-%m-%d %H:%M:%S"), argv, "#" * 60))
        try:
            p = subprocess.run(argv, capture_output=True, text=True,
                               timeout=timeout, encoding="utf-8", errors="replace")
            out = (p.stdout or "") + (p.stderr or "")
            rc = p.returncode
        except subprocess.TimeoutExpired as e:
            out = (e.stdout or "") + (e.stderr or "") + "\n# TIMEOUT after %ss\n" % timeout
            rc = 124
        fh.write(out)
        fh.write("\n%s\n# returncode: %s\n" % ("#" * 60, rc))
    return {"rc": rc, "out": out, "log": log}


def run_scene(project, scene=None, user_args=None, timeout=120,
              headless=False, godot=None):
    """Run a project (optionally a specific scene by res:// path).

    headless=True -> no window/render (logic + error scan only; NO screenshots).
    Returns {rc, out, log}.
    """
    godot = godot or gk_env.find_godot()
    argv = [godot, "--path", project]
    if headless:
        argv.append("--headless")
    if scene:
        argv.append(scene)
    if user_args:
        argv.append("--")
        argv.extend(user_args)
    return _run(argv, timeout)


def check(project, timeout=90, godot=None):
    """Fast parse/import gate: open the project headless and quit after 2 frames.
    Surfaces GDScript parse errors, missing resources, broken ext_resource paths
    WITHOUT opening a window. Returns {rc, out, log}. Scan out for 'SCRIPT ERROR'
    / 'ERROR' / 'Failed loading'."""
    godot = godot or gk_env.find_godot()
    argv = [godot, "--headless", "--path", project, "--quit-after", "2"]
    return _run(argv, timeout)


def import_project(project, timeout=120, godot=None, force=False):
    """Run an import scan so `class_name` globals get registered (writes
    .godot/global_script_class_cache.cfg). A FRESH project (no .godot) fails to
    resolve any `class_name` type ("Could not find type X") until this runs —
    and so does ADDING a new class_name to an already-imported project. So we
    re-import when the cache is missing OR any .gd/.cs is newer than the cache
    (mtime). Cheap + idempotent once everything is up to date. Returns {rc,...}."""
    godot = godot or gk_env.find_godot()
    cache = os.path.join(project, ".godot", "global_script_class_cache.cfg")
    if os.path.exists(cache) and not force:
        cache_mtime = os.path.getmtime(cache)
        newest = 0.0
        for root, _dirs, files in os.walk(project):
            if os.sep + ".godot" in root:
                continue
            for f in files:
                if f.endswith((".gd", ".cs")):
                    try:
                        newest = max(newest, os.path.getmtime(os.path.join(root, f)))
                    except OSError:
                        pass
        if newest <= cache_mtime:
            return {"rc": 0, "out": "cache up to date; import skipped", "log": None}
    return _run([godot, "--headless", "--path", project, "--import"], timeout)


def capture(project, target, out, settle=6, shots=1, interval=30,
            label="shot", timeout=120, godot=None, extra_args=None):
    """Screenshot a target scene NON-INVASIVELY (does not touch main_scene).

    project : abs path to the Godot project dir (contains project.godot)
    target  : res:// path of the scene to capture (e.g. 'res://world.tscn')
    out     : ABS path. Ends in .png + shots==1 -> exact file; else dir/prefix
              and shots are written as <out>_<label>_000.png ...
    Returns {rc, out, log, shots:[abs_png_paths]}.

    Copies the gdkit harness into the project, runs it, then ALWAYS deletes the
    copies (even on failure).
    """
    godot = godot or gk_env.find_godot()
    copied = []
    try:
        for f in _HARNESS_FILES:
            dst = os.path.join(project, f)
            shutil.copyfile(os.path.join(_GDKIT, f), dst)
            copied.append(dst)
        user_args = [
            "--target=" + target,
            "--out=" + out.replace("\\", "/"),
            "--settle=%d" % settle,
            "--shots=%d" % shots,
            "--interval=%d" % interval,
            "--label=" + label,
        ]
        if extra_args:
            user_args.extend(extra_args)   # forwarded to the target after `--`
        argv = [godot, "--path", project, "res://_godotkit_harness.tscn",
                "--", *user_args]
        res = _run(argv, timeout)
    finally:
        for dst in copied:
            try:
                os.remove(dst)
            except OSError:
                pass
    # Compute expected shot paths DETERMINISTICALLY (the stdout path token is
    # unreliable: globalized paths can contain spaces, e.g. 'Christian Correa').
    # We confirm each by existence + count the harness's ok=true lines.
    expected = []
    if shots == 1 and out.lower().endswith(".png"):
        expected = [out]
    else:
        base = out[:-4] if out.lower().endswith(".png") else out
        expected = ["%s_%s_%03d.png" % (base, label, i) for i in range(shots)]
    res["shots"] = [p for p in expected if os.path.exists(p)]
    res["shots_ok"] = res["out"].count("ok=true")
    return res


def scene_report(project, target, timeout=90, godot=None):
    """Dump the instanced node tree of `target` (res:// path) as a dict:
    {target, ok, nodes:[{name,class,depth,script,transform,visible,children}],
     warnings:[...], errors:[...]}. Runs HEADLESS (no window). Reveals node
     types/scripts/transforms + Godot's own configuration warnings — the tree
     you are blind to from the .tscn text alone."""
    godot = godot or gk_env.find_godot()
    copied = _copy_in(project, _REPORT_FILES)
    try:
        # --quit-after is a backstop: if the harness fails to load (e.g. a parse
        # error in the TARGET's scripts), headless Godot won't hang to timeout.
        argv = [godot, "--headless", "--quit-after", "1200", "--path", project,
                "res://_godotkit_report.tscn", "--", "--target=" + target]
        res = _run(argv, timeout)
    finally:
        _clean(copied)
    out = res["out"]
    b, e = "GODOTKIT_REPORT_BEGIN", "GODOTKIT_REPORT_END"
    if b in out and e in out:
        blob = out.split(b, 1)[1].split(e, 1)[0].strip()
        try:
            return json.loads(blob)
        except json.JSONDecodeError as ex:
            return {"ok": False, "errors": ["JSON parse failed: %s" % ex],
                    "raw": blob, "log": res["log"]}
    return {"ok": False, "errors": ["no report emitted (target failed to load?)"],
            "rc": res["rc"], "log": res["log"]}


if __name__ == "__main__":
    import sys
    print(run_scene(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
