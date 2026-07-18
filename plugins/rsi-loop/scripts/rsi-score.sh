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

if [[ ! -f "$TASK_DIR/score.py" ]]; then
  echo "rsi-score: no score.py in $TASK_DIR" >&2
  exit 2
fi

exec python3 "$TASK_DIR/score.py" "$SPLIT" --solution "$SOLUTION" --json
