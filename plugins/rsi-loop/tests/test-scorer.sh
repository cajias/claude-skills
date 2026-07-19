#!/usr/bin/env bash
# Self-check for every task scorer in the battery: validity enforcement, the
# "score 0 is a report, not a crash" contract, the private-split refusal gate,
# and per-task regression anchors. One combined tally across all three families
# (heuristic optimization, ML engineering, harness engineering).
set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
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

# ── bin-packing (heuristic optimization) ─────────────────────────────
SCORE="$PLUGIN_ROOT/tasks/bin-packing/score.py"
echo "[bin-packing scorer]"

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

cat > "$WORK/cheat.py" <<'PY'
def pack(items, capacity):
    return [list(range(len(items)))]
PY
check "overfull bin scores 0" 0.0 \
  "$(python3 "$SCORE" --public --solution "$WORK/cheat.py" | score_of)"

cat > "$WORK/diag.py" <<'PY'
import json, sys
def pack(items, capacity):
    print(json.dumps({"debug": 1})); sys.exit(0)
PY
check "diagnostic-then-exit scores 0 (no KeyError)" 0.0 \
  "$(python3 "$SCORE" --public --solution "$WORK/diag.py" | score_of)"
check "diagnostic-then-exit reports an error string" "solution produced no 'bins' output" \
  "$(python3 "$SCORE" --public --solution "$WORK/diag.py" | err0_of)"

set +e
python3 "$SCORE" --private --solution "$WORK/ffd.py" >/dev/null 2>&1
check "private refused without RSI_OUTER_LOOP" 3 "$?"
RSI_OUTER_LOOP=1 python3 "$SCORE" --private --solution "$WORK/ffd.py" >/dev/null 2>&1
check "private allowed with RSI_OUTER_LOOP=1" 0 "$?"

mkdir -p "$WORK/empty/public"
echo '[]' > "$WORK/empty/public/instances.json"
cp "$SCORE" "$WORK/empty/score.py"
python3 "$WORK/empty/score.py" --public --solution "$WORK/ffd.py" >/dev/null 2>&1
check "empty instance list exits 4 (no ZeroDivision)" 4 "$?"
set -e

# ── tabular-classification (ML engineering) ──────────────────────────
SCORE="$PLUGIN_ROOT/tasks/tabular-classification/score.py"
echo "[tabular-classification scorer]"

cat > "$WORK/maj.py" <<'PY'
def predict(train, test):
    ones = sum(r[-1] for r in train)
    c = 1 if ones > len(train) - ones else 0
    return [c] * len(test)
PY
# Majority baseline: known CV accuracy (regression anchor for the committed data).
check "majority public CV is the known 0.44" 0.44 \
  "$(python3 "$SCORE" --public --solution "$WORK/maj.py" | score_of)"

cat > "$WORK/knn.py" <<'PY'
def predict(train, test):
    K = 7; out = []
    for q in test:
        ds = sorted((sum((q[i]-r[i])**2 for i in range(len(q))), r[-1]) for r in train)[:K]
        out.append(1 if sum(l for _, l in ds) * 2 > K else 0)
    return out
PY
# A real model must clear the majority baseline by a wide margin (headroom exists).
KNN_CV="$(python3 "$SCORE" --public --solution "$WORK/knn.py" | score_of)"
check "7-NN public CV beats 0.7 (real headroom)" 1 \
  "$(python3 -c "print(1 if $KNN_CV > 0.7 else 0)")"

cat > "$WORK/wronglen.py" <<'PY'
def predict(train, test):
    return [0]  # wrong length on purpose
PY
check "wrong-length prediction scores 0" 0.0 \
  "$(python3 "$SCORE" --public --solution "$WORK/wronglen.py" | score_of)"

cat > "$WORK/boom.py" <<'PY'
def predict(train, test):
    raise ValueError("boom")
PY
check "crashing predict scores 0 (no battery crash)" 0.0 \
  "$(python3 "$SCORE" --public --solution "$WORK/boom.py" | score_of)"

