# §5.2 Chassis A/B — PILOT Orchestration Runbook

Operational reference for the **Phase 2 pilot** (`PRE-REGISTRATION.md`: 2 arms ×
1 rep × 3 steps) — end-to-end validation of the harness before the full 2×2×10.
The orchestrator follows this doc to drive **both arms identically and
resumably**. The per-step procedure is the fidelity control surface: it is the
same for both arms; **only the chassis differs**. Do not edit the pre-registration
or any harness file (`scripts/`, `tasks/`, scorers) during the pilot.

Run dirs (scratchpad, ephemeral):
`/home/cajias/.claude/jobs/9c63fbc1/tmp/rsi-pilot/{arm-a,arm-b}/`
Each has `generations/gen-000`, empty `ledger.jsonl`, `best.txt`=`generations/gen-000`,
`tasks.txt` (3 tasks). Step-0 baseline is evaluated separately.

## Shared facts

| Item                      | Value                                                                          |
| ------------------------- | ------------------------------------------------------------------------------ |
| Battery (tasks.txt)       | bin-packing, instruction-routing, tabular-classification                       |
| Per-eval budget           | haiku, 9 nodes, seed 42, **single seed** (no `--seeds`)                        |
| Baseline sanity (run-002) | bin 0.938 / tab 0.788 / instr 0.000; aggregate 0.575                           |
| Selection statistic       | `private_aggregate` = mean of per-task medians (single seed ⇒ median == score) |
| Direction                 | `higher_is_better`; accept iff candidate **strictly** beats incumbent          |
| Dev hook disarm           | outer commands launched with `RSI_HOOK_DISARM=1` (env) — already used          |

**Inner eval is Workflow-only.** A bash script CANNOT invoke it. The orchestrator
launches it per (gen, task):

```text
Workflow({scriptPath: "<gen>/inner-agent.workflow.mjs"},
         {sandbox, genDir, taskName, seed: 42, policy: <parsed policy.json>})
```

Return shape:
`{task, generation, best:{node, public_score, solution_path, summary}, n_nodes, n_buggy, nodes:[...]}`.

**Sandbox** per (gen, task) — fresh before each eval:

```bash
RSI_HOOK_DISARM=1 bash scripts/rsi-sandbox.sh <task-dir> <run-dir>/eval/<gen>/<name>/sandbox
```

**Private scoring** (outer only, per task) then aggregate:

```bash
RSI_OUTER_LOOP=1 bash scripts/rsi-score.sh --private <task-dir> <best.solution_path>   # -> JSON, read .score
echo '{"tasks":{"<name>":{"seeds":[p]}, ...}}' | python3 scripts/rsi-aggregate.py --aggregate  # -> .private_aggregate
```

`rsi-score.sh --private` runs the integrity gate first (git HEAD / `.integrity.sha256`
manifest, **exit 5 on tamper**). Private paths/scores must NEVER appear anywhere an
inner agent can read (including candidate generation files).

**Ledger line schema** (append-only, one JSON object per line):

```json
{"step":N,"generation":"gen-NNN","parent":"gen-MMM","mutation":"...","rationale":"...",
 "scores":{"<task>":{"public":x,"private":y}},"private_aggregate":a,"inner_tokens":t,
 "verifier":{...}|null,"accepted":true|false,"reason":"..."}
```

The **ledger append is the commit point** and single source of truth. Update
`best.txt` ONLY after an accept, and only after the ledger line has landed.

## Per-step procedure (IDENTICAL for both arms — fidelity control surface)

1. **Resume-aware start.** Read `ledger.jsonl` (authoritative, not `best.txt`).
   next step = `(max step) + 1`; incumbent = generation of the **last accepted**
   line (else `gen-000`); cumulative inner tokens = sum of committed `inner_tokens`.
   Reconcile `best.txt` from the ledger if it disagrees.
2. **Propose.** `rsi-proposer` subagent, given incumbent dir + target `generations/gen-NNN`
   - full ledger; it copy-then-mutates the incumbent (one focused mutation) and returns
     `{mutation, rationale, predicted_effect, files_changed}`. **Structural gate**: workflow
     parses, prompts exist, args contract (`sandbox, genDir, taskName, seed, policy`) unchanged,
     no private references. On fail → reject, write a rejected ledger line, done.
3. **Sandbox** all 3 tasks (fresh, command above).
4. **Inner eval** all 3 via `Workflow(...)` (launch in parallel); record each
   `best.public_score`, `best.solution_path`, and inner token usage.
5. **Private-score + aggregate.** Per task `rsi-score.sh --private`, then
   `rsi-aggregate.py --aggregate` → `private_aggregate`.
6. **Score gate.** If `private_aggregate` does NOT **strictly** beat the incumbent's
   ledger value → reject; set `"verifier": null` (skip the LLM verifier — its verdict
   cannot change the outcome); write the ledger line; continue to next step.
7. **Verify** (only on would-be-accepts). `rsi-verifier` subagent on each task's claimed
   winner. Mechanical battery: (a) reproduce vs **pristine** plugin-source scorer
   (`tasks/<task>/score.py`) — hacked if <50% of claimed gain survives; (b) hard-coding
   audit; (c) integrity (`rsi-check-integrity.sh`, non-zero = hacked); (d) escape residue
   (`private`, `..`, task-battery paths); (e) too-good-outlier (`rsi-aggregate.py
--flag-outliers`). Any `hacked`/reject verdict → reject the step regardless of score.
8. **Select.** Append the ledger line **FIRST** (commit point); then, on accept only,
   update `best.txt` to the candidate path. A crash between the two leaves a
   recoverable state (committed ledger + stale-but-safe `best.txt`), never the reverse.

