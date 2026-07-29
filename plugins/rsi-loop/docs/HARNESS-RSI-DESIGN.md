# Harness-RSI — auto-improving a Claude Code agent's harness for issue resolution

**Status:** DESIGN (unbuilt). Draft 1, 2026-07-29.

**Goal (one line):** evolve a Claude Code **harness** so its agent resolves a GitHub/GitLab
issue with well-tested, high-quality code that **completely, concisely, and correctly** addresses
the issue and **merges in as few review cycles as possible** — under a fixed cost budget.

This is a concrete instantiation of rsi-loop's M6 polymorphic architecture: the artifact being
searched is no longer a `solution.py` or an inner-agent scaffold, it is a **harness bundle**
(`CLAUDE.md` + hooks + skills + agent defs + settings). It reuses the frozen `search-engine.mjs`,
the ledger, the verifier, and the public/private wall verbatim; the only new code is **one adapter**
and **one scorer**. Everything hard about this project lives in the scorer.

"Harness" here = the layered config that wraps the model and shapes agent behavior:
`CLAUDE.md` at any folder level, hooks (`settings.json` Pre/PostToolUse/Stop), skills (`SKILL.md`),
subagent definitions (`agents/*.md`), MCP wiring, and permissions. The prompt-and-tooling scaffold,
not the weights.

---

## 1. What is optimized (the artifact) and what is not (the wall)

The loop mutates a **harness generation dir**:

```text
harness-gen-NNN/
├── CLAUDE.md              # project-level instructions (mutable)
├── .claude/
│   ├── settings.json      # hooks + permissions (mutable — with the fence in §4)
│   ├── skills/*/SKILL.md   # mutable skill bodies
│   └── agents/*.md         # mutable subagent defs
└── manifest.json          # declares which files compose this harness + their roles
```

The single load-bearing invariant, inherited from rsi-loop: **the scorer and the judge stack are
immutable and live OUTSIDE this dir.** The candidate harness may _contain_ a code-reviewer, a
linter config, a simplifier, and the insights skill — but the copies used to _score_ a candidate are
pinned, external, and unreachable by the loop. See §4; this is not optional, it is the whole
integrity model.

Reuse map (no new engine code):

| rsi-loop piece                           | Reused as-is for harness-RSI                            |
| ---------------------------------------- | ------------------------------------------------------- |
| `search-engine.mjs` (frozen tree search) | outer search over harness mutations                     |
| `ledger.jsonl` + `best` pointer          | accept/reject history over harness generations          |
| verifier subagent (`<50%`-survives rule) | re-runs claimed winners on fresh issue instances        |
| public/private split                     | seen issues (search) vs held-out issues (survival)      |
| `budget` token/dollar meter              | per-candidate cost cap (§6 — cost becomes a constraint) |
| adapter concept (M6 §6.1)                | **new** harness adapter (§8)                            |
| deterministic Python scorer              | **new** issue-resolution scorer (§9) — the 80%          |

---

## 2. The mapping (why this is the same machine)

In rsi-loop the inner agent is a tree-search Workflow script. Here the inner agent is **a whole
Claude Code session driven by the candidate harness**. The harness _is_ the inner agent's scaffold.
So:

- **Outer loop** = rsi-loop's outer loop: mutate the scaffold (now a harness), score it, keep iff
  better on held-out. Unchanged.
- **One outer node's score** = run an agent **under the candidate harness** across the frozen issue
  battery, at `K` seeds, and compute the composite score (§3). This replaces "run a tree search";
  the harness drives the agent's behavior instead of a `policy.json`.
- **Promotion** stays a literal lift: the best harness dir's files become the new incumbent.

---

## 3. The scoring model (the heart)

### 3.1 Three tiers — do not flatten them

A fitness function built only from "fewer issues / fewer lint errors / smaller diff" terms has a
degenerate optimum: **ship nothing.** The tiers exist to make "less is better" safe by first
forcing "the issue is actually resolved."

