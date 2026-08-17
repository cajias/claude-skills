# rsi-loop

AIDE²-style recursive self-improvement loop for Claude Code: an outer-loop agent iteratively
rewrites an inner tree-search research agent, keeping rewrites only when they beat the incumbent
on **private held-out scores** under a **fixed budget**, with layered reward-hacking defenses and
RSI-ladder measurement.

**Status: M1–M4 shipped; M5 machinery built.** The standalone inner agent, the outer step
(propose → evaluate → verify → select), the full three-family task battery, the unattended
`/rsi:run` driver, robust aggregation + reward-hack outlier detection, the hand-tuned
`gen-human` baseline, the `holdout-tasks/` generalization set, `/rsi:report`, and `/rsi:ignite`
are all implemented. The build roadmap and current milestone state live in
[docs/PLAN.md](docs/PLAN.md) and [docs/CONTINUATION.md](docs/CONTINUATION.md).

Method sources: [Weco AIDE² report](https://www.weco.ai/blog/first-evidence-of-recursive-self-improvement),
[4-level RSI ladder](https://www.weco.ai/blog/4-levels-of-recursive-self-improvement),
[explainx summary](https://explainx.ai/blog/weco-aide2-recursive-self-improvement-rsi-ladder-july-2026).

## Commands

- `/rsi:autoresearch <task-dir>` — standalone AIDE-style inner agent: tree-search autoresearch
  on any task with a `task.md` and `score.py` (runs the current best evolved generation)
- `/rsi:init` — scaffold a run (generations, task battery, ledger)
- `/rsi:step [n]` — execute outer-loop steps (propose → evaluate → verify → select)
- `/rsi:run` — drive `/rsi:step` unattended, bounded by `--max-steps`, an inner-token
  `--budget`, and a `--plateau` stop condition; resume-aware for multi-day runs
- `/rsi:report` — lineage, scores, and falsifiable RSI-ladder evidence (slope vs. the
  hand-tuned baseline, holdout generalization deltas, hack-rate trend)
- `/rsi:ignite` — the Level-2 "ignition" swap test (best generation into the proposer role)

## Task battery

Three AIDE² families under `tasks/`, each with a public/private split and an immutable scorer:
`bin-packing` (heuristic optimization), `tabular-classification` (ML engineering; public =
5-fold CV, private = held-out test set), and `instruction-routing` (harness engineering; the
solution is a tiny agent scaffold). Second-order generalization is measured on `holdout-tasks/`
— one unseen task per family plus a far-OOD time-series forecast — which no run ever trains on.

## Ratchet (§13.2 Track 1)

§13.1 proves a single real task cannot license a harness edit (MDE at K=1 is 0.124; real gains are
0.02–0.05), so online _optimization_ is off the table. What is available online is _hardening_,
which needs no counterfactual and no statistics because it is monotone: every real failure — a
review finding, a CI break, a revert, an escaped bug — becomes a permanent regression case with the
fix as its golden ref, and no future harness may regress it. `scripts/rsi-ratchet.py` is that bank:
`add` banks a failure, `check` re-verifies every banked repro, `list` prints one line per case.
Exit codes are `0` holds, `1` **the ratchet bit** (a repro regressed), `2` usage/unreadable bank,
`3` refused (id already banked), `4` tampered. Exit 1 is reserved for a real regression, so no
internal error can impersonate one.

The bank is append-only by DETECTION, not prevention — inner agents share this uid, so a read-only
bit is theatre. Every `add` witnesses the case file's sha256 in `ratchet/ledger.jsonl`, and `check`
reconciles bank against ledger in both directions before running any repro: a witnessed case that
vanished or changed is a tamper, and so is a case file the ledger never vouched for (which is what
stops a wiped ledger from laundering a deletion into a pass). Because the witness is over bytes,
`ratchet/` is in `.prettierignore` — a reformat would forge a tamper alarm. There is deliberately
no `retire`/`delete`: retiring a saturated case is a human act appended to the ledger, never
something the loop can call. Detection has a bound: a writer who tampers with a case _and_ rewrites
its ledger line to match passes `check`, so the real rail is that both are committed to git — ledger
lines are only ever appended, and a diff that modifies an existing line is the tamper signal a
reviewer must reject.

To bank a new failure, fix it first, then hand the tool a repro that passes now and would fail if
the fix were reverted (verify both directions before banking — the tool rejects an empty repro but
cannot detect a vacuous one):

```bash
python3 plugins/rsi-loop/scripts/rsi-ratchet.py add \
  --bank plugins/rsi-loop/ratchet \
  --id ls-lint-ignores-pycache --source ci-break \
  --summary "a stray __pycache__ failed ls-lint, which does not read .gitignore" \
  --repro 'grep -qF "**/__pycache__" .ls-lint.yml' \
  --golden .ls-lint.yml
```

Repros run through the shell in the caller's cwd, so write them relative to the repo root — that is
where CI runs `check`, as the `Ratchet — banked cases still fixed` step of `test-rsi-loop`.

## Safety

Inner agents run in sandboxes built from public materials only; the plugin's PreToolUse hook
(`hooks/deny-private.py`) denies any read of a `private/` split or write to the immutable
harness. Only the outer loop scores private data, gated behind `RSI_OUTER_LOOP=1`. Integrity is
DETECTION, not prevention (agents share the harness uid): `rsi-check-integrity.sh` anchors
scorers/data to git HEAD or a checksum manifest, and private scoring refuses a tampered harness.
CI runs the full suite — `test-deny-hook.sh`, `test-scorer.sh`, `test-integrity.sh`,
`test-aggregate.sh`, and `test-report.sh`.