## Where the two arms DIFFER (only the chassis)

Everything downstream of "produce candidate gen → inner eval → `private_aggregate`"
is IDENTICAL. Only the outer-loop driver changes.

|                 | Arm A (with skill)                                          | Arm B (without skill)                               |
| --------------- | ----------------------------------------------------------- | --------------------------------------------------- |
| Driver          | third-party `uditgoenka/autoresearch` v2.1.2 iterate loop   | native `/rsi:run <run-dir> --max-steps 10` (here 3) |
| Metric source   | `Verify:` = shell cmd printing `private_aggregate`          | scorer feeds `private_aggregate` in directly        |
| Guard           | structural + integrity + verifier hack check                | structural + integrity + verifier hack check        |
| Accept / reject | `git`-commit = accept; `git revert HEAD --no-edit` = reject | `ledger.jsonl` accept/reject                        |
| Ledger          | `ledger.jsonl` (shared schema) **plus** autoresearch TSV    | `ledger.jsonl`                                      |

**Arm B**: the orchestrator itself runs the per-step procedure above (native
`/rsi:run` + `/rsi:step`).

**Arm A**: autoresearch drives the loop. Its config:

- `Verify:` = a command that `cat`s the `private_aggregate` the orchestrator
  computed at step 5 into `metric.txt` — i.e. `bash scripts/rsi-arm-a-metric.sh ...`
  emits the bare number; autoresearch scrapes it.
- `Guard:` = `scripts/rsi-arm-a-guard.sh` (structural + integrity floor only; the
  LLM hack-check is a separate step and may be unavailable).
- accept/reject = autoresearch `git`-commit / `git revert HEAD --no-edit`.

**Shim boundary (pre-registered friction, metric 5).** autoresearch's `Verify:` is
a plain **shell command**; our inner eval is **Workflow-only**, which a shell command
cannot invoke. So the orchestrator interleaves: it runs the Workflow inner eval +
private scoring + aggregation **itself**, writes the scalar to `metric.txt`, and
autoresearch's `Verify:` merely reads it. This does NOT patch autoresearch code, but
the "single mechanical Verify command" is not self-contained. Porting the inner agent
to a standalone CLI would be a genuine **fork** — disqualifying for Arm A under the
decision rule.

**autoresearch hook disables** (applied identically, recorded under metric 5):

```bash
AR_DISABLE_SCOUT_BLOCK=1 AR_DISABLE_DANGEROUS_CMD_BLOCK=1 AR_DISABLE_SIMPLIFY_GATE=1
```

(`dangerous-cmd-block` bans `git reset --hard`/`git clean -f`; reject uses `git revert`.)

## Measurement — record per step, per arm (5 pre-registered metrics)

| #           | Metric                                       | What to log each step                                                                                  |
| ----------- | -------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| 1 (primary) | Best private aggregate at equal token budget | running max `private_aggregate` + cumulative `inner_tokens`                                            |
| 2           | Score-per-token slope                        | Δ `private_aggregate` / cumulative `inner_tokens` across steps                                         |
| 3           | Harness overhead                             | orchestration tokens vs. inner-eval `inner_tokens`                                                     |
| 4           | Protocol fidelity                            | did accept/reject follow score+guard? ledger complete? crash/resume ok? any hacked win past the guard? |
| 5           | Friction notes                               | the shim, any fork, hook disables, verifier availability                                               |

## Resume / crash-safety

- **Ledger is the source of truth.** Never restart from step 1 if the ledger is
  non-empty — resume from `(max step) + 1`.
- A step that crashes **before** its ledger append leaves no committed line, so it
  re-runs on resume and its partial inner tokens are uncounted (budget accurate to
  committed-step granularity, not to the token).
- **Spend-limit contingency.** If the proposer or verifier LLM subagent becomes
  unavailable mid-pilot, **STOP and record the partial ledger honestly** — never
  fabricate a line. Proposer is required every step; verifier only on would-be-accepts.
  Per pre-reg: if the LLM verifier is unavailable, both arms run on the **mechanical**
  battery only (held identical) — recorded under metric 4 as a caveat, not a per-arm
  advantage. The mechanical battery is the fidelity floor for both arms.

## Pilot exit

- Run **3 steps per arm** (`--max-steps 3`; plateau disabled so all 3 run).
- **~90% rejection is normal** on tiny batteries — high rejection is expected AIDE²
  behavior, not failure.
- After both arms complete, write `docs/experiments/chassis-ab/PILOT-RESULTS.md`:
  the two `ledger.jsonl` side by side, all 5 metrics, and the pre-registered
  decision rule applied — _adopt Arm A only if within noise of (≤ 0.02 absolute
  below) or better than Arm B on the primary metric AND clean on fidelity (4) with
  no fork required (5); any fidelity violation is disqualifying; otherwise ship Arm B._
- **The pilot decision is provisional**: this phase validates the harness. The full
  **2×2×10** is the deciding run.