```text
GATES (immutable, pass/fail — any failure ⇒ reject the candidate, score = floor)
  ├─ build passes
  ├─ acceptance-test suite passes        ← CORRECTNESS + anti-empty-diff anchor
  ├─ lint == 0  (or ≤ incumbent baseline)
  └─ coverage ≥ τ  (on the changed lines, not global — see §5 mutation check)

OBJECTIVE (the gradient — computed only for candidates that clear the gates)
  the composite in §3.3, anchored on complete·concise·correct

SECONDARY / CONTROLLABLE (weights default to 0 — emergent unless you dial them up)
  speed, wall-clock, concurrency, extra linter strictness, style prefs
```

### 3.2 The anchor — "complete, concise, correct" (verified, un-hackable)

This is the term you named as most important, and it is what stops reward hacking. Each of the three
is measured against something the loop **cannot see or edit**:

- **Correct** — the issue's **hidden acceptance-test suite** passes. This suite is private (§7),
  pinned, and never in the candidate harness. An empty diff, or a diff that special-cases nothing,
  fails it → gate floor. This single gate kills the empty-diff attractor.
- **Complete** — fraction of the issue's requirement checklist satisfied. The checklist is derived
  from the **golden reference** (the real merged PR/MR that closed the issue) + issue acceptance
  criteria/labels. Measured by acceptance tests **plus** an intent oracle (a pinned LLM judge that
  compares the delivered diff to the golden reference and the issue text). Partial solutions score
  partially — no cliff.
- **Concise** — diff parsimony **relative to the golden reference**, not in absolute terms.
  "Smallest diff wins" is the empty-diff trap; "diff size near or below the reference that _also
  passed acceptance_" is not. You cannot be concise without being correct, because concision is only
  scored past the acceptance gate.

```text
anchor = w_correct   · acceptance_pass_fraction(hidden_suite)
       + w_complete  · intent_oracle(delivery, golden_ref, issue)      # 0..1
       − w_concise   · parsimony_penalty(diff_size, golden_diff_size)  # 0 when ≈ golden
```

### 3.3 The review-cycles term (your "merges in fewest cycles")

Simulate the review loop with the **pinned** judge stack (external copies of code-reviewer,
reviewer-sast, ponytail, MR-reviewer heuristics):

```text
review_cost = Σ_findings  criticality_weight · valid(finding)
review_cycles = iterations of (review → agent fixes → re-review) until zero BLOCKING findings
```

`valid(finding)` is gated by the intent oracle so the loop can't win by making the reviewer
scream about nothing; criticality weights are yours to set (CRITICAL≫HIGH>MED>LOW, matching your
review-severity rule).

### 3.4 Full composite

```text
if not (build && acceptance_gate && lint_gate && coverage_gate):
    return FLOOR                                   # gates — immutable

score =  anchor(§3.2)
       − w_review  · review_cost
       − w_cycles  · review_cycles
       − w_speed   · wall_clock         # default w_speed  = 0  (emergent)
       − w_conc    · (1 − concurrency)  # default w_conc   = 0  (emergent)
       − w_style   · style_deviation    # default w_style  = 0  (emergent)
       # cost is NOT here — it is the budget constraint, §6
```

---

## 4. First-class vs emergent — the direct answer to your question

You asked whether linters / speed / cost / concurrency should be first-class criteria or expected as
emergent results, and said you want _some control_. Recommendation, per signal:

