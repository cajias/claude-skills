import { test } from "node:test";
import assert from "node:assert/strict";
import { runWorkflow } from "./harness.mjs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SCRIPT = path.join(HERE, "..", "humanize.js");

const baseArgs = {
  text:
    "This stands as a testament. But here is the thing: " +
    "it is not just X, it is Y.",
  patterns: {
    categories: [{ id: "x", name: "X", priority: "high" }],
  },
  prompts: { analysis: "A", suggestion: "S", verification: "V" },
  mechanicalFindings: [
    {
      span: "stands as a testament",
      category: "inflated-symbolism",
      priority: "high",
      why: "m",
      source: "regex",
    },
  ],
  config: {
    max_iterations: 3,
    auto_fix_priority: ["critical", "high"],
  },
};

test("throws a helpful error on missing required args", async () => {
  const { error } = await runWorkflow({
    scriptPath: SCRIPT,
    args: {},
    mockAgent: () => null,
  });
  assert.match(String(error), /requires args/);
});

test(
  "clean text short-circuits: no findings -> no revise, no " + "residual",
  async () => {
    const mockAgent = (_p, opts) =>
      opts.label?.startsWith("analyze") ? { findings: [] } : null;
    const { result, agentCalls } = await runWorkflow({
      scriptPath: SCRIPT,
      args: { ...baseArgs, mechanicalFindings: [] },
      mockAgent,
    });
    assert.equal(result.residual.length, 0);
    assert.equal(result.iterations, 0);
    assert.equal(agentCalls.filter((c) => c.opts.label === "revise").length, 0);
  },
);

test(
  "runs 3 analyze lenses and dedups against mechanical " + "findings",
  async () => {
    const mockAgent = (_p, opts) => {
      if (opts.label?.startsWith("analyze"))
        return {
          findings: [
            {
              span: "stands as a testament",
              category: "inflated-symbolism",
              priority: "high",
              why: "dup",
            },
          ],
        };
      if (opts.label === "revise") return { revisedText: "Clean text." };
      if (opts.label?.startsWith("review"))
        return { verdict: "pass", residual: [], notes: "" };
      return null;
    };
    const { result, agentCalls } = await runWorkflow({
      scriptPath: SCRIPT,
      args: baseArgs,
      mockAgent,
    });
    assert.equal(
      agentCalls.filter((c) => c.opts.label?.startsWith("analyze")).length,
      3,
    );
    assert.equal(result.residual.length, 0);
    assert.ok(result.fixedByPriority.high >= 1);
  },
);

test("fidelity guard rejects a meaning-damaging rewrite", async () => {
  const mockAgent = (_p, opts) => {
    if (opts.label?.startsWith("analyze"))
      return {
        findings: [
          {
            span: "X",
            category: "buzzwords",
            priority: "high",
            why: "x",
          },
        ],
      };
    if (opts.label === "revise") return { revisedText: "DAMAGED" };
    if (opts.label === "review:fidelity")
      return {
        verdict: "needs-work",
        residual: [
          {
            span: "X",
            category: "fidelity",
            priority: "high",
            why: "dropped a claim",
          },
        ],
        notes: "meaning changed",
      };
    if (opts.label?.startsWith("review"))
      return { verdict: "pass", residual: [], notes: "" };
    return null;
  };
  const { result } = await runWorkflow({
    scriptPath: SCRIPT,
    args: baseArgs,
    mockAgent,
  });
  assert.equal(result.revisedText, baseArgs.text);
  assert.equal(result.fidelity.pass, false);
  assert.ok(result.residual.some((r) => /fidelity guard blocked/.test(r.why)));
});

test(
  "loops until high-priority residual clears, capped at " + "max_iterations",
  async () => {
    let round = 0;
    const mockAgent = (_p, opts) => {
      if (opts.label?.startsWith("analyze"))
        return {
          findings: [
            {
              span: "a",
              category: "buzzwords",
              priority: "high",
              why: "x",
            },
          ],
        };
      if (opts.label === "revise") return { revisedText: "rev" + ++round };
      if (opts.label === "review:residual")
        return {
          verdict: "needs-work",
          residual: [
            {
              span: "a" + round,
              category: "buzzwords",
              priority: "high",
              why: "still",
            },
          ],
          notes: "",
        };
      if (opts.label?.startsWith("review"))
        return { verdict: "pass", residual: [], notes: "" };
      return null;
    };
    const { result, agentCalls } = await runWorkflow({
      scriptPath: SCRIPT,
      args: {
        ...baseArgs,
        config: {
          max_iterations: 3,
          auto_fix_priority: ["critical", "high"],
        },
      },
      mockAgent,
    });
    assert.equal(result.iterations, 3);
    assert.equal(agentCalls.filter((c) => c.opts.label === "revise").length, 3);
  },
);
