---
name: teaching-reached-correction
description: |
  Learned from user correction: Teaching: reached | Correction: User wants 'because' instead of 'a bug' | User need: 'to' | Avoid: 'reached. so the tests correctly assert:\n- `mockcreateservicesource` called 1 time (not `mockupdateservicesource`)\n- `mockcreateroute` called 1 time (not `mockupdateroute`)\n\n### this is not a bug because:\n1' | Expected behavior: 'handle capability provider updated event\"\n- line 464-465: \"should update route when baseurl has changed\" (a2a)\n- line 485-486: \"should update route when baseurl has changed\" (mcp)\n- line 506-507: \"should update route when protocol path has changed\"\n- line 527-528: \"should update route when both baseurl and protocol path have changed\"\n- line 591-592: \"should handle protocol switch from mcp to a2a\"\n\nall 6 are in the update event handling path where the refactor changed from direct `update*` calls to `createorupdate*` (create-first upsert)'
author: Claude Code (extracted by Claudeception v4.0)
version: 1.0.0
date: 2026-04-01
tags: ["correction", "learned", "negation_reference"]
level: user
breakthrough_score: 48.72
---

# Teaching: reached | Correction: User wants 'because' instead

## Problem / Use Case

Analyze this conversation and determine: Does the assistant have more autonomous work to do RIGHT NOW?

Conversation:
[
{
"parentUuid": "35661aba-b79e-4696-947d-c3e7c32e6f39",
"isSidechain":

## When to Use This Skill

When making similar mistakes to: negation_reference

## Solution / Approach

Teaching: reached | Correction: User wants 'because' instead of 'a bug' | User need: 'to' | Avoid: 'reached. so the tests correctly assert:\n- `mockcreateservicesource` called 1 time (not `mockupdateservicesource`)\n- `mockcreateroute` called 1 time (not `mockupdateroute`)\n\n### this is not a bug because:\n1' | Expected behavior: 'handle capability provider updated event\"\n- line 464-465: \"should update route when baseurl has changed\" (a2a)\n- line 485-486: \"should update route when baseurl has changed\" (mcp)\n- line 506-507: \"should update route when protocol path has changed\"\n- line 527-528: \"should update route when both baseurl and protocol path have changed\"\n- line 591-592: \"should handle protocol switch from mcp to a2a\"\n\nall 6 are in the update event handling path where the refactor changed from direct `update*` calls to `createorupdate*` (create-first upsert)'

## Verification

- Apply the corrected approach and verify user acceptance

## Extraction Context

- Extracted automatically by Claudeception v4.0
- Breakthrough score: 48.72
- Classification: user
- Confidence: 0.85
- Corrections detected: 4