set +e
python3 "$SCORE" --private --solution "$WORK/knn.py" >/dev/null 2>&1
check "private refused without RSI_OUTER_LOOP" 3 "$?"
RSI_OUTER_LOOP=1 python3 "$SCORE" --private --solution "$WORK/knn.py" >/dev/null 2>&1
check "private allowed with RSI_OUTER_LOOP=1" 0 "$?"
set -e

# ── instruction-routing (harness engineering) ────────────────────────
SCORE="$PLUGIN_ROOT/tasks/instruction-routing/score.py"
echo "[instruction-routing scorer]"

cat > "$WORK/router.py" <<'PY'
import re
def _nums(s): return [int(x) for x in re.findall(r"-?\d+", s)]
def solve(instruction):
    s = instruction.strip().lower()
    if "[" in s:
        items = [x.strip() for x in s[s.index("[")+1:s.index("]")].split(",")]
        if any(k in s for k in ["largest","maximum","biggest"]): return max(int(x) for x in items)
        m = re.search(r"(\d+)(?:st|nd|rd|th)?\s+item|item number (\d+)|element (\d+)", s)
        if m: return items[next(int(g) for g in m.groups() if g)-1]
        if any(k in s for k in ["how many","count","size"]): return len(items)
    if any(k in s for k in ["add","plus","sum"]): n=_nums(s); return n[0]+n[1]
    if "subtract" in s: n=_nums(s); return n[1]-n[0]
    if "minus" in s or re.search(r"-?\d+\s*-\s*-?\d+", s): n=_nums(s); return n[0]-n[1]
    if any(k in s for k in ["multiply","times","product"]): n=_nums(s); return n[0]*n[1]
    words=[w for w in re.findall(r"[a-z]{2,}", s) if w not in
           ("reverse","the","word","spell","backwards","reversed","uppercase","convert","to",
            "shout","how","many","letters","in","length","of","count","what","is")]
    if "revers" in s or "backwards" in s: return words[-1][::-1]
    if "uppercase" in s or "shout" in s: return words[-1].upper()
    if "letters" in s or "length" in s: return len(words[-1])
    return ""
PY
# A real parser clears both splits well; anchors that headroom and generalization.
check "router public score is 1.0 (canonical phrasings)" 1.0 \
  "$(python3 "$SCORE" --public --solution "$WORK/router.py" | score_of)"
ROUTER_PRV="$(RSI_OUTER_LOOP=1 python3 "$SCORE" --private --solution "$WORK/router.py" | score_of)"
check "router private score beats 0.8 (generalizes)" 1 \
  "$(python3 -c "print(1 if $ROUTER_PRV > 0.8 else 0)")"

cat > "$WORK/lookup.py" <<'PY'
# A hard-coded lookup of public answers: aces public, fails held-out private.
def solve(instruction):
    return {"add 11 and 16": "27"}.get(instruction.strip(), "")
PY
LOOKUP_PRV="$(RSI_OUTER_LOOP=1 python3 "$SCORE" --private --solution "$WORK/lookup.py" | score_of)"
check "public-answer lookup scores ~0 on private (anti-overfit)" 0.0 "$LOOKUP_PRV"

cat > "$WORK/gamed.py" <<'PY'
import json, sys
# Denominator-gaming attempt: emit ONE crafted-correct answer (27 == first
# public case) then exit before the runner scores the rest. A truncating scorer
# would report 1.0/1; the count-mismatch guard must score every case 0 instead.
print(json.dumps({"answers": [{"ok": True, "value": "27"}]})); sys.exit(0)
def solve(instruction): return ""
PY
check "short-answers denominator gaming scores 0 (not 1.0)" 0.0 \
  "$(python3 "$SCORE" --public --solution "$WORK/gamed.py" | score_of)"

cat > "$WORK/broken.py" <<'PY'
def solve(instruction)  # syntax error
PY
check "import-error solution scores 0 for every case" 0.0 \
  "$(python3 "$SCORE" --public --solution "$WORK/broken.py" | score_of)"

set +e
python3 "$SCORE" --private --solution "$WORK/router.py" >/dev/null 2>&1
check "private refused without RSI_OUTER_LOOP" 3 "$?"
set -e

echo
echo "all scorers: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
