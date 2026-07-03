export const meta = {
  name: "humanize-writing",
  description:
    "Multi-agent AI-writing humanizer: analyze (3 lenses) " +
    "-> revise -> adversarial review (4 lenses) -> " +
    "loop-until-clean.",
  phases: [{ title: "Analyze" }, { title: "Revise" }, { title: "Evaluate" }],
};

// ---- args normalization (object | JSON-string |
// undefined) ----
let opts = args;
if (typeof opts === "string") {
  try {
    opts = JSON.parse(opts);
  } catch {
    opts = {};
  }
}
opts = opts || {};
const { text, patterns, prompts, mechanicalFindings = [], config = {} } = opts;
if (!text || !patterns || !prompts) {
  throw new Error(
    "humanize-writing requires args {text, patterns, " +
      "prompts}.\n" +
      "text = document string; patterns = parsed " +
      "patterns.json; prompts = {analysis, suggestion, " +
      "verification}.\n" +
      "Got args=" +
      JSON.stringify(args) +
      "\n" +
      "Invoke as: Workflow({ scriptPath, args: { text, " +
      "patterns, prompts, mechanicalFindings, config } })",
  );
}

const MAX_ITERS = config.max_iterations || 5;
const AUTOFIX = config.auto_fix_priority || ["critical", "high"];
const keyOf = (f) => `${f.category}|${(f.span || "").trim().toLowerCase()}`;
const dedup = (arr) => {
  const seen = new Set();
  const out = [];
  for (const f of arr) {
    const k = keyOf(f);
    if (!seen.has(k)) {
      seen.add(k);
      out.push(f);
    }
  }
  return out;
};
const isAutofix = (f) => AUTOFIX.includes(f.priority);

const FIND_SCHEMA = {
  type: "object",
  required: ["findings"],
  properties: {
    findings: {
      type: "array",
      items: {
        type: "object",
        required: ["span", "category", "priority", "why"],
        properties: {
          span: { type: "string" },
          category: { type: "string" },
          priority: {
            enum: ["critical", "high", "medium", "low"],
          },
          why: { type: "string" },
          suggestedFix: { type: ["string", "null"] },
        },
      },
    },
  },
};
const REVISE_SCHEMA = {
  type: "object",
  required: ["revisedText"],
  properties: {
    revisedText: { type: "string" },
  },
};
const REVIEW_SCHEMA = {
  type: "object",
  required: ["verdict", "residual", "notes"],
  properties: {
    verdict: { enum: ["pass", "needs-work"] },
    notes: { type: "string" },
    residual: {
      type: "array",
      items: {
        type: "object",
        required: ["span", "category", "priority", "why"],
        properties: {
          span: { type: "string" },
          category: { type: "string" },
          priority: {
            enum: ["critical", "high", "medium", "low"],
          },
          why: { type: "string" },
          suggestedFix: { type: ["string", "null"] },
        },
      },
    },
  },
};

// ---- Phase 1: Analyze (3 lenses, parallel) ----
phase("Analyze");
const LENSES = [
  {
    label: "analyze:A",
    focus:
      "high-signal tells: chatbot artifacts, buzzwords, " +
      "promotional language, inflated symbolism, " +
      "editorializing, conversational hooks / forced sass",
  },
  {
    label: "analyze:B",
    focus:
      "structural tells: negative parallelism, participle " +
      "endings, rule of three, transition overuse, " +
      "over-bulleting / list-ification",
  },
  {
    label: "analyze:C",
    focus:
      "style/low tells: em-dash overuse, hedge words, " +
      "weasel words, filler openings and closings",
  },
];
const catSummary = JSON.stringify(
  patterns.categories.map((c) => ({
    id: c.id,
    name: c.name,
    priority: c.priority,
  })),
);
const analyzePrompt = (focus) =>
  `You are an AI-writing detector. Analyze the TEXT ` +
  `for this lens only: ${focus}.\n` +
  `Ground calls in these pattern categories: ` +
  `${catSummary}\n` +
  `A deterministic regex pass already found these — ` +
  `do NOT re-report them, only add contextual matches ` +
  `it would miss: ${JSON.stringify(mechanicalFindings)}\n` +
  `Reference guidance:\n${prompts.analysis}\n\n` +
  `TEXT:\n"""${text}"""\n\nReturn findings as JSON.`;

const lensResults = await parallel(
  LENSES.map(
    (l) => () =>
      agent(analyzePrompt(l.focus), {
        label: l.label,
        phase: "Analyze",
        schema: FIND_SCHEMA,
      }),
  ),
);

let findings = dedup([
  ...mechanicalFindings.map((f) => ({ ...f, source: "regex" })),
  ...lensResults
    .filter(Boolean)
    .flatMap((r) => (r.findings || []).map((f) => ({ ...f, source: "agent" }))),
]);
log(
  `Analyze: ${findings.length} findings (` +
    `${lensResults.filter(Boolean).length}/3 lenses reported)`,
);

if (findings.length === 0) {
  return {
    revisedText: text,
    fixedByPriority: {},
    residual: [],
    iterations: 0,
    fidelity: { pass: true, notes: "no findings" },
    quality: { pass: true, notes: "no findings" },
  };
}

// ---- Phases 2 + 3: revise / evaluate loop ----
let current = text;
let iterations = 0;
let residual = findings;
let fidelity = { pass: true, notes: "" };
let quality = { pass: true, notes: "" };
let prevKeys = "";

