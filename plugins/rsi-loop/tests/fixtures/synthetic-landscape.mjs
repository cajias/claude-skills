// Deterministic synthetic search landscape for exercising search-engine.mjs
// without any LLM / Workflow runtime. Shared by the Step-1 polymorphism test and
// the Step-4 ignition-instrument test — keep it clean and reusable.
//
// The landscape is a 1-D quality parameter theta in [0,1] with an optimum at
// theta* = 0.8. A node's public_score is a smooth quadratic bump around theta*
// plus a tiny (seed, node)-derived noise term, so scores are distinct but the
// ranking is stable. Root drafts spread deterministically across [0,1] by index;
// fix operators step halfway toward theta*.

const THETA_STAR = 0.8;
const PHI_FRAC = 0.6180339887498949; // golden-ratio fractional step spreads [0,1)
const NOISE_SCALE = 1e-3;

// Seedable Lehmer (MINSTD) RNG factory. No Math.random / Date.now (both are
// Workflow-forbidden and would break determinism).
export function makeRng(seed) {
  let state = (seed >>> 0) % 2147483647 || 1;
  return function rand() {
    state = (state * 48271) % 2147483647;
    return state / 2147483647;
  };
}

// One reproducible draw keyed purely by (seed, node) — order-independent, so
// score() stays a pure function of its arguments.
function noise(seed, node) {
  const r = makeRng((seed >>> 0) * 2654435761 + (node >>> 0) + 1);
  return (r() - 0.5) * NOISE_SCALE;
}

// Landscape scorer: 1 - (theta - theta*)^2 + eps. Always > 0 for theta in [0,1]
// (min ~0.36 at theta=0), so a node is only "buggy" when forced.
export function score(theta, seed, node) {
  return 1 - (theta - THETA_STAR) ** 2 + noise(seed, node);
}

// Mock proposer: step halfway from the parent toward the optimum.
export function propose(parentTheta) {
  return parentTheta + (THETA_STAR - parentTheta) / 2;
}

// Deterministic theta for a root draft, spread across [0,1) by index.
export function draftTheta(index) {
  return ((index + 1) * PHI_FRAC) % 1;
}

const DRAFT_RE = /^draft:node-(\d+)$/;
const FIX_RE = /^(debug|improve):node-(\d+)<-node-(\d+)$/;

// Build a deterministic deps.runAgent-compatible closure over a shared theta
// ledger. It reads the engine's `label` to recover op + node ids, computes the
// node's theta (draft => spread by index; fix => propose from the target), and
// returns a generic node result. `buggyIds` forces specific node ids buggy so a
// test can exercise debug routing.
export function makeRunAgent({ seed, thetas, buggyIds = new Set() }) {
  return async function runAgent(call) {
    const label = call.label || "";
    let id, theta;
    const d = DRAFT_RE.exec(label);
    const f = FIX_RE.exec(label);
    if (d) {
      id = Number(d[1]);
      theta = draftTheta(id);
    } else if (f) {
      id = Number(f[2]);
      const targetId = Number(f[3]);
      theta = propose(thetas.get(targetId) ?? 0);
    } else {
      throw new Error(`unrecognized agent label: ${label}`);
    }
    thetas.set(id, theta);
    const forced = buggyIds.has(id);
    const s = score(theta, seed, id);
    return {
      code: `theta=${theta}`,
      public_score: forced ? 0 : s,
      buggy: forced || s <= 0,
      summary: `node-${id}`,
    };
  };
}

// Full deterministic deps object. `logs` captures deps.log lines (needed to
// assert the engine interprets `algorithm`). `budgetTotal` of 0 leaves max_nodes
// as the sole loop bound.
export function makeDeps({
  seed = 42,
  budgetTotal = 0,
  buggyIds = new Set(),
} = {}) {
  const thetas = new Map();
  const logs = [];
  return {
    thetas,
    logs,
    runAgent: makeRunAgent({ seed, thetas, buggyIds }),
    parallel: (thunks) => Promise.all(thunks.map((t) => t())),
    phase: () => {},
    log: (msg) => logs.push(String(msg)),
    budget: { total: budgetTotal, remaining: () => Number.MAX_SAFE_INTEGER },
    rand: makeRng(seed),
  };
}
