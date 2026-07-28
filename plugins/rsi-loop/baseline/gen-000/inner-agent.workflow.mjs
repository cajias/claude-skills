export const meta = {
  name: "aide0-inner-agent",
  description:
    "AIDE0 baseline tree-search inner agent: 5 parallel drafts, then a greedy debug/improve loop selected on public score, with naive full-history context.",
  phases: [
    {
      title: "Draft",
      detail: "parallel initial solutions, different directions",
    },
    {
      title: "Search",
      detail: "debug random buggy leaf, else improve greedy best",
    },
  ],
};

// ── Inputs (provided by the /rsi:autoresearch or outer-step harness) ──
// args = {
//   sandbox:  absolute path of the inner sandbox (task.md, score.py, public/, nodes/)
//   genDir:   absolute path of the generation directory (prompts/, policy.json, search-engine.mjs)
//   policy:   parsed contents of genDir/policy.json (scripts cannot read files)
//   seed:     integer RNG seed for reproducibility (default 42)
//   taskName: display name for logs
// }
// Harness may deliver args as a JSON string — accept both encodings.
const A = typeof args === "string" ? JSON.parse(args) : args || {};
const sandbox = A.sandbox;
const genDir = A.genDir;
const policy = A.policy || {};
const taskName = A.taskName || "task";
if (!sandbox || !genDir)
  throw new Error("args.sandbox and args.genDir are required");

// ─── INLINED ENGINE (self-contained: Workflow runtime forbids dynamic imports) ───
// Source of truth: baseline/gen-000/search-engine.mjs — kept byte-identical
// (sans export) and enforced by tests/test-shim-self-contained.sh. Edit the
// engine there, then re-inline.
const MIN_BUDGET_UNITS = 20000;

function budgetOk(budget) {
  return !budget.total || budget.remaining() >= MIN_BUDGET_UNITS;
}

// Assemble the prior-node history string the fix operators see. context_mode is
// load-bearing: "summary-only" drops every code body, "full-history" (default)
// keeps them. This genuinely changes the string handed to adapter.fixPrompt.
function buildHistory(nodes, contextMode) {
  const summaryOnly = contextMode === "summary-only";
  return nodes
    .map((n) => {
      const head =
        `### node-${n.id} [op=${n.op}` +
        (n.parent === null ? "" : ` parent=node-${n.parent}`) +
        ` score=${n.public_score} buggy=${n.buggy}]\n` +
        `summary: ${n.summary}`;
      return summaryOnly ? head : head + `\n\`\`\`\n${n.code}\n\`\`\``;
    })
    .join("\n\n");
}

// Record a node with generic keys only. A missing/failed result records a buggy
// node so the search can route a debug op at it.
function record(nodes, id, op, parent, result) {
  nodes.push({
    id,
    op,
    parent,
    code: result ? result.code : "",
    public_score:
      result && typeof result.public_score === "number"
        ? result.public_score
        : 0,
    buggy: result ? Boolean(result.buggy) || result.public_score <= 0 : true,
    summary: result ? result.summary : "agent failed or was skipped",
  });
  return nodes[nodes.length - 1];
}

// Argmax by public_score (the greedy best pick, also the "greedy-public" parent).
function argmaxScore(candidates) {
  return candidates.reduce((a, b) => (b.public_score > a.public_score ? b : a));
}

// Improve-parent rule. selection is load-bearing: "random" picks a uniform
// random non-buggy leaf via deps.rand; "greedy-public" (default) takes argmax.
function pickImproveParent(nodes, selection, rand) {
  const nonBuggy = nodes.filter((n) => !n.buggy);
  const pool = nonBuggy.length ? nonBuggy : nodes;
  if (selection === "random") {
    const childOf = new Set(
      nodes.filter((n) => n.parent !== null).map((n) => n.parent),
    );
    const leaves = pool.filter((n) => !childOf.has(n.id));
    const from = leaves.length ? leaves : pool;
    return from[Math.floor(rand() * from.length)];
  }
  return argmaxScore(pool);
}

