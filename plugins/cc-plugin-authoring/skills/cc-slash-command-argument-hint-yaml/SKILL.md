---
name: cc-slash-command-argument-hint-yaml
description: |
  Fix for Claude Code slash command frontmatter that fails to parse when
  `argument-hint:` is given square-bracketed placeholder values. Use when:
  (1) authoring `commands/<name>.md` files in a CC plugin and the
  frontmatter shows `argument-hint: [working-dir] [team-name]` or similar
  multi-token bracketed values; (2) a frontmatter-validation test
  (e.g. `yaml.safe_load(block)` over the SKILL/command frontmatter)
  raises `ScannerError` or `ConstructorError` complaining about flow
  sequences or "expected a mapping"; (3) the slash command silently
  doesn't appear in `/help` after install, or a plugin-marketplace test
  asserting the `description` field is present trips because the whole
  frontmatter parse blew up. The fix is to QUOTE the value as a single
  string. Covers the same trap for `commands/<name>.md` directly authored
  in CC format AND APM-managed marketplaces shipping commands via APM.
author: Claude Code
version: 1.0.0
date: 2026-05-08
---

# CC slash command `argument-hint` YAML parse trap

## Problem

When authoring a Claude Code slash command (`plugins/<plugin>/commands/<name>.md`),
the convention shown in many examples is:

```yaml
---
description: Run a multi-team competition.
argument-hint: [working-dir] [team-name]
allowed-tools: Bash
---
```

This **does not parse as YAML.** `[working-dir]` is a single-element flow
sequence. `[working-dir] [team-name]` is two flow sequences with whitespace
between them — invalid syntax for a scalar value. `yaml.safe_load` raises
`ScannerError` or `ConstructorError`.

Claude Code's command loader may swallow the parse error silently and the
command never appears in `/help`. Worse: in a plugin marketplace context,
a downstream test that asserts every command's frontmatter has a
`description` field will fail because the whole frontmatter block failed
to parse, not because `description` was actually missing — leading to
~30 minutes of looking at the wrong field.

## Trigger conditions

Any of these:

- `yaml.safe_load(frontmatter)` raises `yaml.scanner.ScannerError` or
  `yaml.constructor.ConstructorError`, often pointing at the
  `argument-hint:` line.
- A plugin-marketplace test like:

  ```python
  fm = yaml.safe_load(frontmatter_block)
  assert "description" in fm
  ```

  fails with a YAML error instead of an `assert` failure.

- The slash command was added to `plugins/<name>/commands/<cmd>.md` but
  doesn't show up in Claude Code's `/help` after `apm install`.
- The frontmatter on disk shows a value with multiple bracketed tokens:

  ```yaml
  argument-hint: [working-dir] [team-name]
  argument-hint: [path]
  argument-hint: [up|down]
  ```

## Solution

**Quote the value as a single string.** The angle-bracket form is the
idiomatic placeholder convention for shell argument hints:

```yaml
argument-hint: "<working-dir> <team-name>"
argument-hint: "<path>"
argument-hint: "[up|down]"          # square brackets = optional; OK INSIDE the quoted string
```

Quoting turns the value into a YAML scalar; the brackets are now just
characters in a string and don't trigger flow-sequence parsing.

If you genuinely want a YAML list of hint tokens (rare; the loader
typically wants a single string), use the explicit list form:

```yaml
argument-hint:
  - working-dir
  - team-name
```

But this is almost never what `argument-hint` consumers expect — they
treat it as display text shown next to the slash command in `/help`.
Stick with the quoted-string form.

## Verification

After quoting:

```python
import yaml
fm = yaml.safe_load(frontmatter_block)   # no longer raises
assert fm["argument-hint"] == "<working-dir> <team-name>"
```

In Claude Code:

```text
/help                                    # the command now appears
```

In the plugin tests (e.g., `tests/test_plugin_marketplace.py`):

```bash
uv run pytest tests/test_plugin_marketplace.py -v
# every command's `description` assertion runs against a parsed dict,
# not a parse exception
```

## Example — full command file (corrected)

```markdown
---
description: Scaffold a new team folder inside an existing competition working directory.
argument-hint: "<working-dir> <team-name>"
allowed-tools: Bash
---

You are running `/nautilus-competition:init-team`. Invoke:

    compete init-team {{1}} {{2}}

If the binary isn't on PATH, surface the install hint from
`plugins/nautilus-competition/README.md` (Install section).
```

## Notes

- The trap fires specifically on **multi-token** bracketed values. A
  single bare bracketed token like `argument-hint: [path]` parses as a
  one-element list, which the command loader may also reject (depending
  on how strictly it expects a string). Quote it for safety.
- Prettier and other YAML formatters generally leave bracketed flow
  sequences alone; they don't auto-quote, so the fix has to be by hand.
- This is unrelated to the `[tool.ruff.lint.per-file-ignores]` style
  square-bracket usage in `pyproject.toml` (TOML, different parser).
- Origin: discovered while shipping slash commands for the
  `cajias/nautilus-competition` APM plugin (May 2026). The agent's
  `_parse_frontmatter()` test helper caught it on first run; quoting
  all four `argument-hint` values made the test pass.

## References

- YAML 1.2 flow-sequence productions:
  <https://yaml.org/spec/1.2.2/#742-flow-sequence>
- Claude Code command authoring:
  <https://docs.claude.com/en/docs/claude-code/plugins> (commands section)
- Plugin development skill (`plugin-dev:command-development`) — the
  authoritative reference for command frontmatter fields. This skill
  documents the YAML-parse pitfall the command-development skill
  doesn't cover head-on.
