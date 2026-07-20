---
name: schema-drift-playbook
description: |
  Three-part fix for schema drift between a strict validator/spec and looser
  data that producers actually emit. Use when: (1) lint/validation flags many
  pre-existing records as invalid, (2) emitters routinely omit or rename
  fields the spec requires, (3) the natural instinct is to fix the data OR
  the spec — but fixing only one lets the drift reappear. Covers relaxation,
  migration, and upstream-producer fix as a coordinated change.
author: Claude Code
version: 1.0.0
date: 2026-04-19
---

# Schema Drift Playbook

## Problem

A validator (lint, schema check, type system) enforces a strict shape. Producers
(agents, tools, migrations, users) emit a looser shape. Over time, valid data
accumulates that the validator rejects. Naive fixes fail:

- **Fix only the data** → producers keep emitting the loose shape; drift returns
- **Fix only the spec** → spec loses meaning; enum/provenance signals get lost
- **Fix only the producer** → existing records still flagged

The right move is a coordinated three-part change.

## Context / Trigger Conditions

Apply this playbook when you see:

- Validation reports large counts of same-shaped failures (not 1–2 outliers)
- The failing records are internally consistent — just missing "required" fields
- Producers are scripts/agents/tools, not a single human who can be retrained
- The spec's "required" list mixes truly-load-bearing fields with nice-to-haves

Signals this ISN'T schema drift (skip this playbook):

- A single record is malformed → just fix that record
- Spec was recently tightened and data predates the tightening → one-shot migration is enough
- Values are invalid (wrong enum) vs. missing → that's a data quality problem, not schema drift

## Solution

### Step 1: Classify fields by actual load

Open the validator and sort each required field into:

| Category | Definition | Treatment |
|---|---|---|
| **Strict** | Absence breaks downstream code or loses irrecoverable provenance | Keep required |
| **Recommended** | Useful defaults exist; absence is cosmetic | Move to optional/recommended list |
| **Either-or** | Two fields hold the same information under different schemas | Validate via helper, not per-field |

Example from a real frontmatter validator:

- Strict: `tags`, `source`, `created` (provenance you can't regenerate)
- Recommended: `id`, `status`, `confidence`, `scope` (have safe defaults)
- Either-or: `type` (canonical) vs `type` holding a knowledge-type value (simplified)

### Step 2: Relax the spec with dual-acceptance

Update the validator to accept both shapes. Introduce a resolver helper:

```python
def get_knowledge_type(metadata):
    """Return knowledge type from either schema."""
    kt = metadata.get("knowledge_type")
    if isinstance(kt, str) and kt in VALID_TYPES:
        return kt
    t = metadata.get("type")
    if isinstance(t, str) and t in VALID_TYPES:
        return t
    return None
```

Validation then checks `get_knowledge_type(meta) is not None` rather than per-field
presence. Canonical schema still passes; simplified schema also passes.

### Step 3: Write a migration command (idempotent, dry-run default)

Don't modify records inline from a one-shot script. Make it a proper CLI
subcommand so:

- It's discoverable (`--help` lists it)
- It's testable
- It can be re-run if more drifted records appear later

Required properties:

- **Idempotent**: running twice is a no-op the second time
- **Dry-run default**: `--apply` to actually write
- **JSON output option**: `--json` for machine inspection
- **Preserve provenance**: if a date is embedded in the record, use it; don't default to "now"
- **Sentinel for unrecoverable fields**: e.g., `source: "migrated:unknown"` — passes lint, stays auditable

### Step 4: Fix the upstream producer

This is the step teams skip. Without it, drift returns in weeks.

Common producers and their fixes:

- **Agents writing via Write/Edit tools** → update skill/prompt to mandate the canonical CLI (`kb compile --write-note`)
- **Scripts using a template** → update the template
- **Manual entry** → add a `kb new` command that emits the canonical shape

Document WHY in the producer's skill/readme so the next author doesn't
regress: "Use the CLI path because direct Write bypasses frontmatter
generation and creates schema drift."

### Step 5: Verify

Run the validator on real data:

```bash
kb migrate-frontmatter --apply
kb lint --json | jq '.frontmatter | map(select(.fields_missing | length > 0)) | length'
# Should output: 0
```

## Verification

- Validator reports 0 issues on the full corpus
- Migration is idempotent (running twice is a no-op)
- Producer fix is deployed (skill updated, code merged)
- A new test covers the dual-acceptance case so regression is caught

## Example

Real case from an Obsidian-based knowledge wiki:

- **Before**: 49 of 134 notes failed `kb lint` due to missing `id`, `status`, `confidence`, `scope` fields + `type: pattern` (simplified) rejected as invalid
- **Change**: (a) relaxed `frontmatter.py` to dual-accept, (b) added `kb migrate-frontmatter` CLI, (c) updated `compile-note` skill to mandate `kb compile --write-note` over direct file writes
- **After**: `kb lint` reports 0 issues across all 134 notes; future compile runs via CLI path will emit canonical shape; migration rerunnable if drift recurs

## Notes

- Coverage: add a direct test for the resolver helper and at least one CLI-level test showing the simplified schema passes. The resolver is where regressions hide.
- If the spec has been relaxed across many fields, don't bundle them — one PR per logical change. Reviewers can reason about "either-or on knowledge_type" but not "15 loosened constraints."
- Migration sentinels (`migrated:unknown`) should be *greppable* so you can audit how many records needed them later.
- If the producer is a hostile/untrusted source (external API, user input), don't relax the spec — validate at the boundary and reject. This playbook is for cooperative drift within a system you control.

## Related

- **Dual-write migrations** (for data-plane schema changes): write to both old and new shape for a deprecation window before removing the old path
- **Expand-contract pattern**: add new field, backfill, switch readers, remove old field — analogous but for data platforms
