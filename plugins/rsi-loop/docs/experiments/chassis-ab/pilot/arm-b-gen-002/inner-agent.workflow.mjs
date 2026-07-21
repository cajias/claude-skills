export const meta = {
  name: "aide2-adversarial-probe-selected-agent",
  description:
    "AIDE0 tree-search inner agent with ONE mutation: the search runs on CLEAN public score (never trading away public quality), then a SINGLE SHARED adversarial probe battery — hard held-out-style paraphrase/structural perturbations of the PUBLIC inputs, synthesized ONCE by a decoupled probe author that never sees any candidate's code and computes the correct answers itself from the task definition — is applied IDENTICALLY to the near-best-public candidates. The final best is re-ranked by probe score, with an anti-saturation guard: a flat/uniform (non-discriminating) or oracle-unavailable battery falls back to deterministic top-public selection, so healthy tasks (bin-packing, tabular) do not regress while a paraphrase-overfit instruction-routing lookup is demoted below a synonym-tolerant parser.",
  phases: [
    {
      title: "Draft",
      detail: "parallel initial solutions, different directions",
    },
    {
      title: "Search",
      detail:
        "debug random buggy leaf, else improve greedy best on public score",
    },
    {
      title: "Probe",
      detail:
        "synthesize one shared adversarial probe battery, apply it identically to near-best-public candidates, re-rank the final best (with anti-saturation fallback to top-public)",
    },
  ],
};

// ── Inputs (provided by the /rsi:autoresearch or outer-step harness) ──
// args = {
//   sandbox:  absolute path of the inner sandbox (task.md, score.py, public/, nodes/)
//   genDir:   absolute path of the generation directory (prompts/, policy.json)
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

const NUM_DRAFTS = policy.num_drafts ?? 5;
const MAX_NODES = policy.max_nodes ?? 9;
const MODEL = policy.model ?? "haiku";
const EFFORT = policy.effort ?? "low";
// ── Probe-phase knobs ────────────────────────────────────────────────
// How many of the near-best-public candidates the shared probe re-ranks.
const PROBE_TOP_K = policy.probe_top_k ?? 3;
// Public-score tolerance for eligibility: only candidates whose public score
// is within this margin of the best public score may WIN via the probe. This
// caps any public sacrifice — a strictly worse-public node (e.g. a weaker
// tabular model) can never displace the strong baseline, which is what fixes
// the gen-001 tabular regression. On instruction-routing every top candidate
// is public 1.0 (exact ties), so the whole tier is eligible.
const PROBE_PUBLIC_MARGIN = policy.probe_public_margin ?? 0.02;
// Anti-saturation guard: the probe only OVERRIDES the top-public pick when the
// candidates' probe scores are spread by at least this much. A flat/uniform
// result (all ~equal, e.g. all 1.0 or all 0.0) means the battery did not
// discriminate — treat it as a FAILED discriminator and fall back to
// deterministic top-public selection (so healthy tasks do not regress).
const PROBE_SPREAD_EPS = policy.probe_spread_eps ?? 0.15;
// Size of the shared adversarial battery.
const PROBE_BATTERY_SIZE = policy.probe_battery_size ?? 12;
// The real per-generation directions live in policy.json (`draft_directions`),
// which the harness always passes. This inline list is only a last-resort
// default for a hand-run with no policy — keep it generic, not a shadow copy of
// any specific generation's tuned directions.
const DIRECTIONS =
  policy.draft_directions ??
  Array.from(
    { length: NUM_DRAFTS },
    (_, i) => `distinct solution direction #${i + 1}`,
  );

// Deterministic Lehmer RNG — Workflow scripts have no Math.random by design.
let rngState = ((A.seed ?? 42) >>> 0) % 2147483647 || 1;
function rand() {
  rngState = (rngState * 48271) % 2147483647;
  return rngState / 2147483647;
}

