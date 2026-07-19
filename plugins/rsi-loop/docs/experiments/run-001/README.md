# run-001 — first bi-level RSI run (M2 exit test)

Three manual outer-loop steps on the bin-packing task, fixed budget per evaluation
(9 nodes, haiku inner model, seed 42). Full step records in `ledger.jsonl`; candidate
generations preserved alongside.

| Step | Generation | Mutation | Public | Stress | Private | Outcome |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | gen-000 | baseline AIDE0 | 0.9648 | — | 0.9379 | incumbent |
| 1 | gen-001 | stress-suite tie-breaker | 0.9648 | 0.9339 | 0.9379 | rejected (tie) |
| 2 | gen-002 | family-diverse explore-on-stall | 0.9648 | 0.9598 | **0.9405** | **accepted** |
| 3 | gen-003 | lexicographic exploit-the-explorer | 0.9648 | 0.9400 | 0.9379 | rejected (regression) |

**M2 exit criterion met**: 3 manual outer steps, ≥1 accepted generation on the private
held-out score (gen-002). Acceptance rate 1/3 — high rejection is expected AIDE² behavior.

## What each step taught (and fed into the next)

1. **Step 1**: better measurement alone can't help — the verifier proved the stress suite was
   real and honest, but all 9 nodes were algorithmically equivalent sorted-greedy variants, so
   no metric could separate them. Diagnosis: search diversity, not scoring.
2. **Step 2**: attacking diversity worked — family-committed drafts + a code-blind
   explore-on-stall operator produced 9 algorithm families; an explored multi-start
   construction tied public but won stress AND private. The step-1 tie-breaker, kept in place,
   is what made the winner selectable. First verified self-improvement.
3. **Step 3**: the follow-on mutation (exploit the winning explore lineage) was never
   exercised — the self-generated stress suite is rebuilt each run, and this run's suite
   separated nothing, so the exploit branch never fired and selection regressed to FFD.
   Diagnosis recorded for future proposers: the tie-breaker instrument is unstable
   run-to-run; stabilize it before refining policies that consume it.

## Faithfulness notes

- Selection was strict private-aggregate improvement; private data never entered any inner
  context (deny hook + public-only sandboxes; verifier checked for escape residue each time).
- Verification: winning claims reproduced end-to-end (public + stress), hard-coding audit,
  scorer integrity diffs, mechanism explanation. Step-2's win survived all checks; step-1's
  no-op and step-3's instrument failure were both diagnosed by the verify pass — the
  diagnoses, not just the scores, drove the next proposals (as in the paper).
- Budget: ~0.5M inner tokens per evaluation, constant across steps (472k / 496k / 492k /
  501k) — no candidate won by scaling.

## Open items feeding M3+

- Stress-suite instability (step 3) — candidate fix belongs to future outer steps, not the
  harness: e.g. persist the suite generator spec in the generation so the instrument is fixed
  across the run.
- Single-task battery so far; heterogeneity pressure (3 task families) arrives in M3.
- Chassis A/B experiment (§5.2 of PLAN.md) still pending — native Workflow outer loop is the
  only chassis exercised so far (Arm B).
