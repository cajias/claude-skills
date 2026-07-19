---
description: Drive the outer loop for many steps (propose→evaluate→verify→select) until a stop condition
argument-hint: "<run-dir> [--max-steps N] [--budget TOKENS] [--seeds K] [--plateau P]"
---

Run the AIDE²-style outer loop unattended on the run in "$ARGUMENTS", repeating
the [`/rsi:step`](rsi-step.md) procedure until a stop condition fires. This is
the `ralph-loop`-style driver: a bounded loop with an explicit completion
condition, not an open-ended one.

## Arguments

- `<run-dir>` (required) — an initialized run dir (see [`/rsi:init`](rsi-init.md)).
- `--max-steps N` (default 10) — hard cap on outer steps this invocation.
- `--budget TOKENS` (optional) — cumulative **inner** token budget across the
  run; stop before a step that would exceed it. This is the paper's fixed-budget
  constraint at the run level (per-eval budget is fixed separately in the
  generation's `policy.json`). If omitted, only `--max-steps` and `--plateau`
  bound the run.
- `--seeds K` (default 1) — evaluate each candidate under K seeds and select on
  the robust cross-seed aggregate (see step 4 below). K≥3 also enables the
  seed-level too-good-result removal. More seeds cut tiny-battery noise at linear
  cost.
- `--plateau P` (default 4) — stop early after P consecutive rejected steps (the
  search has stalled; a human should inspect the diagnoses before spending more).
  `--plateau 0` disables the plateau stop so the run always executes the full
  `--max-steps` — used by `/rsi:ignite` to hold both arms to an equal step budget.

## Procedure

1. **Resume-aware start (ledger is the source of truth).** Read `ledger.jsonl`;
   treat it, not `best.txt`, as authoritative. Derive:
   - next step number = `(max step in ledger) + 1`;
   - incumbent = the generation named by the **last accepted** ledger line
     (fall back to `generations/gen-000` if none accepted). **Reconcile
     `best.txt` against this**: if `best.txt` disagrees (e.g. a crash landed
     between the ledger append and the `best.txt` write, per `rsi-step.md`
     step 7), rewrite `best.txt` from the ledger — never trust a `best.txt` that
     names a generation absent from, or not accepted in, the ledger;
   - cumulative inner tokens = sum of `inner_tokens` over committed ledger lines.
   Re-invoking `/rsi:run` on the same dir continues where the last one stopped —
   never restart from step 1 if the ledger is non-empty. Caveat: a step that
   crashed *before* its ledger append leaves no committed line, so its partial
   inner-token spend is not counted and the step re-runs on resume (re-spending
   those tokens). The `--budget` guard is therefore accurate to committed-step
   granularity, not to the token; size `--budget` with that slack in mind.

2. **Budget/step guard, then one step.** Before each step, stop and report if:
   any of `--max-steps` (steps taken this invocation), `--budget` (cumulative
   inner tokens; stop if the last step's cost suggests the next would exceed the
   remaining budget), or `--plateau` (consecutive rejections) is reached.
   Otherwise run exactly one `/rsi:step` (its full propose→evaluate→verify→select
   procedure), appending its ledger line.

3. **Multi-seed evaluation and robust selection.** When `--seeds K > 1`, run the
   candidate's inner workflow K times with seeds `42, 43, …, 42+K-1`, scoring
   private each time. Aggregate for selection with the immutable helper:

   ```bash
   echo '{"tasks": {"<task>": {"seeds": [p1, p2, …]}, …}}' \
     | python3 plugins/rsi-loop/scripts/rsi-aggregate.py --aggregate
   ```

   Its `private_aggregate` (mean of per-task medians) is the selection statistic
   — robust to a single lucky or hacked seed. Record the full per-task seed
   vector in the ledger line under `scores.<task>.private_seeds` so the run is
   auditable. With `K == 1` this reduces to the single private score, exactly as
   `/rsi:step` does today.

4. **Checkpoint every step.** The ledger line and `best.txt` are the durable
   state; write them after each step so a crash or a scheduled-wakeup boundary
   loses at most the in-flight step (which re-runs cleanly on resume). Do not
   batch ledger writes to the end.

5. **Stop and report.** When a stop condition fires, print: steps run this
   invocation, accepted vs rejected counts, the incumbent generation and its
   private aggregate, cumulative inner tokens vs budget, and which condition
   stopped the run (`max-steps` | `budget` | `plateau`). Expect a high rejection
   rate — ~90% in the paper — and a plateau stop is a normal outcome, not a
   failure.

## Multi-day / unattended pacing

For runs longer than one session, drive `/rsi:run` from a scheduled wakeup
(`send_later` / a Routine) that re-invokes it on the same run dir: each wakeup
resumes from the ledger (step 1) and advances a few steps within the session's
budget. Because selection state lives entirely in `ledger.jsonl` + `best.txt`,
the run survives container recycling between wakeups.

Never edit the harness (`scripts/`, `tasks/`, scorers) during a run; the
immutability boundary is the anti-hack wall. Private paths and scores must never
reach an inner agent — the sandboxes carry no private split, and the deny hook
is the fast-feedback backstop.
