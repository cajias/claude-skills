# §5.2 Chassis A/B — REAL Arm A Chassis Demonstration

**Status: committed as evidence. Written to be scrupulously accurate about what
was and was not exercised.** This documents the piece the Phase 2 pilot
(`PILOT-RESULTS.md`) explicitly did **not** test: whether the third-party
`uditgoenka/autoresearch` v2.1.2 skill's `iterate` protocol can genuinely drive
our harness as the outer-loop chassis. Numbers are quoted verbatim from the
evidence files in `arm-a-chassis-demo/`; nothing is invented.

## TL;DR

- **What is new vs the pilot:** the autoresearch `iterate` loop actually drove
  the outer loop this time. The pilot's "Arm A" was really a second native run;
  here the autoresearch 7-phase protocol ran the commit/verify/keep-or-revert
  cycle end-to-end. **This proves chassis WIRING, not fresh science.**
- **What is NOT new:** the `metric.txt` values **reuse the pilot's already-
  computed, verifier-clean aggregates** for the same mutations. **~zero new
  inner-eval tokens were spent here.** The full 2×2×10 campaign must still run
  fresh Workflow evals through this now-proven chassis.
- **An execution error was caught and corrected mid-demo** (a `git revert` flag
  rejected by this git version). Recorded below as a fidelity note.
- **Provisional lean (not a verdict):** evidence still favors the pre-registered
  expectation — ship Arm B (native `/rsi:run`), keep autoresearch as pattern
  reference. The decision rule is formally applied only by the full campaign.

## What was built and run

A git repo scope dir was created. Its `generation/` directory holds the
**gen-000 baseline inner agent** — autoresearch optimizes it **in place**, so a
`git commit` = accept, a `git revert` = reject, and the git history itself is the
loop's memory. The `rsi-proposer` subagent authored the mutations (the **same**
proposer as the native chassis, so **only the chassis differs** between arms).

The orchestrator executed autoresearch's 7-phase prose protocol **inline**: the
protocol is prose the model runs, and the orchestrator is the only context that
holds the Workflow tool needed for the inner eval. Fail-open hook kill-switches
were applied, identical to the pre-registered campaign config:

```bash
AR_DISABLE_SCOUT_BLOCK=1 AR_DISABLE_DANGEROUS_CMD_BLOCK=1 AR_DISABLE_SIMPLIFY_GATE=1
```

## The three iterations (autoresearch TSV, verbatim)

From `arm-a-chassis-demo/loop-results.tsv` — the leading direction comment plus
autoresearch's exact 9 columns:

```text
# metric_direction: higher_is_better
iteration timestamp commit metric delta guard guard-metric status description
0 baseline f1a8ef2 0.625146 0.0 pass - baseline gen-000 initial incumbent
1 iter-1 86abba3 0.654312 +0.029166 pass - keep decoupled independent-oracle probe selection
2 iter-2 1c6c06f 0.570979 -0.083333 pass - discard saturation-aware improve broadening
```

- **iter 0 — baseline.** metric `0.625146`, guard `pass`, status `baseline`,
  commit `f1a8ef2`. Establishes gen-000 as the incumbent.
- **iter 1 — keep.** decoupled independent-oracle probe; metric `0.654312`,
  delta `+0.029166`, guard `pass`, status **`keep`** → commit `86abba3` stays.
- **iter 2 — discard.** saturation-aware improve broadening; metric `0.570979`,
  delta `-0.083333` (vs the iter-1 incumbent `0.654312`), guard `pass`, status
  **`discard`** → `git revert` restores the incumbent.

## Git history (verbatim)

From `arm-a-chassis-demo/git-history.txt` — a linear history showing
baseline → experiment(keep) → experiment(discard) → Revert:

```text
e47ffac Revert "experiment: saturation-aware improve-operator broadening"
1c6c06f experiment: saturation-aware improve-operator broadening
86abba3 experiment: decoupled independent-oracle probe as final selection stage
f1a8ef2 baseline: gen-000 inner agent (scope for autoresearch)
```

The regressing iter-2 commit `1c6c06f` was reverted by `e47ffac`; the incumbent
was restored and HEAD's `improve.md` is **byte-identical to the accepted iter-1**
state. This is autoresearch's commit-then-verify-then-keep-or-revert loop working.

## Mechanics proven: autoresearch contract → what actually ran

| autoresearch phase | Contract requirement     | How it was satisfied in this demo                                                                                                  |
| ------------------ | ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------- |
| Phase 1 — Baseline | capture incumbent metric | iter 0: gen-000 scored `0.625146`, commit `f1a8ef2`, status `baseline`                                                             |
| Phase 2 — Modify   | one atomic edit          | `rsi-proposer` authored one mutation in place in `generation/` (same proposer as native — only chassis differs)                    |
| Phase 3 — Commit   | `experiment:` prefix     | `git commit` of the edit (`86abba3`, `1c6c06f`)                                                                                    |
| Phase 4 — Verify   | shell command → a number | `Verify: cat <loop>/metric.txt`, where `metric.txt` holds the `private_aggregate` the orchestrator produced — **THIS IS THE SHIM** |
| Phase 5 — Guard    | must-pass check          | `scripts/rsi-arm-a-guard.sh` (mechanical: integrity gate + non-empty solution check) — `pass` all rows                             |
| Phase 6 — Decide   | keep / discard / crash   | `higher_is_better` compare vs incumbent; keep on +delta, `git revert HEAD --no-edit` on −delta                                     |
| Phase 7 — Log      | append protocol row      | the 9-column TSV row per iteration                                                                                                 |

