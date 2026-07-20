---
name: iterative-build-loop
description: >-
  Execution harness for driving a milestone-based implementation plan to a real,
  test-verified done — an outer loop over milestones, an inner ultracode loop per
  milestone (each milestone exits only when the end-to-end behavior test it unlocks
  actually RUNS green), plus a consolidation phase after every iteration that turns
  hard-won learnings into durable memory, a skill (via skill-creator), or a project
  hook (via hookify or update-config). Use this WHENEVER you're about to EXECUTE a milestone /
  loop-of-loops plan or iterate a build "until done" — phrases like "execute the
  implementation plan", "run the milestone plan", "iterate until done", "loop of
  loops", "ultracode this plan to green", "build to green", or working through
  milestones with test-gated exits. Every pass makes the harness smarter, so later
  milestones hit less friction than earlier ones. This is the EXECUTE step for a
  plan that already exists; to author or write the milestone plan and its design
  docs in the first place, use the design-plan-docs skill instead.
---

# Iterative Build Loop

An execution harness for a milestone plan — the kind `design-plan-docs` produces. It does
two jobs at once. First, it drives **each milestone to a real, test-verified done**: a
milestone is finished only when the specific behavior test it unlocks runs green, not when
the code merely looks complete. Second, it **compounds** — every iteration ends by turning
what you just learned into durable memory, a skill, or a hook, so the next iteration never
re-hits the same friction. The build gets easier as it goes because the harness gets smarter
as it goes.

Use it right after a plan exists and it's time to *build*. If there's no milestone plan yet,
author one first (see `design-plan-docs`), then come back here to execute it.

## The loop of loops

- **Outer loop over milestones.** The main goal is simple: every milestone's exit
  behavior-test is green. Together those green tests *are* the shippable deliverable — there
  is no separate "done" beyond them.
- **Inner loop per milestone.** Iterate (ultracode-style — keep going until the gate passes)
  on one milestone until its exit criterion actually holds: a specific end-to-end behavior
  test it unlocks runs green. The inner loop has exactly one exit condition — that test
  passing when actually run.
- **Clear context between milestones.** Treat each milestone as self-contained: load *its*
  "context to load" (the files and contracts the plan names for it) fresh, and don't lean on
  session state a sibling milestone happened to leave behind. Cleared context keeps each loop
  cheap (you carry only what this milestone needs) and prevents cross-contamination, where a
  stale assumption from milestone 2 quietly breaks milestone 5.
- **Pick the next runnable milestone** = one whose dependencies are all done. Milestones with
  no dependency edge between them are independent and can run in parallel. Goals stay
  immutable during a run — you're executing the plan, not renegotiating it mid-flight.
- **Track the milestone DAG in the task list.** The DAG *is* your work list, so make it one:
  create a task per milestone up front (`TaskCreate`), mark it `in_progress` when you start it,
  and mark it `completed` only when its full done-criteria hold (exit test green, review clean,
  simplified — see below). This keeps progress observable, survives the context clearing between
  milestones, and turns "pick the next runnable milestone" into a concrete lookup instead of a
  guess. Done milestones stay done, so a resumed run skips them instead of redoing them — and because each is committed as you finish it (see below), that done-ness is recorded in git history too, not just the task list.

## Launching a run

Two Claude Code features make the loop actually loop instead of stopping after one pass:

- **`/goal`** — "Set a goal Claude checks before stopping." It registers a goal Claude must verify is satisfied before it's allowed to stop, so it *is* the loop's stop-gate: as long as the goal's condition is unmet, the run keeps going. This is what turns "attempt the work" into "iterate until the work is genuinely done."
- **the `ultracode` keyword** — include it when you kick off a run to switch on the max-effort, multi-agent, iterate-until-done orchestration this harness relies on. Without it you tend to get a single-pass attempt; with it, the run keeps working the problem until the gate is green.

Map them onto the two loops:

