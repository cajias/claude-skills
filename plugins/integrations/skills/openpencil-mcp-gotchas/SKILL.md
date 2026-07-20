---
name: openpencil-mcp-gotchas
description: |
  Operational gotchas + recovery for driving the OpenPencil design editor through its MCP server (open-pencil / openpencil-mcp; the mcp__open-pencil__* tools — render, export_image, export_svg, set_image_fill, set_layout_child, set_font_range, new_document, save_file). Use when: (1) export_image returns "No visible nodes to export" though get_page_tree shows real nodes; (2) rendered text overflows/overlaps because a font (Inter, Newsreader, IBM Plex, Geist) is not installed and the app rasterizes with a wider fallback; (3) justify="space-between" in render JSX does not right-align children; (4) the app stops responding and every mcp__open-pencil__* call returns {"error":"RPC timeout (30s)"}; (5) set_image_fill hangs the app when given a real-photo-sized base64; (6) setting up open-pencil MCP for Claude Code. Complements the official open-pencil/skills@open-pencil API skill with the edge cases it does not cover.
author: Claude Code
version: 1.0.0
date: 2026-06-30
---

# OpenPencil MCP — Gotchas & Recovery

The official `open-pencil/skills@open-pencil` skill documents the tool API. This skill captures the operational edge cases that aren't in the docs and cost real debugging time.

## Setup (one-time)

- `brew install --cask openpencil` (macOS desktop app)
- `npm install -g @open-pencil/mcp` (provides the `openpencil-mcp` stdio binary)
- `claude mcp add --scope user open-pencil openpencil-mcp`
- (optional) add `"mcp__open-pencil__*"` to `permissions.allow` in `~/.claude/settings.json`
- The **desktop app must be RUNNING** — the stdio MCP server connects to it over WebSocket on **port 7601**. MCP tools only register at **Claude Code session start**, so after `claude mcp add` you must restart Claude Code before the `mcp__open-pencil__*` tools appear.

## Gotcha 1 — export_image "No visible nodes to export"

Symptom: `export_image` returns `{"error":"No visible nodes to export"}` even though `get_page_tree`/`get_node` show the node with real width/height, solid fills, opacity 1, visible true.
Cause: a node created purely via MCP (`render`/`new_document`) isn't painted on the app canvas until it is brought into view; the raster exporter needs a painted scene.
Fix: before `export_image`, call `select_nodes({ids:[id]})` then `viewport_zoom_to_fit({ids:[id]})`, THEN `export_image`.
Note: `export_svg` works WITHOUT this (computed from the scene graph, not rasterized) — use it to sanity-check geometry/text.

## Gotcha 2 — Missing fonts silently break layout

Symptom: text overflows its box / overlaps neighbors in `export_image`, even though the JSX gave it a fixed width and `get_page_tree` shows it "wrapped".
Cause: the requested font isn't installed, so the app lays out with the intended font's metrics but rasterizes with a wider fallback → overflow. Confirmed NOT installed: Inter, Newsreader, IBM Plex Sans/Mono, Geist. Confirmed installed: Georgia, Helvetica Neue.
Fix: check with `list_available_fonts({family:"X"})` BEFORE rendering; use an installed family (Georgia for serif, Helvetica Neue for sans). Always give a wrapping `<Text>` an explicit `w={...}` so it wraps instead of auto-widening to one long line.

## Gotcha 3 — justify="space-between" doesn't right-align

Symptom: a row Frame with `justify="space-between"` does NOT push its last child to the right edge (children sit together at the left).
Fix: give the left/main child sizing FILL so it eats the free space and pushes siblings to the edge. In JSX set the child `w="fill"`; or after render `set_layout_child({id, sizing_horizontal:"FILL", grow:1})`. This is how right-aligned link-row arrows and a split footer were achieved.

## Gotcha 4 — App hangs; every call returns RPC timeout (30s)  [the important one]

Symptom: a heavy `render` (or other op) returns `{"error":"RPC timeout (30s)"}`, and afterwards EVERY `mcp__open-pencil__*` call (even `get_current_page`) times out. The OpenPencil process and the port-7601 listener are still alive.
Key insight: the node process LISTENING on 7601 is the MCP server itself (`openpencil-mcp`), NOT the app — the app is the WS *client*. So the MCP connection (your tools) survives an app restart.
Recovery:

1. `kill <OpenPencil.app PID>` — kill ONLY the app process (`pgrep -f 'OpenPencil.app/Contents/MacOS/OpenPencil'`). Do NOT kill the process listening on 7601 (that's the MCP server; killing it drops your tools until a Claude Code restart).
2. `open -a OpenPencil` — relaunch; it reconnects to the surviving MCP server (verify with `lsof -nP -iTCP:7601 | grep ESTABLISHED`).
3. The relaunched app starts EMPTY (unsaved in-memory work is gone) → `new_document` then re-run your `render`. A fresh app reliably handles the same render that hung.
Mitigation: SAVE often (`save_file`) so a hang costs little; prefer one `render` of the whole tree on a fresh doc over many incremental edits.

## Gotcha 5 — set_image_fill base64 hangs the app (don't embed real photos)

Symptom: `set_image_fill({id, image_data:<base64>})` with a real-photo-sized image hangs the app (RPC timeout, then full hang per Gotcha 4).
Cause: `set_image_fill` only accepts inline base64, and real-photo byte sizes exceed the MCP inline-transport limit (see [[mcp-file-upload-base64-transport-limit]]). Even downscaled-but-still-photographic images wedged it.
Fix: don't embed real photos via `set_image_fill`. Use a colored placeholder Frame in the design and keep the real photo in the actual product (e.g. the website's `public/`), not the `.fig`. Tiny icon-sized PNGs may be OK — verify byte size first.

## render JSX quick reference

`<Frame name w h flex gap p bg rounded justify align>` and `<Text font size weight color w>`.

- `w`/`h`: number, `"fill"`, or `"hug"`. `flex`: `"col"`/`"row"`. `bg`/`color`: hex.
- `render` opts: `{jsx, parent_id?, replace_id?, insert_index?, x?, y?}`. `replace_id` swaps a node in place. One call can build an entire tree.

## Verification

- After recovery: `get_current_page` returns quickly (not a timeout).
- After the export fix: `export_image` returns image data instead of "No visible nodes".
- After the font/width fix: re-export PNG; text wraps within its box.

## References

- Official skill: <https://skills.sh/open-pencil/skills/open-pencil>  (`npx skills add open-pencil/skills@open-pencil`)
- MCP setup docs: <https://openpencil.dev/programmable/mcp-server>
- Related: [[mcp-file-upload-base64-transport-limit]]
