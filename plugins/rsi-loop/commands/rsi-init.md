---
description: Scaffold an rsi-loop run directory (generations, ledger, best pointer)
argument-hint: "[run-dir] [--tasks task1,task2,...]"
---

Initialize an AIDE²-style RSI run.

1. Resolve the run dir from "$ARGUMENTS" (default: `rsi-runs/run-<next-number>` in the
   session scratchpad unless the user names a path). Create:
   - `generations/gen-000/` — copy of `plugins/rsi-loop/baseline/gen-000`
   - `ledger.jsonl` — empty
   - `best.txt` — containing `generations/gen-000`
   - `tasks.txt` — one task dir per line (from `--tasks`, default: every dir under
     `plugins/rsi-loop/tasks/`)
2. Baseline the incumbent: for each task, evaluate gen-000 with the evaluation procedure in
   `rsi-step.md` steps 3–4 (sandbox → inner workflow → outer private scoring). Do NOT run the
   verifier (step 5) on the baseline — gen-000 is the plugin's own known-clean generation and
   becomes the incumbent unconditionally; record `"verifier": null`. Append a
   `{"step": 0, "generation": "gen-000", ...}` ledger line with its public/private scores.
   Skip this baseline only if the user passes `--no-baseline`.
3. Report the run dir, the tasks in the battery, and gen-000's baseline scores.

Ledger line schema (one JSON object per line, append-only). `rationale` and the per-task
`stress` sub-score are optional (present when the proposer/generation supply them); `verifier`
is `null` for the step-0 baseline and an object otherwise:
{"step": N, "generation": "gen-NNN", "parent": "gen-MMM" | null, "mutation": "...",
"rationale": "..." (optional), "scores": {"<task>": {"public": x, "private": y, "stress": z?}},
"private_aggregate": <mean of private scores>, "inner_tokens": N,
"verifier": {"verdict": "...", "findings": [...], "recommendation": "..."} | null,
"accepted": true|false, "reason": "..."}
