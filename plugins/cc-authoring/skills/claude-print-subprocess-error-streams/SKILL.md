---
name: claude-print-subprocess-error-streams
description: |
  Fix for opaque `RuntimeError: Claude session failed: ` (or any wrapper-error
  with empty content) when wrapping `claude --print --output-format json` in
  Python subprocess. Use when: (1) you wrap `claude --print` (or any
  `claude` non-interactive CLI invocation) via `subprocess.run` /
  `subprocess.communicate` to drive batch automation; (2) the subprocess
  exits with non-zero returncode but `result.stderr` is empty so your error
  message is empty; (3) you suspect an error happened inside the Claude
  session but can't see it. Root cause: `claude --print --output-format
  json` writes its session result — including errors as
  `{"is_error": true, ...}` JSON — to STDOUT, not STDERR. Wrappers that
  surface only `result.stderr` lose the actual error. The fix is to
  surface BOTH streams in the wrapper's RuntimeError, with `result.stdout`
  taking the larger budget since errors are JSON there.
author: Claude Code
version: 1.0.0
date: 2026-05-07
---

# claude-print-subprocess-error-streams

## Problem

A Python subprocess wrapper invokes `claude --print --output-format json`
to drive batch automation. The Claude session fails internally; the
subprocess exits non-zero. Your wrapper raises:

```
RuntimeError: Claude session failed:
```

Empty error content. You don't know what happened.

## Context / Trigger Conditions

- Code path looks like:

  ```python
  result = subprocess.run(
      ["claude", "--print", "--output-format", "json", prompt],
      capture_output=True, text=True, timeout=...,
  )
  if result.returncode != 0:
      raise RuntimeError(f"Claude session failed: {result.stderr[:400]}")
  ```

- You see the empty-tail error message above.
- Direct invocation of the same command at the shell succeeds (or fails
  with a visible error).
- The actual error is inside `result.stdout`, which your wrapper threw
  away.

## Solution

`claude --print --output-format json` writes its session output —
including any error envelope as `{"is_error": true, "result": "..."}`
JSON — to **STDOUT**, not stderr. Stderr is reserved for
binary-launch errors (missing executable, permission denied, etc.).
Most actual session errors land on stdout.

**Always surface both streams in the wrapper's error message**, with
stdout getting the larger budget since the JSON envelope is verbose:

```python
if result.returncode != 0:
    raise RuntimeError(
        f"Claude session failed (rc={result.returncode}). "
        f"stderr={result.stderr[:300]!r} stdout={result.stdout[:600]!r}"
    )
```

If you parse JSON, also check the `is_error` flag explicitly even on
returncode==0:

```python
import json

if result.returncode != 0 or not result.stdout.strip():
    raise RuntimeError(
        f"Claude session failed (rc={result.returncode}). "
        f"stderr={result.stderr[:300]!r} stdout={result.stdout[:600]!r}"
    )
try:
    payload = json.loads(result.stdout)
except json.JSONDecodeError as e:
    raise RuntimeError(f"non-JSON stdout: {e}; raw={result.stdout[:600]!r}")
if payload.get("is_error"):
    raise RuntimeError(f"Claude session reported error: {payload!r}")
```

## Verification

After patching the wrapper, trigger a failure deliberately (e.g., pass
a prompt that asks Claude to immediately exit with an error, or break
the auth token, or use a non-existent model). The new error message
should now include the JSON envelope from stdout, e.g.:

```
RuntimeError: Claude session failed (rc=1).
  stderr=''
  stdout='{"type":"result","subtype":"error_during_execution",
          "is_error":true,"duration_ms":...,
          "result":"<actual error description>"}'
```

## Notes

- `--output-format json` (and `--output-format stream-json`) both put
  session content on stdout. Stderr remains for hard-launch errors only.
- For `--output-format text` (default), the same principle holds — the
  text result and any internal errors go to stdout.
- Ephemeral failures (network blips, transient API errors) can produce
  exit 1 with empty stdout AND empty stderr. The patched message will
  surface that as `stderr='' stdout=''` — at least you can distinguish
  "Claude responded with an error" from "Claude couldn't even start".
- Use `result.stdout[:600]!r` (with `!r`) so you see the literal repr
  including `\n` escapes — important when the JSON spans multiple lines
  in the terminal.
- If your wrapper passes the prompt as a positional arg AND uses
  `capture_output=True, text=True`, you've already bought into the
  stdout-capture pattern — surfacing it on error is consistent.
- This is specifically a subprocess-wrapper hazard. Interactive
  `claude` (no `--print`) prints errors to the user-visible TUI and
  doesn't have this issue.

## Example: real-world bug encountered

A `nautilus_competition` team's `entry.py:train(ctx)` wrapped
`claude --print --output-format json` via the harness's
`agent_runner.run_claude` helper. A transient session failure produced:

```
RuntimeError: Claude session failed:
```

Logged to `runs/<id>/round_NN/eval/<team>/FAILED.json` with empty
`error` field. Direct re-invocation of the same prompt and cwd at the
shell succeeded. The wrapper had been hiding the failure detail by
surfacing only `result.stderr` (empty) and ignoring `result.stdout`.

Fix: changed every `entry.py` (7 teams in that workspace) to the
two-stream pattern shown above. The next failure surfaced the actual
JSON error envelope, which made root-cause diagnosis a one-step
operation.

## References

- Claude Code documentation on print mode and output formats:
  <https://docs.claude.com/en/docs/claude-code/cli-reference> (consult the
  `--print` and `--output-format` options).
- `subprocess.CompletedProcess` (Python stdlib) — both `stdout` and
  `stderr` are populated separately when `capture_output=True`.
