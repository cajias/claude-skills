# Kickoff prompt for implementing rsi-loop

> **Status: build banked (M1–M4 done, M5 machinery built, §5.2 resolved → ship Arm B).**
> M1–M4 exit criteria are met and committed; the native chassis (`/rsi:step` / `/rsi:run`) is
> shipped and the `/rsi:ignite` machinery is built. **To CONTINUE, read `docs/CONTINUATION.md`**
> (the resume snapshot) — the next live phase is **M3 steps 4–10** (extend run-002 from incumbent
> gen-005), then the M5 `/rsi:ignite` ignition run. The prompt below is the original
> **from-scratch contract**, retained for reference; its 5-step loop and Definition of done are
> still the governing standard for any remaining work.

Paste the prompt below into a fresh Claude Code session on this repo to start (or resume) the build.

---

Implement the `rsi-loop` plugin end-to-end, following the spec in
`plugins/rsi-loop/docs/PLAN.md` on the designated branch (the work currently lives on
`worktree-soft-crafting-bachman`). The plan
is the contract: an AIDE²-style bi-level RSI loop — tree-search inner agent (draft/debug/
improve), outer propose→evaluate→select loop on private held-out scores under a fixed token
budget, three-layer reward-hacking defenses, and RSI-ladder measurement. Work milestone by
milestone (M1 → M5) and do not start a milestone until the previous one's exit criteria are
demonstrably met. **Most of this is already banked** — M1–M4 are done, M5 machinery is built,
and §5.2 is resolved (see the status banner above and `docs/CONTINUATION.md`); the remaining live
work is **M3 steps 4–10** and the **M5 ignition run**. Apply the loop below to that remaining work.

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
messages and push to the designated branch. (Most M1–M5 boxes are already checked; the live
work left to run this loop against is **M3 steps 4–10** and the **M5 ignition run** — see
`docs/CONTINUATION.md` for the exact resume steps and the current incumbent, gen-005.)

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
- **uditgoenka/autoresearch** — **§5.2 chassis A/B: DONE / RESOLVED.** The pre-registered
  experiment ran and the decision rule shipped **Arm B** (native `/rsi:step` / `/rsi:run`);
  autoresearch is kept as a pattern reference, not the chassis. Evidence is under
  `plugins/rsi-loop/docs/experiments/chassis-ab/`. No install or run needed to continue.
- **deep-research pattern** — model the verifier agent's adversarial claim-checking on it.
- **ralph-loop ergonomics** — `/rsi:run` takes max-iterations and a completion condition the
  same way.

Definition of done — all of the following, verified in the final iteration's test run.
Checked boxes are already banked; the two unchecked items are the remaining live work:

- [x] M1–M4 exit criteria met (standalone `/rsi:autoresearch` solves a task under budget;
      ≥1 accepted generation on private score in a 3-step manual run; `/rsi:run` produces a sane
      ledger — run-002 banked at step 3, gen-005 incumbent; `/rsi:report` produces ladder-level
      evidence against the hand-tuned baseline and holdout tasks — Level 0 & 1 met).
- [ ] **M3 steps 4–10** — extend the unattended `/rsi:run` from incumbent gen-005 to the full
      10-step ladder (clearest lever: tabular-classification private is stuck at 0.7875 across
      gen-000→005; try a data-perturbation probe mode — feature noise / row resampling / mild shift).
- [ ] **M5 ignition run** — `/rsi:ignite` executes the Level-2 swap test (machinery built; run pending).
- [x] §5.2 experiment executed and recorded, winner shipped as `/rsi:step` (**Arm B, native**).
- [x] Plugin promoted into `.claude-plugin/marketplace.json`; repo validation green.
- [ ] PLAN.md kept matching what was actually built as the remaining runs land, with every
      deviation explained.

The inner eval is **Workflow-tool-only**, so the outer loop must be driven from a
Workflow-tool-capable session — not a headless shell and not a subagent. Every ledger line must
come from real Workflow compute or be clearly marked not-yet-run; do not fabricate any score.

Everything committed and pushed to the designated branch (currently
`worktree-soft-crafting-bachman`). If a step is blocked on something only I can decide, ask;
otherwise keep iterating until done.
