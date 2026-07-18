# Continuation state — rsi-loop implementation

Snapshot for resuming the KICKOFF.md build in a fresh session. Everything needed lives in
this repo; the scratchpad run directory is ephemeral and fully reconstructable from
`docs/experiments/run-001/`.

## Where the build stands (2026-07-18)

- **M1 — done** (`docs/experiments/m1-smoke-bin-packing.md`): gen-000 verified end-to-end;
  deny-hook suite 29/29 (`tests/test-deny-hook.sh`); `/rsi:autoresearch` live.
- **M2 — exit criteria met** (`docs/experiments/run-001/README.md`): 3 manual outer steps,
  gen-002 accepted (private 0.9405 > 0.9379), steps 1 and 3 rejected with recorded
  diagnoses. **The §5.2 chassis A/B experiment has NOT run yet** — it is the deferred
  decision below.
- **M3, M4, M5 — not started.**

## Deferred decision (ask the user before heavy spend)

The pre-registered §5.2 chassis A/B (autoresearch plugin vs native Workflow outer loop) is
2 arms x 2 reps x 10 steps ≈ 40 evaluations x ~0.5M inner tokens ≈ 20M+ tokens, ~20h.
Options laid out to the user (answer deferred): (a) full pre-registered scale, (b) reduced
pilot first (1 rep x 5 steps per arm, ~5M tokens) — recommended, (c) defer chassis
experiment and proceed to M3. Do not launch any arm without the user's choice.

## How to resume a live run

1. `RUN=<scratchpad>/rsi-runs/run-001 && mkdir -p $RUN/generations $RUN/eval`
2. Copy `docs/experiments/run-001/{gen-001,gen-002,gen-003}` into `$RUN/generations/`,
   plus `plugins/rsi-loop/baseline/gen-000` as `$RUN/generations/gen-000`.
3. Copy `docs/experiments/run-001/ledger.jsonl` to `$RUN/ledger.jsonl`;
   `run-state.json` has the incumbent (gen-002) and next step number (4) —
   write `$RUN/best.txt` and `$RUN/tasks.txt` from it.
4. Outer-step procedure: `commands/rsi-step.md` (proposer prompt pattern used for steps 1-3
   is reflected in `agents/proposer.md`; per-eval budget: haiku, 9 nodes, seed 42).

## Operational gotchas (hard-won, do not rediscover)

- The Workflow runtime delivers `args` as a JSON **string** — every generation script starts
  with the parse-both-encodings line; keep it when proposers write new generations.
- Workflow scripts: no `Date.now`/`Math.random` (seeded Lehmer RNG instead), `export const
meta = {...}` pure literal first, plain JS only.
- Private scoring only via `RSI_OUTER_LOOP=1 bash scripts/rsi-score.sh --private ...`
  (the deny hook blocks everything else; `RSI_HOOK_DISARM=1` disarms for plugin dev).
- Inner evals: ~0.5M tokens / ~30 min each on bin-packing (fixed 9-node budget).
- Structural gate before spending eval budget: files present, policy.json valid,
  meta-literal + args-parse lines intact, no private/holdout references in prompts
  outside prohibition sentences.

## Known open issues (from run-001 ledger)

- Self-generated stress suite is rebuilt per run → unstable tie-breaker instrument
  (step-3 rejection root cause). Candidate fix belongs in a future PROPOSED generation
  (e.g. persist suite spec in the generation dir), not in the immutable harness.
- Single-task battery; M3 adds the ML-engineering and harness-engineering families
  (pure-stdlib Python only — no numpy/sklearn in this environment).
- `skills/rsi-loop/SKILL.md` is still a placeholder (update when /rsi:init + /rsi:step have
  been exercised end-to-end by a user-facing flow, M3).
