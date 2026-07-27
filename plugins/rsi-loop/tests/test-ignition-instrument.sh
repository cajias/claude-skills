#!/usr/bin/env bash
# Tests for rsi-ignition.py: the Level-2 ignition instrument (§6.1.4 + §6.1.6).
# Covers the 4 planted-verdict self-check, the three §6.1.6 K=3 controls
# (POSITIVE / NEGATIVE / UNDERPOWERED — the M5-guarding assertions), and the
# --calibrate MDE seed table. Deterministic, seeded, zero LLM, < 2s.
set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IGN="$PLUGIN_ROOT/scripts/rsi-ignition.py"
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
verdict() { python3 "$IGN" decide "$@" | field "v['verdict']"; }

echo "[rsi-ignition]"

# --- 1. the 4 planted-verdict self-check (§6.1.4) ---------------------------
set +e
python3 "$IGN" decide --self-check >/dev/null 2>&1
check "decide --self-check exits 0 (4 planted verdicts pass)" 0 "$?"
set -e

# --- 2. flat trajectory generator for the K=3 controls ----------------------
# control rises 0.50->0.70; ignited = control + gap at every g (so gap is the
# realized asymptote gap and ΔR>0). σ_d fixed at 0.05 → MDE(3)=0.072.
gen() { # $1 gap  → paired 3-seed payload on stdout
  python3 - "$1" <<'PY'
import json, sys
gap = float(sys.argv[1])
G, seeds = 8, [42, 43, 44]
ctrl = {str(s): [round(0.50 + 0.20 * (i / G), 6) for i in range(G + 1)] for s in seeds}
ign = {str(s): [round(v + gap, 6) for v in ctrl[str(s)]] for s in seeds}
print(json.dumps({"seeds": seeds, "G": G, "control": ctrl, "ignited": ign, "sigma_d": 0.05}))
PY
}

# (1) POSITIVE — effect 0.15 ≫ MDE(3)=0.072 → must IGNITE (SUPPORTED).
V="$(gen 0.15 | verdict --planted-positive-cleared true)"
check "POSITIVE effect 0.15 → IGNITION (SUPPORTED)" SUPPORTED "$V"

# (2) NEGATIVE — promoted == stock (effect 0) → NO IGNITION (guards M5's
# signal-free verdict). Within ±MDE, ΔR≈0 → NO_RESULT, never SUPPORTED.
V="$(gen 0.0 | verdict --planted-positive-cleared true)"
check "NEGATIVE effect 0 → NO IGNITION (NO_RESULT, not SUPPORTED)" NO_RESULT "$V"

# (3) UNDERPOWERED — effect 0.03 (M5-scale), MDE(3)=0.072 > 0.03 → INCONCLUSIVE
# (NO_RESULT), NOT a false ignition (the exact scenario M5 mishandled).
V="$(gen 0.03 | verdict --planted-positive-cleared true)"
check "UNDERPOWERED effect 0.03 < MDE → INCONCLUSIVE (NO_RESULT)" NO_RESULT "$V"

# Power precondition is a hard gate: an instrument that cannot resolve its
# planted positive returns NO_RESULT even on an otherwise-clean 0.15 arm.
V="$(gen 0.15 | verdict --planted-positive-cleared false)"
check "power precondition fails → NO_RESULT regardless of arms" NO_RESULT "$V"

# --- 3. power --calibrate reproduces the §6.1.6 MDE seed table ---------------
# A null ΔA sample with SD exactly 0.05 must yield MDE(3)≈0.072, MDE(25)≈0.025.
CAL="$(echo '{"null_deltas":[0.05,0.05,-0.05,-0.05,0.0]}' \
  | python3 "$IGN" power --calibrate --target-effect 0.03)"
check "calibrate measures σ_d = 0.05 from null sample" 0.05 \
  "$(echo "$CAL" | field "v['calibrated']['sigma_d_measured']")"
check "MDE(3) ≈ 0.072" True \
  "$(echo "$CAL" | field "abs(v['mde_seed_table']['3'] - 0.072) < 0.001")"
check "MDE(25) ≈ 0.025" True \
  "$(echo "$CAL" | field "abs(v['mde_seed_table']['25'] - 0.025) < 0.001")"
check "K_req(0.03) = 18 seeds (declare inconclusive up front if unfunded)" 18 \
  "$(echo "$CAL" | field "v['k_req']['seeds_required']")"

# power without --calibrate reproduces MDE at a given K from a supplied σ_d.
check "power --sigma-d 0.05 --K 3 → MDE 0.072" True \
  "$(python3 "$IGN" power --sigma-d 0.05 --K 3 | field "abs(v['mde_at_K']['mde'] - 0.072) < 0.001")"

# --- 4. usage errors ---------------------------------------------------------
set +e
echo 'not json' | python3 "$IGN" decide >/dev/null 2>&1
check "bad JSON on decide exits 2" 2 "$?"
echo '{"null_deltas":[0.05,0.05]}' | python3 "$IGN" power --calibrate >/dev/null 2>&1
check "calibrate with N_null < 5 exits 2" 2 "$?"
set -e

echo
echo "rsi-ignition: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
