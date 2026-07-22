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

Implement the `rsi-loop` plugin end-to-end per `plugins/rsi-loop/docs/PLAN.md` on the
designated branch (work lives on `worktree-soft-crafting-bachman`). The plan is the contract: an
AIDE²-style bi-level RSI loop — tree-search inner agent (draft/debug/improve), outer
propose→evaluate→select loop on private held-out scores under a fixed token budget, three-layer
reward-hacking defenses, RSI-ladder measurement. Work milestone by milestone (M1 → M5); don't start
one until the previous's exit criteria are met. **Most is banked** — M1–M4 done, M5 machinery built,
§5.2 resolved (see banner above and `docs/CONTINUATION.md`); live work is **M3 steps 4–10** and the
**M5 ignition run**. Apply the loop below to it.

Run every milestone through this loop until it converges:

1. **Build** — implement the milestone's components exactly as specified.
2. **Test** — repo gates (`bash scripts/test-skills.sh rsi-loop`, `bash scripts/validate.sh`) plus
   behavioral tests (e.g. prove the deny hook blocks an inner agent reading `private/`).
3. **Gap analysis** — a subagent diffs the implementation against PLAN.md section by section, listing
   every requirement missing, weakened, or silently changed. Each gap is next-iteration work; justified
   deviations update PLAN.md in the same commit with a reason.
4. **Adversarial check** — independent refuter subagents: leak private scores into inner-agent context,
   reward-hack the harness, fake a passing metric, break resume/crash recovery, disprove the exit-criteria
   claim. Every confirmed break loops to step 1.
5. **Bar-raise** — reviews protocol fidelity and code quality (/code-review, /simplify), blocking
   sign-off until gap list and adversarial findings are empty.

Repeat 1–5 until a full iteration yields zero gaps and zero surviving adversarial findings — only then
is the milestone done. Commit each green iteration (conventional commits) and push.

Skills/tools: **skill-creator** (author every skill + eval batteries; benchmark trigger accuracy);
**Workflow tool** (both loops as Workflow scripts — parallel drafts, budget enforcement, cheap-model
inner agents via per-agent overrides, structured scores, journals); **cc-plugin-authoring** (in-repo;
gotchas before commands/hooks); **verify** (each change end-to-end); **code-review / simplify** (every
bar-raise); **deep-research pattern** (model the verifier's adversarial claim-checking on it);
**ralph-loop** (`/rsi:run` takes max-iterations + a completion condition). **uditgoenka/autoresearch** —
**§5.2 chassis A/B RESOLVED**, shipped **Arm B** (native `/rsi:step` / `/rsi:run`); autoresearch kept as
pattern reference, not the chassis. Evidence: `docs/experiments/chassis-ab/`.

Definition of done — verified in the final test run; checked boxes banked, one unchecked is live (M5):

- [x] M1–M4 met (standalone `/rsi:autoresearch` solves a task under budget; ≥1 accepted generation on
      private score in a 3-step run; `/rsi:run` produces a sane ledger — run-002 ran to a plateau stop, gen-006
      incumbent; `/rsi:report` gives ladder evidence vs baseline and holdouts — Level 0 & 1 met).
- [x] **M3 steps 4–10** — `/rsi:run` extended from gen-005 to a plateau stop at 10 ledger steps (~37.9M
      inner tokens). The data-perturbation probe (gen-006) is the accepted lever: robust re-baseline
      exposed gen-005's 0.856 as a lucky single seed (true 0.644), and gen-006 clears it at 0.725 on
      `--seeds 3` medians. Evidence in `docs/experiments/run-002/` (ledger + M3-FINDINGS.md).
- [ ] **M5 ignition run** — `/rsi:ignite` runs the Level-2 swap test (machinery built; run pending).
- [x] §5.2 executed and recorded, winner shipped as `/rsi:step` (**Arm B, native**).
- [x] Plugin promoted into `.claude-plugin/marketplace.json`; repo validation green.
- [x] PLAN.md kept matching what was built, every deviation explained (as-built reconciliation done —
      seeds-3 protocol switch, modality-aware probe, plateau outcome, harness phantom-node gap recorded).

Inner eval is **Workflow-tool-only** — drive the outer loop from a Workflow-tool-capable session, not a
headless shell or subagent. Every ledger line must come from real Workflow compute or be marked
not-yet-run; do not fabricate any score.

Commit and push to the branch. If blocked on a decision only I can make, ask; else keep iterating.
