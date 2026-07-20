---
name: design-phase-artifacts
description: >-
  Use whenever the user asks to "do the design", "design this feature/change", produce design docs,
  write up an architecture, or plan a non-trivial change before implementation — this is the DESIGN
  phase of their AI-native SDLC. Trigger it even when they don't say "artifact" or name the documents.
  It produces a C4 architecture overview plus FIVE Notion design artifacts (Logical Design, Structural
  Design, Implementation Plan, Test & Verification Plan, Evaluation Plan), each grounded in the real
  code, and it encodes the content contract for each document plus the Notion publishing and
  orchestration gotchas. Prefer this over generic planning skills when the deliverable is a design that
  will be published to Notion.
---

# Design-Phase Artifacts (AI-native SDLC)

## What "design" means here

The user's lifecycle is Define → Design → Implement → Evaluate → Release. When they ask for "design",
they expect the DESIGN phase worked in full, not a single document. The deliverable is a C4
architecture overview that serves as the single source of truth, plus FIVE artifacts, each published
as its own Notion sub-page under the project's design parent page, and each grounded in the real code.
Deliver the set, not one doc.

The throughline behind every correction the user has made: design docs describe **intent and
verification at altitude, as a coherent narrative, grounded in the real scaffolding** — not code, not
ceremony, not a flat checklist. Hold that altitude and most of the rules below follow naturally.

## Ground first, before writing anything

Read the source of truth and the real code before drafting; never invent file or function names.

- The C4 overview design page is the single source of truth. Read it first.
- The SDLC bar comes from the user's playbook in Notion: "01 — The 5 Phases Pipeline" and
  "The AI-native SDLC". Read both for the per-phase expectations.
- Read the actual code modules you will cite. If a doc claims a function or file, it must exist.

## The five artifacts and their content contract

Each artifact opens with a one-line link back to the C4 overview and cross-references the other four by
title. Each section opens with short prose, then the diagram or table.

### 1. Logical Design — what the system does

Behaviour, independent of code shape. Include: testable behavioral requirements derived from the C4
acceptance criteria; the inputs and outputs of each flow; a lifecycle state diagram; the invariants
that must always hold; and an "AI Context" section recording the durable WHY (the model has no
cross-session memory, so the reason the change exists is written down here).

Fold every decision into ONE cohesive "Design decisions" section, written as flowing prose so the
design reads as a whole. Do NOT use ADRs here — no per-entry Status / Date / Context / Decision /
Consequences blocks. This is a design, not a decision log. No code.

### 2. Structural Design — what the code looks like

Where new modules sit (honouring the existing split), what existing modules are reused, the calibration
constants named, and a component diagram. Two things the user specifically expects:

- A **project file-layout tree**, grounded in the project's scaffolding convention. For this user that
  convention is the polyglot-monorepo-cookiecutter at ~/Projects/workspace/polyglot-monorepo-cookiecutter
  (src-layout package, flat tests/, ruff + mypy + vulture). Mark new and edited files in the tree, add a
  placement table (new file → cookiecutter convention → actual repo path → reason), and call out where
  the repo diverges from the template.
- Interfaces described as high-level OPERATIONS in a table (operation → home module → inputs → output →
  nature). Do NOT paste function-signature code blocks. The behavioural contracts live in the Logical
  Design; here you name the operations and their nature.

### 3. Implementation Plan — a workflow, not a checklist

This reads as a loop, with milestones in narrative form. The structure the user expects:

- A per-step rule: a step is done only when it has been reviewed, simplified, checked for gaps against
  the design intent, and verified by running something.
- A fixed closing gate at the end of every milestone — the "downward steps": (1) code review the diff,
  (2) simplify and remove anything the design did not call for, (3) gap assessment comparing what was
  built to the C4 and Logical Design intent, (4) verify with the milestone's behavioral check plus the
  full suite and the lint/type/dead-code gate. A milestone closes only on a pass that finds zero gaps;
  otherwise the gate spawns tasks for the next iteration and the milestone loops.
- A retrospective at the end of each iteration: what was done, and what would have made it faster. The
  answer updates this workflow, a lint rule, or a skill — the flywheel.
- An overall workflow Definition of Done across dimensions (behaviour, code quality, operational,
  governance, learning).
- Flag the steps that always need explicit human sign-off (adding a dependency, any destructive
  operation), and show milestone dependencies and what can run concurrently.

