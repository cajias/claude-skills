#!/usr/bin/env bash
# rsi-check-integrity.sh — detect tampering of a task's immutable harness.
# Part of the immutable rsi-loop harness.
#
# Usage: rsi-check-integrity.sh <task-dir>
#
# Exit 0 = the scorer / task spec / instance data match their trusted baseline;
# exit 1 = tampered (or unverifiable). This is the writer-gap defense that
# actually holds: inner agents run as the same uid as the harness (often root),
# so OS read-only bits cannot PREVENT a write — but we can DETECT one and refuse
# to trust a score derived from a tampered scorer.
#
# Trust anchor, in order of preference:
#   1. git — if the task dir is tracked, any diff vs HEAD in score.py/task.md/
#      public/private is tampering. Git objects are outside the working tree an
#      inner agent edits, so HEAD is a clean reference.
#   2. .integrity.sha256 — a checksum manifest written when the dir was
#      provisioned (by rsi-sandbox.sh, or rsi-init for a run battery).
# If neither exists the harness cannot be verified — treated as a hard failure,
# because scoring against an unverifiable scorer is exactly what this guards.
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: rsi-check-integrity.sh <task-dir>" >&2
  exit 2
fi
TASK_DIR="$1"
if [[ ! -d "$TASK_DIR" ]]; then
  echo "rsi-integrity: no such task dir: $TASK_DIR" >&2
  exit 2
fi

# Immutable pathspecs (some may be absent, e.g. a sandbox has no private/).
SPECS=(score.py task.md public private)

if git -C "$TASK_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  changed="$(git -C "$TASK_DIR" status --porcelain -- "${SPECS[@]}" 2>/dev/null || true)"
  if [[ -n "$changed" ]]; then
    echo "rsi-integrity: FAIL — immutable harness differs from git HEAD:" >&2
    echo "$changed" | sed 's/^/    /' >&2
    exit 1
  fi
  echo "rsi-integrity: OK (git-clean) $TASK_DIR" >&2
  exit 0
fi

if [[ -f "$TASK_DIR/.integrity.sha256" ]]; then
  if ( cd "$TASK_DIR" && sha256sum --quiet -c .integrity.sha256 ) >/dev/null 2>&1; then
    echo "rsi-integrity: OK (manifest) $TASK_DIR" >&2
    exit 0
  fi
  echo "rsi-integrity: FAIL — checksum mismatch vs .integrity.sha256 in $TASK_DIR" >&2
  exit 1
fi

echo "rsi-integrity: FAIL — no git and no .integrity.sha256; harness unverifiable in $TASK_DIR" >&2
exit 1
