#!/usr/bin/env bash
# Phase-0 power gate (PLAN.md §6.1.6): the covenant that unblocks A/B spend.
# Drives the REAL search() engine over a synthetic landscape via injected
# closures (zero LLM, zero network, <2s) and proves the assembled pipeline
# (engine → best-so-far → rsi-ignition.py decide) resolves a planted +0.15
# policy-lift positive at K=3 while returning NO_RESULT on 0-effect and
# ~0.03-effect controls. Exit 0 = gate clears. This is what CI runs.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(cd "$DIR/.." && pwd)"
PASS=0
FAIL=0

echo "[phase0-gate]"

set +e
node "$PLUGIN_ROOT/scripts/rsi-phase0-gate.mjs"
RC=$?
set -e
if [[ "$RC" -eq 0 ]]; then
  PASS=$((PASS + 1)); printf '  ok   gate cleared (positive→SUPPORTED, negative/underpowered/precond→NO_RESULT)\n'
else
  FAIL=$((FAIL + 1)); printf '  FAIL gate did not clear (node exit %s) — A/B budget MUST NOT be released\n' "$RC"
fi

echo
echo "phase0-gate: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
