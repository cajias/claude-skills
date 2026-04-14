---
name: teaching-variables-anthropic
description: |
  Learned from user correction: Teaching: variables: anthropic_model: 'opus' ``` or add a guard condition: ```yaml agent-mr:implement: rules: - if: '$agent_mr_v1_enabled == "true"' when: never - when: never # default: disabled ``` --- ## summary | aspect | finding | |--------|---------| | **model selection (v1)** | v1 hardcoded model in image; `anthropic_model` env var is ignored (dead code) | | **model selection (v2)** | v2 properly reads `anthropic_model` env var (line 54 in | Correction: User wants 'the' instead of 'defined in' | Avoid: 'variables: anthropic_model: 'opus' ``` or add a guard condition: ```yaml agent-mr:implement: rules: - if: '$agent_mr_v1_enabled == "true"' when: never - when: never # default: disabled ``` --- ## summary | aspect | finding | |--------|---------| | **model selection (v1)** | v1 hardcoded model in image; `anthropic_model` env var is ignored (dead code) | | **model selection (v2)** | v2 properly reads `anthropic_model` env var (line 54 in' | Expected behavior: 'v1 be disabled?** **recommendation**: **yes'
author: Claude Code (extracted by Claudeception v4.0)
version: 1.0.0
date: 2026-03-23
tags: ["correction", "learned", "negation_reference"]
level: user
breakthrough_score: 89.59
---

# Teaching: variables: anthropic_model: 'opus' ``` or add a gu

## Problem / Use Case

<task-notification>
<task-id>a6e8f02acb746877f</task-id>
<tool-use-id>toolu_bdrk_013f7GBZ3bTTomTJnJdzGL4e</tool-use-id>
<output-file>/private/tmp/claude-504/-Users-cajias-Projects-omega-worktree-agent

## When to Use This Skill

When making similar mistakes to: negation_reference

## Solution / Approach

Teaching: variables: anthropic_model: 'opus' `or add a guard condition:`yaml agent-mr:implement: rules: - if: '$agent_mr_v1_enabled == "true"' when: never - when: never # default: disabled ``` --- ## summary | aspect | finding | |--------|---------| | **model selection (v1)** | v1 hardcoded model in image; `anthropic_model` env var is ignored (dead code) | | **model selection (v2)** | v2 properly reads `anthropic_model` env var (line 54 in | Correction: User wants 'the' instead of 'defined in' | Avoid: 'variables: anthropic_model: 'opus' ``` or add a guard condition: ```yaml agent-mr:implement: rules: - if: '$agent_mr_v1_enabled == "true"' when: never - when: never # default: disabled ```--- ## summary | aspect | finding | |--------|---------| | **model selection (v1)** | v1 hardcoded model in image;`anthropic_model`env var is ignored (dead code) | | **model selection (v2)** | v2 properly reads`anthropic_model` env var (line 54 in' | Expected behavior: 'v1 be disabled?\***\*recommendation**:\*\*yes'

## Verification

- Apply the corrected approach and verify user acceptance

## Extraction Context

- Extracted automatically by Claudeception v4.0
- Breakthrough score: 89.59
- Classification: user
- Confidence: 0.85
- Corrections detected: 2
