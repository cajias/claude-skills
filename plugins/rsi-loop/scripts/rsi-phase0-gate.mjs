// Phase-0 power gate (PLAN.md §6.1.6, §6.1 lines 775-776).
//
// THE COVENANT that unblocks real A/B spend. It is a DETERMINISTIC PROXY: it
// drives the REAL search() engine over a synthetic landscape via injected
// closures — zero network, zero LLM, <2s — and proves the *assembled* pipeline
// (engine → best-so-far trajectory → rsi-ignition.py decide) can resolve a
// planted +0.15 policy-lift positive at K=3 while returning NO_RESULT on a
// 0-effect and a ~0.03 effect. If the positive control does NOT return
// SUPPORTED, the instrument has not demonstrated power and A/B budget MUST NOT
// be released.
//
// LITERAL-POLICY-LIFT PROOF: in the positive control the ONLY difference
// between the control and ignited arms is the value of num_drafts / max_nodes
// in the policy dict. Same engine, same adapter, same landscape, same seeds —
// the gap is created purely by a fixed-schema knob change (the §6.1.1 cp-lift
// mechanism). The gate asserts this diff programmatically (see literalLiftDiff).
//
// GATE-LOCAL LANDSCAPE: the shared fixture's propose() steps a fixed HALFWAY
// toward theta*=0.8 and draftTheta() spreads by golden ratio — under those,
// both arms saturate near 1.0 and the policy knobs barely move the asymptote.
// So the gate reuses the fixture's RNG + scorer (the noise model and theta*),
// but supplies its own draft spread (higher draft index → closer to theta*, so
// more drafts reach a better start) and a SMALLER propose step (so more
// max_nodes = more improve steps = a measurably higher plateau). This keeps the
// shared fixture untouched (Step-1's test stays green) while making the two
// policy knobs the sole driver of the realized gap. base/slope/step below are
// the calibration knobs — tuned so stock(2,4) vs rigged(8,12) ≈ 0.15 and
// stock(2,4) vs barely(3,5) ≈ 0.03 through the real engine.

import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { search } from "../baseline/gen-000/search-engine.mjs";
import { makeRng, score } from "../tests/fixtures/synthetic-landscape.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const IGNITION = join(HERE, "rsi-ignition.py");

const THETA_STAR = 0.8;
const SEEDS = [42, 43, 44];
const SIGMA_D = 0.05; // planning value (§6.1.4); MDE(3)=2.487·0.05/√3 ≈ 0.072

// Gate-local landscape calibration (the tuning knobs — see header).
const DRAFT_BASE = 0.25; // theta of draft #0
const DRAFT_SLOPE = 0.07; // extra theta per draft index (more drafts → higher start)
const DRAFT_CAP = 0.79; // never overshoot theta* from a draft
const PROPOSE_STEP = 0.1; // fraction of the gap to theta* closed per improve step

// The three §6.1.6 policies. All fields shared except the two lifted knobs, so
// the positive control is provably a literal num_drafts/max_nodes lift.
const BASE_POLICY = {
  model: "haiku",
  effort: "low",
  algorithm: "aide0-greedy-tree-search",
  context_mode: "full-history",
  selection: "greedy-public",
};
const STOCK = { ...BASE_POLICY, num_drafts: 2, max_nodes: 4 };
const RIGGED = { ...BASE_POLICY, num_drafts: 8, max_nodes: 12 };
const BARELY = { ...BASE_POLICY, num_drafts: 3, max_nodes: 5 };

const DRAFT_RE = /^draft:node-(\d+)$/;
const FIX_RE = /^(debug|improve):node-(\d+)<-node-(\d+)$/;

// Gate-local draft spread: higher index → closer to theta* (capped short of it).
const draftTheta = (i) => Math.min(DRAFT_BASE + DRAFT_SLOPE * i, DRAFT_CAP);
// Gate-local proposer: close PROPOSE_STEP of the remaining gap to theta*.
const propose = (parentTheta) =>
  parentTheta + PROPOSE_STEP * (THETA_STAR - parentTheta);

// A deterministic deps for one engine run: runAgent recovers op+ids from the
// engine's label, computes theta (draft → spread by index; fix → propose from
// the target), and scores via the SHARED fixture scorer. No LLM, no I/O.
function makeGateDeps(seed) {
  const thetas = new Map();
  return {
    runAgent: async (call) => {
      const label = call.label || "";
      const d = DRAFT_RE.exec(label);
      const f = FIX_RE.exec(label);
      let id, theta;
      if (d) {
        id = Number(d[1]);
        theta = draftTheta(id);
      } else if (f) {
        id = Number(f[2]);
        theta = propose(thetas.get(Number(f[3])) ?? 0);
      } else {
        throw new Error(`unrecognized agent label: ${label}`);
      }
      thetas.set(id, theta);
      const s = score(theta, seed, id);
      return {
        code: "",
        public_score: s,
        buggy: s <= 0,
        summary: `node-${id}`,
      };
    },
    parallel: (thunks) => Promise.all(thunks.map((t) => t())),
    phase: () => {},
    log: () => {},
    budget: { total: 0, remaining: () => Number.MAX_SAFE_INTEGER },
    rand: makeRng(seed),
  };
}

// Minimal generic adapter — the gate exercises the engine, not any artifact kind.
const ADAPTER = {
  rules: "",
  nodeSchema: { type: "object" },
  artifactPath: (id) => `/gate/node-${id}`,
  draftPrompt: () => "",
  fixPrompt: () => "",
};

// Best-so-far trajectory B(g): running max of node public_score after each node.
function bestSoFar(nodes) {
  let run = -Infinity;
  return nodes.map((n) => (run = Math.max(run, n.public_score)));
}

