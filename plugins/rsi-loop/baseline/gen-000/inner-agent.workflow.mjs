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

// The pure search core travels with the generation dir (proposer copies the
// whole dir). The Workflow tool runs this body inside an async function, so a
// static `import` is illegal and a relative dynamic import cannot resolve —
// import the engine by its absolute path under genDir.
const { search } = await import(`${genDir}/search-engine.mjs`);

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
