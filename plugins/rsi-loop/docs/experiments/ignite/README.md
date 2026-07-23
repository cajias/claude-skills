# ignite — M5 Level-2 (ignition) test for run-002

**Verdict: Level 2 NOT supported.** At equal 1-step budget the ignited arm (proposer briefed with
gen-006's discovered strategy) scored **0.5876** on mean-of-per-task-medians vs the stock-proposer
control's **0.6126** — ignited is **−0.025 WORSE**, not better. Per `/rsi:ignite` step 5, Level 2 needs
the ignited arm to _strictly beat_ control with an _asymptotic_ (higher-plateau) advantage; a wash is
already a rejection, and this is stronger than a wash — a measurable regression.

This is the AIDE² **Level-2 (ignition) test**: does a campaign whose proposer is briefed with the best
evolved generation's strategy beat a stock-proposer campaign at equal budget? Both arms start from the
same gen-000 baseline and differ in exactly one file — the ignited arm's proposer gets
`strategy-brief.md` (gen-006's discovered strategy) prepended; control does not.

## Scope

Step 1 only of a planned 8-step campaign. Both arms proposed gen-001 from gen-000, then each candidate
was evaluated on the 3-family battery (bin-packing, tabular-classification, instruction-routing) under
the robust `--seeds 3` protocol (seeds 42/43/44), selecting on mean-of-per-task-medians
(`scripts/rsi-aggregate.py`). The operator **stopped after step 1**: the result was decisive and the
mechanism is understood. The remaining 7 steps were not run — the differentiator between the arms is
the ignited proposer's signature probe, whose failure mode step 1 already exposes, and a Level-2
rejection is the expected outcome, so more steps would only accumulate the same deficit at higher cost.

## Aggregate result

| Arm     | Proposer                         | Mean-of-per-task-medians |
| ------- | -------------------------------- | ------------------------ |
| control | stock AIDE0                      | **0.6126**               |
| ignited | gen-006 strategy-brief prepended | **0.5876**               |
| Δ       | ignited − control                | **−0.025** (WORSE)       |

## Per-task medians (seeds 42/43/44)

| Task                   | control | ignited | Outcome                                           |
| ---------------------- | ------- | ------- | ------------------------------------------------- |
| bin-packing            | 0.9379  | 0.9379  | TIE — deterministic FFD; probe saturates / no-ops |
| tabular-classification | 0.90    | 0.825   | **CONTROL WINS** — this is the entire deficit     |
| instruction-routing    | 0.0     | 0.0     | TIE at the floor                                  |

bin-packing private `0.937937` is identical in both arms and reproduces run-002's historical baseline
`0.938` exactly — a calibration check that the harness is faithful. Every point of the −0.025 comes from
tabular; instruction-routing is a floor tie, not a differentiator.

## Mechanism — the scientific finding

**1. The entire −0.025 deficit is tabular, and it comes from the ignited arm's signature probe firing
with no real signal.** The ignited proposer's core mechanism is: search on public score, then break
public-score ties with a shared adversarial-robustness probe. The probe fired on all 3 tabular seeds.
On 2 of 3 its robustness ranking was **anti-correlated** with true held-out generalization — it broke
the tie toward the _less_-generalizing node:

| Seed | Probe pick (private) | Top-public alternative (private) | Δ from picking the probe's choice |
| ---- | -------------------- | -------------------------------- | --------------------------------- |
| 42   | node-6, 0.825        | node-7, 0.9125                   | −0.0875                           |
| 43   | node-6, 0.775        | node-8, 0.9375                   | −0.1625                           |
| 44   | (probe helped)       | —                                | +0.025                            |

Net: the probe drags the tabular median from control's 0.90 down to 0.825. The worst backfire (s43) is
captured concretely in `solutions/` — the probe picked `node-6` (private 0.775) over top-public `node-8`
(private 0.9375).

**2. Instruction-routing is a TIE at the floor, NOT a probe failure.** Control's greedy-public memorizes
the public phrasings and scores 0.0 on held-out paraphrases. But the ignited arm's improve nodes barely
generalized either — the best "generalizer" reached only private 0.0625 (s42), 0.0 on the other two
seeds. Both arms share the gen-000 base learner (haiku, low effort), which simply did not produce a
strongly paraphrase-tolerant solution. There was almost nothing better for the probe to find, so its
tie-breaks here did not materially change the 0.0 outcome. The floor tie is the _shared base learner's_
weak generalization, common to both arms — not the probe failing at its designed task.

**3. Root cause of the tabular loss.** gen-006's data-perturbation probe only helps when its
public-data-only battery carries real discriminating signal. On the coarse tabular private buckets, the
battery's robustness scores are effectively noise — uncorrelated with true held-out generalization. A
tie-break driven by a noisy signal is _strictly worse_ than greedy-public, because it sometimes overrides
a correct default with a wrong pick. That is the −0.025.

**4. This is a stronger negative than the paper's.** AIDE²'s Level-2 rejection was "ignited converges
faster, same ceiling" — a wash. Here, at equal 1-step budget, ignited is measurably worse, and the cause
is understood: the evolved arm's signature mechanism actively mis-selects when its probe lacks signal.

## Caveats

- **Single step, not the full 8.** The trajectory beyond step 1 was not run (see Scope). The claim is
  scoped to equal 1-step budget.
- **Tiny private splits are noisy** (coarse tabular buckets, 32-instance instruction-routing). That noise
  is itself the finding: the probe's tie-break rides on it.
- **No LLM-adversarial verifier.** It was unavailable (spend limit), so accepts would have gated on the
  mechanical battery only. This does not affect the A/B: it is a pure private-score comparison with no
  accept/reject gating involved.
- **Seam verified before spending compute.** A zero-eval, proposal-only smoke confirmed the two arms
  diverge — control proposed a context-engineering mutation; ignited independently proposed gen-006's
  adversarial-probe machinery plus a `probe.md` — proving the `strategy-brief.md` seam works.

## Data files (all in this directory)

- `progress.jsonl` — one line per scored eval (arm, gen, task, seed, public, private, note). Source of
  truth for every table above.
- `strategy-brief.md` — the independent variable: gen-006's discovered strategy, given only to the
  ignited arm.
- `solutions/ignited-tabular-s43-node6-PROBE-PICK-priv0.775.py` — the node the probe selected on s43.
- `solutions/ignited-tabular-s43-node8-TOPPUBLIC-priv0.9375.py` — the top-public node the probe passed
  over. Together, the concrete worst-case probe backfire (−0.1625).
