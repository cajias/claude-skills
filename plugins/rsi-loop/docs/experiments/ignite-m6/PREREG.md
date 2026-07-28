# M6 isomorphic-ignition — pre-registration

**Pre-registered before any eval spend (§6.1.4). Committed \_\_\_\_ (date to be filled by the committer).**

Honesty stance (binding): `NO_RESULT` is the stated **prior** and a **full success** — the paper (AIDE²)
measured Level 2 honestly and did not claim it. A faked or eyeballed `SUPPORTED` is a **failure** of this
experiment regardless of what the arms do. Every verdict is computed by `scripts/rsi-ignition.py decide`
from real trajectories; no eval score is ever fabricated. This document is a contract, committed to git
before a single paid campaign runs.

## 1. Hypothesis & prior

**Hypothesis.** A campaign whose operating scaffold IS the best evolved generation (its `policy.json` +
`prompts/` promoted verbatim into the outer seat) reaches a strictly higher, sustained asymptote than the
stock gen-000 scaffold at equal budget.

**Prior (stated up front).** `NO_RESULT` — paper parity. AIDE² found "converged faster, no asymptotic
advantage." This is a measurement, not a target.

## 2. Arms (one-byte-difference invariant)

- **control** — the stock `baseline/gen-000` scaffold (`policy.json` + `prompts/`), unmodified.
- **ignited** — the same `baseline/gen-000` scaffold with `{policy.json, prompts/*}` **replaced** by the
  best discovered inner scaffold's bytes (the lift).

The **only** difference between the arms is the bytes of `arm-ignited/{policy.json, prompts/*}`. Engine,
adapter, battery, seeds (42/43/44), budget, verifier, and deny hook are **byte-identical**.

**Frozen 8-field vocabulary.** The promotable policy has exactly these 8 fields, shared verbatim by both
seats — no new field is introduced or permitted:

| Field              | gen-000 value              |
| ------------------ | -------------------------- |
| `algorithm`        | `aide0-greedy-tree-search` |
| `num_drafts`       | `5`                        |
| `max_nodes`        | `9`                        |
| `model`            | `haiku`                    |
| `effort`           | `low`                      |
| `context_mode`     | `full-history`             |
| `selection`        | `greedy-public`            |
| `draft_directions` | 5 strings                  |

Prompts: `draft.md`, `debug.md`, `improve.md`.

**Why NOT run-002 / gen-006.** The promoted scaffold is discovered from a **fresh gen-000 M6 inner
campaign under the frozen 8-field engine** — NOT the run-002 gen-006 lineage. gen-006 carries 7
out-of-vocabulary fields plus engine-resident Probe machinery that a frozen generic engine cannot
interpret; lifting it would smuggle in mechanism the outer seat cannot honestly run.

## 3. Design constants

- **G = 8** meta-generations (`--max-steps 8`).
- **Seeds 42 / 43 / 44** (K = 3).
- **Tail = {6, 7, 8}** — the sustained-plateau window.
- **`--plateau 0`** — early stop disabled so both arms execute an equal step budget; "equal budget" is
  enforced, not assumed.
- **G ≥ 4 hard floor** — no verdict below 4 completed meta-generations.
- **Three-tier battery:**
  - **SELECTION** (drives outer search): `tabular-classification` (pub 200 / priv 400, SE ~0.015),
    `bin-packing` (pub 40 / priv 120, SE ~0.02).
  - **OUTER-PRIVATE survival** (off-search, decides scaffold acceptance): `instruction-routing`
    (pub 60 / priv 160, SE ~0.024).
  - **HOLDOUT** (untouched, scored once at `/rsi:report`): `holdout-tasks/` (one per family + far-OOD
    time-series).

## 4. MDE & power

MDE(K) = 2.487·σ_d/√K. σ_d is a **planning** value (0.05) until Phase-0 `--calibrate` **measures** it on
the real battery. At the planning σ_d:

| K           | MDE(K)   |
| ----------- | -------- |
| 3 (default) | 0.071794 |
| 5           | 0.055611 |
| 10          | 0.039323 |
| 25          | 0.024870 |

K_req(effect) = ceil((2.487·σ_d/effect)²) at σ_d = 0.05:

- K_req(0.025) = **25 seeds** (a 0.025-scale effect is unresolvable at K=3).
- K_req(0.15) = **1 seed**.

**Hard power precondition (gate).** The planted known-positive must exceed MDE(K) on the instrument. If it
does not, the verdict is `NO_RESULT` regardless of the arms.

