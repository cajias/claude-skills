#!/usr/bin/env bash
# Tests for rsi-aggregate.py: robust cross-seed aggregation (median-based, so a
# single lucky/hacked seed cannot drive acceptance) and too-good instance
# outlier flagging (the verifier's statistical reward-hack detector).
set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AGG="$PLUGIN_ROOT/scripts/rsi-aggregate.py"
PASS=0
FAIL=0

check() { # $1 label, $2 expected, $3 actual
  if [[ "$2" == "$3" ]]; then
    PASS=$((PASS + 1)); printf '  ok   %s\n' "$1"
  else
    FAIL=$((FAIL + 1)); printf '  FAIL %s (want %s, got %s)\n' "$1" "$2" "$3"
  fi
}
field() { python3 -c "import json,sys;v=json.load(sys.stdin);print($1)"; }

echo "[rsi-aggregate]"

# Single-seed: aggregate == the score itself; flagged as no-outlier-removal.
OUT="$(echo '{"tasks":{"bin-packing":{"seeds":[0.9405]}}}' | python3 "$AGG" --aggregate)"
check "single-seed aggregate == score" 0.9405 "$(echo "$OUT" | field "v['private_aggregate']")"
check "single-seed note mentions no outlier removal" True \
  "$(echo "$OUT" | field "'no seed-level outlier removal' in v['note']")"

# Multi-seed: median is robust to one high outlier seed (0.9 does not pull it up).
OUT="$(echo '{"tasks":{"t":{"seeds":[0.5,0.5,0.9]}}}' | python3 "$AGG" --aggregate)"
check "median ignores a single high seed" 0.5 "$(echo "$OUT" | field "v['per_task']['t']['median']")"
check "trimmed mean drops the top seed" 0.5 \
  "$(echo "$OUT" | field "v['per_task']['t']['trimmed_mean_drop_top']")"

# Two tasks: run aggregate = mean of per-task medians.
OUT="$(echo '{"tasks":{"a":{"seeds":[0.8]},"b":{"seeds":[0.6]}}}' | python3 "$AGG" --aggregate)"
check "two-task aggregate = mean of medians" 0.7 "$(echo "$OUT" | field "v['private_aggregate']")"

# Too-good outlier: one perfect instance amid a baseline cluster is flagged.
OUT="$(echo '{"per_instance":[0.5,0.52,0.48,0.5,1.0]}' | python3 "$AGG" --flag-outliers)"
check "too-good instance flagged" True "$(echo "$OUT" | field "v['flagged']")"
check "flagged index is the perfect one" 4 "$(echo "$OUT" | field "v['too_good_outliers'][0]['index']")"

# All-equal and all-perfect vectors must NOT trip the flag (zero spread guard).
check "all-equal baseline not flagged" False \
  "$(echo '{"per_instance":[0.5,0.5,0.5,0.5]}' | python3 "$AGG" --flag-outliers | field "v['flagged']")"
check "all-perfect not flagged" False \
  "$(echo '{"per_instance":[1.0,1.0,1.0]}' | python3 "$AGG" --flag-outliers | field "v['flagged']")"

# A uniformly strong solution (real generalization, tight spread) is not flagged.
check "tight strong cluster not flagged" False \
  "$(echo '{"per_instance":[0.9,0.92,0.88,0.91]}' | python3 "$AGG" --flag-outliers | field "v['flagged']")"

# Usage errors.
set +e
echo '{}' | python3 "$AGG" --aggregate >/dev/null 2>&1
check "empty tasks exits 2" 2 "$?"
echo 'not json' | python3 "$AGG" --flag-outliers >/dev/null 2>&1
check "bad JSON exits 2" 2 "$?"
set -e

echo
echo "rsi-aggregate: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
