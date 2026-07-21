# §5.2 Chassis A/B — Pre-Registration

**Status: LOCKED before compute (Phase 0). No eval token has been spent.** Every
result cell below reads `not yet run`. This document must not be edited post-hoc
except in an explicit, dated **Deviations** section at the end.

This is an **engineering** decision — which outer-loop driver to ship as
`/rsi:step`'s chassis — **not a new scientific claim** (PLAN.md §5.2;
CONTINUATION.md:44-45: "An engineering decision, not a new scientific claim;
apply the pre-registered decision rule"). The point of locking it now is that the
outer loop is the experiment's control surface: if we choose it after seeing
scores we cannot later claim the protocol was neutral.

## Arms

Everything else is held identical across arms: `baseline/gen-000` starting point,
the 3-family battery, proposer + verifier prompts **and** models, per-eval token
budget, and seed. Only the outer-loop driver differs.

|                 | Arm A (with skill)                                                                    | Arm B (without skill)                                       |
| --------------- | ------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| Driver          | third-party `uditgoenka/autoresearch` v2.1.2 (on-disk contract version 2.1.0)         | native `/rsi:run <run-dir> --max-steps 10`                  |
| Metric source   | its `Verify:` shell command prints our `private_aggregate` as a bare number on stdout | our scorer feeds `private_aggregate` into the loop directly |
| Guard           | structural + integrity + verifier hack check                                          | structural + integrity + verifier hack check                |
| Accept / reject | its `git`-commit = accept; `git revert HEAD --no-edit` = reject                       | `ledger.jsonl` accept/reject                                |
| Ledger          | writes `ledger.jsonl` (shared schema) **plus** its own TSV                            | `ledger.jsonl`                                              |

## Protocol

- **2 arms × 2 reps × 10 outer steps** on the 3-family battery (bin-packing +
  tabular-classification + instruction-routing) = **4 campaigns**.
- Per-eval budget: **haiku, 9 nodes, seed 42**. Multi-seed via `--seeds` is **NOT**
  used for the chassis comparison — single seed 42, matching run-002.
- Both arms write the **same** `ledger.jsonl` schema so runs are directly comparable.
- Estimated total **≈ 20M+ tokens / ~20h** (≈ 1.5–1.7M inner tokens per step).
- Resume-aware pacing: `ledger.jsonl` + `best.txt` are the durable state; drive
  multi-hour runs via scheduled wakeups re-invoking the arm on the same run dir
  (resume from ledger + best.txt), never a single blocking session.

## Metrics (pre-registered, priority order)

Quoted from PLAN.md §5.2 (lines 318–325):

1. **Primary**: best private aggregate score reached at equal total token budget.
2. Score-per-token slope across steps (efficiency of the loop itself).
3. Harness overhead: tokens spent on orchestration vs. on inner-agent evaluation.
4. Protocol fidelity: did accept/reject always follow private score + guard? any
   hacked win slipping past the guard? ledger completeness; crash/resume behavior
   mid-run.
5. Friction notes: forks/patches needed, multi-task score plumbing, verifier
   integration.

## Decision rule (verbatim, PLAN.md §5.2 lines 327–332)

> adopt Arm A only if it is within noise of or better than Arm B on the primary
> metric **and** clean on fidelity (4) with no fork required (5). Any fidelity
> violation is disqualifying regardless of score — the outer loop is the
> experiment's control surface and must be exactly the paper's protocol.
> Otherwise ship Arm B and keep autoresearch as pattern reference. Either way the
> losing arm's run stays in the repo under `docs/experiments/` as evidence.

## "Within noise" — operational definition (pre-registered)

With only 2 reps per arm we **cannot** compute a real confidence interval. We
therefore pre-register a conservative rule instead of deciding it after seeing
scores:

> Arm A is **within noise of** Arm B on the primary metric if the difference in
> best `private_aggregate` (max over the 2 reps of each arm) is **≤ 0.02
> absolute**. If Arm A is more than 0.02 **below** Arm B, Arm A **loses** on the
> primary metric.

Calibration: 0.02 is roughly one instruction-routing tie-break's worth of
aggregate movement. run-002 single-step gains ranged **0.073–0.208**, so 0.02 is
well inside a single meaningful step. This threshold is a **judgment call locked
in advance, not a statistical CI** — stated plainly so it cannot be reinterpreted
once results exist.

## Known architectural friction, pre-declared

Declared **now, before results**, so it cannot later read as post-hoc
rationalization.

- autoresearch's `Verify:` is a **shell command** that prints a number. Our inner
  eval (`inner-agent.workflow.mjs`) runs **only** via the Workflow / `agent()`
  runtime (an agent tool), which a plain shell command cannot invoke.
- **Chosen bridge (a shim):** the agent running the autoresearch loop performs the
  Workflow inner eval + private scoring + aggregation **itself** at the Verify
  step and writes the scalar to `metric.txt`; autoresearch's `Verify:` is then
  `cat metric.txt`. This does **not** patch autoresearch's code, but it does mean
  the "single mechanical Verify command" is **not truly self-contained** — the
  loop cannot run unattended purely from a shell command.