### 4. Test & Verification Plan — goals and verification methods

Behavioral (end-to-end) checks first, then per-component checks, each traced back to a Logical Design
behaviour. State each check as a GOAL plus a VERIFICATION METHOD in given/when/then prose. Do NOT paste
test code or pytest bodies. Name the real harness and fixtures, the coverage target, and the pre-commit
gate. Keep a table of existing tests to invert or retire.

### 5. Evaluation Plan — gap analysis in two readiness dimensions

A traceability matrix mapping each design claim and acceptance criterion to its verification. Track CODE
readiness (tests green, ruff/mypy/vulture clean, coverage at or above target) SEPARATELY from
OPERATIONAL readiness (runs on real data, the model loads, any tunable knob is calibrated, destructive
operations verified against a clean git tree, a regression pass). Include a risk register. Calibration
of tunable thresholds belongs here, against real data.

## Universal rules for every artifact

- High-level descriptions, well-defined goals, and their verification methods. No code in design docs —
  describe operations in prose and tables. Diagrams as needed (mermaid and file trees are fine; they are
  not "code").
- Ground every claim in the C4 source and the real code. Never invent names.
- Professional technical writing: concrete, varied sentence openings, minimal dashes, no marketing tone.

## Notion mechanics

- Create pages with notion-create-pages: parent is the project's design parent page, properties carry
  the title, give an emoji icon, and never put the title in the body.
- Edit with notion-update-page: update_content for an anchored search-and-replace (surgical edits, the
  old_str must match exactly), replace_content for a full rewrite, insert_content to add at the start or
  end.
- Diagrams: fenced ```mermaid blocks (quote node labels containing parentheses; use <br>, not \n).
  Tables: the <table header-row="true"> XML form, cells hold rich text only.
- C4 colour key: Person #08427B, System #1168BD, Container #438DD5, Component #85BBF0, External #999999,
  New (added by this design) #FFD43B.
- If unsure about the markdown, read the resource notion://docs/enhanced-markdown-spec with
  ReadMcpResourceTool (server "plugin_Notion_notion"); do not fetch that URI with notion-fetch.

## Orchestration gotchas (this is where time gets lost)

- Subagent Notion MCP access is unreliable. In a five-way fan-out, four agents published and one never
  connected, despite many retries. Do not assume a subagent can read or write Notion.
- Keep Notion reads and writes in the MAIN session. Subagents do read-only code grounding and DRAFT
  content; the main session fetches the C4 and playbook and publishes or edits the pages.
- The main thread may be blocked from writing files by an orchestrator hook, while subagents are not.
  See the cc-hooks-main-vs-subagent and plan-mode-orchestrator-write-deadlock skills. Consequence: even a
  shared grounding file must be written by a subagent, but the main session can still call Notion MCP
  tools and Read files.
- Verify published results by fetching the parent page's children, not by trusting agent self-reports —
  drafting agents often go idle without returning their URLs. See team-mode-orchestration-verification.
- Practical flow: main fetches C4 and playbook → a subagent writes a grounding file distilling them →
  fan out drafters that read the grounding plus the real code and hand drafts back → main publishes each
  via notion-create-pages → main verifies via the parent page's child list → main applies edits via
  notion-update-page.

## Worked example — Emergent Tag Taxonomy (karpathy-llm-wiki)

The first full run of this skill. Reuse these page ids to find the playbook and the exemplar artifacts.

- Playbook: "01 — The 5 Phases Pipeline" 38e8e91cd1b98175933ed84e15a536ca; "The AI-native SDLC"
  37d8e91cd1b9811b928ac09a556840ea
- Project design parent: "LLM Wiki Taxonomy Extension" 38e8e91cd1b9802eb72ff68ee08b8d09
- C4 source of truth: "Design — Emergent Tag Taxonomy (C4)" 38e8e91cd1b981e1a472c257b7fd6c94
- Logical Design 38e8e91cd1b981d1b474ec6904d7cd55; Structural Design 38e8e91cd1b9815a8601c6e8736cb250;
  Implementation Plan 38e8e91cd1b9818bb549c228bd3b8248; Test & Verification Plan
  38e8e91cd1b98108820be8f566a2f55b; Evaluation Plan 38e8e91cd1b9812480cfd5f77961201d
