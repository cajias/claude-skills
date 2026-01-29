---
name: obsidian-memory:search-navigation
description: Use this skill for efficient Obsidian vault navigation and search. Covers which MCP tools to use, search strategies, batch operations, and how to leverage frontmatter summaries for quick triage.
---

# Obsidian Search & Navigation

Efficient strategies for finding and accessing information in the Obsidian vault.

## MCP Tool Selection Guide

### Quick Reference

| Need | Tool | Why |
|------|------|-----|
| Read one file | `read_note` | Direct access |
| Read multiple files | `read_multiple_notes` | Batch (max 10) |
| Check file exists/metadata | `get_notes_info` | No content load |
| Get just frontmatter | `get_frontmatter` | See summary without content |
| Search by content | `search_notes` with `searchContent: true` | Full-text search |
| Search by metadata | `search_notes` with `searchFrontmatter: true` | Find by type/status/tags |
| Browse structure | `list_directory` | See folder contents |
| Find all tags | `manage_tags` with `operation: list` | See note's tags |
| Vault overview | `get_vault_stats` | Size, recent files |

### Tool Details

#### `get_frontmatter` - Fast Metadata Check
```
Use when: You need to understand what a file is about without reading content
Returns: Just the YAML frontmatter (type, status, summary, tags)
Perfect for: Triaging multiple files quickly
```

#### `get_notes_info` - Batch Metadata
```
Use when: Checking multiple files at once (up to array of paths)
Returns: Path, size, modified date, hasFrontmatter flag
Perfect for: Quick scan of a folder's contents
```

#### `search_notes` - Find Content
```
Parameters:
- query: Search text
- searchContent: true (default) - search in note body
- searchFrontmatter: true - search in YAML frontmatter
- limit: Max results (default 5, max 20)
- caseSensitive: false (default)

Use searchFrontmatter for:
- Finding notes by type: "type: decision"
- Finding by status: "status: active"
- Finding by summary keywords
```

#### `read_multiple_notes` - Batch Read
```
Parameters:
- paths: Array of note paths (max 10)
- includeContent: true (default)
- includeFrontmatter: true (default)

Use when: You know which files you need and want to read them efficiently
```

## Search Strategies

### Strategy 1: Frontmatter-First (Recommended)

When looking for notes on a topic:

1. **Search frontmatter** for summary keywords
   ```
   search_notes(query: "authentication", searchFrontmatter: true, searchContent: false)
   ```

2. **Get info** on promising results
   ```
   get_notes_info(paths: [results])
   ```

3. **Read** only the relevant ones
   ```
   read_note(path: "the-one-I-need.md")
   ```

### Strategy 2: Structure-Based

When you know the category:

1. **List directory** to see options
   ```
   list_directory(path: "knowledge-base/aws-services")
   ```

2. **Get frontmatter** for files of interest
   ```
   get_frontmatter(path: "knowledge-base/aws-services/lambda-patterns.md")
   ```

3. **Read** if summary matches need

### Strategy 3: Tag-Based

When looking for cross-cutting concerns:

1. **Search frontmatter** for tag
   ```
   search_notes(query: "#blocker", searchFrontmatter: true)
   ```

2. **Or search content** for inline tags
   ```
   search_notes(query: "#decision", searchContent: true)
   ```

### Strategy 4: Recent Activity

When looking for recent work:

1. **Get vault stats** with recent files
   ```
   get_vault_stats(recentCount: 10)
   ```

2. **Read** recent files that look relevant

## Efficient Patterns

### Pattern: Quick Context Load

Before starting work on a client/project:
```
1. list_directory("engagements/active/[client]")
2. read_note("engagements/active/[client]/context.md")
3. If decisions folder exists: list_directory + get_frontmatter on ADRs
```

### Pattern: Find Related Decisions

When making a technical choice:
```
1. search_notes(query: "[technology]", searchFrontmatter: true)
2. Filter results for type: decision
3. read_multiple_notes on relevant ADRs
```

### Pattern: People Lookup

When someone is mentioned:
```
1. list_directory("people")
2. Look for matching filename
3. read_note("people/[name].md")
```

### Pattern: Session Context Recovery

When resuming previous work:
```
1. list_directory("agent-workspaces")
2. Find relevant session folder by date/context
3. read_note("agent-workspaces/[session]/context.md")
```

## Performance Tips

1. **Prefer frontmatter search** over content search when possible (faster)
2. **Use `get_notes_info`** before reading full notes (check if worth reading)
3. **Batch reads** with `read_multiple_notes` instead of multiple `read_note` calls
4. **Use `limit`** parameter in search to avoid overwhelming results
5. **Check `hasFrontmatter`** in `get_notes_info` - files without it need full read

## Folder Quick Reference

| Path | Contains |
|------|----------|
| `engagements/active/` | Current client work |
| `engagements/completed/` | Archived engagements |
| `knowledge-base/` | Reference material by technology |
| `playbooks/` | Reusable methodologies |
| `people/` | Information about individuals |
| `career/` | Brag doc, promotion materials |
| `agentic-platform-program/` | Tech lead domain work |
| `agent-workspaces/` | Session workspaces |
| `agent-workspaces/shared/` | Cross-session persistent notes |

## Common Searches

| Looking for... | Search approach |
|----------------|-----------------|
| Active blockers | `search_notes("#blocker", searchFrontmatter: true)` |
| Decisions on X | `search_notes("type: decision", searchFrontmatter: true)` + filter |
| Lessons learned | `list_directory("knowledge-base/lessons-learned")` |
| Person info | `list_directory("people")` + `read_note` |
| Recent session | `get_vault_stats(recentCount: 5)` |

## Related

- See `obsidian-memory:memory-system` skill for when/what to store
- Check `CLAUDE.md` in vault root for vault-specific conventions
