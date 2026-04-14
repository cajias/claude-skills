---
name: teaching-applied-current
description: |
  Learned from user correction: Teaching: applied** - current code passes `changed_files`, but scoping only works if workspaces ≤ 5 (line 85) - for 6 tasks each changing ≤2 packages, verify scoping is triggered - may already be working; add telemetry to confirm - **estimated savings**: 3-4 minutes (if scoping cuts per-task validation by 50%) **optimization #3b: skip validation for deterministic tasks** - for pure env var renames with no logic changes, validation is overkill - add task metadata: `validation_required: true/false` - skip validation on low-risk tasks - **estimated savings**: 2-3 minutes (if 3-4 of 6 tasks are deterministic) --- ## bottleneck #4: claude code cli startup overhead **location**: `agents/base | Correction: User wants 'reasoning' instead of 'complex' | Avoid: 'reinstall - add flag: `if deps_already_installed: skip` - **estimated savings**: 5 minutes **optimization #5b: skip quality gates entirely for deterministic tasks** - if all 6 tasks are env var renames with no new code' | Expected behavior: 'reduce this by 60-70% **code evidence**: ```python # line 1019 in orchestrator'
author: Claude Code (extracted by Claudeception v4.0)
version: 1.0.0
date: 2026-03-24
tags: ["correction", "learned", "negation_reference"]
level: user
breakthrough_score: 11.73
---

# Teaching: applied\*\* - current code passes `changed_files`, b

## Problem / Use Case

<task-notification>
<task-id>acdbc1988bfec38ee</task-id>
<tool-use-id>toolu_bdrk_01MT55AD8BfoTBVntQq9ZKwV</tool-use-id>
<output-file>/private/tmp/claude-504/-Users-cajias-Projects-omega-worktree-agent

## When to Use This Skill

When making similar mistakes to: negation_reference

## Solution / Approach

Teaching: applied** - current code passes `changed_files`, but scoping only works if workspaces ≤ 5 (line 85) - for 6 tasks each changing ≤2 packages, verify scoping is triggered - may already be working; add telemetry to confirm - **estimated savings**: 3-4 minutes (if scoping cuts per-task validation by 50%) **optimization #3b: skip validation for deterministic tasks** - for pure env var renames with no logic changes, validation is overkill - add task metadata: `validation_required: true/false` - skip validation on low-risk tasks - **estimated savings**: 2-3 minutes (if 3-4 of 6 tasks are deterministic) --- ## bottleneck #4: claude code cli startup overhead **location**: `agents/base | Correction: User wants 'reasoning' instead of 'complex' | Avoid: 'reinstall - add flag:`if deps_already_installed: skip` - **estimated savings**: 5 minutes **optimization #5b: skip quality gates entirely for deterministic tasks** - if all 6 tasks are env var renames with no new code' | Expected behavior: 'reduce this by 60-70% **code evidence\*\*: ```python # line 1019 in orchestrator'

## Verification

- Apply the corrected approach and verify user acceptance

## Extraction Context

- Extracted automatically by Claudeception v4.0
- Breakthrough score: 11.73
- Classification: user
- Confidence: 0.85
- Corrections detected: 6