- **Outer loop.** Set the main goal with `/goal`: *every milestone's exit behavior-test is green* (the shippable deliverable). Because `/goal` blocks stopping until that holds, the run carries across milestones until everything is done.
- **Inner loop (per milestone).** Set that milestone's sub-goal with `/goal`: *its exit behavior-test runs green*. Then work the milestone with the `ultracode` keyword. Claude can't stop until that test passes — so the milestone reaches a genuine, test-verified done rather than "looks done."

Recipe: `/goal` (main goal — all exit tests green) → for each runnable milestone: `/goal` (its exit-test-green sub-goal) + iterate with `ultracode` until that test runs green, then clear the quality gate (`code-review` + `simplify`, fixing what they surface) → commit the milestone (message names it) → run the consolidation phase → move to the next runnable milestone → the run stops only once the main `/goal` condition (every exit test green) is satisfied.

## Match the model and agent to the task

When you author the execution workflow, don't make every agent identical. Tier deliberately by
how hard the step is: a mechanical step doesn't need the strongest model, and paying for one
everywhere is wasteful and slow.

- **Strongest model (e.g. Opus) for the hard work** — novel code against frozen contracts,
  integration and wiring, tricky reasoning, adversarial verification of subtle logic. Spend the
  most where a weaker model would quietly get it wrong.
- **Cheaper, faster model (e.g. Sonnet; Haiku for the truly trivial) for mechanical work** —
  running the exit test and diffing its output (the independent verifier), the short
  consolidation retrospective, authoring data or docs (YAML criteria, a README, a manifest).
  These are checkable at a glance, so spend less.
- **Reach for a specialized agent, not a generic one, when a step has a match** — a code-review
  agent for the review pass, a code-simplifier for cleanup, a test-focused agent for behavior
  specs. A purpose-built agent beats general-purpose on its home turf.

Worked example for one milestone: builder → strong (Opus); the independent verifier,
consolidation, and data/doc authoring → cheap (Sonnet/Haiku); the review and simplify passes →
their specialized agents. Matched tiering keeps the whole run affordable and fast without giving
up correctness where it actually matters.

This is a workflow-authoring decision — set the model and agent per step when you build the loop,
not per keystroke while running it. Keep the default lazy: only override the model when you're
confident a tier fits; otherwise inherit the session model.

## Every milestone exits on a real test

The exit criterion is the specific behavior / end-to-end test the milestone unlocks, taken
from the project's BDD test plan. The inner loop stops only when that test goes green when
actually executed — not when the implementation "should" work, not when the diff looks right.
A milestone with no green test is not done, however convincing the code looks. This is what
keeps "done" honest: the test runs, it passes.

But a green test only proves the behavior — it says nothing about whether the change is clean.
A milestone is done only once it has also passed a quality gate. At the end of each milestone
iteration, *before* you mark it done, run the `code-review` skill and the `simplify`
(code-simplification) skill over **that milestone's** changes, and fix every issue they surface.
So the full done-criteria is three things at once: the exit behavior-test runs green, the
`code-review` issues are resolved, and `simplify` has been applied.

Once those three hold, **commit that milestone before moving on**, with a message that names
it. This is load-bearing, not bookkeeping — learned from a real run. The `code-review` and
`simplify` skills operate on the git **diff**, so keeping each milestone on its own commit is
what gives them a clean, scoped diff to act on: the previous milestone is already committed, so
this one's changes stand alone. Leave everything uncommitted across milestones and that diff
blurs into one ever-growing blob — the quality-gate skills have nothing sharp to review and
quietly no-op or fall back to a manual pass. The commit also drops a **resumable checkpoint**: a
cleared-context or resumed run reads straight from disk and history which milestones are
genuinely done, and picks up cleanly at the next runnable one instead of redoing finished work.

Do this per milestone, not deferred to the end of the whole build. The codebase compounds across
milestones — each later one is built on the code the earlier ones left behind — so review debt or
needless complexity you postpone doesn't stay its original size; it makes every following
milestone harder to reason about and change. Clean-as-you-go is what keeps the compounding
positive.

## Consolidation phase — run at the END of every iteration (inner AND outer)

This is the heart of the skill and the reason the loop compounds. After each iteration — each
inner-loop pass that resolved something, and each milestone boundary — pause for a **short**
retrospective before charging into the next one:

