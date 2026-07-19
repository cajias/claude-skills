#!/usr/bin/env bash
# Tests for the harness-integrity guard (rsi-check-integrity.sh + rsi-score.sh
# --private gate). This is the writer-gap defense that holds under a shared uid
# (root), where OS read-only bits cannot prevent a write: we DETECT tampering
# and refuse to score. Covers both trust anchors — git (plugin source) and the
# .integrity.sha256 manifest (sandbox / run copies).
set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CHK="$PLUGIN_ROOT/scripts/rsi-check-integrity.sh"
SANDBOX_SH="$PLUGIN_ROOT/scripts/rsi-sandbox.sh"
SCORE_SH="$PLUGIN_ROOT/scripts/rsi-score.sh"
TASK_DIR="$PLUGIN_ROOT/tasks/bin-packing"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
PASS=0
FAIL=0

check() { # $1 label, $2 expected-exit, $3 actual-exit
  if [[ "$2" == "$3" ]]; then
    PASS=$((PASS + 1)); printf '  ok   %s\n' "$1"
  else
    FAIL=$((FAIL + 1)); printf '  FAIL %s (want exit %s, got %s)\n' "$1" "$2" "$3"
  fi
}

cat > "$WORK/sol.py" <<'PY'
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

echo "[harness integrity]"

# 1. git anchor: the committed plugin-source task dir is clean.
set +e
bash "$CHK" "$TASK_DIR" >/dev/null 2>&1
check "git-tracked task dir verifies clean" 0 "$?"
set -e

# 2. manifest anchor: a fresh sandbox (no git) verifies clean.
SB="$WORK/sandbox"
bash "$SANDBOX_SH" "$TASK_DIR" "$SB" >/dev/null
set +e
bash "$CHK" "$SB" >/dev/null 2>&1
check "fresh sandbox verifies clean (manifest)" 0 "$?"

# 3. manifest anchor: tampering the sandbox scorer is detected.
echo "# tamper" >> "$SB/score.py"
bash "$CHK" "$SB" >/dev/null 2>&1
check "tampered sandbox scorer detected" 1 "$?"

# 4. manifest anchor: tampering instance data is detected.
bash "$SANDBOX_SH" "$TASK_DIR" "$SB" >/dev/null # rebuild clean
echo "[]" > "$SB/public/instances.json"
bash "$CHK" "$SB" >/dev/null 2>&1
check "tampered sandbox instance data detected" 1 "$?"

# 5. no anchor at all → unverifiable is a hard failure.
NB="$WORK/noanchor"
mkdir -p "$NB"; cp "$TASK_DIR/score.py" "$TASK_DIR/task.md" "$NB/"
bash "$CHK" "$NB" >/dev/null 2>&1
check "no git and no manifest is a hard fail" 1 "$?"

# 6. rsi-score.sh --private refuses a tampered (manifest) harness with exit 5.
cp -R "$TASK_DIR/private" "$SB/private" 2>/dev/null || true # give the copy a private split
# regenerate manifest to include private, then tamper
( cd "$SB" && find score.py task.md public -type f -exec sha256sum {} + | LC_ALL=C sort > .integrity.sha256 )
echo "# tamper again" >> "$SB/score.py"
RSI_OUTER_LOOP=1 bash "$SCORE_SH" --private "$SB" "$WORK/sol.py" >/dev/null 2>&1
check "rsi-score --private refuses tampered harness (exit 5)" 5 "$?"
set -e

# 7. The same guarantees hold for every task in the battery, not just
#    bin-packing: each committed task dir verifies git-clean, each fresh
#    sandbox verifies by manifest, and a tampered sandbox scorer is detected.
for t in tabular-classification instruction-routing; do
  TD="$PLUGIN_ROOT/tasks/$t"
  set +e
  bash "$CHK" "$TD" >/dev/null 2>&1
  check "$t: git-tracked task dir verifies clean" 0 "$?"
  SBT="$WORK/sandbox-$t"
  bash "$SANDBOX_SH" "$TD" "$SBT" >/dev/null
  bash "$CHK" "$SBT" >/dev/null 2>&1
  check "$t: fresh sandbox verifies clean (manifest)" 0 "$?"
  echo "# tamper" >> "$SBT/score.py"
  bash "$CHK" "$SBT" >/dev/null 2>&1
  check "$t: tampered sandbox scorer detected" 1 "$?"
  set -e
done

echo
echo "harness integrity: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
