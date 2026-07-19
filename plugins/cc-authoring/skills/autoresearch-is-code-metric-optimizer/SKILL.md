---
name: autoresearch-is-code-metric-optimizer
description: |
  The `/autoresearch:autoresearch` Claude Code skill is a CODE-METRIC
  OPTIMIZER (modify → verify → keep/discard loop). Use when: (1) you are
  about to invoke `/autoresearch:autoresearch` to do literature / web
  research (it does NOT fetch papers, search the web, or synthesize cited
  reports — use `/deep-research` for that); (2) you have a measurable
  target (test pass rate, perf delta, p&l, win rate, composite metric)
  AND code-or-config that can be modified to hit it — that IS the right
  use case, including non-traditional optimization targets like trading
  strategy backtest results; (3) you're confused about when to reach for
  the BASE skill vs the sub-skills `:reason` (adversarial debate) or
  `:probe` (8-persona interrogation) — the base skill is for iterative
  optimization with a clear verify function; the sub-skills are for
  qualitative investigation when there is no verify function.
author: Claude Code
version: 1.1.0
date: 2026-06-02
---

# /autoresearch is a code-metric optimizer (in the broad sense)

## Problem

Two common misreadings of `/autoresearch:autoresearch`:

**Misreading 1: "It's a web research skill."** It is NOT. It does not fetch papers, search the web, or synthesize cited reports. That is `/deep-research`.

**Misreading 2: "It only works for traditional 'code' metrics like test coverage."** Also wrong. The skill works for ANY iterative-modification problem with a measurable verify function. That includes:

- Iterating a Python strategy file against a backtest metric (e.g., trading competitions)
- Iterating a YAML config against a deploy success signal
- Iterating a prompt template against an eval score
- Anything else that can be cast as `modify → measure → keep/discard`.

If your problem has a clear "did this change improve the metric?" check, the base skill IS the right tool. The "code" in "code-metric optimizer" is just shorthand for "an artifact you can re-generate" — not specifically Python source.

## Context / Trigger Conditions

**Use the BASE `/autoresearch:autoresearch` when:**

- You have an artifact you can modify (code, config, prompt, dataset)
- AND a programmatic verify function (test suite, backtest, eval harness, lint pass count)
- AND you want to iterate toward a target value of the verify metric
- Even if the domain looks like "research" (e.g., "investigate trading strategies") — what matters is whether you have a verify function. With one, it's optimization, not investigation.

**Use the sub-skills when:**

- `:reason` — you have a CLAIM (not an artifact) you want adversarially debated by judges
- `:probe` — you have a TOPIC you want interrogated by N personas to surface considerations
- `:plan` — convert a goal into scope/metric/direction
- `:scenario` — what-if analysis
- These are for qualitative work where there is no programmatic verify function.

**Use `/deep-research` when:**

- You actually need to fetch web sources, papers, or external knowledge
- You want a cited report
- The work is literature / synthesis, not optimization

## Solution

### Decision tree

```
Do you have a measurable verify function (test, benchmark, backtest, eval)?
├── YES → /autoresearch:autoresearch  (the base skill optimizes against it)
└── NO  → Do you need web sources?
         ├── YES → /deep-research
         └── NO  → /autoresearch:autoresearch:probe (qualitative interrogation)
                   or /autoresearch:autoresearch:reason (adversarial debate)
```

### BASE skill invocation knobs (actual API, from SKILL.md v2.1.0)

The base `/autoresearch` skill uses **structured keyword args** (not `--flags`) and universal flags. The actual invocation form:

```
/autoresearch
Goal: <what you want to achieve — describes the optimization target>
Scope: <which files/components can be modified>
Metric: <the numeric or pass/fail measure — e.g., "gain_factor × win_rate">
Verify: <shell command that returns pass/fail or a scalar score>
Iterations: N   (default: 25; use "unlimited" to opt-in to unbounded)
```

Universal flags (apply to all looping subcommands):

- `--evals` — add mid-loop checkpoints + final summary
- `--evals-interval N` — override checkpoint frequency
- `--chain <targets>` — sequential handoff after completion (e.g., `--chain evals`)

The "modify → verify → keep/discard" loop runs for up to `Iterations:` cycles.
Results land in `autoresearch/autoresearch-{YYMMDD}-{HHMM}/`.

For competition-style iteration (trading, perf tuning, config search), the
invocation looks like:

```
/autoresearch
Goal: Produce a strategy.py that passes gain > 1.0 AND win_rate >= 0.5
Scope: strategy.py (parameter values, signal logic, position sizing)
Metric: composite = gain_factor × win_rate; gate: gain > 1.0 AND win_rate >= 0.5
Verify: uv run python backtest.py --strategy strategy.py
Iterations: 5
```

Note: **no `--modify`, `--target`, or `--judges` flags in the base skill** — those are
sub-skill flags. The base skill's only knobs are `Goal/Scope/Metric/Verify/Iterations`
and the universal flags above.

## Verification

After choosing the skill, sanity-check: "If a human ran this same loop manually — modify file, run script, check score — would the loop be coherent without external context (papers, web)?" If yes → base autoresearch is right. If no → you need a research-flavored skill.

## Example: GOOD use of the base skill (corrected from a prior misframe)

A trading competition iterates `strategy.py` against:

- Verify: train-window backtest returns `{gain, win_rate}`
- Gate: `gain > 1.0 AND win_rate >= 0.5`
- Score: composite = gain × win_rate

```
/autoresearch
Goal: Find strategy parameters that clear the pass gate (gain>1.0, win_rate>=0.5)
Scope: strategy.py — signal logic, indicator periods, position sizing
Metric: composite = gain_factor × win_rate; gate: gain > 1.0 AND win_rate >= 0.5
Verify: uv run python backtest.py --strategy attempts/<iter>/strategy.py
Iterations: 5
```

Even though the domain is "trading research," the LOOP is "modify code → run backtest → keep if better." Use the base skill, not `:probe`/`:reason`.

## Example: BAD use of the base skill

"Investigate which market-making algorithms cite the Stoikov-Avellaneda paper, summarize the field, and tell me the SOTA."

There's no artifact to modify. There's no verify function. You want web sources. Use `/deep-research`.

## Notes

- This skill SUPERSEDES an earlier (v1.0) framing that incorrectly steered "trading strategy iteration" away from the base skill and toward `:probe`/`:reason`. v1.1 (this version) corrects that: if you have a verify function, use the base skill.
- The base skill's `modify → verify → keep` loop scales from tiny per-file metric tweaks to whole-strategy iteration. The boundary is the verify function, not the domain.
- The sub-skills `:reason` and `:probe` remain valid choices when there is NO programmatic verify function — e.g., "which of these 3 strategy ideas is theoretically strongest?" where you can't run a backtest yet.
- Discovered during competition_3 iteration 0 (2026-06-02) in
  `~/Projects/workspace/nautilus-competition-run`.

## References

- The autoresearch skill cluster: `~/.claude/plugins/cache/autoresearch/autoresearch/2.1.2/skills/autoresearch/SKILL.md`
- Companion skill for literature/web research: `/deep-research`
- Prior misframe: competition_3 Plan Task 3 steered 6 teams onto `:reason`/`:probe`; this skill corrects the mental model.
