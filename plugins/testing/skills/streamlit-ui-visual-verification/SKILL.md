---
name: streamlit-ui-visual-verification
description: |
  Verify Streamlit dashboard changes by opening a real browser — not just probing
  the HTTP server. Use when: (1) you modified a Streamlit app and want to sign
  off on the change, (2) a smoke test passed via curl/HTTP 200 but you haven't
  actually looked at the page, (3) the change touched data-source selection,
  tab widgets from `extra-streamlit-components`, or dropdown population wired
  to a backend, (4) an exit gate / PR review needs UI evidence not just import
  evidence. Covers the "server-up ≠ UI-works" trap, iframe-isolated widget
  gotcha in extra-streamlit-components, Playwright MCP fallback when the
  claude-in-chrome extension is disconnected, and the specific failure signature
  where HTTP 200 + zero tracebacks + empty dropdowns means data binding silently
  broke between modules and the UI layer.
author: Claude Code
version: 1.0.0
date: 2026-04-08
---

# Streamlit UI: Visual Verification Required

## Problem

Streamlit dashboards fail in a particularly deceptive way: **the server stays
up, the Python side throws no exceptions, HTTP probes return 200, module
imports all work from the REPL — and the user-facing UI is still broken.**

The failure mode is not a crash. It's a silent two-sources-of-truth drift:

1. You edited module code (`modules/data_connector.py`) and added a new feature
   (e.g., a `PARQUET` data source enum). Unit-level smoke works.
2. You edited the Streamlit entry (`app/main.py`) at the call sites where the
   module is **instantiated** (e.g., `DataConnector(source="PARQUET", ...)`).
3. You forgot that the user doesn't instantiate anything — they click a button
   in an `extra-streamlit-components` tab widget. That widget is defined
   somewhere ELSE in `app/main.py` as a fixed list like:

   ```python
   chosen = stx.tab_bar(data=[
       stx.TabBarItemData(id="CSV", title="CSV", description="..."),
       stx.TabBarItemData(id="CLICKHOUSE", title="ClickHouse", description="..."),
   ])
   ```

4. Because `extra-streamlit-components` renders that widget **inside an
   iframe**, its state is isolated from the main Streamlit rerun graph. Adding
   a new branch in the module layer has ZERO effect on what shows up in the
   iframe. The user still sees only CSV and ClickHouse.

5. All server-side smoke tests pass. All imports succeed. The app "runs." The
   user opens it and the dropdowns are empty because PARQUET was never clicked.

This is how a Phase 1 integration can pass 8 exit-gate checks and still ship
a broken UI. The fix is cheap; the lesson is expensive.

## Context / Trigger Conditions

Apply this skill whenever ANY of the following are true:

- You made changes to a Streamlit app and plan to mark work complete / pass an exit gate
- You modified a module that the UI consumes (data connectors, strategy loaders, model wrappers) and you are about to call the change "done"
- The app uses `extra-streamlit-components` (`stx.tab_bar`, `stx.CookieManager`, etc.) — these render in iframes with isolated state
- A review pipeline is about to sign off based only on: curl probe, HTTP 200, no tracebacks in logs, module import success
- You added a new enum value, data source, strategy type, or dropdown option in Python and you're not 100% sure the UI widget also knows about it
- You are debugging "why doesn't my new feature show up in the app?"
- A teammate reports smoke tests green but the user says "the dashboard looks wrong"

## Solution

### Core principle: server-up ≠ UI-works

There are four levels of verification, each strictly weaker than the next.
Never claim "done" below Level 4 for UI-facing work.

| Level | What it proves | What it misses |
|---|---|---|
| **L1 — Imports** | Python module API is syntactically/type-wise intact | Whether the app calls the module at all |
| **L2 — Direct call** | Module returns correct data when called directly | Whether the UI ever triggers that call path |
| **L3 — HTTP probe** | Tornado is listening, Streamlit booted | Whether React rendered, widgets populated, events wired |
| **L4 — Visual check** | The user-visible UI shows the expected state | Nothing (this IS the ground truth the user sees) |

**L3 is the trap.** `curl localhost:8501` returning 200 tells you absolutely
nothing about whether the tab bar has a PARQUET button. Stop treating HTTP
probes as "smoke tests passed."

### Visual verification via Playwright MCP

The tool of choice is Playwright MCP
(`mcp__plugin_playwright_playwright__browser_*`). It works regardless of whether
the claude-in-chrome extension is connected.

Minimum viable visual check:

```
1. mcp__plugin_playwright_playwright__browser_navigate → http://localhost:8501
2. mcp__plugin_playwright_playwright__browser_wait_for → text="DataConnector" or a stable element
3. mcp__plugin_playwright_playwright__browser_snapshot → accessibility tree
4. mcp__plugin_playwright_playwright__browser_take_screenshot → filename: feature-YYYYMMDD.png
5. mcp__plugin_playwright_playwright__browser_console_messages → assert no red errors
```

### Assertions the snapshot must satisfy

Do NOT merely take a screenshot and move on. Inspect the accessibility tree
from `browser_snapshot` for explicit content:

- **New enum/option present**: the new button/tab appears with the expected label
- **Dropdowns populated**: Exchange/Symbol/TimeFrame (or equivalent) contain at least one option
- **No empty chart area**: the chart container has child elements, not just a placeholder
- **No error banner**: no `st.error` / `st.exception` rendered

If any assertion fails, the work is NOT done. This is a hard gate, not a soft
soft heuristic.

### The extra-streamlit-components iframe gotcha

`extra-streamlit-components` tab_bar, cookie_manager, etc. render in iframes.
That has two consequences:

