# Eval: semantic-search

Plugin path: plugins/semantic-search

## Capability Evals

[CAPABILITY EVAL: semantic-search-structure]
Task: Verify plugin has all required structural files and fields
Success Criteria:

- [ ] .claude-plugin/plugin.json exists and is valid JSON
- [ ] plugin.json has name, description, and version fields
- [ ] At least one skills/ subdirectory with a SKILL.md file
- [ ] Each SKILL.md has YAML frontmatter with name and description
- [ ] No APM references (apm pack, apm marketplace, Agent Package Manager)
      Expected Output: All structural checks pass
      Grader: code-based (bash — see scripts/test-skills.sh)

[CAPABILITY EVAL: semantic-search-skill-quality]
Task: Verify skill descriptions are specific and triggerable
Success Criteria:

- [ ] Description is specific (not generic boilerplate)
- [ ] Skill content is substantial (> 200 chars per SKILL.md)
- [ ] Triggering context is clear in the description
- [ ] No placeholder text (TODO, TBD) in production skills
      Expected Output: All skill quality checks pass
      Grader: code-based (char count, grep)

## Regression Evals

[REGRESSION EVAL: semantic-search-claude-native]
Baseline: APM era (pre-migration)
Tests:

- plugin.json uses Claude-native format (not APM format): MUST PASS
- No APM CLI dependency for installation: MUST PASS
- Plugin installable by copying to ~/.claude/plugins/: MUST PASS
  Result: 3/3 must pass

## Plugin-Specific Checks

### Skills inventory

| Skill           | Trigger phrases                                                                    | Command(s)                              |
| --------------- | ---------------------------------------------------------------------------------- | --------------------------------------- |
| semantic-search | "What do I know about X?", "Find notes about...", search knowledge base by meaning | `/index-notes`, `/search-notes <query>` |

### Skill: semantic-search

- **Location**: `.claude-plugin/skills/semantic-search/SKILL.md`
- **What it does**: Embeds Obsidian Zettelkasten notes with `all-MiniLM-L6-v2`
  (local, no API calls) via sentence-transformers, stores vectors in LanceDB
  (embedded, serverless, stored in vault `.lancedb/`), and surfaces results by
  semantic similarity.
- **Implementation pattern**: Shells out to
  `uv run --project ${CLAUDE_PLUGIN_ROOT} ss-search "<query>"`, parses JSON
  results, then reads top 2-3 matching notes via Obsidian MCP tools
  (`mcp__obsidian__read_note`), and summarizes for the user.
- **Environment variables required**:
  - `SEMANTIC_SEARCH_VAULT_PATH` (default: `/Users/rc/Documents/Obsidian Vault`)
  - `SEMANTIC_SEARCH_DB_PATH` (default: `/Users/rc/Documents/Obsidian Vault/.lancedb`)

### Plugin-specific assertions

- [ ] `plugin.json` keywords include `semantic-search`, `zettelkasten`, `obsidian`, `lancedb`, `embeddings`
- [ ] `plugin.json` author field is present (name: "rc")
- [ ] SKILL.md description references natural-language trigger phrases ("What do I know about X?", "Find notes about...")
- [ ] SKILL.md documents the `ss-search` CLI entry point and expected JSON output format
- [ ] SKILL.md documents the `ss-index` CLI command for re-indexing
- [ ] Skill instructs Claude to use `mcp__obsidian__read_note` for reading matched notes (Obsidian MCP integration)
- [ ] No hardcoded vault paths in SKILL.md — environment variables are used instead
- [ ] `uv run --project ${CLAUDE_PLUGIN_ROOT}` invocation pattern is present (not bare `ss-search`)
- [ ] `pyproject.toml` defines `ss-index`, `ss-search`, and `ss-status` as script entry points

## Metrics Target

- pass@1: 100% for structure (deterministic)
- pass@3: > 90% for skill quality