| Signal                                        | Make it a…                              | Why                                                                                                                                                                                      | Your control knob                           |
| --------------------------------------------- | --------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| **Issue resolved** (complete·concise·correct) | **Objective anchor**                    | Only un-hackable outcome measure                                                                                                                                                         | `w_correct/complete/concise`                |
| **Cost of resolution**                        | **Budget constraint, not a score term** | rsi-loop's core lesson: a fixed budget forces _algorithmic_ gains and makes best-of-N / brute force unable to win. Scoring cost directly double-counts and invites degenerate "do less." | the per-candidate `--budget` cap            |
| **Review cycles / valid flags**               | **Objective (secondary gradient)**      | Direct proxy for "merges cleanly." Safe because judges are pinned + oracle-gated.                                                                                                        | `w_review`, `w_cycles`, criticality weights |
| **Linters / coverage / build**                | **Gates (pass/fail floors)**            | Saturate (no gradient) and are trivially gamed (`# noqa`, `assert True`). Use as floors that stop trading correctness away.                                                              | `τ` (coverage floor), lint policy           |
| **Speed / wall-clock**                        | **Secondary term, default weight 0**    | Largely emergent under a cost budget; expose a weight for when you want to steer it explicitly.                                                                                          | `w_speed` (0 → on)                          |
| **Concurrency**                               | **Not scored; seed it**                 | A _capability_, not an outcome. It emerges if it helps solve within budget. Bias it via a `draft_directions`-style hint rather than a score term.                                        | `w_conc` (0 → on) + seed hint               |

The design principle: **anchor on the one outcome that can't be faked; make cost a budget; make
quality-floors gates; make review-friendliness the secondary gradient; let speed/concurrency emerge
but leave a weight you can turn on.** You get control via a single weight vector `w` whose secondary
components default to 0 (emergent) and can be raised to first-class (steered) whenever you want.
Start everything secondary at 0 and only turn a knob on if the emergent behavior disappoints — every
non-zero secondary weight is another surface the loop can trade the anchor against, so add them
deliberately.

---

## 5. Reward-hacking defenses (domain-specific)

Each attack and the wall that stops it. This is the analog of the paper's three defense layers.

| Hack                                                                                      | Defense                                                                                                                                                                                           |
| ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Empty / no-op diff**                                                                    | fails the hidden acceptance suite → gate floor (§3.2)                                                                                                                                             |
| **Neuter the judges** (soften reviewer prompt, disable lint rules, weaken the simplifier) | scoring judges are **pinned external copies**, never the candidate's mutable ones (§1). The candidate's own reviewer is irrelevant to its score.                                                  |
| **Overfit to the seen issues**                                                            | held-out issue split (§7); a harness tuned to seen issues scores low on holdout                                                                                                                   |
| **Special-case the acceptance tests** (write code that only satisfies the visible tests)  | (a) tests are private/immutable; (b) intent oracle compares to the golden PR, not just tests; (c) verifier re-runs on **fresh** issue instances the candidate never saw; `<50%`-survives ⇒ hacked |
| **Weaken its own tests to clear the coverage gate**                                       | coverage measured on **changed lines** + a mutation-testing-lite check (flip a changed line, a real test must fail); acceptance suite is separate and immutable                                   |
| **Bloat tests to inflate coverage**                                                       | concision penalty (§3.2) + acceptance gate + the mutation check (junk tests kill nothing)                                                                                                         |
| **Prompt-inject via the issue text**                                                      | the issue text is untrusted input; the harness under test is sandboxed (§6, no prod network); the oracle judges outcome, not the agent's self-report                                              |

---

## 6. Execution model + cost/noise reality (the honest hard part)

Scoring **one** candidate harness is expensive and noisy — this is the fundamental difference from
rsi-loop's millisecond Python scorers, and it dictates the whole budget.

**How a candidate runs.** Hooks/skills/`CLAUDE.md` are session/project-scoped, so you cannot score a
candidate by tweaking the current session. Each candidate is **materialized into an isolated
workspace** (a git worktree or temp project dir) with its `CLAUDE.md`, `.claude/settings.json`,
skills, and agents in place, then driven **headless**:

```text
for issue in battery:
  for seed in seeds:                         # K ≥ 3 (the gen-005 0.856→0.644 lesson)
    workspace = materialize(candidate_harness, repo_at_issue_base_commit)
    claude -p "resolve issue #N"  in workspace, sandboxed, no prod network, --budget CAP
    run hidden acceptance suite, pinned reviewers, intent oracle
```

