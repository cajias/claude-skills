---
name: design-plan-docs
description: >-
  Generate the layered design-phase document set for a project — a north-star Project
  Intent doc plus Logic Design, Structural Design, Implementation Plan, and BDD Test Plan
  — each as a separate file under docs/design/, grounded in the maintainer's llm wiki and
  following a fixed content contract. Use this WHENEVER the user asks to "do the design",
  "write the design docs", "generate the plan docs", "create the design/plan documents",
  or to produce a logic design, structural design, implementation plan, or test plan
  before coding. Also use it when starting the design phase of any non-trivial feature or
  project, even if the user names only ONE of the documents. It enforces the house rules
  learned from real corrections: positive framing, requirement→tenet traceability, Mermaid
  diagrams (C4 + milestone DAG), and reusing existing scaffolds. This AUTHORS the
  plan and design docs; once the milestone plan exists and you're ready to execute
  it to green, use the iterative-build-loop skill instead.
---

# Design Plan Docs

Produce a coherent, layered set of design documents **before** implementation. Each doc
sits at one altitude and derives from the one above it, so a reviewer can ratify _intent_
without re-litigating _mechanism_. Write them as **separate files** under `docs/design/`
(the user reviews them individually and they become durable project artifacts).

## When to use

Any "let's design this / write the plan docs / do the design phase" request — even if the
user names only one document (e.g. "write the implementation plan"). Produce the whole
chain unless the user scopes it down; a lone doc with no intent above it floats free.

## The document set — author in this order

```
docs/design/
  00-project-intent.md      # north star: vision · tenets · measurable success criteria
  01-logic-design.md        # what & why + architecture (C4)
  02-structural-design.md   # code layout: folders/files + module boundaries
  03-implementation-plan.md # milestone DAG for loop-of-loops execution
  04-bdd-test-plan.md       # behavior as the primary gate
```

The chain: **00 → 01 (goals+use-cases+requirements) → 02 → 03 → 04.** Everything below 00
traces back to it (see Traceability).

## Step 1 — Ground the contracts in the llm wiki (do this first)

The maintainer's wiki defines the house content contracts. Pull them before authoring so
structure matches — don't invent headings. The wiki lives at
`~/Documents/Obsidian Vault/llm-wiki` and is queried with the `kb` CLI:

```bash
export KARPATHY_WIKI_ROOT="$HOME/Documents/Obsidian Vault/llm-wiki"
kb search "logical structural implementation test design document sections" --json
```

Read the notes it returns in full and cite them inline in each doc as `[[note-name]]`.
The load-bearing ones (search these if the query above misses them):

- `hld-documents-separate-solution-intent-from-implementation-detail-via-a-fixed-7` — the 7-section HLD structure (shapes 00/01).
- `c4-model-describes-systems-at-four-abstraction-levels-context-containers` — Context→Containers→Components→Code (shapes 01).
- `structure-implementation-plans-as-sequential-foundation-then-parallel-branches` — Group A→B→C→D (shapes 03).
- `three-tier-testing-behavior-integration-unit-with-behavior-as-primary-gate`, `write-gherkin-before-code-not-after`, `gherkin-scenarios-should-describe-behavior-not-ui-mechanics` — shape 04.
- `smart-goals-make-agent-objectives-measurable-and-bound-the-monitoring-loop`, `goals-must-be-immutable-during-execution` — shape 00's success criteria.

## Step 2 — Content contract per document

### 00 — Project Intent (the north star)

Tech-free. It states what must remain true so goals below can change without moving the
star. Sections: **Vision** (one line) · **Why this matters** (problem) · **Who it's for**
(actors) · **What it is** (positive; no "is not") · **Tenets** — the immutable
constraints, id'd `T1..Tn` · **Success criteria** — measurable/observable signals id'd
`SC1..SCn`, each tagged with the tenets it serves (per the SMART-goals note) · **Scope
(v1)** and **Future directions** (positive; see below) · **Derivation & trace rule**.

### 01 — Logic Design (what & why + architecture)

Context/problem · **Goals** (each cites the `T#`/`SC#` it serves) · Actors & use cases ·
Capabilities/behavior · Domain model (nouns + rules + invariants) · Key design decisions
(each with alternatives considered) · **Architecture (C4 model)** — Context, Container, and
Component levels, each **with a Mermaid diagram** · a runtime **data-flow** diagram (the
end-to-end path, e.g. scan → score → apply) · **Interfaces & data contracts** (the external
command/API signature → output schema, the data/config schemas, reference resolution) ·
**Runtime & permission model** (what runs read-only vs. what writes, and when — e.g. writes
only on apply, after confirm) · Open questions (owner + resolution point) · Scope (v1) &
future directions.

### 02 — Structural Design (code layout)