// Debug-parent rule (fixed): a uniform random buggy leaf via deps.rand.
function pickDebugParent(nodes, rand) {
  const childOf = new Set(
    nodes.filter((n) => n.parent !== null).map((n) => n.parent),
  );
  const buggyLeaves = nodes.filter((n) => n.buggy && !childOf.has(n.id));
  if (!buggyLeaves.length) return null;
  return buggyLeaves[Math.floor(rand() * buggyLeaves.length)];
}

// The one implemented strategy. For ANY algorithm value we default to it; the
// value is logged so it is demonstrably interpreted, not inert.
const DEFAULT_ALGORITHM = "aide0-greedy-tree-search";

async function search(deps, policy, adapter) {
  const { runAgent, parallel, phase, log, budget, rand } = deps;

  const numDrafts = policy.num_drafts ?? 5;
  const maxNodes = policy.max_nodes ?? 9;
  const model = policy.model ?? "haiku";
  const effort = policy.effort ?? "low";
  const directions =
    policy.draft_directions ??
    Array.from(
      { length: numDrafts },
      (_, i) => `distinct candidate direction #${i + 1}`,
    );
  const algorithm = policy.algorithm ?? DEFAULT_ALGORITHM;
  const contextMode = policy.context_mode ?? "full-history";
  const selection = policy.selection ?? "greedy-public";

  // algorithm is interpreted here: only the greedy tree-search is implemented,
  // so any value falls back to it — but we log which value drove the run.
  if (algorithm !== DEFAULT_ALGORITHM) {
    log(`algorithm "${algorithm}" not implemented; using ${DEFAULT_ALGORITHM}`);
  } else {
    log(`algorithm: ${algorithm}`);
  }

  const rules = adapter.rules;
  const schema = adapter.nodeSchema;

  // ── Phase 1: parallel root drafts ──────────────────────────────────
  phase("Draft");
  const nodes = [];
  const draftResults = await parallel(
    Array.from(
      { length: numDrafts },
      (_, i) => () =>
        runAgent({
          prompt: adapter.draftPrompt({
            id: i,
            direction: directions[i % directions.length],
            rules,
          }),
          label: `draft:node-${i}`,
          phase: "Draft",
          schema,
          model,
          effort,
        }),
    ),
  );
  draftResults.forEach((r, i) => record(nodes, i, "draft", null, r));
  log(`drafts done: scores [${nodes.map((n) => n.public_score).join(", ")}]`);

  // ── Phase 2: greedy debug/improve loop ─────────────────────────────
  phase("Search");
  while (nodes.length < maxNodes) {
    if (budget.total && !budgetOk(budget)) {
      log(
        `stopping early: budget nearly exhausted (${budget.remaining()} left)`,
      );
      break;
    }
    const id = nodes.length;
    const debugTarget = pickDebugParent(nodes, rand);
    let op, target;
    if (debugTarget) {
      op = "debug";
      target = debugTarget;
    } else {
      op = "improve";
      target = pickImproveParent(nodes, selection, rand);
    }
    const history = buildHistory(nodes, contextMode);
    const result = await runAgent({
      prompt: adapter.fixPrompt({ op, id, target, history, rules }),
      label: `${op}:node-${id}<-node-${target.id}`,
      phase: "Search",
      schema,
      model,
      effort,
    });
    record(nodes, id, op, target.id, result);
    log(`node-${id} (${op} of node-${target.id}): score ${nodes[id].public_score}`);
  }

  // ── Best pick (generic; greedy on public_score among non-buggy) ────
  const valid = nodes.filter((n) => !n.buggy);
  const best = argmaxScore(valid.length ? valid : nodes);
  return {
    best: {
      node: best.id,
      public_score: best.public_score,
      artifact_path: adapter.artifactPath(best.id),
      summary: best.summary,
    },
    n_nodes: nodes.length,
    n_buggy: nodes.filter((n) => n.buggy).length,
    nodes: nodes.map(({ code, ...meta }) => meta),
  };
}

// Deterministic Lehmer RNG — Workflow scripts have no Math.random by design.
// Moved out of the engine (kept impure, injected via deps).
let rngState = ((A.seed ?? 42) >>> 0) % 2147483647 || 1;
function rand() {
  rngState = (rngState * 48271) % 2147483647;
  return rngState / 2147483647;
}

