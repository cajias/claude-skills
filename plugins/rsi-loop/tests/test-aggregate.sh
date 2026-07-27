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

# ── --power-check (§6.1.3 battery-resolution gate) ────────────────────
# Synthetic per-instance vectors, deterministic (seeded generator inside the
# test), zero LLM. `powered` builds vectors sized to the new N with tight
# dispersion (SE within budget); the other payloads are engineered to fail one
# assertion each. verdict "powered" -> exit 0; "underpowered — inconclusive" -> exit 1.
echo "[rsi-aggregate --power-check]"

# POWERED: N=(400,120,160), tight spread so per-task bootstrap SE < se_max, and
# the pooled 0.03 planted effect resolves at alpha=0.05.
powered_payload() {
  python3 - <<'PY'
import json, random
def vec(mean, n, spread, seed):
    r = random.Random(seed)
    return [max(0.0, min(1.0, mean + spread * (r.random() * 2 - 1))) for _ in range(n)]
print(json.dumps({"tasks": {
    "tabular-classification": {"per_instance": vec(0.90, 400, 0.30, 1), "se_max": 0.02},
    "bin-packing":            {"per_instance": vec(0.85, 120, 0.20, 2), "se_max": 0.02},
    "instruction-routing":    {"per_instance": vec(0.80, 160, 0.30, 3), "se_max": 0.025},
}}))
PY
}
set +e
OUT="$(powered_payload | python3 "$AGG" --power-check)"; RC=$?
set -e
check "powered battery exits 0" 0 "$RC"
check "powered verdict is 'powered'" powered "$(echo "$OUT" | field "v['verdict']")"
check "powered pass is True" True "$(echo "$OUT" | field "v['pass']")"
check "powered planted-delta resolves" True "$(echo "$OUT" | field "v['planted_delta']['resolved']")"

# UNDERPOWERED (SE fails): small, maximally over-dispersed vector -> bootstrap
# SE far above se_max. Guards the M5 signal-free failure.
set +e
OUT="$(echo '{"tasks":{"t":{"per_instance":[0.0,1.0,0.0,1.0,0.0,1.0,0.0,1.0],"se_max":0.02}}}' | python3 "$AGG" --power-check)"; RC=$?
set -e
check "over-dispersed SE fails, exits 1" 1 "$RC"
check "SE-fail verdict is inconclusive" "underpowered — inconclusive" "$(echo "$OUT" | field "v['verdict']")"
check "SE-fail task pass is False" False "$(echo "$OUT" | field "v['per_task']['t']['pass']")"

# UNDERPOWERED (planted-Δ unresolvable): tiny near-ceiling pool. se_max is loose
# enough that SE passes, but a saturated pool cannot resolve a 0.03 effect
# (clamped diffs collapse toward 0) -> the non-saturating precondition bites.
set +e
OUT="$(echo '{"tasks":{"t":{"per_instance":[1.0,1.0,0.99,1.0,0.98],"se_max":0.05}}}' | python3 "$AGG" --power-check)"; RC=$?
set -e
check "unresolvable planted-delta exits 1" 1 "$RC"
check "planted-delta not resolved" False "$(echo "$OUT" | field "v['planted_delta']['resolved']")"

# usage / parse errors keep the exit-2 convention.
set +e
echo '{}' | python3 "$AGG" --power-check >/dev/null 2>&1
check "power-check empty tasks exits 2" 2 "$?"
echo 'not json' | python3 "$AGG" --power-check >/dev/null 2>&1
check "power-check bad JSON exits 2" 2 "$?"
set -e

echo
echo "rsi-aggregate: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
