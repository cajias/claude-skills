# Kickoff prompt for implementing rsi-loop

Paste the prompt below into a fresh Claude Code session on this repo to start the build.

---

Implement the `rsi-loop` plugin end-to-end, following the spec in
`plugins/rsi-loop/docs/PLAN.md` on branch `claude/rsi-skills-implementation-o8q1zv`. The plan
is the contract: an AIDE²-style bi-level RSI loop — tree-search inner agent (draft/debug/
improve), outer propose→evaluate→select loop on private held-out scores under a fixed token
budget, three-layer reward-hacking defenses, and RSI-ladder measurement. Work milestone by
milestone (M1 → M5) and do not start a milestone until the previous one's exit criteria are
demonstrably met.

Run every milestone through this iterative loop until it converges:

1. **Build** — implement the milestone's components exactly as specified in the plan.
2. **Test** — write and run real tests: repo gates (`bash scripts/test-skills.sh rsi-loop`,
   `bash scripts/validate.sh`) plus behavioral tests (e.g. the private-dir deny hook must
   actually block an inner agent reading `private/` — prove it with a failing attempt).
3. **Gap analysis** — a dedicated subagent diffs the implementation against PLAN.md section by
   section and lists every requirement that is missing, weakened, or silently changed. Each gap
   becomes work for the next iteration; if a deviation is genuinely justified, update PLAN.md
   in the same commit and say why.
4. **Adversarial check** — spawn independent adversarial subagents whose only job is to refute:
   try to leak private scores into inner-agent context, reward-hack the harness, fake a passing
   metric, break resume/crash recovery, and disprove the milestone's exit-criteria claim.
   Every confirmed break loops back to step 1.
5. **Bar-raise** — a bar-raiser subagent reviews for fidelity to the paper's protocol and for
   code quality (use /code-review and /simplify), and blocks milestone sign-off until both the
   gap list and adversarial findings are empty.

Repeat 1–5 until a full iteration produces zero gaps and zero surviving adversarial findings —
only then is the milestone done. Commit at each green iteration with conventional-commit
messages and push to the designated branch.

Use these skills and tools while building:

- **skill-creator** — author every skill in the plugin (rsi-loop, autoresearch) and build eval
  batteries for them; use its benchmarking to test skill trigger accuracy.
- **Workflow tool** — implement both loops as Workflow scripts (parallel drafts, budget
  enforcement via `budget`, cheap-model inner agents via per-agent model overrides, structured
  score outputs, journals for transcripts).
- **cc-plugin-authoring** (in-repo plugin) — consult for plugin-authoring gotchas before
  writing commands/hooks.
- **verify** — exercise each change end-to-end before committing, not just unit tests.
- **code-review / simplify** — run at every bar-raise step.
- **uditgoenka/autoresearch** — install for M2 and run the §5.2 chassis A/B experiment exactly
  as pre-registered (2×2 paired runs, same seeds/budget); write results to
  `plugins/rsi-loop/docs/experiments/` and let the pre-registered decision rule pick the
  outer-loop chassis. Do not skip the losing arm's write-up.
- **deep-research pattern** — model the verifier agent's adversarial claim-checking on it.
- **ralph-loop ergonomics** — `/rsi:run` takes max-iterations and a completion condition the
  same way.

Definition of done — all of the following, verified in the final iteration's test run:

- M1–M5 exit criteria all met (standalone `/rsi:autoresearch` solves a task under budget;
  ≥1 accepted generation on private score in a 3-step manual run; a 10-step unattended
  `/rsi:run` with a sane ledger; `/rsi:report` produces ladder-level evidence against the
  hand-tuned baseline and holdout tasks; `/rsi:ignite` runs the Level-2 swap test).
- §5.2 experiment executed and recorded, winner shipped as `/rsi:step`.
- All repo validation green; the plugin promoted into `.claude-plugin/marketplace.json`.
- PLAN.md updated so it matches what was actually built, with every deviation explained.

Everything committed and pushed to `claude/rsi-skills-implementation-o8q1zv`. If a step is
blocked on something only I can decide, ask; otherwise keep iterating until done.
