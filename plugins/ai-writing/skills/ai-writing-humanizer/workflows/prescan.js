// prescan.js — deterministic AI-writing pre-scan.
// Plain Node module: fs IS allowed here (this runs in real Node,
// NOT the Workflow sandbox).
import fs from "node:fs";

function toRegex(p) {
  const isRegex = p.regex === true || p.type === "regex"; // honor the DB's regex flag
  let body = isRegex
    ? p.pattern
    : p.pattern.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); // escape literal
  if (!isRegex && p.type === "word") {
    // single-token literals get word boundaries so "unlock" doesn't
    // fire inside "unlocked"
    body = `\\b${body}\\b`;
  }
  return new RegExp(body, "gi");
}

export function scan(text, patterns, config = {}) {
  const findings = [];
  for (const cat of patterns.categories || []) {
    for (const p of cat.patterns || []) {
      const re = toRegex(p);
      let m;
      while ((m = re.exec(text)) !== null) {
        findings.push({
          span: m[0],
          category: cat.id,
          priority: cat.priority,
          why: `matches ${cat.name} pattern "${p.pattern}"`,
          suggestedFix:
            (p.replacements && p.replacements[0]) ||
            (p.action === "delete" ? "" : null),
          source: "regex",
        });
        // avoid zero-width infinite loop
        if (m.index === re.lastIndex) re.lastIndex++;
      }
    }
  }
  // em-dash overuse (raw count vs threshold per 500 words)
  const emThreshold =
    (config.strict_thresholds && config.strict_thresholds.em_dash) || 2;
  const words = (text.match(/\S+/g) || []).length;
  const emCount = (text.match(/—/g) || []).length;
  if (words > 0 && (emCount / words) * 500 > emThreshold) {
    findings.push({
      span: `${emCount} em dashes / ${words} words`,
      category: "em-dash-overuse",
      priority: "low",
      why: `more than ${emThreshold} em dashes per 500 words`,
      suggestedFix: null,
      source: "regex",
    });
  }
  // em-dash spacing tell: word—word squeezed with no spaces
  const spaced = /\w+—\w+/g;
  let sm;
  while ((sm = spaced.exec(text)) !== null) {
    findings.push({
      span: sm[0],
      category: "em-dash-spacing",
      priority: "low",
      why:
        "em dash squeezed between words with no spaces (common " +
        "ChatGPT tell)",
      suggestedFix: sm[0].replace("—", ", "),
      source: "regex",
    });
  }
  // over-bulleting / list-ification density
  const lines = text.split("\n");
  const bullets = lines.filter((l) => /^\s*([-*•]|\d+\.)\s+/.test(l)).length;
  if (lines.length >= 10 && bullets / lines.length > 0.4) {
    findings.push({
      span: `${bullets}/${lines.length} lines are list items`,
      category: "over-bulleting",
      priority: "medium",
      why: "excessive bullet/list density where prose may read " + "better",
      suggestedFix: null,
      source: "regex",
    });
  }
  return findings;
}

// CLI: node prescan.js <textFile> <patternsJson> [configJson]
// prints findings JSON
if (import.meta.url === `file://${process.argv[1]}`) {
  const [, , textFile, patternsFile, configFile] = process.argv;
  const text = fs.readFileSync(textFile, "utf8");
  const patterns = JSON.parse(fs.readFileSync(patternsFile, "utf8"));
  const config = configFile
    ? JSON.parse(fs.readFileSync(configFile, "utf8"))
    : {};
  process.stdout.write(JSON.stringify(scan(text, patterns, config), null, 2));
}