function clamp01(x) {
  if (typeof x !== "number" || Number.isNaN(x)) return 0;
  if (x < 0) return 0;
  if (x > 1) return 1;
  return x;
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

// Battery authored ONCE, decoupled from every solver. Each probe is a full
// positional-argument call plus the correct expected output the author derives
// from the task definition itself.
const PROBE_BATTERY_SCHEMA = {
  type: "object",
  properties: {
    oracle_available: {
      type: "boolean",
      description:
        "true ONLY if, from the task definition alone, you can compute the exact correct output for a novel input with certainty (a deterministic symbolic task). false if the correct output depends on held-out data, on an optimum you cannot compute by hand, or on a learned model — in that case return an empty probes array.",
    },
    entry: {
      type: "string",
      description:
        "name of the solution entry function from task.md (e.g. solve, pack, predict)",
    },
    probes: {
      type: "array",
      description:
        "hard, held-out-STYLE perturbed inputs (paraphrase/synonym/structural variants of the PUBLIC input format) with the correct expected output you computed yourself. Empty if oracle_available is false.",
      items: {
        type: "object",
        properties: {
          args: {
            type: "array",
            description:
              "positional arguments to pass to the entry function for this probe",
          },
          expected: {
            type: "string",
            description:
              "the exact correct output for this input, as a string (compared via str(result).strip())",
          },
          note: {
            type: "string",
            description: "one phrase: which perturbation this exercises",
          },
        },
        required: ["args", "expected"],
        additionalProperties: false,
      },
    },
    note: {
      type: "string",
      description: "one line: how the battery was built",
    },
  },
  required: ["oracle_available", "entry", "probes"],
  additionalProperties: false,
};

const PROBE_EVAL_SCHEMA = {
  type: "object",
  properties: {
    results: {
      type: "array",
      description: "one entry per candidate you were given, in any order",
      items: {
        type: "object",
        properties: {
          node: { type: "integer", description: "candidate node id" },
          n_correct: {
            type: "integer",
            description:
              "probes on which this candidate's output matched expected",
          },
          n_total: {
            type: "integer",
            description: "probes actually run for this candidate",
          },
          probe_score: {
            type: "number",
            description:
              "n_correct / n_total in [0,1] — the REAL measured fraction, never estimated (0 if the candidate crashed on every probe)",
          },
        },
        required: ["node", "n_correct", "n_total", "probe_score"],
        additionalProperties: false,
      },
    },
    note: { type: "string", description: "one line: how the driver ran" },
  },
  required: ["results"],
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

// Naive full-history context — deliberately weak (AIDE0), headroom for the
// outer loop to discover context engineering.
function historyText(nodes) {
  return nodes
    .map(
      (n) =>
        `### node-${n.id} [op=${n.op}${n.parent === null ? "" : ` parent=node-${n.parent}`} score=${n.public_score} buggy=${n.buggy}]\n` +
        `summary: ${n.summary}\n\`\`\`python\n${n.code}\n\`\`\``,
    )
    .join("\n\n");
}

function draftPrompt(id, direction) {
  return `You are the DRAFT operator of a tree-search research agent working on "${taskName}" (creating node-${id}).

1. Read ${sandbox}/task.md — it defines the solution contract and scoring.
2. Read ${genDir}/prompts/draft.md and follow its method.
3. Direction for THIS draft (differentiate from sibling drafts): ${direction}
4. Write a complete solution to ${nodePath(id)}.
5. Score it: cd ${sandbox} && python3 score.py --public --solution nodes/node-${id}/solution.py --json
6. Return the structured output (exact solution code, real score, buggy flag, one-line summary).

Rules:
- ${RULES}`;
}

function fixPrompt(op, id, target, nodes, promptFile) {
  const goal =
    op === "debug"
      ? `node-${target.id} is buggy (score ${target.public_score}). Diagnose the failure and produce a FIXED solution.`
      : `node-${target.id} is the current best (score ${target.public_score}). Produce an IMPROVED solution with a strictly better public score.`;
  return `You are the ${op.toUpperCase()} operator of a tree-search research agent working on "${taskName}" (creating node-${id}, child of node-${target.id}).

1. Read ${sandbox}/task.md.
2. Read ${genDir}/prompts/${promptFile} and follow its method.
3. ${goal}
4. Full search history so far (all nodes):

${historyText(nodes)}

5. Write your new complete solution to ${nodePath(id)}.
6. Score it: cd ${sandbox} && python3 score.py --public --solution nodes/node-${id}/solution.py --json
7. Return the structured output (exact solution code, real score, buggy flag, one-line summary).

Rules:
- ${RULES}`;
}

// Probe author: decoupled from every candidate (never shown any node's code).
// It reads the task definition and public inputs, then synthesizes ONE hard,
// held-out-STYLE battery whose correct answers IT computes from task semantics.
function probeAuthorPrompt() {
  return `You are the PROBE-AUTHOR of a tree-search research agent working on "${taskName}". You do NOT write or see any candidate solution — you build a SINGLE, SHARED adversarial probe battery that will be used to pick the most GENERAL of several already-working candidates.

1. Read ${sandbox}/task.md — note the exact entry function name/signature and the answer format.
2. Read ${sandbox}/public/instances.json to learn the PUBLIC input phrasings/format.
3. Read ${genDir}/prompts/probe-battery.md and follow its method.
4. Decide oracle_available: it is true ONLY if you can, from the task definition ALONE, compute the exact correct output for a NOVEL input with certainty (a deterministic, symbolic task). If the correct output depends on data you cannot see, on an optimum you cannot compute by hand, or on a learned model, set oracle_available=false and return an EMPTY probes array — do not guess answers.
5. If oracle_available: synthesize ${PROBE_BATTERY_SIZE} HARD probes. Each is a held-out-STYLE perturbation of the public input format — a paraphrase, synonym substitution, reordered/restructured clause, different surface form, or edge-case argument — that a genuine solver handles but a solution that merely memorized the exact public phrasings would FAIL. For each probe give the positional \`args\` for the entry function and the \`expected\` output that YOU computed from the task's rules. Cover the full range of operations/behaviors, not just one.

Return the structured battery (oracle_available, entry, probes[], note).

Rules:
- ${RULES}
- These are held-out-STYLE probes SYNTHESIZED from the public task definition. They are NOT a private/held-out split and must never reference one.
- Report only probes whose expected answer you are CERTAIN of from the task rules. Never fabricate an answer you cannot derive.`;
}

// Probe evaluator: applies the ONE shared battery IDENTICALLY to every
// candidate. It only runs code and reports measured fractions; it does not
// author or judge the battery, so selection stays decoupled from the solver.
function probeEvalPrompt(battery, candidates) {
  const cand = candidates.map((c) => `  - node-${c.id}: ${c.path}`).join("\n");
  return `You are the PROBE-EVALUATOR of a tree-search research agent working on "${taskName}". Apply ONE fixed, shared probe battery IDENTICALLY to each candidate and report the REAL measured pass fractions. Do NOT modify the battery, and do NOT change any candidate's solution file.

1. Read ${sandbox}/task.md to confirm the entry function "${battery.entry}" and its signature.
2. Read ${genDir}/prompts/probe-eval.md and follow its method.
3. The shared battery (same for every candidate) is:
\`\`\`json
${JSON.stringify(battery.probes, null, 1)}
\`\`\`
4. Candidates to evaluate (each already has a working solution.py):
${cand}
5. Write ONE small standard-library driver under ${sandbox}/nodes/ that, given a solution path, imports it, calls ${battery.entry}(*args) for each probe, and compares str(result).strip() to the probe's expected string. Run it once PER candidate (identical battery each time). A probe the candidate crashes on counts as a miss for that candidate, not a skip.
6. For each candidate report node id, n_correct, n_total (= number of probes), and probe_score = n_correct / n_total.

Return the structured results.

Rules:
- ${RULES}
- Apply the SAME battery to every candidate — never tailor probes to a candidate.
- Report the REAL measured pass counts only — never estimate or fabricate them.`;
}

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
    path: nodePath(id),
    // Filled in during the Probe phase (null = not probed).
    probe_score: null,
  });
}

