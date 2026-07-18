---
description: Run the inner tree-search autoresearch agent standalone on a task directory
argument-hint: "<task-dir> [--gen <generation-dir>] [--seed N]"
---

Run the rsi-loop inner agent (AIDE0-style tree search) standalone on the task the user named.

Steps:

1. Resolve inputs from "$ARGUMENTS":
   - `task-dir`: must contain `task.md`, `score.py`, and `public/`. If relative, resolve
     against the current project; `plugins/rsi-loop/tasks/<name>` also works by bare name.
   - generation dir: `--gen` if given; else the run's `best` pointer if inside an rsi run;
     else `plugins/rsi-loop/baseline/gen-000`.
   - seed: `--seed` if given, else 42.
2. Build a fresh sandbox in the session scratchpad:
   `bash plugins/rsi-loop/scripts/rsi-sandbox.sh <task-dir> <scratchpad>/rsi-autoresearch/<task-name>/sandbox`
   This copies ONLY public materials. Never copy anything else into the sandbox.
3. Read `<generation-dir>/policy.json` and launch the generation's Workflow script:
   `Workflow({scriptPath: "<generation-dir>/inner-agent.workflow.mjs", args: {sandbox, genDir, taskName, seed, policy}})`
   Pass `policy` as the parsed JSON of policy.json. The script tolerates args arriving as a
   JSON string.
4. When the workflow completes, report to the user: best node id, public score, node/bug
   counts, token spend, and the path of the best solution.
5. Public scores only. Do NOT run private scoring unless the user explicitly asks; if they
   do, run `RSI_OUTER_LOOP=1 bash plugins/rsi-loop/scripts/rsi-score.sh --private <task-dir>
<best-solution>` yourself (outer context) and label the result clearly as held-out.

Never expose `private/` paths or contents to any inner agent, and never edit files under the
task directory or the generation harness while a run is active.
