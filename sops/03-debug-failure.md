# SOP-03 — A run / parse failed: classify & fix

## Gate 1 — get the log
Every `run.*` call writes a log to `logs/<ts>.log` and returns its path in
`res["log"]`. Read it. The real error is an `at: res://file.gd:<line>` line.

## Gate 2 — consult memory FIRST
Search `LEARNINGS.md` + `references/gotchas/` for the error signature. A prior
VERIFIED fix beats reasoning from scratch.

## Gate 3 — classify
```python
from godotkit import debug
print(debug.report(LOG_PATH))     # -> signature(s) + probable cause + mapped fix
```
Known signatures: `inferred_variant_parse_error`, `editor_only_method_at_runtime`,
`no_stdout_windows`, `gdscript_parse_error`, `nil_instance_access`,
`godot3_to_4_api`, `resource_load_failed`, `headless_no_render`.

## Gate 4 — apply the mapped fix, bounded retry (max 2)
Apply ONE fix, re-run, re-read. If two attempts don't clear it, build a minimal
repro (smallest scene/script that still fails) and STOP — surface the log +
hypothesis. **Never fake success or claim it works unverified.**

## Gate 5 — record (only after it PASSES)
Append to LEARNINGS.md keyed by `error_signature`, with `verified_by` = the
log/screenshot that proved the fix. Promote durable lessons into
`references/gotchas/`. Add a new signature to `debug.py` if it'll recur.
