---
description: Run one AIDE²-style outer-loop step (propose → evaluate → verify → select)
argument-hint: "<run-dir> [n-steps]"
---

Execute outer-loop steps on the run in "$ARGUMENTS" (default 1 step). You are the outer
agent; inner agents are cheap models launched via the generation's Workflow script.

Per step N:

1. Read `best.txt` (incumbent) and the full `ledger.jsonl`.
2. **Propose**: spawn the `rsi-proposer` agent with the incumbent dir, target dir
   `generations/gen-NNN` (next number), and the ledger contents. If the run dir contains
   `ignite/strategy-brief.md` (an ignited-arm run created by `/rsi:ignite`), prepend that
   brief to the proposer prompt so its rewrites follow the evolved strategy; otherwise omit it
   (stock proposer). It writes the candidate generation and returns
   `{mutation, rationale, predicted_effect}`.
   Gate: the candidate must still pass structural checks (workflow script parses, prompts
   exist, args contract unchanged). On failure, record a rejected ledger line and stop.
3. **Evaluate** on every task in `tasks.txt`:
   a. Fresh sandbox: `bash plugins/rsi-loop/scripts/rsi-sandbox.sh <task-dir> <run-dir>/eval/gen-NNN/<task>/sandbox`
   b. Launch `Workflow({scriptPath: "<candidate>/inner-agent.workflow.mjs", args: {sandbox,
genDir: <candidate>, taskName, seed: 42, policy: <parsed policy.json>}})` and await it.
   Record its best public score and inner token usage.
4. **Private scoring** (outer context only): for each task,
   `RSI_OUTER_LOOP=1 bash plugins/rsi-loop/scripts/rsi-score.sh --private <task-dir> <best-solution>`.
   Compute `private_aggregate` with the immutable helper so the statistic is
   robust and auditable — pass one seed's score per task (single-step default) or
   the full seed vector under `/rsi:run --seeds K`:
   `echo '{"tasks": {"<task>": {"seeds": [p, …]}, …}}' | python3 plugins/rsi-loop/scripts/rsi-aggregate.py --aggregate`.
   Its `private_aggregate` (mean of per-task medians) is the selection statistic;
   with a single seed it equals the mean private score across tasks.
5. **Score gate**: if `private_aggregate` does NOT strictly beat the incumbent's ledger value,
   the step is a rejection — skip the verifier (its verdict cannot change the outcome and each
   run is a full LLM subagent), record `"verifier": null`, and go to step 7. Only when the
   candidate would otherwise be accepted do you continue to step 6.
6. **Verify**: spawn the `rsi-verifier` agent on each task's claimed winner. It re-scores
   against the pristine plugin-source scorer and runs
   `scripts/rsi-check-integrity.sh <task-dir>` (which `rsi-score.sh --private` already
   enforced in step 4). It also feeds the winner's per-instance private scores to
   `python3 plugins/rsi-loop/scripts/rsi-aggregate.py --flag-outliers`; a flagged
   too-good instance is refutation evidence to explain mechanically or reject. Any
   `hacked` verdict — including a tampered-harness integrity failure — ⇒ the step is
   rejected regardless of scores.
7. **Select**: accept iff the candidate passed the score gate (step 5) AND the verifier is
   clean. **Append the full ledger line FIRST** (schema in `rsi-init.md`) — the ledger append
   is the commit point and the single source of truth. Only after it lands, on accept, update
   `best.txt` to the candidate path. `best.txt` is a derived cache of "the generation of the
   last accepted ledger line"; ordering the writes this way means a crash between them leaves a
   recoverable state (a committed ledger with a stale-but-safe `best.txt`), never a `best.txt`
   promoted to a generation that has no ledger line. Rejected generations stay on disk.
8. Tell the user: step number, mutation, scores vs. incumbent, verifier verdict (or "not run —
   rejected on score"), accepted/rejected. Expect most steps to be rejections; that is normal
   AIDE² behavior, not failure.

Never edit the harness (`scripts/`, `tasks/`, scorers) during a run. Private paths and scores
must never appear in anything an inner agent can read — including the candidate generation's
files; if the proposer leaked private references into prompts, reject the step at the gate.
