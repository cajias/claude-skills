import { test } from "node:test";
import assert from "node:assert/strict";
import { scan } from "../prescan.js";

const patterns = {
  categories: [
    {
      id: "inflated-symbolism",
      name: "Inflated Symbolism",
      priority: "high",
      patterns: [
        {
          pattern: "stands as a testament",
          type: "phrase",
          replacements: ["shows"],
        },
      ],
    },
    {
      id: "conversational-hooks",
      name: "Conversational Hooks",
      priority: "high",
      patterns: [
        {
          pattern: "but here'?s the thing",
          type: "phrase",
          regex: true,
          replacements: ["but"],
        },
      ],
    },
    {
      id: "ai-lexicon-2025",
      name: "AI Lexicon 2025",
      priority: "medium",
      patterns: [
        {
          pattern: "unlock",
          type: "word",
          replacements: ["enable", "allow"],
        },
      ],
    },
  ],
};

test("matches a literal phrase pattern", () => {
  const f = scan("This stands as a testament to X.", patterns);
  assert.ok(
    f.some(
      (x) => x.category === "inflated-symbolism" && /testament/.test(x.span),
    ),
  );
});

test("matches a regex pattern (apostrophe variant)", () => {
  const f = scan("But here's the thing: no.", patterns);
  assert.ok(f.some((x) => x.category === "conversational-hooks"));
});

test("flags the em-dash spacing tell and suggests a comma", () => {
  const f = scan("a word—word b", patterns);
  const hit = f.find((x) => x.category === "em-dash-spacing");
  assert.ok(hit);
  assert.equal(hit.suggestedFix, "word, word");
});

test("flags over-bulleting when list density is high", () => {
  const text = [
    "intro",
    "- a",
    "- b",
    "- c",
    "- d",
    "- e",
    "- f",
    "- g",
    "- h",
    "- i",
    "- j",
  ].join("\n");
  const f = scan(text, patterns);
  assert.ok(f.some((x) => x.category === "over-bulleting"));
});

test("clean prose produces no findings", () => {
  const f = scan("The cat sat on the mat and looked outside.", patterns);
  assert.equal(f.length, 0);
});

test("word-type literal patterns match with word boundaries only", () => {
  const hitFor = scan("unlock this", patterns);
  assert.ok(hitFor.some((x) => x.category === "ai-lexicon-2025"));

  const noHitFor = scan("the door unlocked", patterns);
  assert.ok(!noHitFor.some((x) => x.category === "ai-lexicon-2025"));
});
