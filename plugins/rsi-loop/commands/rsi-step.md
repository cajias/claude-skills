---
description: Run one AIDE²-style outer-loop step (propose → evaluate → verify → select)
argument-hint: "<run-dir> [n-steps]"
---

Execute outer-loop steps on the run in "$ARGUMENTS" (default 1 step). You are the outer
agent; inner agents are cheap models launched via the generation's Workflow script.

Per step N:

1. Read `best.txt` (incumbent) and the full `ledger.jsonl`.
2. **Propose**: spawn the `rsi-proposer` agent with the incumbent dir, target dir
   `generations/gen-NNN` (next number), and the ledger contents. It writes the candidate
   generation and returns `{mutation, rationale, predicted_effect}`.
   Gate: the candidate must still pass structural checks (workflow script parses, prompts
   exist, args contract unchanged). On failure, record a rejected ledger line and stop.
3. **Evaluate** on every task in `tasks.txt`:
   a. Fresh sandbox: `bash plugins/rsi-loop/scripts/rsi-sandbox.sh <task-dir> <run-dir>/eval/gen-NNN/<task>/sandbox`
   b. Launch `Workflow({scriptPath: "<candidate>/inner-agent.workflow.mjs", args: {sandbox,
      genDir: <candidate>, taskName, seed: 42, policy: <parsed policy.json>}})` and await it.
      Record its best public score and inner token usage.
4. **Private scoring** (outer context only): for each task,
   `RSI_OUTER_LOOP=1 bash plugins/rsi-loop/scripts/rsi-score.sh --private <task-dir> <best-solution>`.
   `private_aggregate` = mean private score across tasks.
5. **Verify**: spawn the `rsi-verifier` agent on each task's claimed winner. Any `hacked`
   verdict ⇒ the step is rejected regardless of scores.
6. **Select**: accept iff `private_aggregate` strictly beats the incumbent's ledger value and
   the verifier allows it. On accept, write the candidate path into `best.txt`. Either way,
   append the full ledger line (schema in `rsi-init.md`) — rejected generations stay on disk.
7. Tell the user: step number, mutation, scores vs. incumbent, verifier verdict,
   accepted/rejected. Expect most steps to be rejections; that is normal AIDE² behavior, not
   failure.

Never edit the harness (`scripts/`, `tasks/`, scorers) during a run. Private paths and scores
must never appear in anything an inner agent can read — including the candidate generation's
files; if the proposer leaked private references into prompts, reject the step at the gate.
