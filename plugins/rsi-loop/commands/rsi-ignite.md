---
description: Level-2 ignition test — does a campaign driven by the best evolved generation beat the baseline campaign at equal budget?
argument-hint: "<source-run-dir> [--steps N] [--budget TOKENS]"
---

Run the AIDE² **Level-2 (ignition)** test for the run in "$ARGUMENTS". Level 2
asks whether the system's *self-improvement ability* has itself improved: does a
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
- **Arm I (ignited)**: the proposer is briefed with the *discovered strategy*
  of the source run's best generation — its `policy.json` and operator prompts,
  and the ledger rationales of every accepted step on its lineage — and told to
  propose in that idiom (the evolved agent's own search/context principles
  driving the next rewrites). This is the "best generation swapped into the
  outer role" from PLAN.md §2.

## Procedure

1. Read the source run's `best.txt`, its accepted-lineage ledger lines, and the
   best generation dir (`policy.json`, `prompts/*.md`). Summarize the discovered
   strategy into an "ignited proposer" brief (a few sentences of concrete
   principles: which operators, what context each gets, what selection rule).
   Record the brief in `<source-run-dir>/ignite/strategy-brief.md`.

2. Scaffold two fresh runs with `/rsi:init` (no baseline re-eval needed beyond
   gen-000): `<source>/ignite/arm-control` and `<source>/ignite/arm-ignited`,
   both with the full battery.

3. Drive each with `/rsi:run` for the same `--max-steps N` (default 8) and equal
   `--budget`. Arm I's `/rsi:step` proposer calls prepend the strategy brief to
   the proposer prompt; Arm C uses the stock proposer. Everything else identical.

4. Compare with the analyzer:
   `python3 plugins/rsi-loop/scripts/rsi-report.py --ledger <arm>/ledger.jsonl`
   for each arm. Report side by side: best private aggregate at equal budget,
   improvement slope, acceptance rate, and hack rate.

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
