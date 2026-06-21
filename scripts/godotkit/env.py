"""env.py — locate the Godot executable + report version. PURE PYTHON (no engine).

This machine (pinned): Godot 4.4 .NET (Mono) build at
  %LOCALAPPDATA%\\Programs\\Godot\\Godot_v4.4-stable_mono_win64\\

Always prefer the *_console.exe on Windows: the plain .exe detaches from the
console so you get NO stdout (you'd be blind to GDScript errors). The console
build prints to the pipe.

Override with the GODOT env var (full path to the console exe).
"""

import os
import shutil
import subprocess

# Pinned known-good location on THIS box (verified 2026-06-21).
_PINNED = [
    os.path.expandvars(
        r"%LOCALAPPDATA%\Programs\Godot\Godot_v4.4-stable_mono_win64"
        r"\Godot_v4.4-stable_mono_win64_console.exe"
    ),
]

# Fallbacks if the pin moves / on another box.
_NAMES = [
    "Godot_v4.4-stable_mono_win64_console.exe",
    "Godot_v4.4-stable_win64_console.exe",
    "godot_console.exe",
    "godot",
    "Godot",
]


def find_godot():
    """Return an absolute path to a usable Godot CLI binary, or raise."""
    env = os.environ.get("GODOT")
    if env and os.path.exists(env):
        return env
    for p in _PINNED:
        if os.path.exists(p):
            return p
    for n in _NAMES:
        hit = shutil.which(n)
        if hit:
            return hit
    raise RuntimeError(
        "Godot not found. Set GODOT=/full/path/to/Godot_*_console.exe "
        "(use the *_console.exe on Windows or you get no stdout)."
    )


def version(godot=None):
    """Return Godot's --version string (e.g. '4.4.stable.mono.official...')."""
    godot = godot or find_godot()
    out = subprocess.run(
        [godot, "--version"], capture_output=True, text=True, timeout=30
    )
    return (out.stdout or out.stderr).strip().splitlines()[-1].strip()


if __name__ == "__main__":
    g = find_godot()
    print("GODOT =", g)
    print("VERSION =", version(g))
