import { test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { runWorkflow, stripMetaBlock } from "./harness.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SCRIPT = path.join(HERE, "..", "goal-prompt.js");

const baseArgs = { repo: "owner/proj", milestone: "1" };

const ISSUES = {
  milestoneTitle: "Local end-to-end verification backbone",
  issues: [
    { number: "22", title: "Wire the harness", summary: "s", labels: [] },
    { number: "23", title: "Add the probe", summary: "s", labels: [] },
  ],
};
const VERIFY = {
  command: "cargo xtask e2e",
  justification: "real runner; scripts/e2e-test.sh cannot fail",
  canFail: true,
  rejected: ["scripts/e2e-test.sh"],
};
const analysisFor = (n) => ({
  number: n,
  title: `Issue ${n}`,
  intent: "do the thing",
  bddScenario: { given: "g", when: "w", then: "t" },
  dependsOn: [],
  blocked: false,
});
const directive = (text = "D") => ({ directive: text, charCount: text.length });

/**
 * Route a mocked agent call by its label. `critics` is consulted per round so
 * a test can make the panel dirty then clean.
 */
function router({ critics = () => ({ findings: [] }), issues = ISSUES } = {}) {
  let round = 0;
  const perRound = new Map();
  return (prompt, opts) => {
    const label = (opts && opts.label) || "";
    if (label === "survey:issues") return issues;
    if (label === "survey:verify-cmd") return VERIFY;
    if (label.startsWith("analyze:#")) {
      return analysisFor(label.split("#")[1]);
    }
    if (label === "assemble:directive") return directive();
    if (label.startsWith("critic:")) {
      const lens = label.split(":")[1];
      // Count a round once all three lenses for it have been served.
      const n = perRound.get(lens) || 0;
      perRound.set(lens, n + 1);
      round = Math.max(round, n + 1);
      return critics(n + 1, lens);
    }
    if (label.startsWith("revise:")) return directive("D-revised");
    return null;
  };
}

test("meta declares name, description and four phases", async () => {
  const raw = await readFile(SCRIPT, "utf8");
  const metaSrc = raw.slice(0, raw.indexOf("};") + 2);
  assert.match(metaSrc, /export const meta = \{/);
  assert.match(metaSrc, /name: "milestone-goal-prompt"/);
  assert.match(metaSrc, /description:/);
  for (const p of ["Survey", "Analyze", "Assemble", "Verify"]) {
    assert.ok(metaSrc.includes(`"${p}"`), `meta.phases missing ${p}`);
  }
  // Pure literal: no interpolation or spread inside the meta block.
  assert.ok(!/\$\{|\.\.\./.test(metaSrc), "meta must be a pure literal");
});

test("stripping meta leaves a runnable body", async () => {
  const raw = await readFile(SCRIPT, "utf8");
  const stripped = stripMetaBlock(raw);
  assert.ok(!stripped.includes("export const meta"));
  assert.ok(stripped.includes("phase("));
});

test("missing args throws an informative error naming what to pass", async () => {
  for (const args of [undefined, {}, { repo: "o/p" }, { milestone: "1" }]) {
    const { error } = await runWorkflow({ scriptPath: SCRIPT, args });
    assert.ok(error, `expected a throw for args=${JSON.stringify(args)}`);
    assert.match(error.message, /requires args \{repo, milestone\}/);
    assert.match(error.message, /Invoke as: Workflow\(/);
  }
});

test("accepts a JSON-string args payload", async () => {
  const { error } = await runWorkflow({
    scriptPath: SCRIPT,
    args: JSON.stringify(baseArgs),
    mockAgent: router(),
  });
  assert.equal(error, null);
});

test("clean panel converges after two dry rounds without revising", async () => {
  const { result, error, logs } = await runWorkflow({
    scriptPath: SCRIPT,
    args: baseArgs,
    mockAgent: router(),
  });
  assert.equal(error, null);
  assert.equal(result.rounds, 2, "two dry rounds should stop the loop");
  assert.equal(result.findingsApplied, 0);
  assert.equal(result.converged, true);
  assert.equal(result.directive, "D");
  assert.ok(logs.some((l) => /dry streak 2\/2/.test(l)));
});

test("a dirty round revises, then two dry rounds stop the loop", async () => {
  const { result, error } = await runWorkflow({
    scriptPath: SCRIPT,
    args: baseArgs,
    mockAgent: router({
      critics: (round, lens) =>
        round === 1 && lens === "completeness"
          ? {
              findings: [
                {
                  summary: "DoD gate missing lint",
                  severity: "blocking",
                  fix: "add lint",
                },
              ],
            }
          : { findings: [] },
    }),
  });
  assert.equal(error, null);
  assert.equal(result.rounds, 3, "1 dirty + 2 dry");
  assert.equal(result.findingsApplied, 1);
  assert.equal(result.converged, true);
  assert.equal(result.directive, "D-revised");
});

test("a repeated finding is deduped so the loop still converges", async () => {
  const same = {
    findings: [{ summary: "Same gap", severity: "advisory", fix: "f" }],
  };
  const { result, error } = await runWorkflow({
    scriptPath: SCRIPT,
    args: baseArgs,
    mockAgent: router({ critics: () => same }),
  });
  assert.equal(error, null);
  // Round 1 is new; rounds 2-3 are the identical finding, deduped to dry.
  assert.equal(result.rounds, 3);
  assert.equal(result.findingsApplied, 1, "the repeat must not re-apply");
  assert.equal(result.converged, true);
});

test("persistently NEW findings hit the 4-round cap and report non-convergence", async () => {
  let n = 0;
  const { result, error, logs } = await runWorkflow({
    scriptPath: SCRIPT,
    args: baseArgs,
    mockAgent: router({
      critics: () => ({
        findings: [
          {
            summary: `distinct gap ${(n += 1)}`,
            severity: "blocking",
            fix: "f",
          },
        ],
      }),
    }),
  });
  assert.equal(error, null);
  assert.equal(result.rounds, 4, "hard cap");
  assert.equal(result.converged, false);
  assert.ok(logs.some((l) => /4-round cap/.test(l)));
});

test("an empty milestone returns early without assembling", async () => {
  const { result, error, phases } = await runWorkflow({
    scriptPath: SCRIPT,
    args: baseArgs,
    mockAgent: router({ issues: { milestoneTitle: "Empty", issues: [] } }),
  });
  assert.equal(error, null);
  assert.equal(result.directive, null);
  assert.deepEqual(result.issues, []);
  assert.equal(result.rounds, 0);
  assert.ok(!phases.includes("Assemble"), "must not reach Assemble");
});

test("a failed survey throws rather than emitting a hollow directive", async () => {
  const { error } = await runWorkflow({
    scriptPath: SCRIPT,
    args: baseArgs,
    mockAgent: (prompt, opts) =>
      (opts && opts.label) === "survey:issues" ? null : VERIFY,
  });
  assert.ok(error);
  assert.match(error.message, /Survey failed/);
});

test("issue count over the cap is logged, never silently truncated", async () => {
  const many = {
    milestoneTitle: "Big",
    issues: Array.from({ length: 5 }, (_, i) => ({
      number: String(i + 1),
      title: `t${i + 1}`,
    })),
  };
  const { result, error, logs } = await runWorkflow({
    scriptPath: SCRIPT,
    args: { ...baseArgs, config: { maxIssues: 2 } },
    mockAgent: router({ issues: many }),
  });
  assert.equal(error, null);
  assert.equal(result.issues.length, 2);
  assert.ok(
    logs.some((l) => /exceeds cap 2/.test(l) && /NOT\s+covered/.test(l)),
    "truncation must be logged as incomplete coverage",
  );
});

test("blocked issues are surfaced in the result", async () => {
  const { result, error } = await runWorkflow({
    scriptPath: SCRIPT,
    args: baseArgs,
    mockAgent: (prompt, opts) => {
      const label = (opts && opts.label) || "";
      if (label === "survey:issues") return ISSUES;
      if (label === "survey:verify-cmd") return VERIFY;
      if (label === "analyze:#22")
        return {
          ...analysisFor("22"),
          blocked: true,
          blockedReason: "needs #24",
        };
      if (label === "analyze:#23") return analysisFor("23");
      if (label === "assemble:directive") return directive();
      if (label.startsWith("critic:")) return { findings: [] };
      return null;
    },
  });
  assert.equal(error, null);
  assert.deepEqual(result.blocked, [{ number: "22", reason: "needs #24" }]);
});

test("a critic that fails to report is called out as unverified", async () => {
  const { error, logs } = await runWorkflow({
    scriptPath: SCRIPT,
    args: baseArgs,
    mockAgent: (prompt, opts) => {
      const label = (opts && opts.label) || "";
      if (label === "critic:correctness") return null;
      return router()(prompt, opts);
    },
  });
  assert.equal(error, null);
  assert.ok(
    logs.some((l) => /UNVERIFIED, not clean/.test(l)),
    "a dead critic must not read as a clean lens",
  );
  assert.ok(
    logs.some((l) => /streak does not advance/.test(l)),
    "an unverified lens must not buy a dry round",
  );
});

test("a permanently dead critic never converges, even with the others clean", async () => {
  const { result, error } = await runWorkflow({
    scriptPath: SCRIPT,
    args: baseArgs,
    mockAgent: (prompt, opts) => {
      const label = (opts && opts.label) || "";
      if (label === "critic:correctness") return null;
      return router()(prompt, opts);
    },
  });
  assert.equal(error, null);
  assert.equal(
    result.converged,
    false,
    "unverified lens must block convergence",
  );
  assert.equal(result.rounds, 4, "should exhaust the cap instead");
});

test("the workflow never reaches for forbidden sandbox APIs", async () => {
  const raw = await readFile(SCRIPT, "utf8");
  for (const bad of [
    "Date.now",
    "Math.random",
    "new Date",
    "require(",
    "readFile",
  ]) {
    assert.ok(!raw.includes(bad), `workflow must not use ${bad}`);
  }
});

// The close-out only survives compression because BOTH the must-retain list and
// the completeness lens name it. Drop either and the assembler is free to trim
// it with every other test still green — so assert both sites, not the file.
test("the automation-recommender close-out is named in both prompt sites", async () => {
  const raw = await readFile(SCRIPT, "utf8");
  const site = (from, to) =>
    raw.slice(raw.indexOf(from), raw.indexOf(to)).replace(/"\s*\+\s*"/g, "");
  const critic = site("lens: \"completeness\"", "lens: \"correctness\"");
  const retain = site("The directive MUST retain", "Hard limit:");
  for (const [name, text] of [
    ["completeness critic", critic],
    ["must-retain list", retain],
  ]) {
    assert.ok(text.length > 0, `${name} block not found`);
    assert.ok(
      text.includes("claude-automation-recommender"),
      `${name} must name the automation recommender`,
    );
  }
  // Candidate-guard framing, not auto-install: the loop runs unattended.
  assert.ok(
    retain.includes("candidate") && retain.includes("never auto-install"),
    "must-retain list must keep the candidate-guard / no-auto-install framing",
  );
});
