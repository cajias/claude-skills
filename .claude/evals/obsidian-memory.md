# Eval: obsidian-memory

Plugin path: plugins/obsidian-memory

## Capability Evals

[CAPABILITY EVAL: obsidian-memory-structure]
Task: Verify plugin has all required structural files and fields
Success Criteria:

- [ ] .claude-plugin/plugin.json exists and is valid JSON
- [ ] plugin.json has name, description, and version fields
- [ ] At least one skills/ subdirectory with a SKILL.md file
- [ ] Each SKILL.md has YAML frontmatter with name and description
- [ ] No APM references (apm pack, apm marketplace, Agent Package Manager)
      Expected Output: All structural checks pass
      Grader: code-based (bash — see scripts/test-skills.sh)

[CAPABILITY EVAL: obsidian-memory-skill-quality]
Task: Verify skill descriptions are specific and triggerable
Success Criteria:

- [ ] Description is specific (not generic boilerplate)
- [ ] Skill content is substantial (> 200 chars per SKILL.md)
- [ ] Triggering context is clear in the description
- [ ] No placeholder text (TODO, TBD) in production skills
      Expected Output: All skill quality checks pass
      Grader: manual (not implemented by scripts/test-skills.sh)

## Regression Evals

[REGRESSION EVAL: obsidian-memory-claude-native]
Baseline: APM era (pre-migration)
Tests:

- plugin.json uses Claude-native format (not APM format): MUST PASS
- No APM CLI dependency for installation: MUST PASS
- Plugin installable by copying to ~/.claude/plugins/: MUST PASS
  Result: 3/3 must pass

## Plugin-Specific Checks

### Skills Inventory

The plugin ships with two skills under skills/:

| Skill name                        | Directory                 | Purpose                                                                                                                                                                                              |
| --------------------------------- | ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| obsidian-memory:memory-system     | skills/memory-system/     | Teaches Claude to use Obsidian as primary workspace and persistent memory — covers when to write, where to write (decision tree), session folder protocol, and what NOT to store                     |
| obsidian-memory:search-navigation | skills/search-navigation/ | Efficient vault navigation and search — covers MCP tool selection guide, four named search strategies (frontmatter-first, structure-based, tag-based, recent activity), and batch operation patterns |

Assertions for each skill:

- [ ] YAML frontmatter present with name and description fields
- [ ] Description contains specific trigger conditions (not vague)
- [ ] Body has at least one reference table or decision aid
- [ ] No APM references or stale installation paths in skill body

### memory-system Skill Assertions

The `obsidian-memory:memory-system` skill establishes Obsidian as Claude's primary workspace.

- [ ] Describes session folder naming convention: `agent-workspaces/claude-[YYYYMMDD]-[HHMMSS]-[context]/`
- [ ] Lists the four standard session files: context.md, scratchpad.md, findings.md, tasks.md
- [ ] Contains a write-location decision tree (text or table form)
- [ ] Documents standard YAML frontmatter fields: type, status, date, summary, tags, related
- [ ] Calls out `agent-workspaces/shared/persistent.md` as cross-session persistent store
- [ ] Tag taxonomy table is present with Status, Type, Priority, and Sharing categories
- [ ] "What NOT to Store" section exists (generated code, secrets, large binaries)
- [ ] Cross-references `obsidian-memory:search-navigation` skill

### search-navigation Skill Assertions

The `obsidian-memory:search-navigation` skill provides efficient vault lookup patterns.

- [ ] MCP tool selection quick-reference table covers all core mcp\_\_obsidian tools
- [ ] Documents `searchFrontmatter` vs `searchContent` distinction for `search_notes`
- [ ] Four named search strategies are present (frontmatter-first, structure-based, tag-based, recent activity)
- [ ] Performance tips section exists with at least 3 recommendations
- [ ] Folder quick-reference table maps canonical vault paths (engagements/,
      knowledge-base/, people/, agent-workspaces/, etc.)
- [ ] Common searches reference table present mapping lookup goals to tool calls
- [ ] Cross-references `obsidian-memory:memory-system` skill

### MCP Dependency Assertions

Both skills rely on the Obsidian MCP server (`mcp__obsidian__*` tools). Neither
skill should hardcode vault paths — vault location is expected to come from the
MCP server configuration.

- [ ] No hardcoded `/Users/` or `~/Documents/Obsidian Vault` paths in skill bodies
- [ ] MCP tool names referenced match the `mcp__obsidian__` prefix convention
- [ ] `read_multiple_notes` batch limit (max 10) documented in search-navigation

### plugin.json Field Assertions

- [ ] `name` field is `obsidian-memory`
- [ ] `version` field follows semver (currently 1.2.0)
- [ ] `keywords` array includes: obsidian, memory, mcp
- [ ] `author.name` field present (not top-level string — uses object form)

## Metrics Target

- pass@1: 100% for structure (deterministic)