const NODE_SCHEMA = {
  type: "object",
  properties: {
    code: {
      type: "string",
      description: "full contents of the solution.py you wrote",
    },
    public_score: {
      type: "number",
      description:
        'the "score" field printed by score.py --public (0 if it failed)',
    },
    buggy: {
      type: "boolean",
      description:
        "true if scoring errored, any per-instance error was non-null, or score is 0",
    },
    summary: { type: "string", description: "one line: approach and result" },
  },
  required: ["code", "public_score", "buggy", "summary"],
  additionalProperties: false,
};

const RULES = [
  `Work ONLY inside ${sandbox} — never read or write anything outside it.`,
  "Use ONLY the public data (task.md, public/, score.py --public). Never reference or attempt to access any private or held-out split; your solution must generalize beyond the public instances, and hard-coding public-instance answers counts as failure.",
  "The solution must be deterministic, standard-library-only, and fast.",
  "Always actually run the public scorer and report its real output — never estimate or fabricate a score.",
].join("\n- ");

function nodePath(id) {
  return `${sandbox}/nodes/node-${id}/solution.py`;
}

// ── gen-000 "solution" adapter ───────────────────────────────────────
// All artifact-kind-specific text lives here (solution.py, task.md, score.py,
// the sandbox wall). The engine sees only these closures.
const adapter = {
  artifactKind: "solution",
  nodeSchema: NODE_SCHEMA,
  rules: RULES,
  artifactPath: nodePath,
  draftPrompt({ id, direction, rules }) {
    return `You are the DRAFT operator of a tree-search research agent working on "${taskName}" (creating node-${id}).

1. Read ${sandbox}/task.md — it defines the solution contract and scoring.
2. Read ${genDir}/prompts/draft.md and follow its method.
3. Direction for THIS draft (differentiate from sibling drafts): ${direction}
4. Write a complete solution to ${nodePath(id)}.
5. Score it: cd ${sandbox} && python3 score.py --public --solution nodes/node-${id}/solution.py --json
6. Return the structured output (exact solution code, real score, buggy flag, one-line summary).

Rules:
- ${rules}`;
  },
  fixPrompt({ op, id, target, history, rules }) {
    const goal =
      op === "debug"
        ? `node-${target.id} is buggy (score ${target.public_score}). Diagnose the failure and produce a FIXED solution.`
        : `node-${target.id} is the current best (score ${target.public_score}). Produce an IMPROVED solution with a strictly better public score.`;
    return `You are the ${op.toUpperCase()} operator of a tree-search research agent working on "${taskName}" (creating node-${id}, child of node-${target.id}).

1. Read ${sandbox}/task.md.
2. Read ${genDir}/prompts/${op}.md and follow its method.
3. ${goal}
4. Full search history so far (all nodes):

${history}

5. Write your new complete solution to ${nodePath(id)}.
6. Score it: cd ${sandbox} && python3 score.py --public --solution nodes/node-${id}/solution.py --json
7. Return the structured output (exact solution code, real score, buggy flag, one-line summary).

Rules:
- ${rules}`;
  },
};

// Bind the Workflow runtime globals into the engine's deps boundary.
const deps = {
  runAgent: (o) =>
    agent(o.prompt, {
      label: o.label,
      phase: o.phase,
      schema: o.schema,
      model: o.model,
      effort: o.effort,
    }),
  parallel,
  phase,
  log,
  budget,
  rand,
};

const r = await search(deps, policy, adapter);

// Re-map the engine's generic output to the EXACT historical return shape.
return {
  task: taskName,
  generation: genDir,
  best: {
    node: r.best.node,
    public_score: r.best.public_score,
    solution_path: r.best.artifact_path,
    summary: r.best.summary,
  },
  n_nodes: r.n_nodes,
  n_buggy: r.n_buggy,
  // Re-attach the artifact-specific per-node `path` the historical shape carried
  // (engine node records are generic and omit it); key order stays identical.
  nodes: r.nodes.map((n) => ({ ...n, path: nodePath(n.id) })),
};
