---
name: playwright-mcp-singleton-lock-workaround
description: |
  Workaround for "Browser is already in use for .../mcp-chrome-..., use --isolated
  to run multiple instances of the same browser" error from Playwright MCP. Use when:
  (1) You need to run browser automation but another teammate/session is already
  holding the Playwright MCP Chrome instance, (2) `mcp__plugin_playwright_playwright__browser_navigate`
  / `browser_snapshot` / `browser_close` all fail with the same Chrome SingletonLock
  error, (3) You're in a multi-agent team mode where two agents both need browser
  automation concurrently. Covers how to drive an isolated headless Chromium using
  `uv run --with playwright` without installing any new project dependencies.
author: Claude Code
version: 1.0.0
date: 2026-04-08
---

# Playwright MCP SingletonLock Workaround

## Problem

The Playwright MCP server (`@playwright/mcp`) launches Chromium against a fixed
`--user-data-dir` at `~/Library/Caches/ms-playwright/mcp-chrome-<hash>/`. Chrome
enforces a `SingletonLock` file inside that directory so only ONE Chrome
process can own it at a time.

In a **multi-agent team mode** (Claude Code's `TeamCreate` + multiple subagents),
if two agents both need Playwright MCP browser automation, the second one to
call any `mcp__plugin_playwright_playwright__browser_*` tool gets:

```
Error: Browser is already in use for /Users/<you>/Library/Caches/ms-playwright/mcp-chrome-XXXXXXX, use --isolated to run multiple instances of the same browser
```

Every subsequent call — `browser_navigate`, `browser_snapshot`, `browser_close`,
even `tabs_context_mcp` — returns the same error. `browser_close` does NOT
release the lock because the lock is held by a different MCP server instance,
not this one.

The `--isolated` flag the error mentions is an argument to the `playwright-mcp`
CLI itself, which is spawned by the Claude Code harness — **you cannot pass it
from the tool call site**. Claude-in-chrome is often unavailable as a fallback
("Browser extension is not connected").

## Context / Trigger Conditions

Apply this workaround when ALL of the following are true:

- You're in team mode or suspect another agent is using Playwright MCP
- `ps aux | grep playwright-mcp` shows a running MCP server from a different session
- Any `mcp__plugin_playwright_playwright__browser_*` call returns
  `"Browser is already in use for .../mcp-chrome-..., use --isolated..."`
- `browser_close` returns the same error (you can't even reset state)
- `mcp__claude-in-chrome__tabs_context_mcp` returns
  `"Browser extension is not connected"`

If you're NOT in team mode and hit this, try killing the stale playwright-mcp
process first: `pgrep -f playwright-mcp | xargs kill` — that may be enough.

## Solution

Drive a fully isolated Chromium from Python using the Playwright binary cache
that Playwright MCP already populated at `~/Library/Caches/ms-playwright/`.
**No new project dependencies are installed** — `uv run --with playwright`
creates an ephemeral venv that lasts only for the command.

### Step 1: Confirm Chromium is available in the cache

```bash
uv run --with playwright python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    b.close()
    print('chromium ok')
"
```

Expected output: `chromium ok`. If it says "Executable doesn't exist at ...",
you need `uv run --with playwright playwright install chromium` first — but
if the Playwright MCP server has ever run successfully on this machine, the
binary is already there.

### Step 2: Write a standalone verification script

Put the script in `/tmp/` (not in the repo — it's throwaway). Give it a real
`viewport`, capture `console` and `pageerror` events, and assert on
`page.evaluate("document.body.innerText")` contents. Key idiom:

```python
from playwright.sync_api import sync_playwright

console_messages = []
errors = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.on("console", lambda m: console_messages.append({"type": m.type, "text": m.text}))
    page.on("pageerror", lambda e: errors.append(str(e)))

    page.goto("http://localhost:8501", wait_until="networkidle", timeout=60_000)
    page.wait_for_timeout(3000)
    page.wait_for_function("document.body.innerText.includes('Data source')", timeout=30_000)

    # Walk iframes for iframe-isolated widgets (e.g. extra-streamlit-components)
    for f in page.frames:
        try:
            loc = f.get_by_text("Parquet", exact=False)
            if loc.count() > 0:
                loc.first.click(timeout=5000)
                break
        except Exception:
            pass

    page.wait_for_timeout(4000)
    body = page.evaluate("document.body.innerText")
    page.screenshot(path="/path/to/evidence.png", full_page=True)
    browser.close()

print("BINANCE in body:", "BINANCE" in body)
print("console errors:", sum(1 for m in console_messages if m["type"] == "error"))
print("page errors:", len(errors))
```

### Step 3: Run it

```bash
uv run --with playwright python /tmp/verify_ui.py
```

That's it. The ephemeral chromium launched by this command uses a
**different** user-data-dir than the MCP server, so SingletonLock never
conflicts.

### Step 4 (optional): Regression test across tabs

Write a second script that clicks every tab and asserts controls render
without tracebacks. Run them as two separate processes so each gets a fresh
browser context.

## Verification

You should be able to answer yes to all of:

1. Did the script print your expected assertion results (e.g., "BINANCE in body: True")?
2. Did `browser.close()` exit cleanly without "Browser is already in use"?
3. Did your screenshot file appear on disk?
4. Is the teammate's Playwright MCP session still working (you didn't kill their Chrome)?
5. Did you **not** add `playwright` to `pyproject.toml` / `requirements.txt`?

If all yes, you have a working parallel path and the teammate is unaffected.

## Example

**Real incident (2026-04-08, nautilus-trader-streamlit Task 1.11):**

Agent `fixer-2` needed to visually verify a Streamlit PARQUET tab fix using
Playwright MCP. Agent `explorer-1` (same team, different session) was still
holding the MCP Chrome instance. Every `browser_navigate` call returned:

```
Error: Browser is already in use for ~/Library/Caches/ms-playwright/mcp-chrome-082c387, use --isolated to run multiple instances of the same browser
```

`browser_close` returned the same error. `mcp__claude-in-chrome__tabs_context_mcp`
returned "Browser extension is not connected."

**Workaround used:**

```bash
# /tmp/verify_parquet_ui.py drives its own chromium via sync_playwright().
# Isolated user-data-dir — no conflict with MCP.
uv run --with playwright python /tmp/verify_parquet_ui.py
```

Output:

```
Assertion 1 — Parquet tab visible: True
Assertion 2a — BINANCE in Exchange: True
Assertion 2b — BTCUSDT in Symbol: True
Assertion 2c — 60min in TimeFrame: True
Assertion 2d — bar_type rendered: True
Console errors count: 0
Page errors count: 0
OVERALL: PASS
```

Screenshot saved to `.playwright-mcp/phase1-task111-parquet-working.png`.
Team lead received evidence; task #11 marked complete. `explorer-1`'s session
was unaffected.

## Notes

- **`uv run --with <pkg>` is the key primitive.** It creates an ephemeral venv
  just for that command, installs `playwright` (and its 3 deps) in ~20ms on
  warm cache, and never touches your project `pyproject.toml`. This is the
  right escape hatch whenever you need a one-shot dev tool without polluting
  dependencies.
- **The chromium binary is shared.** Playwright respects `PLAYWRIGHT_BROWSERS_PATH`
  or the default `~/Library/Caches/ms-playwright/`, and both the MCP server
  and your ephemeral script resolve to the same install. You are NOT downloading
  a second chromium.
- **Each `sync_playwright()` block gets an isolated user-data-dir** by default
  (Playwright generates a temp dir for each `launch()`). This is DIFFERENT from
  what the Playwright MCP server does — MCP pins a fixed dir for session
  persistence, which is what causes the SingletonLock.
- **`browser_close` is not a fix.** In the team-mode scenario, the lock is held
  by a different process. `browser_close` can't release someone else's lock;
  it just returns the same error.
- **Don't `kill` the other playwright-mcp process.** That kills your teammate's
  active work. Use the isolated workaround instead.
- **Don't hammer the MCP tool waiting for it to free up.** If the teammate is
  mid-task you may wait forever. Go isolated.
- **Streamlit-specific note:** `extra-streamlit-components` tab bars render
  inside an iframe at a URL like
  `http://localhost:8501/component/extra_streamlit_components.TabBar.tab_bar/...`.
  `page.get_by_text("Parquet")` on the main page will NOT find it. You MUST
  iterate `page.frames` and call `f.get_by_text(...)` on each frame. See the
  sibling skill `streamlit-ui-visual-verification` for more.
- **Headless is fine** — the goal is the DOM, not a physical window. Playwright
  drives headless Chromium just as well as headed.
- **Evidence attachment.** Save screenshots to
  `<repo>/.playwright-mcp/` so they end up in the git working tree for commit
  (team-lead expects `.png` evidence in SendMessage). The directory name is a
  convention that matches what the Playwright MCP server uses.

## References

- [Playwright Python sync API](https://playwright.dev/python/docs/api/class-playwright)
- [uv run --with docs](https://docs.astral.sh/uv/guides/scripts/#running-a-script-with-dependencies)
- Sibling skill: `streamlit-ui-visual-verification` (how to verify Streamlit
  dashboards without falling into the "server-up ≠ UI-works" trap)
- Sibling skill: `team-mode-orchestration-verification` (why you trust the
  filesystem / rendered DOM over teammate self-reports)
- Incident that produced this skill: nautilus-trading Phase 1 dashboard
  integration, Task 1.11 PARQUET tab fix, fixer-2 agent, 2026-04-08