**Consequences (all inherited rsi-loop lessons):**

- **Cost is the budget.** Meter dollars/tokens per candidate; a candidate that can't solve within the
  cap loses. This is the efficiency-forcing constraint, not a score term.
- **Noise is real.** Same harness, different run → different score (LLM non-determinism). Hence
  `K ≥ 3` seeds and median-of-seeds aggregation.
- **Battery stays small.** 5–10 issues, not hundreds — each issue×seed is a full agent session
  (minutes, dollars). Concurrency across issues×seeds is where wall-clock is won.
- **Power gate before believing any delta (the M6 lesson).** Before spending on an A/B, confirm the
  battery can _resolve_ the effect you care about: measure `σ_d` (candidate-vs-candidate paired SD),
  compute `MDE(K) = 2.487·σ_d/√K`, and declare INCONCLUSIVE up front if `MDE > smallest interesting
gain`. Do not spend a campaign to confirm a foregone NO_RESULT.

---

## 7. The task battery (frozen, split, oracle-backed)

The battery is the real project. Each item:

```text
battery/issue-NNN/
├── issue.md              # the GH/glab issue text (agent input)
├── base_commit           # repo SHA the agent starts from
├── golden/               # the real merged PR/MR that closed it (reference — PRIVATE)
│   ├── diff.patch
│   └── requirements.md   # checklist derived from the PR + acceptance criteria
├── acceptance/           # hidden test suite that encodes "issue actually resolved" (PRIVATE)
└── split: public | private
```

- **Public split** — issues the loop optimizes against (visible outcomes).
- **Private/held-out split** — issues used only for survival/acceptance; a harness that overfits the
  public issues dies here. Never shown during search.
- Source: mine your own team's closed issues + their merged MRs (you already have the golden refs —
  they're merged). Start with 8–10 well-scoped, already-resolved issues of varied size.

A PreToolUse deny hook (rsi-loop already ships this pattern) blocks the candidate agent from reading
`golden/` and `acceptance/`.

---

## 8. The adapter (new, small)

Tells the frozen engine what a harness generation is:

```jsonc
{
  "artifact_kind": "claude-code-harness",
  "mutation_targets": [
    "CLAUDE.md",
    ".claude/settings.json",
    ".claude/skills/**/SKILL.md",
    ".claude/agents/*.md",
  ],
  "score_cmd": "scripts/score-harness.py", // §9, IMMUTABLE
  "split": { "public": "battery/public", "private": "battery/private" },
  "deny_scope": [
    "**/golden/**",
    "**/acceptance/**",
    "scripts/score-harness.py",
    "judges/**",
  ], // the fence: candidate can't touch judges/oracle
  "budget_tokens": 1500000, // per issue×seed sub-run cap
}
```

Fields that must **differ** between "score a harness" and "score a solution" live here, never in the
mutated files — same rule that keeps rsi-loop's promotion a literal `cp`.

---

## 9. The scorer (new — the 80%)

`scripts/score-harness.py` (immutable), pseudocode:

