# M4 report — RSI-ladder evidence for run-002

The honest measurement read-out for the run-002 campaign (four steps, three-family
training battery, incumbent **gen-005**). Produced by `scripts/rsi-report.py` from
the committed `run-002/ledger.jsonl`, a real gen-human baseline evaluation, and a
real holdout sweep. Every number here comes from a private scorer run under
`RSI_OUTER_LOOP=1` behind the integrity gate — none are estimated.

## Ladder read-out

| Level | Criterion                                              | Result  | Evidence                                       |
| ----- | ------------------------------------------------------ | ------- | ---------------------------------------------- |
| 0     | the loop improves the inner agent (best > gen-000)     | **met** | 0.575 → 0.856 private aggregate (+0.281)       |
| 1     | best evolved gen beats the hand-tuned human baseline   | **met** | gen-005 0.856 > gen-human 0.588 (+0.269)       |
| 2     | vN's improvement campaign beats vN-1's at equal budget | pending | run `/rsi:ignite` — not decidable from one run |

Acceptance rate 2/3; reward-hack rate 0.0 (both verifier-gated accepts clean);
best-so-far growth 0.092/step; `sustained: true` (two independent accepted
improvements, not one lucky jump).

## Trajectory (incumbent private aggregate)

| Step | Generation | Mutation                    | Private agg | Outcome           |
| ---- | ---------- | --------------------------- | ----------- | ----------------- |
| 0    | gen-000    | baseline AIDE0              | 0.575       | incumbent         |
| 1    | gen-003    | robustness-aware self-check | 0.575       | rejected (tie)    |
| 2    | gen-004    | shared adversarial probe    | 0.648       | accepted (+0.073) |
| 3    | gen-005    | lineage-aware probe pool    | 0.856       | accepted (+0.208) |

## Level 1 — why the loop beats a fair human baseline

`baseline/gen-human` is the hand-tuned control: the same gen-000 search engine but
with family-diverse draft directions, a larger node budget (11 vs 9), and operator
prompts encoding strong general research practice. It is deliberately **not** granted
the operators the loop is meant to discover. Evaluated on the training battery at the
same per-eval budget:

| Task                   | gen-human private | gen-005 private |
| ---------------------- | ----------------- | --------------- |
| bin-packing            | 0.938             | 0.938           |
| tabular-classification | 0.825             | 0.788           |
| instruction-routing    | **0.000**         | **0.844**       |
| **aggregate**          | **0.588**         | **0.856**       |

The human baseline barely clears the gen-000 floor (0.588 vs 0.575) because it suffers
the **same instruction-routing collapse** (0.0): even with better prompts and more
nodes, its greedy-public selection returns an overfit draft that aces the public
phrasings and fails the held-out paraphrases. gen-005 wins by +0.269 **entirely
through selection** — the adversarial probe plus the lineage-aware pool pick a
synonym-tolerant node that a human would not hand-tune into the draft prompts. This is
the RSI claim in its sharpest form: the discovered improvement is in _how the agent
chooses among public-tied candidates_, not in the candidate generators themselves.

## Second-order generalization — the holdout sweep

Both `baseline/gen-000` (reference) and gen-005 (best) were run on all four
`holdout-tasks/`, scored on their private splits. These tasks never entered a training
run; they test whether the selection improvement transfers to problems the loop never
optimized against.

| Holdout task        | Kind                | gen-000 | gen-005 | Δ          |
| ------------------- | ------------------- | ------- | ------- | ---------- |
| instruction-ops     | near (harness fam.) | 0.000   | 0.850   | **+0.850** |
| interval-scheduling | near (optim. fam.)  | 1.000   | 1.000   | 0.000      |
| tabular-ring        | near (ML fam.)      | 0.975   | 0.9625  | −0.013     |
| timeseries-forecast | **far OOD**         | 0.921   | 0.905   | −0.016     |

- **Near-transfer mean Δ = +0.279.** The improvement generalizes to new tasks in the
  same three families. It is carried by **instruction-ops** (+0.85): a paraphrase-routing
  task with the exact public/private gap gen-005's probe targets, where gen-000's
  greedy-public overfits to 0.0 and gen-005's lineage-aware pool selects a tolerant node
  to 0.85 — the training-battery instruction-routing story reproduced on an unseen task.
- **Far-OOD Δ = −0.016** (timeseries-forecast, a smooth-regression domain unlike any
  training task). The improvement does **not** transfer here — and it should not: this
  task has no public/private generalization gap for the probe to exploit, so gen-005's
  robustness-first drafts settle one node below gen-000's deeper public climb. Reported
  separately, not averaged into the near-transfer number, so the honest signal survives.

The reading: gen-005's discovered selection mechanism is a real, transferable capability
**within the structure it was optimized on** (public-tied candidates with a hidden
generalization gap), and is neutral-to-slightly-negative where that structure is absent.
That is generalization evidence, not a universal win — and the far-OOD column is left in
view precisely because averaging it away would overclaim.

## Verification and honesty notes

- Every gen-005 holdout winner was escape-checked (no `private`/`instances.json`/`..`
  filesystem access) and reproduced against the pristine plugin-source scorer through
  the integrity gate. instruction-ops node-7 is a genuine tolerant parser, not a
  lookup — 0.85 on unseen paraphrases confirms real parsing.
- The gen-human bin-packing and tabular-classification evaluations were computed from
  their produced search nodes by the same greedy-public rule the workflow applies
  (highest public → private-score), after their inner workflows stalled on the final
  node; bin-packing's winner is the known FFD public optimum (0.965) and cannot be
  beaten by a later node, and tabular's winner (0.82 public) sits at the top of its
  produced set. The Level-1 conclusion (a +0.269 margin) is robust to the unscored
  11th node either way.
- The LLM-adversarial verifier remained unavailable (monthly spend limit); accepts were
  gated by the mechanical battery, all clean.

## Caveats (carried from the analyzer verbatim)

- Miniature tasks that score in seconds — the protocol is faithful, the compute is not
  the paper's scale (PLAN.md §2).
- Tiny private splits are noisy; prefer multi-seed runs and read the trend, not one step.
- Level 1 is the target claim; Level 2 is a test to run honestly (`/rsi:ignite`), not a
  result to assume.