**Phase-0 gate already CLEARS** (`node scripts/rsi-phase0-gate.mjs`): planted policy-lift ΔA = 0.149434 ≫
MDE(3) = 0.0718 → SUPPORTED; stock-vs-stock ΔA = 0 → NO_RESULT; underpowered 0.03-scale ΔA = 0.028 < MDE →
NO_RESULT; precond `planted_positive_cleared=false` → NO_RESULT. The instrument has demonstrated power.

## 5. Verdict rules (§6.1.4)

| Verdict   | Condition                                                                                                                                                                                                                                                                                                            | Meaning                                                                              |
| --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| SUPPORTED | ΔA ≥ MDE AND all seeds ΔA_s > 0 (sign test ≤ α) AND sustained for all seeds over tail {6,7,8} AND ΔR ≥ 0                                                                                                                                                                                                             | Ignited reaches a strictly higher, sustained plateau — Level 2 clears                |
| REFUTED   | ΔA ≤ −MDE (or within ±MDE while ΔR ≤ −MDE — faster-losing)                                                                                                                                                                                                                                                           | Ignited plateau measurably worse                                                     |
| NO_RESULT | power precondition fails; OR \|ΔA\| < MDE (within noise — the paper's actual outcome: ΔR>0 with \|ΔA\|<MDE ⇒ Level 2 not claimed = "converged faster, no asymptotic advantage"); OR ΔA ≥ MDE while ΔR < 0 (higher plateau only via a late jump while converging slower — inconclusive); OR sign/sustained gate fails | Instrument couldn't resolve a clean asymptote win — Level 2 not supported, ≠ refuted |

### Metric definitions

- **Best-so-far** B(g) = max(pa(1..g) of accepted generations), B(0) = gen-000 baseline (monotone).
- **Asymptote** A = mean(B(G−1), B(G)) (mean-of-last-2).
- **Rate** R = (1/G)·Σ(B(g) − B(0)) — corroborative only, never alone → SUPPORTED.
- **Paired per-seed deltas** ΔA_s, ΔR_s; point estimates ΔA = median_s ΔA_s, ΔR = median_s ΔR_s.
- **Sign test.** n=3 all-same-sign p = 0.125 (gate at n=3, corroborative); escalate to seeds 42–46 →
  5/5 p = 0.031.
- **Power precondition (hard gate).** The planted known-positive must exceed MDE(K) on the instrument
  (Phase-0 clears at 0.149 ≫ 0.072). If not, verdict is NO_RESULT regardless of the arms.

## 6. Phased budget with stop rules (the M5 spend covenant)

Tokens are primary; dollars are a reporting conversion (haiku inner ~$2/M, strong proposer ~$6/M). Node
economics: inner node ~55K tok (~$0.11); inner campaign = 1 outer node's score = 2 tasks × 3 seeds,
token-capped, ~2.0M tok (~$4); outer node (loaded) = inner campaign + proposer edit (0.15M strong @ $6/M ≈
$0.9) = ~2.15M tok (~$4.9); outer campaign (1 arm, 1 rep) = 8 meta-gens × outer node = ~17.2M tok (~$39);
paired A/B R=3 = 2 arms × 3 reps = 6 campaigns = ~103M tok (~$233). B_inner ≈ 335K tok/sub-run (~$0.67),
tuned so the incumbent spends 80–90%.

**`BUDGET_CEILING_USD` must be set before any paid phase. If it is unset, do all free work and stop.**
Never exceed the ceiling; never start a phase whose worst-case cost exceeds remaining budget. Never
fabricate an eval score.

- **Phase-0 — real-battery `--calibrate` (~$8).** Measures σ_d, prints K_req.
  **STOP RULE:** if budget can't fund K_req seeds for the smallest interesting effect → declare
  **INCONCLUSIVE up front**, spend nothing on a campaign.
- **Phase-1 — paired pilot R=2 (4 campaigns × ~$39 ≈ ~$155; cumulative with Phase-0 ~$163).**
  **STOP RULE:** feed each arm's best-so-far trajectory to `rsi-ignition.py decide`; if |ΔA| < MDE(K) →
  `NO_RESULT`, **most runs STOP HERE**.
- **Phase-2 — add R=3 ONLY if Phase-1 is within noise AND budget allows (→ ~$233 ceiling).**

## 7. Deviations logged

- **Artifacts are `.mjs` + prompt bundles, not `.py`.** Logged deviation from AIDE²'s Python artifacts;
  the mechanism (policy + prompt lift under a frozen engine) is preserved.
- **n=3 is too small for a t-test.** We do not run one. Two honest gates stand in: the hard power
  precondition (MDE) and the sign test (n=3 → p=0.125, corroborative; escalate to n=5 → p=0.031 if a
  clean sign emerges).
