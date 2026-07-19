---
description: Level-2 ignition test — does a campaign driven by the best evolved generation beat the baseline campaign at equal budget?
argument-hint: "<source-run-dir> [--max-steps N] [--budget TOKENS]"
---

Run the AIDE² **Level-2 (ignition)** test for the run in "$ARGUMENTS". Level 2
asks whether the system's _self-improvement ability_ has itself improved: does a
campaign whose proposer is informed by the best evolved generation (`vN`) beat
what the baseline proposer (`vN−1`) produces from the same start at the same
budget? The paper measured this honestly and did **not** claim it (AIDE47-as
-outer converged faster but showed no asymptotic advantage). Expect to do the
same: this command is instrumented to measure, not to pass.

## Design (a paired A/B, everything held equal but the proposer)

Both arms start from `baseline/gen-000`, use the same task battery, the same
per-eval budget and seeds, the same verifier, and the same total step/token
budget. They differ in ONE thing — who proposes:

- **Arm C (control)**: the standard `rsi-proposer` (as in `/rsi:step`).
- **Arm I (ignited)**: the proposer is briefed with the _discovered strategy_
  of the source run's best generation — its `policy.json` and operator prompts,
  and the ledger rationales of every accepted step on its lineage — and told to
  propose in that idiom (the evolved agent's own search/context principles
  driving the next rewrites). This is the "best generation swapped into the
  outer role" from PLAN.md §2.

## Procedure

1. Read the source run's incumbent (derived from the last accepted ledger line),
   its accepted-lineage ledger lines, and the best generation dir (`policy.json`,
   `prompts/*.md`). Summarize the discovered strategy into an "ignited proposer"
   brief (a few sentences of concrete principles: which operators, what context
   each gets, what selection rule).

2. Scaffold two fresh runs with `/rsi:init` (both from gen-000, full battery):
   `<source>/ignite/arm-control` and `<source>/ignite/arm-ignited`. Write the
   brief to `<source>/ignite/arm-ignited/ignite/strategy-brief.md` **only** — this
   is the seam `/rsi:step` step 2 reads to prepend the brief to the proposer, so
   Arm I proposes in the evolved idiom while Arm C (no such file) uses the stock
   proposer. That single file is the ONLY difference between the arms.

3. Drive each arm with `/rsi:run` at the **same** `--max-steps N` (default 8),
   the **same** `--budget`, and `--plateau 0` (disable the early stop) so both
   arms execute an equal step budget — "equal budget" is enforced, not assumed.
   Everything else (battery, seeds, per-eval budget, verifier) is identical.

4. Compare with the analyzer:
   `python3 plugins/rsi-loop/scripts/rsi-report.py --ledger <arm>/ledger.jsonl`
   for each arm, and read each arm's **cumulative inner tokens** (sum of
   `inner_tokens` over its ledger) so the equal-budget claim is measured, not
   asserted. Report side by side: best private aggregate, cumulative inner tokens
   spent, best-so-far growth rate and `n_accepted_improvements`, acceptance rate,
   and hack rate.

5. **Verdict (honest).** Level 2 is supported only if Arm I strictly beats Arm C
   on best-private-aggregate-at-equal-budget **and** the advantage is asymptotic
   (a higher plateau), not merely faster early convergence to the same plateau.
   State explicitly which of these holds. A "converged faster but same ceiling"
   result is a **Level-2 rejection** — the paper's exact finding — and is the
   expected, reportable outcome, not a failure of the command.

Write the two ledgers, the strategy brief, and the verdict under
`<source-run-dir>/ignite/` so the test is reproducible and auditable. As
everywhere, private scores never touch an inner agent; the immutable harness is
never edited during either arm.