1. **Adding a module-level enum does not auto-add a tab_bar item.** You must
   find the `stx.tab_bar(data=[...])` call and append a new `TabBarItemData`
   explicitly. Grep for `tab_bar`, `TabBarItemData`, `import extra_streamlit_components`.

2. **Playwright may need to enter the iframe context.** If `browser_snapshot`
   doesn't show the tab contents, use `browser_evaluate` with a script that
   enumerates `document.querySelectorAll('iframe')` and reads their
   `contentDocument`, or click the iframe frame directly.

### Dispatch brief additions (for teammates)

When dispatching a teammate to modify a Streamlit dashboard, include this in
the brief verbatim:

> **Mandatory visual verification before marking task complete:**
>
> 1. Launch the app: `uv run streamlit run app/main.py --server.headless true --server.port 8501` (run_in_background=true)
> 2. Use Playwright MCP to navigate to `http://localhost:8501`
> 3. Take a snapshot and assert the NEW feature is visible in the rendered UI, not just in the module API
> 4. Take a screenshot with a descriptive filename and commit it to `.claude/evidence/` (or paste the image in your SendMessage reply)
> 5. Kill the streamlit process when done (`kill <pid>` or `pkill -f "streamlit run"`)
>
> **Do NOT report completion based on HTTP 200, import success, or module-level smoke tests alone.** Those are necessary but insufficient. If you cannot produce a screenshot showing the feature working, the task is not done — say so explicitly and ask for help.
>
> **Watch for the extra-streamlit-components iframe gotcha:** if the app uses `stx.tab_bar` or similar widgets, the UI option list is defined in a fixed `data=[...]` argument. Adding a new enum in a module does NOT automatically add a tab. Grep `app/main.py` for `tab_bar` and `TabBarItemData` and edit the widget definition directly.

## Verification

After applying this skill, you should be able to answer yes to all of:

1. **Did I open an actual browser** (Playwright MCP, claude-in-chrome, or manual) and look at the rendered page?
2. **Did I inspect the accessibility tree / DOM** for the new feature's presence, not just take a blind screenshot?
3. **Did I assert that the dropdowns / dynamic content are populated**, not empty?
4. **Did I check the browser console** for red errors (not just the server logs)?
5. **If the UI uses iframe-isolated widgets, did I confirm those were edited** too — not just the module layer?

## Example

**Scenario (real incident, 2026-04-08):** Phase 1 integration of
`nautilus_trader_streamlit`. Task 1.6 was "add PARQUET data source to the
dashboard so it can read a NautilusTrader ParquetDataCatalog."

**What the teammate did:**

- Wrote `modules/parquet_data.py` with a full catalog reader ✓
- Added `PARQUET` branch to `DataConnector` in `modules/data_connector.py` ✓
- Replaced `DataConnector(csv_dir=".")` with `DataConnector(source=NT_DATA_SOURCE, data_dir=NT_DATA_DIR)` at `app/main.py:1521` and `:1686` ✓
- Wrote 4 smoke tests that all passed ✓
- Committed, ran reviewer, passed exit gate ✓

**What the teammate did NOT do:**

- Edit the `stx.tab_bar(data=[...])` definition to add a PARQUET TabBarItemData
- Open a browser and visually confirm the tab bar had a PARQUET button

**What the user saw when they opened the dashboard:**

- Tab bar: only `CSV` and `ClickHouse` buttons (no PARQUET)
- Exchange dropdown: empty
- Symbol dropdown: empty
- TimeFrame dropdown: empty
- Chart area: empty placeholder

**What the exit gate saw:**

- HTTP 200 on `localhost:8501` ✓
- `DataConnector(source='PARQUET', data_dir=...)` importable and returns 8 symbols ✓
- 0 tracebacks in streamlit stderr ✓
- 50/50 tests passed ✓
- → GREEN, signed off

**Root cause:** `extra-streamlit-components` tab_bar renders in an iframe.
The module layer and the iframe widget are two sources of truth. The module
learned about PARQUET; the iframe did not. No amount of HTTP probing would
have caught this.

**Correct verification that would have caught it:**

```
Playwright MCP:
  browser_navigate → http://localhost:8501
  browser_snapshot → accessibility tree
  Assert snapshot contains "PARQUET" text anywhere in tab_bar region
  → Would have failed. Task is not done.
```

## Notes

- **Streamlit's built-in `st.tabs`, `st.selectbox`, etc. are NOT iframe-isolated** — they rerender from the main script. The gotcha is specific to `extra-streamlit-components` and other third-party widgets that use Streamlit's Component API with iframes.
- **Console warnings are OK; console errors are not.** A broken widget will often log red errors but not crash the server.
- **Playwright MCP is the fallback** when `mcp__claude-in-chrome__*` returns "extension not connected." Always have the Playwright path ready.
- **This skill complements `team-mode-orchestration-verification`**: that one says "verify filesystem ground truth before trusting teammate self-reports." This one says "verify *user-visible* ground truth before trusting even the filesystem." They stack.
- **Headless mode is fine** for visual checks via Playwright — Playwright drives headless Chromium regardless. The point is the DOM, not a physical window.
- **Don't commit the running streamlit PID** to memory as "done" — kill it at end of each verification cycle so the next dispatch starts clean.

## References

- [Streamlit Component API — iframe isolation explanation](https://docs.streamlit.io/library/components/components-api)
- [extra-streamlit-components on PyPI](https://pypi.org/project/extra-streamlit-components/)
- Playwright MCP tools: `mcp__plugin_playwright_playwright__browser_*`
- Related skill: `team-mode-orchestration-verification` (sibling: filesystem ground truth)
- Incident that produced this skill: Phase 1 PARQUET dashboard integration, nautilus-trading project, 2026-04-08
