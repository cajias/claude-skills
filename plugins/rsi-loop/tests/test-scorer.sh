#!/usr/bin/env bash
# Self-check for the bin-packing scorer: validity enforcement, the "score 0 is
# a report, not a crash" contract, the private-split refusal gate, and the
# audit regression cases (diagnostic-then-exit, empty instances).
set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCORE="$PLUGIN_ROOT/tasks/bin-packing/score.py"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
PASS=0
FAIL=0

check() { # $1 label, $2 expected, $3 actual
  if [[ "$2" == "$3" ]]; then
    PASS=$((PASS + 1)); printf '  ok   %s\n' "$1"
  else
    FAIL=$((FAIL + 1)); printf '  FAIL %s (want %s, got %s)\n' "$1" "$2" "$3"
  fi
}

score_of() { python3 -c "import json,sys;print(json.load(sys.stdin)['score'])"; }
err0_of() { python3 -c "import json,sys;print(json.load(sys.stdin)['per_instance'][0]['error'])"; }

echo "[bin-packing scorer]"

# Valid First-Fit-Decreasing: known-good public score (regression anchor).
cat > "$WORK/ffd.py" <<'PY'
def pack(items, capacity):
    order = sorted(range(len(items)), key=lambda i: -items[i])
    bins, loads = [], []
    for i in order:
        for j, l in enumerate(loads):
            if l + items[i] <= capacity:
                bins[j].append(i); loads[j] += items[i]; break
        else:
            bins.append([i]); loads.append(items[i])
    return bins
PY
check "FFD public score is the known 0.964762" 0.964762 \
  "$(python3 "$SCORE" --public --solution "$WORK/ffd.py" | score_of)"

# Overfull single bin: invalid packing scores 0, no crash.
cat > "$WORK/cheat.py" <<'PY'
def pack(items, capacity):
    return [list(range(len(items)))]
PY
check "overfull bin scores 0" 0.0 \
  "$(python3 "$SCORE" --public --solution "$WORK/cheat.py" | score_of)"

# Prints a diagnostic JSON line then exits: must be scored 0, not a KeyError.
cat > "$WORK/diag.py" <<'PY'
import json, sys
def pack(items, capacity):
    print(json.dumps({"debug": 1})); sys.exit(0)
PY
check "diagnostic-then-exit scores 0 (no KeyError)" 0.0 \
  "$(python3 "$SCORE" --public --solution "$WORK/diag.py" | score_of)"
check "diagnostic-then-exit reports an error string" "solution produced no 'bins' output" \
  "$(python3 "$SCORE" --public --solution "$WORK/diag.py" | err0_of)"

# Private split refused without the outer-loop env marker.
set +e
python3 "$SCORE" --private --solution "$WORK/ffd.py" >/dev/null 2>&1
check "private refused without RSI_OUTER_LOOP" 3 "$?"
RSI_OUTER_LOOP=1 python3 "$SCORE" --private --solution "$WORK/ffd.py" >/dev/null 2>&1
check "private allowed with RSI_OUTER_LOOP=1" 0 "$?"

# Empty instance list: clean exit 4, not a ZeroDivisionError.
mkdir -p "$WORK/empty/public"
echo '[]' > "$WORK/empty/public/instances.json"
cp "$SCORE" "$WORK/empty/score.py"
python3 "$WORK/empty/score.py" --public --solution "$WORK/ffd.py" >/dev/null 2>&1
check "empty instance list exits 4 (no ZeroDivision)" 4 "$?"
set -e

echo
echo "bin-packing scorer: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