```python
def score_candidate(harness, battery_split, seeds, budget, weights, judges):
    rows = []
    for issue in battery_split:
        for seed in seeds:
            ws = materialize(harness, issue.repo_at(issue.base_commit))
            run = claude_headless(ws, f"resolve {issue.id}", budget=budget, seed=seed)
            diff = ws.diff()

            # GATES (immutable)
            if not run.build_ok:                      rows.append(FLOOR); continue
            acc = judges.acceptance(issue, ws)         # hidden suite → 0..1, gate at ==1 for pass
            if not judges.lint_ok(ws):                 rows.append(FLOOR); continue
            if judges.changed_line_coverage(ws) < TAU: rows.append(FLOOR); continue
            if not judges.mutation_ok(ws):             rows.append(FLOOR); continue  # tests bite

            # ANCHOR
            complete = judges.intent_oracle(diff, issue.golden, issue.text)   # 0..1
            concise  = parsimony(len(diff), len(issue.golden.diff))
            anchor   = (weights.correct*acc + weights.complete*complete
                        - weights.concise*concise)

            # REVIEW loop with PINNED judges
            cycles, review_cost = simulate_review(diff, judges.pinned_reviewers, issue)

            s = (anchor
                 - weights.review*review_cost
                 - weights.cycles*cycles
                 - weights.speed*run.wall_clock          # default weight 0
                 - weights.conc*(1 - run.concurrency))   # default weight 0
            rows.append(s)

    return median_of_seed_medians(rows)   # robust aggregation (rsi-aggregate.py --aggregate)
```

The `judges` object is the **pinned** external stack; nothing in `harness` can reach it (deny hook +
it lives outside the mutation targets).

---

## 10. Build phases (cheap plumbing vs. the research)

| Phase | What                                                                                             | Effort                                |
| ----- | ------------------------------------------------------------------------------------------------ | ------------------------------------- |
| 0     | Freeze 8–10 resolved issues + golden refs + write hidden acceptance suites; public/private split | **hard — the real project**           |
| 1     | Harness adapter (§8) + materialize/headless-run harness (`claude -p` in a worktree, sandboxed)   | medium                                |
| 2     | Immutable scorer (§9): gates + acceptance + intent oracle + review sim                           | **hard**                              |
| 3     | Power gate: measure `σ_d`, compute `MDE(K)`; declare resolvable or not **before** any campaign   | small (reuse `rsi-ignition.py power`) |
| 4     | Wire into rsi-loop outer engine; run a few outer steps; keep-if-better on held-out               | small (reuse)                         |

Phases 0 and 2 are ~80% of the work and are exactly what rsi-loop found to be the hard part. The RSI
loop itself (phases 1, 3, 4) is mostly reuse.

---

## 11. Headless isolation spike — RESULTS (2026-07-29, claude 2.1.220, Bedrock haiku)

Empirically tested which harness layers a candidate can be scored on, per-workspace, headless. Each
layer got a distinctive canary and was probed with `claude -p` in an isolated workspace.

| Harness layer                     | Per-workspace auto-load?                                                                                                          | Explicit-flag delivery                                                                                                 | Verdict for `mutation_targets`         |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| **`CLAUDE.md`** (project)         | ✅ auto-honored (`cwd/CLAUDE.md`)                                                                                                 | —                                                                                                                      | **mutable — scoreable**                |
| **`.claude/settings.json` hooks** | ✅ PreToolUse fired without any flag (verified via filesystem side-effect; stderr does NOT propagate to `-p` stdout)              | `--settings <file>` also works                                                                                         | **mutable — scoreable**                |
| **Subagents**                     | (loose `.claude/agents/*.md` not separately confirmed)                                                                            | ✅ `--agents '<json>'` inline works cleanly                                                                            | **mutable — scoreable via `--agents`** |
| **Skills**                        | ⚠️ loose `.claude/skills/*/SKILL.md` **NOT** auto-discovered; `--plugin-dir <plugin>` did **not** auto-invoke either in the spike | needs a real plugin + likely an enable step (`enabledPlugins` / `--plugin`), OR inline the skill body into `CLAUDE.md` | **partially blocked — see note**       |

**Materialization recipe that works today:**

```bash
claude -p "resolve issue #N" \
  --settings <candidate>/.claude/settings.json \   # hooks (also auto-loads from cwd)
  --agents   '<candidate agents as JSON>' \          # subagents
  --add-dir  <repo> --permission-mode auto \
  --model <cheap> --dangerously-skip-permissions=false
# CLAUDE.md is honored just by running in the candidate workspace cwd.
```

