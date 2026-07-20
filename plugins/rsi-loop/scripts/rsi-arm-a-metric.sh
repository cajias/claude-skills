#!/usr/bin/env bash
# rsi-arm-a-metric.sh — Arm A (autoresearch) metric emitter for the §5.2 chassis A/B experiment.
# Part of the rsi-loop harness (outer loop only).
#
# THE SHIM BOUNDARY (pre-registered friction, PRE-REGISTRATION.md "Known
# architectural friction"): autoresearch's `Verify:` is a plain shell command
# that must print a single number on stdout. Our real inner eval
# (inner-agent.workflow.mjs) runs ONLY via the Workflow / agent() runtime, which
# a shell command cannot invoke. This script is the metric half of the chosen
# bridge: it does NOT run the inner eval. It CONSUMES the per-task winning
# solution files an inner eval already produced, (re)scores them on the private
# split with the immutable harness, aggregates, and prints the scalar. The agent
# driving the loop runs the Workflow eval itself and hands the winners here; that
# is why the loop is "not truly self-contained" — this file is where that seam
# lives, on purpose.
#
# Usage:
#   RSI_OUTER_LOOP=1 rsi-arm-a-metric.sh <task-dir> <winning-solution.py> \
#                                        [<task-dir> <solution.py> ...]
#   - One <task-dir> <solution.py> pair per battery task (3 for the §5.2 battery:
#     bin-packing, instruction-routing, tabular-classification).
#   - Task name in the aggregate = basename of <task-dir> (matches rsi-step and
#     works for run batteries at rsi-runs/<run>/tasks/<name>).
#   - Single seed 42 per task, matching the pre-reg (median == score).
#
# stdout: ONLY the bare private_aggregate number (autoresearch scrapes a bare
#         number for `Verify:`). All diagnostics go to stderr.
# exit  : non-zero if any private score step fails or the integrity gate trips
#         (exit 5), so autoresearch's guard/crash path fires. 2 on usage error.
#
# Private scoring only runs with RSI_OUTER_LOOP=1 (score.py refuses --private
# without it and the PreToolUse deny hook blocks un-prefixed --private). During
# plugin development in a hooked session, launch with RSI_HOOK_DISARM=1 to
# disarm the deny hook (sanctioned dev use — do NOT hardcode it here).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"

if (( $# < 2 || $# % 2 != 0 )); then
  echo "usage: rsi-arm-a-metric.sh <task-dir> <solution.py> [<task-dir> <solution.py> ...]" >&2
  exit 2
fi

# Build the {"tasks":{...}} payload for rsi-aggregate.py, one seed per task.
entries=""
while (( $# )); do
  task_dir="$1"; solution="$2"; shift 2
  name="$(basename "$task_dir")"
  if [[ ! -f "$solution" ]]; then
    echo "rsi-arm-a-metric: missing solution file for $name: $solution" >&2
    exit 1
  fi
  # Private scoring — outer-loop only. rsi-score.sh runs the integrity gate first
  # (exit 5 on tamper), then score.py. Capture with `|| rc=$?` so the REAL exit
  # code survives (an `if ! cmd` wrapper would reset $? to 0 and mask exit 5).
  rc=0
  score_json="$(RSI_OUTER_LOOP=1 bash "$HERE/rsi-score.sh" --private "$task_dir" "$solution")" || rc=$?
  if (( rc != 0 )); then
    echo "rsi-arm-a-metric: scoring failed for $name ($task_dir), rc=$rc" >&2
    exit "$rc"
  fi
  score="$(printf '%s' "$score_json" | python3 -c 'import sys,json; print(json.load(sys.stdin)["score"])')"
  echo "rsi-arm-a-metric: $name private=$score" >&2
  entries="${entries:+$entries,}\"$name\":{\"seeds\":[$score]}"
done

# Mean of per-task medians (single seed ⇒ median == score). Bare number to stdout.
rc=0
agg_json="$(printf '{"tasks":{%s}}' "$entries" | python3 "$HERE/rsi-aggregate.py" --aggregate)" || rc=$?
if (( rc != 0 )); then
  echo "rsi-arm-a-metric: aggregation failed, rc=$rc" >&2
  exit "$rc"
fi
printf '%s' "$agg_json" | python3 -c 'import sys,json; print(json.load(sys.stdin)["private_aggregate"])'