// ── Phase 1: parallel drafts ─────────────────────────────────────────
phase("Draft");
const nodes = [];
const draftResults = await parallel(
  Array.from(
    { length: NUM_DRAFTS },
    (_, i) => () =>
      agent(draftPrompt(i, DIRECTIONS[i % DIRECTIONS.length]), {
        label: `draft:node-${i}`,
        phase: "Draft",
        schema: NODE_SCHEMA,
        model: MODEL,
        effort: EFFORT,
      }),
  ),
);
draftResults.forEach((r, i) => record(nodes, i, "draft", null, r));
log(`drafts done: scores [${nodes.map((n) => n.public_score).join(", ")}]`);

// ── Phase 2: greedy debug/improve loop (CLEAN public score) ──────────
phase("Search");
while (nodes.length < MAX_NODES) {
  if (budget.total && budget.remaining() < 20000) {
    log(
      `stopping early: token budget nearly exhausted (${budget.remaining()} left)`,
    );
    break;
  }
  const id = nodes.length;
  const children = new Set(
    nodes.filter((n) => n.parent !== null).map((n) => n.parent),
  );
  const buggyLeaves = nodes.filter((n) => n.buggy && !children.has(n.id));
  let op, target;
  if (buggyLeaves.length > 0) {
    op = "debug";
    target = buggyLeaves[Math.floor(rand() * buggyLeaves.length)];
  } else {
    op = "improve";
    target = nodes.reduce((a, b) => (b.public_score > a.public_score ? b : a));
  }
  const result = await agent(fixPrompt(op, id, target, nodes, `${op}.md`), {
    label: `${op}:node-${id}<-node-${target.id}`,
    phase: "Search",
    schema: NODE_SCHEMA,
    model: MODEL,
    effort: EFFORT,
  });
  record(nodes, id, op, target.id, result);
  log(
    `node-${id} (${op} of node-${target.id}): score ${nodes[id].public_score}`,
  );
}

