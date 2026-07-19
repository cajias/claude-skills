# M3 battery validation — new task families run end-to-end

Before spending the pending-phase compute (§5.2 chassis A/B, the 10-step exit run) on the
three-family battery, each **new** M3 task family (tabular-classification, instruction-routing)
was solved end-to-end by a real inner agent — the same validate-first check M1 used for
bin-packing. gen-000 (AIDE0 baseline), haiku, seed 42, 9-node budget. Public scores come from
the inner run; private scores are computed outer-side (`RSI_OUTER_LOOP=1`), never in inner
context.

| Task family                        | Workflow        | Public (best) | Private (of best) | Nodes | Buggy | Inner tokens |
| ---------------------------------- | --------------- | ------------- | ----------------- | ----- | ----- | ------------ |
| instruction-routing (harness eng.) | wf_c8f0d000-13e | 1.000         | 0.000             | 9     | 0     | 389,617      |
| tabular-classification (ML eng.)   | wf_a1058cea-dfc | 0.850         | 0.788             | 9     | 0     | 550,346      |

## instruction-routing — severe, genuine, achievable generalization gap

gen-000 produced a keyword-dispatch parser scoring a perfect **1.0 on public** but **0.0 on
the held-out private split** (32 cases). This is the task working exactly as designed, not a
bug — verified three ways:

- The split deliberately paraphrases: public uses the imperative form `add 11 and 16`; private
  uses `what is 7 plus 2`, `sum of 15 and -6`, `spell orange backwards`, `convert python to
uppercase`. gen-000's parser returns `""` on every private phrasing it never saw.
- A robustly-written reference parser (the one in `tests/test-scorer.sh`, which handles
  synonyms like plus/sum and word-form ordinals) scores **1.0 on the same private split** — so
  the ceiling is reachable and the scorer is sound.
- An improve node that reached toward generalization (node-6: word-form ordinals, synonym
  aliases) lifted private from 0.0 to 0.094 — real gradient exists between the 0.0 floor and
  the 1.0 ceiling.

Significance: this is the strongest anti-overfitting signal in the battery. gen-000 overfits
public phrasing almost completely, leaving the entire 0→1 private range as headroom for the
outer loop to discover generalization improvements (broader intent matching, paraphrase
robustness) — the self-referential "improve the agent scaffold" family the paper prizes.

## tabular-classification — realistic ML gap, public-best is not private-best

gen-000 progressed through genuine ML approaches — kNN drafts (0.785) → polynomial-feature
gradient descent (0.83) → z-scored momentum-SGD ensemble (0.84) → multi-strategy voting
ensemble (0.85 public, node-7). Unlike bin-packing's flat plateau, the improve operators made
real public gains here.

The held-out private split (n=5) tells the more important story:

- node-7 (public-best, 0.85): private **0.788**.
- node-0 (a plain kNN draft, public 0.785): private **0.800** — _higher_ than the public-best.

A modest ~6-point public→private gap, plus a mild **overfitting inversion**: the ensemble that
won on public generalized slightly worse than the simpler kNN, so the public leader is not the
private leader. This is exactly the anti-overfitting dynamic the split exists to expose, and it
justifies selecting on private (not public) scores. Caveat: private n=5 is small and noisy —
the multi-seed aggregation (`rsi-aggregate.py`, `--seeds K`) exists to damp exactly this.

## Verdict

Both new M3 families run end-to-end under real compute with 0 buggy nodes, and both exhibit a
genuine public→private generalization gap the outer loop can optimize against:

- **instruction-routing** — validated; severe achievable gap (1.0 → 0.0), the strongest RSI
  headroom in the battery.
- **tabular-classification** — validated; modest gap (0.85 → 0.79) with a public-best ≠
  private-best inversion; realistic ML dynamics.

The three-family battery is ready for the pending-phase campaigns (§5.2 chassis A/B, the M3
10-step exit run). No scorer, split, or harness defects surfaced.