Strictly how the code is organized on disk. Sections: the **file/dir tree** (the actual
folders and files) · **Module boundaries** (one line per folder/file naming what it is
responsible for) · the **layout / reuse-scaffolds decision** (evaluate existing scaffolds —
a monorepo cookiecutter, shared lint-configs — and record which conventions to adopt and
why). Draw the layout **once**: the file/dir tree is the single canonical representation;
Module boundaries is a per-path responsibility list keyed to that tree (never a second
tree), and the layout decision references the canonical tree instead of redrawing it —
duplicated trees drift apart. Architecture, C4, interfaces, and the runtime model live in
01, not here; the only "diagram" in 02 is the text folder-tree.

### 03 — Implementation Plan (the milestone DAG for loop-of-loops execution)

A plan of **milestones**, not a flat task list — the `iterative-build-loop` skill is the
harness that _executes_ this doc, one milestone per loop with context cleared between them.
Milestones form a **DAG**: each names the milestone(s) it depends on, and the plan is ordered
to maximize parallelism — independent milestones run concurrently once their dependencies are
done. The classic shape is one valid DAG: a sequential foundation that freezes the contracts
everything builds against → parallel branches, independent once that foundation is frozen →
sequential cutover → final validation.

Each milestone carries three things:

- **Exit criterion — a behavior test that runs green.** The milestone is done only when a
  specific end-to-end scenario, named from the `04` BDD test plan, actually runs green as a
  runnable command whose result proves the goal — never a subjective "looks done." Name the
  scenario each milestone unlocks; this links every milestone to a `04` scenario, so the
  implementation plan and the test plan move in lockstep.
- **Context to load.** The files and contracts a cleared-context session must read first to
  build this milestone — kept self-contained precisely because context is cleared between
  milestones.
- **Deliverable.** What ships when the exit criterion goes green.

Goals stay immutable during execution. **Include a Mermaid milestone DAG** (see Diagrams).

### 04 — BDD Test Plan (behavior as the primary gate)

Three tiers: **Behavior** (Gherkin `.feature` files at the CLI/API boundary, one per
milestone, written _before_ the code, describing observable behavior not UI mechanics) →
**Integration** → **Unit**. Sign-off = behavior features green AND unit/integration green.
Gherkin steps name the **actors defined in 01** (Actors & use cases / the C4 Context) —
`Given the repo maintainer …`, `When the criteria author …`, never a generic "I" — so each
scenario traces back to a logical-design persona.

## Cross-cutting rules (these are the corrections; honor them every time)

- **Positive framing.** State the target, not the anti-target. No "Non-goals" / "is not" /
  "out of scope" sections — express boundaries as a positive **Scope (v1)** plus a
  **Future directions** roadmap of things wanted later. These docs are read by agents, and
  a negative example is a salient wrong example the model can latch onto. (Dedicated skill:
  `state-the-target`.)
- **Traceability.** 00 defines tenets `T#` and success criteria `SC#`. Every goal/
  requirement in 01 names the `T#`/`SC#` it serves; 04's behavior features assert the
  `SC#`s. Anything tracing to none of them is scope creep — that's what makes "design
  extends from intent" enforceable instead of decorative.
- **Diagrams, not just prose.** 01 gets the Mermaid C4 diagrams (Context/Container/Component)
  plus the runtime data-flow; 03 gets a Mermaid **milestone DAG** — nodes are milestones,
  edges are dependencies, independent milestones drawn on parallel branches (not collapsed
  into one line), and completed milestones marked (a ✅ or a `done` class) so the diagram
  doubles as a progress board for the loop. 02's only "diagram" is its text folder-tree — no
  C4 there. Use fenced ```mermaid blocks. Draw the _decided_ structure — settle layout choices
  before diagramming.
- **Reuse existing scaffolds.** In 02, before proposing a bespoke layout, check the
  maintainer's existing scaffolds (e.g. the polyglot monorepo cookiecutter at
  `~/Projects/workspace/monorepo-cookiecutter`, `lint-configs`, `claude-skills`)
  and adopt the conventions that fit — record the decision + rationale. Don't reinvent a
  layout that already exists a few repos over.
- **Altitude discipline.** 00 bans tech nouns (pure intent); 01 carries the logical
  architecture (C4, interfaces, runtime model) but not on-disk file paths; 02 is only the
  on-disk code layout. Keep each doc at its level so reviewers can approve one without
  re-opening the others.
- **Cross-reference by name, not number.** When one doc cites a section of another, name the
  section ("the Open questions section of `01`"), never `§7` — section numbers renumber as
  docs grow and the reference silently rots. Append new sections rather than inserting
  mid-document, so existing numbering stays stable.

## Output

Separate files `docs/design/00..04.md`, each opening with its own `# NN — Title` header.
When the harness blocks direct writes (orchestrator/plan mode), delegate the file writes to
a subagent. After writing, pause for the user to review before implementation.
