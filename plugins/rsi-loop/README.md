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

## Free labels and the hard line (`scripts/rsi-labels.py`)

Track 2 of the harness-RSI design ([§13.2](docs/HARNESS-RSI-DESIGN.md)) is the observation that some
supervision is already ground truth and costs nothing to collect: user corrections, human review
findings on real MRs, CI failures, reverts. That signal licenses **additive** writes and nothing more.
`fact` appends a record to an append-only `facts.jsonl`; `failure` appends to `failures.jsonl` (the
Track 1 ratchet's feed). Recording a fact is memory, not optimization — it is strictly new
information, so it cannot regress anything.

The point of the tool is the §13.3 hard line, and it is a refusal, not a warning. `gate` exits 3 on
any policy or strategy path: `prompts/`, `policy.json`, `hooks/`, `CLAUDE.md` at any depth,
`agents/*.md`, `SKILL.md`, `skills/**`, `*.workflow.mjs`, `search-engine.mjs`, `commands/*.md`.
Concretely: MDE at K=1 is 0.124 while real harness gains are 0.02–0.05, so a single task cannot
distinguish a real improvement from run-to-run noise. Accepting a policy edit on that evidence is
hill-climbing on noise. Those edits need Track 3's paired counterfactual (both harnesses on the same
task, K ≥ 10–25) plus the §3 gates.

Classification is **path-based** so a policy edit cannot be relabeled as a fact. `fact --scope <policy
path>` is refused for the same reason — you cannot smuggle a prompt rewrite past the gate by
recording it as a "fact about" `prompts/inner.md`. Paths are normalized once before classification
(case, separators, `.`/`..`, trailing dots, NFKC), because a gate that matches raw strings has one
bypass per spelling. Deliberate non-goal: no confusable-script mapping. A Cyrillic lookalike is a
genuinely different directory, and a homoglyph table would refuse innocent paths.

Exit codes: **0** additive-safe / recorded · **2** usage or validation · **3** REFUSED.

```console
$ rsi-labels.py fact --store .rsi/labels --signal user-correction \
    --text "prefers uv over pip for python deps" --source "chat 2026-08-06"
rsi-labels: recorded fact (user-correction)                       # exit 0

$ rsi-labels.py failure --store .rsi/labels --signal ci-failure \
    --summary "test-labels.sh fails on NFKC path" --repro "bash tests/test-labels.sh"
rsi-labels: logged failure (ci-failure)                           # exit 0

$ rsi-labels.py gate --store .rsi/labels --path scripts/rsi-labels.py
rsi-labels: additive-safe — 1 path(s) cleared                     # exit 0

$ rsi-labels.py gate --store .rsi/labels --path prompts/inner.md
rsi-labels: REFUSED — §13.3 hard line.                            # exit 3
  policy path: prompts/inner.md — lives under a prompts/ directory (prompt text is policy)
  single-task evidence never licenses a policy change: MDE(1) = 0.124 (§13.1) ...
```

`tests/test-labels.sh` covers the additive paths, every gated pattern, and the normalization
bypasses; it runs in CI.