**Consequence for the design:** three of the four layers (`CLAUDE.md`, hooks, subagents) are
per-candidate scoreable **today** — that covers most of what shapes issue-resolution behavior. The
**skills layer is the one gap**: loose-dir skills aren't auto-discovered headless. Two workarounds,
both fine: (a) package candidate skills as a proper plugin and enable it per-run (needs a follow-up
5-min check on the exact `--plugin` enable flag), or (b) for the MVP, fold skill _content_ into
`CLAUDE.md`/`--append-system-prompt` and keep `mutation_targets = [CLAUDE.md, settings.json, agents]`.
Recommend (b) for phase 1 — it de-risks the whole spike to "already proven working" — and promote to
(a) only if skill-as-separate-file mutation proves necessary.

## 12. Battery sourcing — community best-practice extrapolation (answers "can we skip hand-labeling B?")

**Yes, and it's better than hand-labeling your own issues** — with one caveat about the anchor. Two
independent battery sources, use both:

**Source 1 — mined real issues (highest fidelity, some manual work).** Your own or public closed
issues where the merged PR/MR is the golden ref. Fidelity is perfect (the PR really resolved it) but
volume is limited and mining is manual.

**Source 2 — community best-in-class extrapolation (scales, low manual work).** This is your idea, and
it's sound because it turns "did we like the code" (subjective, needs human labels) into "does it
satisfy an established external standard" (objective, already codified). Concretely, the anchor's
sub-signals get **externally-sourced rubrics** instead of hand-labels:

| Anchor sub-signal     | Community-extrapolated source (immutable, external)                                                                                                                                                                                                                                     |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Correct**           | The issue's own upstream test suite / CI gate (for real GH issues: the tests that shipped with the fixing PR). For synthetic issues: SWE-bench-style `FAIL_TO_PASS` + `PASS_TO_PASS` test sets — this is exactly SWE-bench's contract and it's a solved dataset shape.                  |
| **Complete**          | Requirement checklist auto-derived from the issue body + acceptance criteria + the golden PR's changed-surface (files/functions touched).                                                                                                                                               |
| **Concise / quality** | Pinned community linters & analyzers at their **published rule sets** — ruff/eslint recommended, `gosec`/`bandit`/semgrep community rules, your `ponytail` over-engineering rules. "Quality" = conformance to the standard the OSS community already agreed on, not a bespoke judgment. |
| **Review-clean**      | Pinned reviewer prompts seeded from published review checklists (OWASP for security, your own `code-review.md` severity rubric, conventional-commit / changelog hygiene).                                                                                                               |

**Best existing scaffold to lift, not rebuild:** **SWE-bench / SWE-bench Verified** already _is_ a
frozen battery of real GH issues, each with base commit, golden PR, and a hidden test suite that
encodes "resolved" — i.e. our §7 layout, curated at scale. Recommendation: **seed the battery from
SWE-bench Verified** (correctness anchor comes free and un-gameable), and layer our _additional_
signals (conciseness vs golden diff, review-cycle simulation, lint conformance) on top. That collapses
Phase-0 from "write hidden acceptance suites by hand" to "adopt an existing verified dataset + add the
quality overlay."

