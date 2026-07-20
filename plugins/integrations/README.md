# integrations

Field notes for driving third-party services from Claude Code. Each skill
captures a failure that cost real debugging time — a silent "No data" panel, an
upload that dies at 15 KB, a browser lock held by another session — plus the
reference material needed to get it right the next time. Skills surface
automatically through Claude Code's semantic matching when you hit one of the
trigger conditions documented in their `SKILL.md`.

## Skills

| Skill                                       | Purpose                                                                                                                                                 |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `grafana-dashboard-datasource-uid-mismatch` | Panels show "No data" when dashboard JSON hardcodes a uid that an unpinned provisioned datasource auto-generated differently.                           |
| `mcp-file-upload-base64-transport-limit`    | Why files over ~15 KB fail through base64-inline MCP tools (Drive, Notion), what to do instead, and Office auto-conversion behavior.                    |
| `notion-publish-generated-markdown`         | Publishing subagent-drafted Notion-flavored markdown: HTML-entity escaping, mermaid reserved-word node ids, confirming pages landed.                    |
| `openpencil-mcp-gotchas`                    | Recovery for the OpenPencil MCP editor: empty exports, missing-font overflow, RPC timeouts, base64 limits on `set_image_fill`.                          |
| `playwright-mcp-singleton-lock-workaround`  | Bypass Playwright MCP's Chrome SingletonLock by driving isolated headless Chromium via `uv run --with playwright`.                                      |
| `workers-best-practices`                    | Reviews and authors Cloudflare Workers code against production practices: streaming, floating promises, global state, secrets, bindings, observability. |
| `wrangler`                                  | Cloudflare Workers CLI reference for Workers, KV, R2, D1, Vectorize, Hyperdrive, Queues, Workflows, and Secrets Store.                                  |

## Install

```bash
cp -r plugins/integrations ~/.claude/plugins/
```
