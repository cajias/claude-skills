import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { scan } from "../prescan.js";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(HERE, "..", "..");
const patterns = JSON.parse(
  readFileSync(path.join(ROOT, "patterns", "patterns.json"), "utf8"),
);
const config = JSON.parse(
  readFileSync(path.join(ROOT, "config", "default.config.json"), "utf8"),
);

test("tell-heavy sample fixture produces findings", () => {
  const text = readFileSync(
    path.join(ROOT, "examples", "before-after-samples.md"),
    "utf8",
  );
  const f = scan(text, patterns, config);
  assert.ok(f.length > 0, "expected the samples file to trip the pre-scan");
});

test(
  "a hand-written clean paragraph produces zero " +
    "findings (false-positive guard)",
  () => {
    const clean =
      "The train left at noon. Rain streaked the " +
      "windows while the fields slid past. " +
      "She read three chapters and fell asleep " +
      "before the last stop.";
    const f = scan(clean, patterns, config);
    assert.equal(f.length, 0);
  },
);
