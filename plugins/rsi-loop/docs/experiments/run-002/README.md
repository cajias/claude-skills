# run-002 — M3 exit run (three-family battery)

The first RSI campaign on the full three-family battery (bin-packing +
tabular-classification + instruction-routing), from the AIDE0 baseline. Fixed
budget per evaluation (9 nodes, haiku, seed 42). Selection is on the robust
private aggregate; the inner agent never sees the private split. Full step
records in `ledger.jsonl`.

| Step | Generation | Mutation                            | bin-pack | tabular | instr-route | Private agg | Outcome               |
| ---- | ---------- | ----------------------------------- | -------- | ------- | ----------- | ----------- | --------------------- |
| 0    | gen-000    | baseline AIDE0                      | 0.938    | 0.788   | 0.000       | 0.575       | incumbent             |
| 1    | gen-003    | robustness-aware selection          | 0.938    | 0.788   | 0.000       | 0.575       | **rejected** (tie)    |
| 2    | gen-004    | shared adversarial robustness probe | 0.938    | 0.788   | **0.219**   | **0.648**   | **ACCEPTED** (+0.073) |
| 3    | gen-005    | lineage-aware probe pool            | 0.938    | 0.788   | **0.844**   | **0.856**   | **ACCEPTED** (+0.208) |

**M3 exit criterion** is a multi-step unattended run with a sane ledger; this
directory is that ledger as it accumulates.

## Step 3 — the pool fix lands the improve leaves (ACCEPTED)

Step 2 left a load-bearing follow-up: gen-004's `probe_topk=4` truncated the
probe candidate pool to the four earliest public-tied nodes — all early
_drafts_ — so the synonym-heavy _improve_ leaves that generalize best were never
probed and could never be selected. gen-005 keeps gen-004's working core (public
search, one shared hard battery, anti-saturation guard, near-public-tie band)
and refines **only the pool**: within the tie band it now always includes every
improve/explore-lineage leaf and scales a still-bounded cap (`probe_topk` 4 base,
`probe_topk_max` 8 ceiling) with the tie count, filling remaining slots with the
strongest drafts as brittle contrast.

The fix landed on the family it targeted:

- **instruction-routing**: the probe pool became `[0,1,5,6,7,8]` — drafts _and_
  improve leaves — with a real spread of 0.375 (drafts at 0.075, improve leaves
  climbing to 0.45). The loop returned the synonym-tolerant improve leaf node-8,
  lifting private **0.219 → 0.844** (+0.625). Verified a genuine 210-line
  tolerant parser (filler-phrase stripping, punctuation normalization, word
  ordinals, synonym sets) — not a lookup; 0.844 on _unseen_ paraphrases is real
  generalization, and no instance-level outlier fired.
- **bin-packing**: the improve leaves entered the pool but the battery correctly
  **saturated** (packing is inherently reorder-robust, all robustness 1.0); the
  guard fell back to deterministic top-public — FFD node-0 returned, private
  **0.938 held, no regression**.
- **tabular-classification**: the pool `[7,8,5,6]` spread 0.273 and returned the
  improve leaf node-8 (public 0.81 → 0.825), private **0.788 held**.

Net: private aggregate **0.856 > 0.648** (+0.208), the **largest single-step
gain in the run** and the **second accepted generation**. Steps 1–3 form a
sustained diagnose → repair → improve → repair-again arc: gen-004 fixed the
saturated instrument, gen-005 fixed the pool coverage that instrument fed on.
`best` now points to gen-005. Accept gated by the same **mechanical** verifier
battery (LLM verifier still unavailable) — all checks clean.

## Step 2 — the loop repairs its own instrument and improves (ACCEPTED)

Given the step-1 diagnosis (self-graded robustness saturates at 1.0), the step-2
proposer was directed to harden the instrument. gen-004 **decouples** the
perturbation generator from the solver: the tree search runs on clean public
score (so it never trades public away), then a single **shared adversarial
probe battery** — hard paraphrase/synonym/structural variants synthesised once
from the public inputs — is applied identically to the top-public candidates,
with an anti-saturation guard that treats a flat-1.0 result as a failed check.

The repair worked:

