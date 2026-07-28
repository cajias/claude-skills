// Pure tree-search core for the rsi-loop inner agent.
//
// This module is the FROZEN substrate (immutability wall): it does no disk I/O,
// touches no runtime globals, and contains zero artifact-kind-specific tokens.
// Everything impure — the agent runner, budget meter, RNG, logging — arrives via
// `deps`. Everything artifact-specific — the kind, path template, record schema,
// wall rules, and operator prompt bodies — arrives via `adapter`. The engine only
// interprets the portable `policy` spec (the 8 fields the outer loop may tune).
//
// Node records use ONLY generic keys: {id, op, parent, code, public_score, buggy,
// summary}. ("code" is a generic body field, not an artifact-kind token.)

// Stop searching once the budget meter can no longer fund a node. Matches the
// historical guard: loop while under the node cap AND (no metered budget OR at
// least this many units remain). ponytail: node cap is the primary bound; the
// token-based estCost primitive is a later step, deliberately not built here.
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

export async function search(deps, policy, adapter) {
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
