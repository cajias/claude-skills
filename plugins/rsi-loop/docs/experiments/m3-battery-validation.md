# M3 battery validation — new task families run end-to-end

Before spending the pending-phase compute (§5.2 chassis A/B, the 10-step exit run) on the
three-family battery, each **new** M3 task family (tabular-classification, instruction-routing)
was solved end-to-end by a real inner agent — the same validate-first check M1 used for
bin-packing. gen-000 (AIDE0 baseline), haiku, seed 42, 9-node budget. Public scores come from
the inner run; private scores are computed outer-side (`RSI_OUTER_LOOP=1`), never in inner
context.

| Task family | Workflow | Public (best) | Private (best) | Nodes | Buggy | Inner tokens |
| --- | --- | --- | --- | --- | --- | --- |
| instruction-routing (harness eng.) | wf_c8f0d000-13e | 1.000 | 0.000 | 9 | 0 | 389,617 |
| tabular-classification (ML eng.) | wf_a1058cea-dfc | _pending_ | _pending_ | — | — | — |

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

## Verdict

instruction-routing: validated — task, split, and scorer all correct; large real RSI headroom.
tabular-classification: awaiting run wf_a1058cea-dfc; results appended on completion.
