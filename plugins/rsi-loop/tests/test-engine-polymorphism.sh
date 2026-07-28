#!/usr/bin/env bash
# Engine polymorphism + grep-zero invariant for the pure search core.
#
# (a) Structural polymorphism: search-engine.mjs contains ZERO artifact-kind
#     tokens (the engine literally cannot name either artifact type).
# (b) Behavioral isomorphism + policy-completeness: two stub adapters differing
#     only in artifact strings produce identical node ledgers under the same
#     policy/seed, and the 3 formerly-hardcoded policy fields (algorithm,
#     context_mode, selection) are load-bearing.
# Runs under plain `node` in <1s with zero network/LLM.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(cd "$DIR/.." && pwd)"
ENGINE="$PLUGIN_ROOT/baseline/gen-000/search-engine.mjs"
PASS=0
FAIL=0

echo "[engine polymorphism]"

# (a) grep-zero: the engine names no artifact type.
HITS="$(grep -Eiwc 'solution|scaffold|task|\.py|generation' "$ENGINE" || true)"
if [[ "$HITS" == "0" ]]; then
  PASS=$((PASS + 1)); printf '  ok   grep-zero: no artifact-kind tokens in search-engine.mjs\n'
else
  FAIL=$((FAIL + 1)); printf '  FAIL grep-zero: %s artifact-kind token(s) in search-engine.mjs:\n' "$HITS"
  grep -Eiwn 'solution|scaffold|task|\.py|generation' "$ENGINE" || true
fi

# (b) behavioral assertions (isomorphism + policy completeness) under plain node.
set +e
node "$DIR/engine-polymorphism.mjs"
NODE_RC=$?
set -e
if [[ "$NODE_RC" -eq 0 ]]; then
  PASS=$((PASS + 1)); printf '  ok   behavioral isomorphism + policy-field assertions\n'
else
  FAIL=$((FAIL + 1)); printf '  FAIL behavioral isomorphism + policy-field assertions (node exit %s)\n' "$NODE_RC"
fi

echo
echo "engine polymorphism: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