// Run one policy arm across all seeds → { seed: B(g)[] }.
async function runArm(policy) {
  const arm = {};
  for (const seed of SEEDS) {
    const r = await search(makeGateDeps(seed), policy, ADAPTER);
    arm[seed] = bestSoFar(r.nodes);
  }
  return arm;
}

// Align every curve of both arms to a common length by HOLDING the final value.
// Best-so-far is monotone, so once an arm hits its node cap it plateaus at its
// final best — padding the shorter arm forward with that plateau is honest, not
// a fabricated gain. G = (max node count over both arms) − 1.
function alignPair(control, ignited) {
  const lens = SEEDS.flatMap((s) => [control[s].length, ignited[s].length]);
  const target = Math.max(...lens);
  const pad = (c) =>
    c.length >= target
      ? c
      : c.concat(Array(target - c.length).fill(c[c.length - 1]));
  const shape = (arm) =>
    Object.fromEntries(SEEDS.map((s) => [String(s), pad(arm[s])]));
  return { G: target - 1, control: shape(control), ignited: shape(ignited) };
}

// Shell out to the REAL verdict instrument (no re-implementation of decide).
function decide(payload, plantedCleared) {
  const out = execFileSync(
    "python3",
    [
      IGNITION,
      "decide",
      "--planted-positive-cleared",
      plantedCleared ? "true" : "false",
    ],
    { input: JSON.stringify(payload), encoding: "utf8" },
  );
  return JSON.parse(out);
}

// Keys where two policy dicts differ (sorted). Proves the literal lift.
function literalLiftDiff(a, b) {
  const keys = new Set([...Object.keys(a), ...Object.keys(b)]);
  return [...keys].filter((k) => a[k] !== b[k]).sort();
}

async function main() {
  const results = [];
  const record = (name, wantVerdict, res, extra = "") =>
    results.push({
      name,
      pass: res.verdict === wantVerdict,
      wantVerdict,
      gotVerdict: res.verdict,
      gap: res.delta_A,
      mde: res.mde,
      extra,
    });

  // ── Positive: control=stock(2,4), ignited=rigged(8,12) → SUPPORTED ─────────
  const stock = await runArm(STOCK);
  const rigged = await runArm(RIGGED);
  const posPair = alignPair(stock, rigged);
  const posPayload = { seeds: SEEDS, sigma_d: SIGMA_D, ...posPair };
  const diff = literalLiftDiff(STOCK, RIGGED);
  const liftOk =
    JSON.stringify(diff) === JSON.stringify(["max_nodes", "num_drafts"]);
  record(
    "POSITIVE  stock(2,4) vs rigged(8,12)",
    "SUPPORTED",
    decide(posPayload, true),
    `literal-lift diff=${JSON.stringify(diff)} ${liftOk ? "(ONLY num_drafts/max_nodes ✓)" : "(UNEXPECTED ✗)"}`,
  );
  if (!liftOk) results[results.length - 1].pass = false;

  // ── Negative: control=stock, ignited=stock (effect 0) → NO_RESULT ──────────
  const negPair = alignPair(stock, await runArm(STOCK));
  record(
    "NEGATIVE  stock(2,4) vs stock(2,4)",
    "NO_RESULT",
    decide({ seeds: SEEDS, sigma_d: SIGMA_D, ...negPair }, true),
  );

  // ── Underpowered: stock vs barely-better(3,5), gap ≈0.03 < MDE → NO_RESULT ──
  const underPair = alignPair(stock, await runArm(BARELY));
  record(
    "UNDERPWR  stock(2,4) vs barely(3,5)",
    "NO_RESULT",
    decide({ seeds: SEEDS, sigma_d: SIGMA_D, ...underPair }, true),
  );

  // ── Power precondition: same positive arms, but instrument could NOT clear
  //    its planted positive → NO_RESULT regardless (the hard M5 gate). ────────
  record(
    "PRECOND   positive arms, planted_positive_cleared=false",
    "NO_RESULT",
    decide(posPayload, false),
  );

  // ── Report ─────────────────────────────────────────────────────────────────
  console.log(
    "Phase-0 power gate — deterministic proxy over the real search() engine\n",
  );
  console.log(
    `landscape: draftTheta=${DRAFT_BASE}+${DRAFT_SLOPE}·i (cap ${DRAFT_CAP}), ` +
      `propose closes ${PROPOSE_STEP} of gap to θ*=${THETA_STAR}; σ_d=${SIGMA_D} → MDE(3)=${results[0].mde}\n`,
  );
  let allPass = true;
  for (const r of results) {
    allPass = allPass && r.pass;
    console.log(
      `  ${r.pass ? "PASS" : "FAIL"}  ${r.name}\n` +
        `        realized gap ΔA=${r.gap}  verdict=${r.gotVerdict} (want ${r.wantVerdict})` +
        (r.extra ? `\n        ${r.extra}` : ""),
    );
  }
  console.log(
    `\nrealized gaps: positive=${results[0].gap} (≫MDE ${results[0].mde}), ` +
      `negative=${results[1].gap}, underpowered=${results[2].gap} (<MDE)`,
  );

  if (allPass) {
    console.log(
      "\nGATE CLEARS: instrument demonstrated power — A/B spend may be released.",
    );
    process.exit(0);
  }
  console.log(
    "\nGATE FAILED: instrument cannot resolve its planted positive — A/B budget MUST NOT be released.",
  );
  process.exit(1);
}

main().catch((e) => {
  console.error("phase0-gate error:", e);
  process.exit(1);
});
