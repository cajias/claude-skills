---
name: skill-creator-trigger-eval-gotchas
version: 1.1.0
description: |
  Six chained gotchas when running the skill-creator plugin's trigger-eval
  machinery (scripts/run_loop.py, scripts/run_eval.py) against a skill. Use
  when: the trigger eval reports 0% recall or "skill never triggers" even on
  verbatim trigger phrases; `python -m scripts.run_loop` fails with
  `ModuleNotFoundError: anthropic`; the loop crashes at the improvement step
  with "Could not resolve authentication method", or improve_description.py
  wants an ANTHROPIC_API_KEY that a subscription-authenticated Claude Code
  session never exports; scores
  look wrong because you launched from the plugin's directory instead of the
  project; 0% recall persists even after moving the skill out of
  .claude/skills/; or harness recall reads low (~50-60%) while ground-truth
  `claude -p` runs trigger the real skill fine. Causes and fixes covered:
  probe shadowing by an already-installed skill, SIBLING-probe shadowing from
  parallel --num-workers writing rival <name>-skill-<uuid> probes into
  .claude/commands/, cwd-sensitive project-root resolution, and the uuid-probe
  semantic gap that makes harness recall a lower bound.
---

# skill-creator-trigger-eval-gotchas

## Problem

The skill-creator plugin's description-optimization loop has four failure
modes that compound, and the worst one (probe shadowing) produces a
confidently WRONG result instead of an error.

## The gotcha chain, in the order you'll hit them

### 1. ModuleNotFoundError: anthropic

`python -m scripts.run_loop` needs the `anthropic` package. Fix:

```bash
cd <skill-creator-dir> && uv run --with anthropic python -m scripts.run_loop ...
```

### 2. cwd-sensitive project root

`run_eval.find_project_root()` walks up from **cwd** to the first `.claude/`
directory. Launching from the plugin cache dir (`~/.claude/plugins/...`)
resolves to `$HOME` — the probe lands in `~/.claude/commands/` and test
sessions run homed to `$HOME`, not your project. Fix: cwd = your project,
module path via PYTHONPATH:

```bash
cd "<project>" && PYTHONPATH=<skill-creator-dir> uv run --with anthropic \
  python -m scripts.run_eval --eval-set ... --skill-path ... --model ...
```

### 3. PROBE SHADOWING — the silent one

The harness does NOT test your skill in place. It writes a command file named
`<skill>-skill-<uuid8>.md` carrying your skill's description, then checks the
stream for THAT name. If the real skill is **already installed** in the
project, Claude matches the query to the REAL skill name and invokes it; the
uuid probe never fires; the harness records 0% trigger rate on every positive
query — including verbatim phrases from the description itself.

**Tell:** recall = 0% across ALL positives (even exact trigger phrases) while
all negatives "pass". Total zero is the signature; genuine undertriggering is
partial.

**Ground-truth check (one command):**

```bash
cd "<project>" && env -u CLAUDECODE claude -p "<verbatim trigger phrase>" \
  --output-format stream-json --verbose 2>/dev/null | grep -c "<real-skill-name>"
```

A large count = the real skill triggered; the harness scores are invalid.

**To measure an installed skill for real:** temporarily move the skill out of
`.claude/skills/` (and any plugin copies) so the probe is the only candidate,
run the eval, move it back. Or accept ground-truth spot checks.

### 4. Improvement step needs an API key

`improve_description.py` calls the Anthropic SDK directly →
`ANTHROPIC_API_KEY` required. Subscription-authenticated Claude Code doesn't
export one. Measurement (`run_eval.py`) is unaffected (it shells out to
`claude -p`). Without a key, do the improvement loop manually: propose a new
description, re-run `run_eval`, iterate.

### 5. SIBLING-probe shadowing — parallel workers poison each other

Same 0%-recall signature as gotcha 3, but it strikes even when the real skill
WAS correctly moved out of `.claude/skills/`. run_eval's default
`--num-workers 10` has each parallel worker write its own
`<name>-skill-<uuid8>.md` probe into the same shared `.claude/commands/`.
Spawned sessions see up to 10 identically-described probes, invoke whichever
uuid they pick (usually a sibling's), and every worker's own-name check fails
— uniform 0/N triggers.

**Tell it apart from gotcha 3:** the real skill is verifiably parked, a
1-probe diagnostic run passes, and a ground-truth `claude -p` shows the
description matching fine.

**Fix: always pass `--num-workers 1`.** Sequential cost is ~13 min for 18
queries in a skill-heavy environment — acceptable, and the only mode that
measures what a real session would see (one candidate probe).

### 6. Probe-name semantic gap — harness UNDERESTIMATES real recall

Even with shadowing fully eliminated, the harness can read falsely LOW. It
registers the skill description under a uuid name (`<skill>-skill-<uuid8>`),
discarding the semantic value of the real skill name. Queries that
ground-truth strongly with the real installed skill (e.g. 7 stream mentions
via `claude -p`) can score 0/N against the uuid probe carrying the
IDENTICAL description — the real name itself was doing matching work the
probe can't replicate.

**Observed instance (2026-06-11, Claude Code 2.1.173, claude-fable-5, skill
`cc-hooks-main-vs-subagent`):** a 7-positive eval set scored 57% run-level
recall on the harness while spot-checked queries — including a harness 0/2
failure — triggered the real skill reliably.

**Consequence: treat harness recall as a LOWER BOUND.** Before "fixing" a
description based on harness failures, ground-truth each failing query
against the real installed skill:

```bash
env -u CLAUDECODE claude -p "<query>" --output-format stream-json --verbose \
  2>/dev/null | grep -c <real-skill-name>
```

Only harden the description for queries that ALSO fail ground truth. Harness
rejection of negatives is unaffected (no shadowing/semantics involved) and
remains trustworthy.

## Notes

- `run_eval` strips the `CLAUDECODE` env var to allow nested `claude -p`; do
  the same in manual ground-truth checks (`env -u CLAUDECODE`).
- In skill-heavy environments (hundreds of installed skills), expect slower
  `claude -p` boots; 3 trials × 20 queries is tens of minutes.
- `run_eval.py` supports `--runs-per-query N` to bound runtime (2 is usually
  enough for a first pass).
- When running the eval from a subagent: launch via `nohup ... &` detached —
  a plain Bash `run_in_background` process is killed at the subagent's turn
  boundary; also clean up the dead run's leftover probe file or it
  sibling-shadows the relaunch.
- With the autoresearch plugin installed, its `scout-block` PreToolUse hook
  denies writes to any `*.log` path — tee the harness output to
  `run_eval.out`, not `run_eval.log`.