- This shim **counts as friction under metric 5** and is recorded there. The
  alternative — porting the inner agent to a standalone CLI a shell `Verify:`
  could call — would be a **genuine fork of our harness**, which the decision rule
  treats as **disqualifying for Arm A**.
- **Honest a priori expectation:** given the fork/shim friction, the likely
  outcome is **"ship Arm B, keep autoresearch as pattern reference."** We run the
  pilot + campaign anyway to produce **real evidence**, not to confirm a foregone
  conclusion. If Arm A surprises us — within noise on primary **and** clean
  fidelity **and** the shim is judged not to rise to "fork" — we adopt it.

## Verifier-availability contingency

run-002 hit the monthly spend limit and its LLM-adversarial verifier subagent
could not run; steps 2–3 were gated by the **mechanical** verifier battery only
(reproduce vs pristine scorer, git integrity, escape-residue, hard-coding audit,
too-good-outlier).

Pre-register: **if the LLM verifier is unavailable during the campaign, both arms
run on mechanical checks only (held identical)**, and this is recorded under
metric 4 as a **caveat, not a per-arm advantage**. The mechanical battery is the
**fidelity floor** for both arms.

## Reward-hack / faithfulness guards (held identical across arms)

- Private scoring is **outer-side only**, via
  `RSI_OUTER_LOOP=1 bash scripts/rsi-score.sh --private`.
- **Integrity gate** before any trusted private score: git HEAD / `.integrity.sha256`
  manifest, **exit 5 on tamper**.
- Each arm scores its **own returned best**, never a hand-picked node.
- **No fabricated ledger lines** — every line comes from real Workflow compute or
  is clearly marked not-yet-run.

## Execution plan / phasing

The user chose **"pilot after scaffolding."**

| Phase        | Scope                                                                     | Compute              |
| ------------ | ------------------------------------------------------------------------- | -------------------- |
| 0 (this doc) | Pre-registration                                                          | none                 |
| 1            | Build + verify Arm A metric adapter / shim; dry-run against cached scores | none (no inner eval) |
| 2            | Pilot = 2 arms × 1 rep × ~3 steps to validate the harness end-to-end      | a few M tokens       |
| 3            | Full 2×2×10 — **only after** the pilot validates                          | ≈ 20M+ tokens        |

## Ledger-schema mapping (Arm A autoresearch TSV → our `ledger.jsonl`)

autoresearch writes to `autoresearch/loop-{YYMMDD}-{HHMM}/*-results.tsv`. Its
core-loop TSV has a leading comment line `# metric_direction: higher_is_better`
then **9 columns** (verbatim):

`iteration, timestamp, commit, metric, delta, guard, guard-metric, status, description`

`status` enum: `baseline, keep, keep (reworked), discard, crash, no-op, hook-blocked, metric-error`.

| autoresearch TSV                                | our `ledger.jsonl`  |
| ----------------------------------------------- | ------------------- |
| `iteration`                                     | `step`              |
| `metric`                                        | `private_aggregate` |
| `commit`                                        | generation SHA      |
| `status` = `keep`                               | `accepted`          |
| `status` = `discard` / `crash` / `metric-error` | `rejected`          |
| direction                                       | `higher_is_better`  |

We additionally emit our own `ledger.jsonl` line per step for Arm A so both arms
are directly comparable regardless of the TSV.

## autoresearch hook note (operational)

Its plugin hooks are **fail-open** with per-hook kill switches
(`AR_DISABLE_<HOOKNAME>=1`). Defensive disables applied **identically** for the
campaign and recorded here:

```bash
AR_DISABLE_SCOUT_BLOCK=1 AR_DISABLE_DANGEROUS_CMD_BLOCK=1 AR_DISABLE_SIMPLIFY_GATE=1
```

- `scout-block` could block our `bash scripts/...` path token if the repo
  `.ckignore` denies `scripts/`.
- `dangerous-cmd-block` bans `git reset --hard` / `git clean -f` — our
  accept/reject must use **`git revert`**, not reset.
- Bash is **warn-only** under privacy-block, so `--private` is not blocked there.

## Results

All cells **not yet run** — this is a protocol lock, populated only by real
Workflow compute.

| Campaign | Arm | Rep | Steps | Best private_aggregate | Score/token slope | Harness overhead | Fidelity    | Outcome     |
| -------- | --- | --- | ----- | ---------------------- | ----------------- | ---------------- | ----------- | ----------- |
| 1        | A   | 1   | 10    | not yet run            | not yet run       | not yet run      | not yet run | not yet run |
| 2        | A   | 2   | 10    | not yet run            | not yet run       | not yet run      | not yet run | not yet run |
| 3        | B   | 1   | 10    | not yet run            | not yet run       | not yet run      | not yet run | not yet run |
| 4        | B   | 2   | 10    | not yet run            | not yet run       | not yet run      | not yet run | not yet run |

## Deviations

_None. Append dated entries here if the locked protocol changes after Phase 0._
