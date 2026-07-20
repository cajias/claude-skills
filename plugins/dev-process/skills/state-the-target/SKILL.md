---
name: state-the-target
description: >-
  When writing any document an AI agent will later read — a spec, PRD, requirements doc,
  design doc, README scope section, or a system/agent prompt — state what you WANT (the
  target), not what you don't (the anti-target). Negative/exclusionary framing ("Non-goals",
  "is not", "does not", "never", "out of scope") plants salient wrong examples the model can
  latch onto and get confused by. Use this WHENEVER writing or reviewing specs, design docs,
  requirements, PRDs, scope/README sections, or agent/system prompts — and ESPECIALLY the
  moment you catch yourself writing a "Non-goals" or "Out of scope" section. Convert every
  exclusion into a positive Scope statement plus a Future-directions roadmap.
---

# State the Target, Not the Anti-Target

Docs and prompts that agents read should describe the destination, not the places you're
avoiding. A line like "this is **not** a CLI" hands the model a vivid, concrete image of a
CLI — exactly the wrong anchor. Positive statements give it the right target to move toward.
This is a house rule learned from real correction: *"the documents should state what we
want, not what we don't."*

## When to use

Any spec, PRD, requirements list, design doc, scope or README section, or system/agent
prompt. Trigger hardest when you're about to write a **Non-goals**, **Out of scope**, or
**What it is / is not** section — that's the exact anti-pattern this exists to prevent.

## The rule

Keep every real boundary — you're not dropping information, you're flipping its polarity:

1. **Non-goals → Scope + Future directions.** Replace the exclusion list with (a) a positive
   **Scope** of what IS included, and (b) a **Future directions** roadmap of what's wanted
   *later*. "Wanted later" is still a positive want, so the boundary survives without a "not".
2. **"is not X" → "is Y".** State the actual identity. The contrast you were drawing is
   almost always expressible as a positive fact.
3. **"never / doesn't" invariants → positive guarantees.** "The scanner never writes" →
   "The scanner is read-only; writes happen in the apply step after confirmation."
4. **Keep decision rationale.** ADR-style "chose X over Y because…" is *reasoning*, not a
   scope anti-goal — that's fine to keep. The target of this rule is scope/identity
   negatives, not the record of alternatives considered.

## Examples

**Example 1 — scope section**
Input:

```
## Non-goals
Not a standalone CLI in v1 · not a web report · does not run linters itself.
```

Output:

```
## Scope (v1)
An in-session plugin producing a terminal report; it verifies lint configs are present and
appropriate (their execution stays with those tools).

## Future directions
Wanted next: a standalone CLI with a CI gate, and a shareable report.
```

**Example 2 — identity line**
Input: `Is not: a linter, a web app, or a CI tool.`
Output: `It runs in the terminal within the session and grades configuration against a
versioned standard.`

**Example 3 — invariant**
Input: `The model never performs a detection a script could do.`
Output: `Every detection a script can perform is performed by a script; the model is used
only for judgment.`

## Why it matters

Requirements and prompts are instructions to a reader who pattern-matches on what's vivid.
A prohibition is less actionable than a target and more likely to be misread ("build the
thing it said not to build"). Positive scope + a roadmap keeps the guardrail *and* points
the reader at the right thing to do.
