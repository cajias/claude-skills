---
name: notion-publish-generated-markdown
description: |
  Gotchas when publishing AI/subagent-drafted Notion-flavored markdown via the
  Notion MCP (notion-create-pages / notion-update-page) — especially design-phase
  artifacts with callouts, <table> blocks, and mermaid diagrams. Use when:
  (1) a published Notion page shows literal "&lt;callout" / "&lt;table" / "&amp;"
  instead of rendered blocks; (2) a subagent returns drafted markdown with HTML
  entities escaped (&lt; &gt; &amp;) that you are about to pass to
  notion-create-pages; (3) a mermaid diagram silently fails to render and a
  subgraph/node id is a reserved word such as `graph`, `end`, or `subgraph`;
  (4) you fanned out drafters to publish pages and need to confirm the pages
  actually landed.
author: Claude Code
version: 1.0.0
date: 2026-06-29
---

# Publishing Generated Markdown to Notion (gotchas)

## Problem

When you delegate Notion page drafting to a subagent and then publish the result,
two failure modes are common and both render as broken pages:

1. The drafted markdown comes back with HTML entities escaped (`&lt;`, `&gt;`,
   `&amp;`). Passed verbatim to `notion-create-pages`, Notion stores the literal
   text `&lt;callout ...&gt;` and `&lt;table&gt;` instead of rendering callouts and
   tables.
2. A mermaid diagram fails to render because a subgraph or node id collides with a
   mermaid reserved keyword (notably `graph`; also `end`, `subgraph`, `class`,
   `style`, `click`).

## Context / Trigger Conditions

- A subagent's returned draft (or a task-notification `<result>`) shows
  `&lt;callout`, `&lt;table`, `&lt;br&gt;`, or `&amp;` where literal `<` / `>` / `&`
  are intended.
- A published Notion page displays raw `<callout>` / `<table>` text instead of
  blocks, or a mermaid block renders as nothing / errors out.
- Mermaid: `subgraph graph["..."]` or a node id named `graph` silently breaks the
  render.

## Solution

Entity unescape, done between draft and publish:

1. Write the drafted body to a file.
2. Unescape, ampersand LAST so you do not double-process:
   `sed -i '' -e 's/&lt;/</g' -e 's/&gt;/>/g' -e 's/&amp;/\&/g' <file>`
   (GNU sed: drop the `''` after `-i`.)
3. Verify: `grep -c '&lt;\|&gt;\|&amp;' <file>` returns 0, and
   `grep -c '<callout\|<table' <file>` returns greater than 0.
4. Publish the cleaned file via `notion-create-pages` (content = cleaned body).

Prefer instructing drafters to BOTH emit literal characters AND run the sed pass
as a safety net before publishing — belt and suspenders, since models
intermittently re-escape.

Mermaid reserved-word collision: never use `graph` (or `end`, `subgraph`, `class`,
`style`, `click`) as a node or subgraph id; rename, e.g. `graph` -> `graphPkg`.
Also quote any node label containing parentheses, and use `<br>` not `\n` for line
breaks in labels.

Verify, do not trust self-reports: after a publish fan-out, fetch the PARENT page
and confirm each child appears in its child list, rather than trusting each
drafter's "published successfully" message.

## Verification

- `grep` for entities returns 0; for `<callout` / `<table` returns greater than 0.
- Fetch the published page: callouts, tables, and mermaid appear as real blocks,
  not literal text.
- Fetch the parent page: every expected sub-page is in the child list.

## Example

Publishing a C4 design doc whose drafter returned `&lt;callout icon="🎯" ...&gt;` and
a `subgraph graph["graph"]`:

- sed-unescaped the body so it held literal `<callout>` / `<table>` / `<br>` / `-->`.
- renamed the `graph` subgraph id to `graphPkg`.
- published via notion-create-pages, then fetched the page (blocks rendered) and
  the parent (all six children present).

## Notes

- Pairs with the `design-phase-artifacts` and `plan-mode-orchestrator-write-deadlock`
  skills: keep Notion reads/writes in the main session, but delegating the
  draft-and-clean to a subagent keeps the large content off the orchestrator's
  context.
- Subagent Notion MCP write access can be flaky; have drafters leave the cleaned
  file on disk and report its path so the main session can publish on failure.
- The Notion MCP token can expire mid-session ("requires re-authorization"); only
  the user can re-auth via `/mcp` — there is no agent-side auth tool.