1. **Aggregate what you learned this iteration.** What failed? What non-obvious fix or
   workaround actually worked? What friction repeated? What surprised you?
2. **Filter for durability.** Capture only what will recur or help future work; skip
   one-offs. YAGNI applies to memories, skills, and hooks too — capture every hiccup and you
   drown the signal in noise, and future-you stops trusting the store.
3. **Route each durable learning to the right artifact:**
   - **Memory** → a fact, preference, or project note that should persist — *context*, not a
     procedure. Write it to the memory system.
   - **Skill** → a reusable procedure or hard-won gotcha ("next time, do X this way"). Create
     or update it with the `skill-creator` skill — don't hand-roll skill files; skill-creator
     encodes the right structure and triggering.
   - **Behavior-enforcement rule** → warn or block an agent action by pattern ("this should never
     happen silently" — e.g. "don't edit `dist/` directly"), with no command to run. Create it
     with the `hookify` skill.
   - **Command-execution hook** → actually RUN a command on a tool event (deno fmt/lint on edit,
     tests on save, format-on-write). This is a native PostToolUse/PreToolUse command hook in
     `settings.json` — create it with the `update-config` skill, not `hookify`, which can't run
     commands.
4. **Apply it immediately** so the very next iteration or milestone benefits — that's what
   turns a note into leverage instead of a diary entry.

### Which artifact? A quick decision guide

Key the choice on what the learning *is*, not on how it felt to discover:

| The learning… | Route to | Tool | Example |
|---|---|---|---|
| persists **context** — a fact, preference, or project note you'll want recalled | Memory | the memory system | "This repo's integration tests need Postgres on :5433, not the default." |
| encodes a **repeatable procedure** or gotcha — "next time, do it this way" | Skill | `skill-creator` | The three-step dance that finally got the flaky driver to connect. |
| needs **pattern enforcement** — warn/block an agent action, no command to run | Behavior-enforcement rule | `hookify` | Warn when an agent edits `dist/` directly. |
| needs a **command run on a tool event** — fmt, lint, tests, format-on-write | Command-execution hook | `update-config` (native PostToolUse/PreToolUse) | Run `deno fmt` on every edit — `hookify` can't. |

When two feel plausible: does it just need to be *remembered* (memory), *followed* (skill), or
*enforced without anyone remembering* (hook)? Enforcement beats a skill beats a note for
anything that bites when you forget it.

## Why this compounds

Each pass eliminates a failure mode at its source — a repeated fix becomes a skill, a
silent-footgun becomes a hook, a load-bearing fact becomes memory. So the same friction can't
cost you twice, the loop accelerates, and later milestones are genuinely easier than earlier
ones. That payoff is what justifies the small per-iteration overhead of stopping to
consolidate — you're paying a minute now to delete a class of minutes later.

## Guardrails

- **Consolidation is short and timeboxed.** Capture and move on. Don't rabbit-hole mid-build
  polishing a skill — the build is the job; the retrospective serves it, not the reverse.
- **Don't over-capture.** A memory, skill, or hook for every hiccup is noise that buries the
  durable stuff. Durable *and* reusable only.
- **Always use `skill-creator` for skills, `hookify` for behavior-enforcement rules, and
  `update-config` for command-execution hooks** — `hookify` warns or blocks by pattern but can't
  run a command, so a hook that must execute one (fmt, lint, tests) goes through `update-config`.
  Each encodes the right structure and triggering; hand-rolled artifacts skip the parts that make
  them fire reliably later.

## Related

- **`design-plan-docs`** — authors the milestone plan (with test-gated exits and per-milestone
  "context to load") that this skill executes.
- **`skill-creator`** — the tool for creating or updating skills during consolidation.
- **`hookify`** — creates behavior-enforcement rules (warn or block an agent action by pattern)
  during consolidation.
- **`update-config`** — creates command-execution hooks (native PostToolUse/PreToolUse hooks in
  `settings.json` that run a command on a tool event) during consolidation.
- **The memory system** — where persistent facts, preferences, and project notes go.
