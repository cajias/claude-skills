import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const patterns = JSON.parse(
  readFileSync(
    path.join(HERE, "..", "..", "patterns", "patterns.json"),
    "utf8",
  ),
);

test("version bumped to 1.1.0", () => {
  assert.equal(patterns.version, "1.1.0");
});

test("has new conversational-hooks category with forced-sass phrases", () => {
  const cat = patterns.categories.find((c) => c.id === "conversational-hooks");
  assert.ok(cat, "conversational-hooks category exists");
  assert.equal(cat.priority, "high");
  const joined = JSON.stringify(cat.patterns);
  // literal, unaffected by the apostrophe-optional restoration
  assert.match(joined, /hot take/i);
  // apostrophe-optional regex source ("'?") is restored verbatim on the hook phrases
  assert.match(joined, /here'\?s the thing/i);
});

test("has new ai-lexicon-2025 category with 2025 buzzwords", () => {
  const cat = patterns.categories.find((c) => c.id === "ai-lexicon-2025");
  assert.ok(cat, "ai-lexicon-2025 category exists");
  const joined = JSON.stringify(cat.patterns);
  assert.match(joined, /empower/i);
  assert.match(joined, /elevate/i);
});

test("all existing category ids preserved (additive only)", () => {
  const expectedIds = [
    "inflated-symbolism",
    "promotional-language",
    "editorializing",
    "transition-overuse",
    "negative-parallelism",
    "participle-endings",
    "weasel-wording",
    "em-dash-overuse",
    "rule-of-three",
    "formatting-patterns",
    "buzzwords",
    "filler-phrases",
    "chatbot-artifacts",
    "section-conclusions",
    "hedge-words",
  ];
  for (const id of expectedIds)
    assert.ok(
      patterns.categories.some((c) => c.id === id),
      `${id} still present`,
    );
});

test('new categories use the type:phrase/word + regex:true convention, never type:"regex"', () => {
  const newCatIds = ["conversational-hooks", "ai-lexicon-2025"];
  for (const catId of newCatIds) {
    const cat = patterns.categories.find((c) => c.id === catId);
    for (const p of cat.patterns) {
      assert.notEqual(
        p.type,
        "regex",
        `${catId}: "${p.pattern}" must not use type:"regex"`,
      );
      if (p.regex === true) {
        assert.ok(
          ["phrase", "word", "ending"].includes(p.type),
          `${catId}: "${p.pattern}" has regex:true but an unexpected type "${p.type}"`,
        );
      }
    }
  }
});
