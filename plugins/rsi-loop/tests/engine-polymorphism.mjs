// Deterministic polymorphism + policy-field proof for search-engine.mjs.
// Runs under plain `node` in well under 1s with zero network/LLM. Driven by
// tests/test-engine-polymorphism.sh; exits non-zero on any failed assertion.
import { search } from "../baseline/gen-000/search-engine.mjs";
import { makeDeps } from "./fixtures/synthetic-landscape.mjs";

let pass = 0;
let fail = 0;
function ok(cond, label) {
  if (cond) {
    pass++;
    console.log(`  ok   ${label}`);
  } else {
    fail++;
    console.log(`  FAIL ${label}`);
  }
}

// Two stub adapters that differ ONLY in artifact-specific strings. These live in
// the TEST, so they MAY name "solution"/"scaffold" — the engine never sees the
// strings, only the closures.
function makeStub(kind, ext) {
  const capturedHistories = [];
  return {
    capturedHistories,
    artifactKind: kind,
    nodeSchema: { type: "object" },
    rules: `Work only inside the ${kind} sandbox.`,
    artifactPath: (id) => `/sandbox/nodes/node-${id}/${kind}.${ext}`,
    draftPrompt: ({ id, direction }) =>
      `[${kind}] draft node-${id} dir=${direction} target=${kind}.${ext}`,
    fixPrompt: ({ op, id, target, history }) => {
      capturedHistories.push(history);
      return `[${kind}] ${op} node-${id}<-node-${target.id} target=${kind}.${ext}\n${history}`;
    },
  };
}

const basePolicy = {
  num_drafts: 3,
  max_nodes: 6,
  model: "haiku",
  effort: "low",
  draft_directions: ["a", "b", "c"],
  algorithm: "aide0-greedy-tree-search",
  context_mode: "full-history",
  selection: "greedy-public",
};

const SEED = 42;

// ── 1. Isomorphism: identical policy + seed + deps construction, adapters that
//       differ only in artifact strings, MUST produce identical ledgers. ──────
const solutionStub = makeStub("solution", "py");
const scaffoldStub = makeStub("scaffold", "mjs");
const rA = await search(makeDeps({ seed: SEED }), basePolicy, solutionStub);
const rB = await search(makeDeps({ seed: SEED }), basePolicy, scaffoldStub);

const draftsA = rA.nodes.filter((n) => n.op === "draft").length;
ok(draftsA === basePolicy.num_drafts, `draft count == num_drafts (${draftsA})`);
ok(
  rB.nodes.filter((n) => n.op === "draft").length === basePolicy.num_drafts,
  "scaffold draft count == num_drafts",
);
ok(
  rA.n_nodes === rB.n_nodes,
  `same total node count (${rA.n_nodes} == ${rB.n_nodes})`,
);
ok(
  rA.n_nodes <= basePolicy.max_nodes,
  `node count <= max_nodes (${rA.n_nodes} <= ${basePolicy.max_nodes})`,
);

const keysA = rA.nodes.map((n) => Object.keys(n).sort().join(","));
const keysB = rB.nodes.map((n) => Object.keys(n).sort().join(","));
ok(
  JSON.stringify(keysA) === JSON.stringify(keysB),
  "identical node-ledger key set",
);
const expectedKeys = "buggy,id,op,parent,public_score,summary";
ok(
  keysA.every((k) => k === expectedKeys),
  `ledger keys are generic (${expectedKeys})`,
);
ok(!rA.nodes.some((n) => "code" in n), "code stripped from returned nodes");

ok(
  JSON.stringify(rA.nodes) === JSON.stringify(rB.nodes),
  "identical node ledgers (isomorphism proof)",
);
ok(
  rA.best.node === rB.best.node,
  `identical greedy best-pick index (node-${rA.best.node})`,
);