while (iterations < MAX_ITERS) {
  const toFix = residual.filter(isAutofix);
  if (toFix.length === 0) break;
  iterations++;

  // Phase 2: Revise
  phase("Revise");
  const revisePrompt =
    `Rewrite the TEXT to fix the AI-writing findings ` +
    `while PRESERVING meaning, facts, claims, ` +
    `citations, and the author's voice. ` +
    `Do not simplify domain/technical terms. Fix the ` +
    `findings; leave everything else untouched.\n` +
    `Guidance:\n${prompts.suggestion}\n\n` +
    `FINDINGS (fix critical/high; also fix medium/low ` +
    `if safe):\n${JSON.stringify(residual)}\n\n` +
    `TEXT:\n"""${current}"""\n\n` +
    `Return the full revised text.`;
  const rev = await agent(revisePrompt, {
    label: "revise",
    phase: "Revise",
    schema: REVISE_SCHEMA,
  });
  if (!rev || !rev.revisedText) {
    log("Revise failed; stopping loop");
    break;
  }
  const candidate = rev.revisedText;

  // Phase 3: Evaluate (4 reviewers, parallel)
  phase("Evaluate");
  const reviewers = [
    {
      label: "review:fidelity",
      prompt:
        `Compare ORIGINAL and REVISION. Did the revision ` +
        `change facts, drop content, alter claims, or ` +
        `break citations? ` +
        `List every meaning-change as a residual finding ` +
        `(category 'fidelity', priority 'high'). ` +
        `verdict='needs-work' if any meaning changed.\n` +
        `ORIGINAL:\n"""${current}"""\n\n` +
        `REVISION:\n"""${candidate}"""`,
    },
    {
      label: "review:residual",
      prompt:
        `Detect AI-writing tells REMAINING in the ` +
        `REVISION, plus any NEW tells it introduced. ` +
        `Checklist:\n${prompts.verification}\n\n` +
        `Report each as a residual finding. ` +
        `verdict='needs-work' if any critical/high ` +
        `remain.\nREVISION:\n"""${candidate}"""`,
    },
    {
      label: "review:quality",
      prompt:
        `Judge the REVISION's prose quality vs the ` +
        `ORIGINAL. Better, or scrubbed into bland/robotic ` +
        `text? Voice intact? ` +
        `If worse or voice lost, verdict='needs-work' and ` +
        `list worst spots (category 'quality', priority ` +
        `'medium').\n` +
        `ORIGINAL:\n"""${current}"""\n\n` +
        `REVISION:\n"""${candidate}"""`,
    },
    {
      label: "review:gap",
      prompt:
        `You are a completeness critic. What did ` +
        `analysis MISS in the REVISION — categories not ` +
        `covered, tells that slipped through, whole ` +
        `sections unaddressed? ` +
        `List them as residual findings. ` +
        `verdict='needs-work' if meaningful gaps exist.\n` +
        `REVISION:\n"""${candidate}"""`,
    },
  ];
  const reviews = await parallel(
    reviewers.map(
      (r) => () =>
        agent(r.prompt, {
          label: r.label,
          phase: "Evaluate",
          schema: REVIEW_SCHEMA,
        }),
    ),
  );
  const byLabel = {};
  reviewers.forEach((r, i) => {
    byLabel[r.label] = reviews[i];
  });
  if (byLabel["review:fidelity"])
    fidelity = {
      pass: byLabel["review:fidelity"].verdict === "pass",
      notes: byLabel["review:fidelity"].notes,
    };
  if (byLabel["review:quality"])
    quality = {
      pass: byLabel["review:quality"].verdict === "pass",
      notes: byLabel["review:quality"].notes,
    };

  // Fidelity guard: reject a meaning-damaging rewrite,
  // keep prior text, mark those fixes blocked
  if (
    byLabel["review:fidelity"] &&
    byLabel["review:fidelity"].verdict === "needs-work"
  ) {
    log(
      `Iteration ${iterations}: fidelity guard rejected ` +
        `the rewrite; keeping prior text`,
    );
    residual = dedup([
      ...toFix.map((f) => ({
        ...f,
        why: (f.why || "") + " [fidelity guard blocked auto-fix]",
      })),
      ...residual.filter((f) => !isAutofix(f)),
    ]);
    break;
  }

  // Accept the candidate
  current = candidate;
  residual = dedup(reviews.filter(Boolean).flatMap((r) => r.residual || []));

  const keys = residual.map(keyOf).sort().join(",");
  if (keys === prevKeys) {
    log(`Iteration ${iterations}: no new progress; ` + `stopping`);
    break;
  }
  prevKeys = keys;

  const remainingHigh = residual.filter(isAutofix);
  log(
    `Iteration ${iterations}: ${residual.length} ` +
      `residual (${remainingHigh.length} ` +
      `high-priority)`,
  );
  if (remainingHigh.length === 0) break;
}

// ---- Phase 5: summarize ----
const fixedByPriority = {};
for (const f of findings) {
  const stillThere = residual.some((r) => keyOf(r) === keyOf(f));
  if (!stillThere)
    fixedByPriority[f.priority] = (fixedByPriority[f.priority] || 0) + 1;
}
return {
  revisedText: current,
  fixedByPriority,
  residual,
  iterations,
  fidelity,
  quality,
};
