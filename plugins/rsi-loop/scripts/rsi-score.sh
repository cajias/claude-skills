#!/usr/bin/env bash
# rsi-score.sh — thin wrapper around a task's immutable score.py.
# Part of the immutable rsi-loop harness.
#
# Usage:
#   rsi-score.sh --public  <task-or-sandbox-dir> <solution.py>
#   RSI_OUTER_LOOP=1 rsi-score.sh --private <task-dir> <solution.py>
#
# The wrapper does not grant private access by itself: score.py refuses
# --private unless RSI_OUTER_LOOP=1 is in the environment, and the plugin's
# PreToolUse hook denies un-prefixed --private commands before they run.
set -euo pipefail

if [[ $# -ne 3 || ( "$1" != "--public" && "$1" != "--private" ) ]]; then
  echo "usage: rsi-score.sh --public|--private <task-dir> <solution.py>" >&2
  exit 2
fi

SPLIT="$1"
TASK_DIR="$2"
SOLUTION="$3"
HERE="$(cd "$(dirname "$0")" && pwd)"

if [[ ! -f "$TASK_DIR/score.py" ]]; then
  echo "rsi-score: no score.py in $TASK_DIR" >&2
  exit 2
fi

# The private split decides acceptance, so its scorer/data must be trusted.
# Detect any tampering of the immutable harness before scoring (agents run as
# the same uid and can overwrite files, but cannot silently pass this check).
# Exit 5 = integrity failure, distinct from a usage/refusal error.
if [[ "$SPLIT" == "--private" ]]; then
  if ! bash "$HERE/rsi-check-integrity.sh" "$TASK_DIR"; then
    echo "rsi-score: refusing to produce a private score from a tampered harness." >&2
    exit 5
  fi
fi

exec python3 "$TASK_DIR/score.py" "$SPLIT" --solution "$SOLUTION" --json