// Adapter is the ONLY thing that injects artifact specifics: same ledger, but
// artifact paths differ by kind/extension.
ok(
  rA.best.artifact_path.endsWith(".py") &&
    rB.best.artifact_path.endsWith(".mjs"),
  "artifact_path is adapter-specific, ledger is not",
);

// ── 2. Debug routing: a buggy draft routes a debug op at it. ─────────────────
const rDebug = await search(
  makeDeps({ seed: SEED, buggyIds: new Set([0]) }),
  basePolicy,
  makeStub("solution", "py"),
);
const debugNode = rDebug.nodes.find((n) => n.op === "debug");
ok(!!debugNode, "buggy draft routes a debug op");
ok(
  debugNode && debugNode.parent === 0,
  "debug op targets the buggy node (parent==0)",
);
// With no buggy nodes, no debug op appears (all fix ops are improve).
const rClean = await search(
  makeDeps({ seed: SEED }),
  basePolicy,
  makeStub("solution", "py"),
);
ok(
  !rClean.nodes.some((n) => n.op === "debug"),
  "no debug op when nothing is buggy",
);

// ── 3. selection is load-bearing: greedy-public vs random pick different improve
//       parents on the same multi-draft state. ────────────────────────────────
const improvePolicy = { ...basePolicy, max_nodes: 4 }; // 3 drafts + exactly 1 improve
const greedyDeps = makeDeps({ seed: SEED });
const rGreedy = await search(
  greedyDeps,
  improvePolicy,
  makeStub("solution", "py"),
);
const greedyImprove = rGreedy.nodes.find((n) => n.op === "improve");

const randomDeps = makeDeps({ seed: SEED });
randomDeps.rand = () => 0; // force the first non-buggy leaf
const rRandom = await search(
  randomDeps,
  { ...improvePolicy, selection: "random" },
  makeStub("solution", "py"),
);
const randomImprove = rRandom.nodes.find((n) => n.op === "improve");

ok(
  !!greedyImprove && !!randomImprove,
  "both selection modes produced an improve op",
);
ok(
  greedyImprove.parent !== randomImprove.parent,
  `selection changes improve parent (greedy=${greedyImprove.parent} random=${randomImprove.parent})`,
);

// ── 4. context_mode is load-bearing: summary-only drops code bodies. ─────────
const fullStub = makeStub("solution", "py");
await search(makeDeps({ seed: SEED }), basePolicy, fullStub);
const summaryStub = makeStub("solution", "py");
await search(
  makeDeps({ seed: SEED }),
  { ...basePolicy, context_mode: "summary-only" },
  summaryStub,
);
const fullHist = fullStub.capturedHistories[0];
const summaryHist = summaryStub.capturedHistories[0];
ok(
  fullHist.includes("```") && fullHist.includes("theta="),
  "full-history includes code bodies",
);
ok(
  !summaryHist.includes("```") && !summaryHist.includes("theta="),
  "summary-only excludes code bodies",
);
ok(
  summaryHist.includes("summary:"),
  "summary-only still carries node summaries",
);

// ── 5. algorithm is interpreted, not inert: unknown value still runs and the
//       chosen algorithm is logged. ─────────────────────────────────────────
const unkDeps = makeDeps({ seed: SEED });
const rUnknown = await search(
  unkDeps,
  { ...basePolicy, algorithm: "aide-human-tuned-tree-search" },
  makeStub("solution", "py"),
);
ok(
  rUnknown.n_nodes === basePolicy.max_nodes,
  "unknown algorithm still runs (fallback)",
);
ok(
  unkDeps.logs.some((l) => l.includes("aide-human-tuned-tree-search")),
  "unknown algorithm value logged",
);
const defDeps = makeDeps({ seed: SEED });
await search(defDeps, basePolicy, makeStub("solution", "py"));
ok(
  defDeps.logs.some((l) => l.includes("algorithm: aide0-greedy-tree-search")),
  "default algorithm logged",
);

console.log(`\nengine polymorphism assertions: ${pass} passed, ${fail} failed`);
process.exit(fail === 0 ? 0 : 1);