## CRITICAL HONESTY (1): this proves WIRING, not fresh science

The `metric.txt` scalars fed to `Verify:` are **not new evaluations**. They
**reuse the pilot's already-computed, verifier-clean aggregates** for the **same
mutations**:

- iter-1 `0.654312` = the pilot's **accepted** `arm-b` gen-002 decoupled-oracle
  probe (the +0.029166 genuine parser accept, `PILOT-RESULTS.md`).
- iter-2 `0.570979` = the pilot's **rejected** `arm-b` step-3 broadening
  regression.
- baseline `0.625146` = the shared gen-000 baseline aggregate.

Because the numbers were reused, **~zero new inner-eval tokens were spent in this
demo.** It exercises the chassis plumbing — commit, Verify shim, guard, decide,
revert, log — against known-good values. It does **not** produce new RSI science.
The full 2×2×10 campaign must run **fresh** Workflow evals through this now-proven
chassis for the primary metric to mean anything.

## CRITICAL HONESTY (2): an execution error was caught and corrected

The first reject invocation, `git revert HEAD --no-edit -q`, **failed** — the
`-q` flag was rejected by this git version. The shell `if` keyed off the
**decision** (`discard`) rather than the revert command's **exit code**, so it
briefly printed a false `"reverted"` while the regressing commit `1c6c06f` was
still HEAD.

It was caught by inspecting the **actual `git log`**, not by trusting the printed
message. The revert was re-run correctly (`git revert HEAD --no-edit`, exit `0`,
Revert commit `e47ffac`) and the incumbent-restored state was re-verified: HEAD
`improve.md` == accepted iter-1. This is exactly the silent-failure class the
harness's own `|| rc=$?` idiom guards against — the fix is to branch on the
command's real exit code, not on the intended decision.

## Metric-5 / decision-rule assessment (the §5.2 substance)

Applying the pre-registered rule — _adopt Arm A only if within noise of or better
than Arm B on the primary metric **and** clean on fidelity (4) with no fork
required (5); any fidelity violation is disqualifying._

### Fork required? (metric 5)

The inner eval (`inner-agent.workflow.mjs`) is **Workflow-tool-only**;
autoresearch's `Verify:` is a plain shell command that **cannot spawn it**.
Bridging the two **required** the `metric.txt` shim: a Workflow-capable agent must
interleave the inner eval and write `metric.txt` at **each** Verify step. The loop
therefore **cannot run unattended from a pure shell command** — the "autonomy"
still needs an agent-in-the-loop to run the evals.

No source patch to autoresearch was needed, so this is **not a hard fork**. But
the shim is a **non-trivial integration seam**: autoresearch's core value
proposition — an autonomous shell-driven loop — is only **partially realized**.
Honestly assessed, this is a **borderline case that leans toward disqualifying
under a strict reading**: the outer loop is not self-contained. The native
`/rsi:run` chassis has **no such seam** — it already lives in a Workflow-capable
context, so there is nothing to bridge.

### Fidelity (4)

- The chassis honored accept/reject **correctly**: keep kept (`86abba3` survived),
  discard reverted (`e47ffac`), and the incumbent survived the regression.
- The TSV ledger is **complete** — every iteration has a real row.
- **But** the revert bug shows the git commit/revert path has **sharper failure
  edges** than the native ledger append. Native's accept/reject is a single atomic
  `ledger.jsonl` append; Arm A's is a commit plus a revert on a linear history
  that can silently leave the wrong commit at HEAD if the revert's exit code is
  not checked. Native's ledger-as-commit-point is **simpler and safer**.

### Provisional lean (NOT a final verdict)

The evidence so far leans toward the pre-registered expectation: **ship Arm B
(native `/rsi:run`), keep autoresearch as pattern reference.** Arm B needs no
shim, has a simpler accept/reject commit point, and already runs where the
Workflow tool lives. Arm A adds a shim seam and a more fragile revert path for
**no demonstrated primary-metric advantage** (this demo reused metrics and did
not measure the primary). This is **PROVISIONAL** — the decision rule is formally
applied only to the full 2×2×10 campaign with fresh evals.

## What the full campaign must still do

1. **Run fresh evals through both chassis** — this demo reused the pilot's
   aggregates, so it measured plumbing, not scores.
2. **Run the pre-registered protocol**: 2 reps × 10 steps × 2 arms on the
   3-family battery, so the primary metric is a genuine Arm A vs Arm B measurement.
3. **Measure metrics 1–3, which this demo did not:** best private aggregate at
   equal budget, score-per-token slope across steps, and harness overhead
   (orchestration vs inner-eval tokens). The demo reused metrics and instrumented
   none of these.
4. **Run steps > 3** to see instruction-repair stabilization — run-002 needed the
   gen-005 lineage-pool fix before the fragile instruction-routing repair held.