// ── Deterministic top-public pick (the incumbent baseline behavior) ──
const valid = nodes.filter((n) => !n.buggy);
const pool = valid.length ? valid : nodes;
// Highest public score; deterministic tie-break by lowest id.
function betterPublic(a, b) {
  if (b.public_score !== a.public_score) return b.public_score > a.public_score;
  return b.id < a.id;
}
let best = pool.reduce((a, b) => (betterPublic(a, b) ? b : a));

// ── Phase 3: shared adversarial probe re-ranking ─────────────────────
// The search never traded away public quality (Phase 2 is clean-public), so
// `best` is already the strong top-public solution. The probe only re-ranks
// WITHIN the near-best-public tier, and only when it genuinely discriminates —
// otherwise we keep `best`. This can demote a paraphrase-overfit lookup below
// a synonym-tolerant parser (instruction-routing) while leaving already-robust
// tasks (bin-packing, tabular) on their top-public pick.
phase("Probe");
let probeNote = "not run";
const tier = pool
  .filter((n) => n.public_score >= best.public_score - PROBE_PUBLIC_MARGIN)
  .sort((a, b) => (betterPublic(a, b) ? -1 : 1))
  .slice(0, PROBE_TOP_K);

if (tier.length < 2) {
  probeNote = `skipped: only ${tier.length} near-best-public candidate(s); keeping top-public node-${best.id}`;
  log(probeNote);
} else if (budget.total && budget.remaining() < 40000) {
  probeNote = `skipped: token budget too low for probe phase; keeping top-public node-${best.id}`;
  log(probeNote);
} else {
  const battery = await agent(probeAuthorPrompt(), {
    label: "probe:author",
    phase: "Probe",
    schema: PROBE_BATTERY_SCHEMA,
    model: MODEL,
    effort: EFFORT,
  });
  const probes = battery && Array.isArray(battery.probes) ? battery.probes : [];
  if (!battery || !battery.oracle_available || probes.length === 0) {
    probeNote = `fallback: no oracle-checkable battery (oracle_available=${battery ? battery.oracle_available : "none"}, probes=${probes.length}); keeping top-public node-${best.id}`;
    log(probeNote);
  } else {
    const evalOut = await agent(
      probeEvalPrompt(
        battery,
        tier.map((n) => ({ id: n.id, path: n.path })),
      ),
      {
        label: "probe:eval",
        phase: "Probe",
        schema: PROBE_EVAL_SCHEMA,
        model: MODEL,
        effort: EFFORT,
      },
    );
    const results =
      evalOut && Array.isArray(evalOut.results) ? evalOut.results : [];
    // Attach measured probe scores to the tier nodes.
    const scored = [];
    for (const n of tier) {
      const r = results.find((x) => x && x.node === n.id);
      if (r && typeof r.probe_score === "number") {
        n.probe_score = clamp01(r.probe_score);
        scored.push(n);
      }
    }
    if (scored.length < 2) {
      probeNote = `fallback: probe returned <2 usable scores; keeping top-public node-${best.id}`;
      log(probeNote);
    } else {
      const ps = scored.map((n) => n.probe_score);
      const spread = Math.max(...ps) - Math.min(...ps);
      if (spread < PROBE_SPREAD_EPS) {
        // Anti-saturation guard: flat/uniform battery = failed discriminator.
        probeNote = `fallback: probe non-discriminating (spread ${spread.toFixed(3)} < ${PROBE_SPREAD_EPS}); keeping top-public node-${best.id}`;
        log(probeNote);
      } else {
        // Re-rank within the tier by probe score; tie-break by public then id.
        const winner = scored.reduce((a, b) => {
          if (b.probe_score !== a.probe_score)
            return b.probe_score > a.probe_score ? b : a;
          return betterPublic(a, b) ? a : b;
        });
        probeNote = `selected node-${winner.id} by probe (score ${winner.probe_score.toFixed(3)}, spread ${spread.toFixed(3)}) over top-public node-${best.id}`;
        log(probeNote);
        best = winner;
      }
    }
  }
}

// ── Result ───────────────────────────────────────────────────────────
return {
  task: taskName,
  generation: genDir,
  best: {
    node: best.id,
    public_score: best.public_score,
    solution_path: best.path,
    summary: best.summary,
  },
  n_nodes: nodes.length,
  n_buggy: nodes.filter((n) => n.buggy).length,
  nodes: nodes.map(({ code, ...meta }) => meta),
};
