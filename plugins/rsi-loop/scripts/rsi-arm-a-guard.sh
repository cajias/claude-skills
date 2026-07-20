#!/usr/bin/env bash
# rsi-arm-a-guard.sh — Arm A (autoresearch) `Guard:` command for the §5.2 A/B experiment.
# Part of the rsi-loop harness (outer loop only).
#
# The mechanical accept-floor autoresearch's must-pass Guard runs (pass/fail by
# exit code) BEFORE a candidate is committed. Pre-reg guard = structural +
# integrity + verifier hack-check; this script is the STRUCTURAL + INTEGRITY
# portion only:
#   (a) rsi-check-integrity.sh on each task dir — git HEAD / manifest anchor;
#       exit 5 from rsi-score is the scoring-side twin, here a non-zero integrity
#       result fails the guard.
#   (b) each winning solution file exists and is non-empty.
# The LLM-adversarial verifier hack-check is a SEPARATE step and may be
# unavailable (pre-reg verifier-availability contingency); this guard does NOT
# invoke an LLM — it is the mechanical floor only.
#
# Usage:
#   rsi-arm-a-guard.sh <task-dir> <solution.py> [<task-dir> <solution.py> ...]
# exit: 0 = pass, non-zero = fail (usage error = 2).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"

if (( $# < 2 || $# % 2 != 0 )); then
  echo "usage: rsi-arm-a-guard.sh <task-dir> <solution.py> [<task-dir> <solution.py> ...]" >&2
  exit 2
fi

while (( $# )); do
  task_dir="$1"; solution="$2"; shift 2
  name="$(basename "$task_dir")"
  if ! bash "$HERE/rsi-check-integrity.sh" "$task_dir"; then
    echo "rsi-arm-a-guard: FAIL — integrity gate tripped for $name ($task_dir)" >&2
    exit 1
  fi
  if [[ ! -s "$solution" ]]; then
    echo "rsi-arm-a-guard: FAIL — missing or empty winning solution for $name: $solution" >&2
    exit 1
  fi
  echo "rsi-arm-a-guard: OK $name" >&2
done

echo "rsi-arm-a-guard: PASS" >&2
exit 0
