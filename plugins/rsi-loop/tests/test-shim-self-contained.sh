#!/usr/bin/env bash
# Shim self-containment guard (M6 runtime blocker).
#
# The Claude Code Workflow runtime FORBIDS dynamic import() ("import() is not
# available in workflow scripts") — Workflow bodies have no FS/module access.
# So the inner-agent shim MUST inline its engine, not import() it. Every prior
# M6 test ran the engine Node-direct (which permits import()), masking this.
#
# This test is the static guard whose absence let the bug ship. Zero LLM/network.
#   (a) No dynamic import()/require() in ANY baseline workflow script.
#   (b) Drift guard: the inlined engine in gen-000's shim is byte-identical to
#       search-engine.mjs (the canonical source of truth) with only `export `
#       stripped from the search signature.
#   (c) Parse: the shim is a valid Workflow-style module body. A Workflow .mjs
#       FAILS plain `node --check` (top-level `return` is mandatory in the
#       runtime but illegal in a standalone-module parse) — this is the runtime
#       contract, not a bug. So we parse via the runtime replica: wrap the body
#       in an async function with `export` stripped + globals injected (same
#       technique as scripts/rsi-phase0-gate.mjs / the engine-polymorphism
#       replica), which parses WITHOUT executing.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_ROOT="$(cd "$DIR/.." && pwd)"
SHIM="$PLUGIN_ROOT/baseline/gen-000/inner-agent.workflow.mjs"
ENGINE="$PLUGIN_ROOT/baseline/gen-000/search-engine.mjs"
PASS=0
FAIL=0

echo "[shim self-contained]"

# (a) No dynamic import()/require() in any workflow script. `import(` not
# preceded by `.` (so no false hit on a hypothetical `.import(` method), plus
# `await import` and `require(`.
HITS="$(grep -REn 'await import|(^|[^.])import[[:space:]]*\(|require[[:space:]]*\(' "$PLUGIN_ROOT"/baseline/*/inner-agent.workflow.mjs || true)"
if [[ -z "$HITS" ]]; then
  PASS=$((PASS + 1)); printf '  ok   no dynamic import()/require() in any baseline workflow script\n'
else
  FAIL=$((FAIL + 1)); printf '  FAIL dynamic import()/require() found (Workflow runtime forbids it):\n%s\n' "$HITS"
fi

# (b) + (c) drift guard and runtime-replica parse.
set +e
node -e '
  const fs = require("fs");
  const shim = fs.readFileSync(process.argv[1], "utf8");
  const eng = fs.readFileSync(process.argv[2], "utf8");
  let pass = 0, fail = 0;
  const ok = (c, label) => { if (c) { pass++; console.log("  ok   " + label); } else { fail++; console.log("  FAIL " + label); } };

  // (b) Drift: engine block (first `const MIN_BUDGET_UNITS` → EOF, export stripped)
  //     must appear VERBATIM in the shim.
  const i = eng.indexOf("const MIN_BUDGET_UNITS");
  const block = eng.slice(i).replace(/\n+$/, "")
    .replace("export async function search", "async function search");
  ok(eng.includes("export async function search"), "engine still exports search (canonical source untouched)");
  ok(shim.includes(block), "inlined engine is byte-identical to search-engine.mjs (sans export)");

  // (c) Runtime-replica parse: strip `export`, inject Workflow globals, build an
  //     AsyncFunction (parses, does NOT execute). Mirrors the phase0-gate replica.
  const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
  const body = shim.replace(/^export /gm, "");
  try {
    new AsyncFunction("args", "agent", "parallel", "phase", "log", "budget", body);
    ok(true, "shim parses as a Workflow-style async body (globals injected, not executed)");
  } catch (e) {
    ok(false, "shim parses as a Workflow-style async body — " + e.message);
  }

  process.exit(fail === 0 ? 0 : 1);
' "$SHIM" "$ENGINE"
RC=$?
set -e
if [[ "$RC" -eq 0 ]]; then
  PASS=$((PASS + 2))
else
  # node printed its own per-assertion lines; count the pass/fail split is not
  # trivial from here, so mark the whole node phase as one failure signal.
  FAIL=$((FAIL + 1))
fi

echo
echo "shim self-contained: $PASS passed, $FAIL failed"
[[ "$FAIL" -eq 0 ]]