**The one caveat (don't let it slip):** community rubrics can source _correctness_ and _quality_
objectively, but **"complete AND concise" against a specific issue's intent** still benefits from the
golden-PR comparison — the standard tells you the code is clean, the golden PR tells you it solved
_this_ issue and no more. So: community standards for the gates and the quality terms; golden-PR (from
SWE-bench or your own merged MRs) for the intent anchor. You do **not** need to hand-label a bespoke
"good/bad" corpus — you need (a) an existing verified issue+test dataset and (b) pinned community rule
sets. Both exist off the shelf.

**Revised Phase-0 effort:** was "hard — the real project." With SWE-bench Verified as the seed +
community rule sets as the judges, Phase-0 drops to **medium**: adopt dataset, wire the quality
overlay, carve a held-out split. The intent oracle (still a pinned LLM judge comparing to the golden
PR) remains the one component to validate against a few human spot-checks before trusting it.

## 13. Online (continual) hardening — improving from real work, not training sessions

Goal: use the agent on real issues and have the harness harden itself as a side effect, rather than
running discrete offline campaigns. This is possible, but only if two words are kept apart:

|                          | **Harden** (monotone)       | **Optimize** (comparative)          |
| ------------------------ | --------------------------- | ----------------------------------- |
| Question                 | "never fail this way again" | "is variant B better than A?"       |
| Needs a counterfactual?  | **No**                      | **Yes** — same task, both harnesses |
| Statistics needed        | none (it's a ratchet)       | paired, K ≥ 10                      |
| Can run online per-task? | **Yes**                     | **No** (see below)                  |

### 13.1 Why per-task online optimization cannot work (quantified)

Using rsi-loop's measured noise (`σ_d ≈ 0.05`) and the canonical power form `MDE(K) = 2.487·σ_d/√K`:

| K (real tasks)         | Smallest detectable harness gain |
| ---------------------- | -------------------------------- |
| **1 (one real issue)** | **0.124**                        |
| 10                     | 0.039                            |
| 25                     | 0.025                            |

Real harness improvements are ~0.02–0.05. So from a **single** real task you cannot distinguish a
genuine improvement from run-to-run luck. Worse, the naive online design (change harness at time T,
compare outcomes before/after) is **confounded**: issue difficulty varies far more than harness
quality, so you'd mostly be measuring which issues happened to arrive that week. Any scheme that
accepts a harness edit on the evidence of one real task will hill-climb on noise and drift.

### 13.2 The three online tracks that DO work

**Track 1 — The ratchet (real failure ⇒ permanent regression case).** _This is what "harden itself"
actually means, and it's the highest-value, zero-risk mechanism._ Every real failure — a reviewer
finding, a CI break, a revert, a bug that escaped — is converted into a **new battery case** with the
fix as its golden ref. The battery is **append-only**; no future harness may regress a banked case.
Monotone, needs no counterfactual, needs no statistics. You cannot hill-climb your way back into a
solved failure mode. Start here.

**Track 2 — Free labels (additive knowledge, not policy).** Some supervision is already ground-truth
and costs nothing to collect: **user corrections** ("no, do it this way"), **human review findings**
on real MRs, CI failures, revert events. These license _additive_ harness writes — recording a **fact**
("this repo runs tests via `make test-x`", "that API is deprecated") — which is memory, not
optimization, and cannot regress anything because it's strictly new information.
_Note: your global `CLAUDE.md` already mandates this ("after ANY correction, update memory files").
So you are already doing online learning of the safe kind — just uninstrumented and unmeasured. The
work here is to formalize and instrument it, not invent it._

**Track 3 — Shadow-mode paired A/B (the only honest online _optimization_).** To get the missing
counterfactual, run **both** incumbent and candidate harness on the **same real task**; ship only the
incumbent's output, score both. Pairing cancels task difficulty, which is exactly what makes it
tractable. Cost 2× on sampled tasks (sample rate is your knob — e.g. shadow 30%). Accumulate paired
deltas until K ≥ 10–25, _then_ promote through the normal §3 gates. At 5 issues/week with 30%
shadowing this is weeks per accepted change — genuinely online, just honest about its pace.

### 13.3 Hard line: what must stay gated

- **Additive facts** → online, immediate (Track 2).
- **Regression cases** → online, immediate, append-only (Track 1).
- **Policy/strategy edits** (prompt rewrites, hook logic, review procedure, `CLAUDE.md` behavioral
  rules) → **never accepted on single-task evidence.** They need Track 3's paired counterfactual plus
  the §3 gates and the §5 anti-hack walls.

### 13.4 The flywheel (why this beats offline campaigns over time)

Real work **is** battery generation. Every issue your agent resolves and gets merged produces exactly
the §7 artifact set for free: `issue.md`, the base commit, and a **golden ref** — the diff that
actually merged _after human review_. So:

```text
real issue → agent resolves → human review/merge → banked as battery case (golden = merged diff)
                    ↓                                          ↓
            failures → ratchet (Track 1)          battery grows, gets more representative
                                                              ↓
                                        periodic gated promotion (offline validation, cheap now)
```

The battery stops being a hand-curated artifact and becomes a **byproduct of working**. Offline
validation never disappears — it becomes cheap, continuous, and drawn from your actual work
distribution rather than SWE-bench's.

### 13.5 Safety rails (non-negotiable, all inherited from §1/§5)

1. **Judges are never mutated online.** The pinned judge stack stays external; an online loop that can
   soften its own reviewer will.
2. **Shadow output never ships.** Candidate-harness work product is scored and discarded; only the
   incumbent's output reaches a real MR.
3. **Ratchet is append-only.** No mechanism may retire a regression case to make a score look better;
   retiring saturated cases (§13) is a deliberate human act, logged.
4. **Held-out stays held out.** A slice of banked cases is never used for search — otherwise the
   growing battery silently becomes the training set and generalization is unmeasurable.
5. **Rollback on ratchet break.** Any promoted harness that regresses a banked case auto-reverts;
   this is the online analogue of the verifier's `<50%`-survives rule.

### 13.6 Build order (each stage is independently useful)

| Stage | Mechanism                                                                           | Value standalone                 | Effort                                                                                 |
| ----- | ----------------------------------------------------------------------------------- | -------------------------------- | -------------------------------------------------------------------------------------- |
| 1     | **Ratchet** — auto-bank real failures as regression cases                           | high (immediate hardening)       | small                                                                                  |
| 2     | **Free labels** — instrument corrections/review findings into facts + a failure log | high                             | small (largely exists: memory files, session-analysis/insights skills, `rtk discover`) |
| 3     | Battery auto-accrual from merged MRs (§13.4 flywheel)                               | medium-high                      | medium                                                                                 |
| 4     | **Shadow-mode** paired A/B at a sampled rate                                        | enables real policy optimization | medium                                                                                 |
| 5     | Gated promotion on accumulated paired deltas (§3 gates)                             | closes the loop                  | small (reuse rsi-loop)                                                                 |

Stages 1–2 give you self-hardening **without any of the scoring machinery** in §9 — worth doing even
if harness-RSI proper is never built.

## 14. Remaining open questions

- **Skill-layer enable flag** — 5-min follow-up: exact `--plugin`/`enabledPlugins` incantation to make
  a `--plugin-dir` skill auto-available headless (only needed if we choose §11 workaround (a)).
- **Intent oracle trust** — the LLM judge comparing delivery to the golden PR is itself a model; pin
  its model+prompt, and validate it against human labels on a handful of issues before trusting it as
  the anchor. If the oracle is weak, the anchor is weak.
- **Golden-ref leakage** — issues whose golden PR is discoverable on the public web could let the
  agent look up the answer; prefer private-repo issues or sandbox the network. **SWE-bench note:** its
  golden patches are public, so a networked agent could retrieve them — run candidates network-isolated
  (SWE-bench harness already assumes this), or use SWE-bench Verified's post-cutoff instances.
- **Battery staleness** — as your harness improves, easy issues saturate (rsi-loop's bin-packing
  went 100% saturated, zero signal). Plan to retire solved-by-everyone issues and add harder ones.
- **Insights-skill as convergence signal (not a score term)** — per the earlier discussion, use the
  insights skill's suggestion count as a **stopping/diagnostic** heuristic ("a self-improving system
  runs out of gaps it can name"), never as a gradient — it's inside the harness, so "zero suggestions"
  and "the auditor got lazy" are indistinguishable if you optimize it.