- **instruction-routing**: the probe produced a real spread across the four
  top-public candidates (node-0 0.052 → node-3 0.381) and returned the
  generalizing node-3 — lifting private **0.0 → 0.219**. Verified a genuine
  parser (the one hard-coding flag was an illustrative code comment; a lookup
  scores 0.0 on the unseen private paraphrases, node-3 scores 0.219).
- **bin-packing**: the probe saturated (packing is inherently reorder-robust),
  the guard flagged it and fell back to deterministic top-public — FFD returned,
  **no degradation** (0.938).
- **tabular-classification**: private held at 0.788 (public search recovered vs
  gen-003's degradation; the probe only re-orders genuine ties).

Net: private aggregate **0.648 > 0.575** (+0.073), so gen-004 is the **first
accepted generation on the three-family battery**. Steps 1–2 are a complete
diagnose → repair → improve arc — the core AIDE² self-improvement claim, on the
full battery. `best` now points to gen-004.

Verification note: the accept was gated by the verifier's **mechanical** checks
(reproduce vs the pristine scorer, git integrity on all three task dirs,
escape-residue, hard-coding audit, outlier) run locally — the LLM-adversarial
verifier subagent could not run because the account hit its **monthly spend
limit** mid-step (it also truncated gen-004's tabular probe-eval). All
mechanical checks were clean.

### Known follow-ups (for when compute resumes)

- `probe_topk=4` capped gen-004's probe pool to the first four public-tied
  nodes, excluding the synonym-heavy _improve_ nodes — node-6 (private **0.5**)
  and node-8 (0.469) would have won if probed. So the accepted 0.219 is real but
  leaves ~0.5 on the table; the next proposer should widen the probe pool or
  scale it with the number of public ties.
- The run is **paused at step 2 of a 10-step target** by the monthly spend
  limit — no further inner-agent compute can run until the limit is raised.

## Step 1 — a faithful rejection with a load-bearing diagnosis

gen-003's mutation (each node self-generates answer-preserving perturbations of
the _public_ inputs, measures a robustness fraction, and selects on
`public × robustness`) was well-aimed at the baseline's dominant weakness —
instruction-routing's public-1.0 / private-0.0 overfitting collapse. The
mechanism partly worked but the **selection instrument saturated**:

- On instruction-routing, every one of the 9 nodes self-reported robustness
  1.0 (they each tested only perturbations they already handle), so
  `combined = public × robustness` tied all nodes at 1.0 and the loop returned
  node-0 (a plain draft, private **0.0**). A synonym-aware node-7 — which added
  "sum/total/plus for add" handling aimed exactly at the private paraphrases —
  reached private **0.344** but tied on the combined score and was not selected.
  (Its solution is preserved here as `gen-003-instr-node7-synonym-aware.py`.)
- On tabular-classification the check _did_ discriminate: node-7's
  floating-point nondeterminism under row-shuffling scored robustness 0.8 and
  was correctly rejected in favor of node-8 (robustness 1.0). But node-8's
  public dropped to 0.83 (< gen-000's 0.85) and its private held at 0.788.
- On bin-packing the returned FFD draft matched the baseline exactly.

Net: the returned bests reproduced gen-000's per-task private scores exactly, so
the aggregate tied at 0.575 and the step was rejected. This is the run-001
tie-breaker-saturation failure in a new form: **an inner agent grading its own
robustness gives itself 1.0.** The diagnosis recorded in the ledger drives the
next proposal — the self-robustness instrument must be adversarial (harder,
held-out-style perturbations the node does not already pass), or diverse
high-public candidates must be handed to the outer private scorer rather than
collapsed by a saturated self-score.

## Faithfulness notes

- The outer loop scored each generation's **own returned best**, never a
  hand-picked better node — the generation's selection policy is exactly what is
  under evaluation, so returning node-0 (0.0) instead of node-7 (0.344) is
  gen-003's result to own, not something the harness corrects.
- Private scoring ran outer-side only (`RSI_OUTER_LOOP=1`); each score passed
  the git/manifest integrity gate before it was trusted.
- Per-task gen-000 baseline scores come from the M3 battery validation runs
  (`../m3-battery-validation.md`).
