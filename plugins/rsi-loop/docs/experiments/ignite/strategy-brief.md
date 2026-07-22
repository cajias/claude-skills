# Ignited proposer brief — discovered strategy of run-002 incumbent (gen-006)

Propose in the idiom the source run evolved, not the stock AIDE0 idiom. The
incumbent lineage gen-000 → gen-004 → gen-005 → gen-006 converged on one core
mechanism: **public search first, then break public-score ties with a shared,
deliberately-hard adversarial robustness probe.** Keep that spine; mutate within
it.

## Operators to keep and how to brief each

- **draft** (5 drafts, distinct `draft_directions`): each draft commits fully to
  its assigned direction (simplest-correct, sorting/preprocessing heuristic,
  incremental best-choice, deterministic local search, and a **robustness-first**
  direction that parses/normalizes input tolerantly). Context: `task.md` contract
  - scoring formula + its one assigned direction + the anti-overfitting warning
    (never hard-code instances; held-out data restates the same intent in different
    surface forms). Do not let siblings hedge toward a generic approach.
- **improve**: operates on the best-by-public node. Context: that node's code,
  its public score, and the **full history of what was already tried, including
  failed improvements** (do not repeat them). One idea per node. When public
  score has headroom → one concrete algorithmic gain; when public is saturated →
  spend the node on **generalization** (tolerant parsing/normalization) because
  that is exactly what the tiebreak rewards.
- **debug**: repair a broken/invalid candidate back to a valid solution; a valid
  mediocre score beats an invalid 0.
- **adversarial probe = two stages, built purely from public data (never sees any
  solution):**
  - _probe-battery builder_ — build ONE shared, hard, equivalence-preserving
    battery strong enough to separate a brittle solution from a generalizing one.
  - _probe evaluator_ — run every tied candidate against that same shared battery
    and report `adversarial_robustness = variants_consistent / variants_total`.

## Selection rule (this is the load-bearing invention — preserve it)

1. Rank by public score. Candidates within `public_tie_band` (0.05) of the top
   are a tie set.
2. Build the tie set as a **pool that GUARANTEES the improve/explore-lineage
   leaves**, not just the top-public drafts (gen-005's fix: `probe_topk` 4 grows
   to `probe_topk_max` 8, scaling with the tie count, bounded). Include the
   strongest drafts too, as brittle contrast.
3. Break the tie with the shared adversarial probe; return the most robust
   candidate. **If the probe saturates (no real spread, `min_spread` 0.1), fall
   back to the top-public node** — never manufacture a distinction that isn't
   there.

## Modality-aware probe (gen-006's accepted gain — keep it modality-routed)

The battery builder auto-detects modality from `task.md` + public input shape:

- **numeric-tabular** → data-perturbation battery (train bootstrap/subsample,
  within-scale feature jitter, noise-feature-column permute, single-feature
  holdout), scored by **test-row prediction stability vs the candidate's
  unperturbed-train baseline** (≥95% label agreement = consistent). An overfit
  model swings and scores low; a regularized one holds.
- **language** → paraphrase/synonym/re-template battery scored by answer
  equivalence.

## Hard-won lineage lessons (do not rediscover; mutate beyond these)

- **gen-004**: a _hardened, shared_ probe instrument (replacing per-node
  self-checks) is what produces real spread — on instruction-routing it separated
  node-0 (private 0.0) from a generalizing node, lifting private 0.0 → 0.219.
- **gen-006**: the modality-aware data-perturbation probe is what broke
  tabular-classification off its multi-generation 0.7875 plateau — the mechanism
  is real and reproducible, so mutations should extend probe fidelity, not
  abandon it.
- **Noise discipline**: tiny private splits (instruction-routing 32 instances,
  coarse tabular buckets) swing hard seed-to-seed. Trust the robust
  mean-of-per-task-medians across seeds, read the trend, not one lucky step.
  bin-packing is deterministic (FFD) and near-saturated — expect the probe to
  saturate there and correctly fall back to public; look for wins on the two
  noisy language/tabular tasks.
