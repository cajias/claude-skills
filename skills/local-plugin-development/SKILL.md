---
name: local-plugin-development
description: |
  Create and install local Claude Code plugins using a local marketplace.
  Use when: (1) developing a new plugin for personal use, (2) creating project-specific
  plugins without publishing, (3) rapid plugin prototyping, (4) user says "create a
  plugin locally" or "add a local plugin". Covers marketplace setup, plugin structure,
  and proper installation via CLI.
author: Claude Code
version: 2.0.0
date: 2026-01-26
---

# Local Plugin Development

## Problem

You want to create a Claude Code plugin for personal use or rapid prototyping without
publishing to a public marketplace.

## Context / Trigger Conditions

- Need to create a plugin quickly for personal use
- Want to prototype a plugin before publishing
- Creating project-specific tooling
- Need skills/commands/agents that are user-specific

## Solution

### 1. Set Up Local Marketplace (One-Time)

Create the marketplace structure:

```bash
mkdir -p ~/.claude/plugins/local-marketplace/.claude-plugin
```

Create `.claude-plugin/marketplace.json`:

```json
{
  "name": "local",
  "owner": {
    "name": "Your Name"
  },
  "plugins": []
}
```

Register it:

```bash
claude plugin marketplace add ~/.claude/plugins/local-marketplace
```

### 2. Create Plugin Structure

```bash
mkdir -p ~/.claude/plugins/local-marketplace/my-plugin/.claude-plugin
mkdir -p ~/.claude/plugins/local-marketplace/my-plugin/skills/my-skill
```

**Directory structure:**

```text
~/.claude/plugins/local-marketplace/
├── .claude-plugin/
│   └── marketplace.json      # Marketplace manifest
└── my-plugin/
    ├── .claude-plugin/
    │   └── plugin.json       # Plugin manifest
    └── skills/
        └── my-skill/
            └── SKILL.md
```

### 3. Create Plugin Manifest

Create `my-plugin/.claude-plugin/plugin.json`:

```json
{
  "name": "my-plugin",
  "description": "What this plugin does",
  "version": "1.0.0",
  "author": {
    "name": "Your Name"
  }
}
```

### 4. Add Plugin to Marketplace

Update `.claude-plugin/marketplace.json`:

```json
{
  "name": "local",
  "owner": {
    "name": "Your Name"
  },
  "plugins": [
    {
      "name": "my-plugin",
      "source": "./my-plugin",
      "description": "What this plugin does"
    }
  ]
}
```

### 5. Install Plugin

```bash
claude plugin install my-plugin@local
```

## Verification

```bash
# List installed plugins
claude plugin list | grep my-plugin

# Should show:
# ❯ my-plugin@local
#   Version: 1.0.0
#   Status: ✔ enabled
```

## Example

Creating an Obsidian memory plugin:

```bash
# Create structure
mkdir -p ~/.claude/plugins/local-marketplace/obsidian-memory/.claude-plugin
mkdir -p ~/.claude/plugins/local-marketplace/obsidian-memory/skills/{memory-system,search-navigation}

# Create plugin.json
cat > ~/.claude/plugins/local-marketplace/obsidian-memory/.claude-plugin/plugin.json << 'EOF'
{
  "name": "obsidian-memory",
  "description": "Persistent memory system using Obsidian vault",
  "version": "1.0.0"
}
EOF

# Create SKILL.md files in each skill directory...

# Add to marketplace.json (edit the plugins array)
# Then install:
claude plugin install obsidian-memory@local
```

## Marketplace JSON Schema

**Important**: The schema differs from what you might guess:

```json
{
  "name": "marketplace-name",
  "owner": {
    "name": "Owner Name"
  },
  "plugins": [
    {
      "name": "plugin-name",
      "source": "./relative/path/to/plugin",
      "description": "Plugin description"
    }
  ]
}
```

Key points:

- `owner` is an object with `name` (not a string)
- `plugins` is an array (not an object)
- `source` uses relative paths from marketplace root

## Managing Plugins

```bash
# List marketplaces
claude plugin marketplace list

# Update marketplace cache
claude plugin marketplace update local

# Disable plugin
claude plugin disable my-plugin@local

# Uninstall
claude plugin uninstall my-plugin@local
```

## Notes

### Why Not Symlinks?

Manual symlinks to `~/.claude/plugins/installed/` may work but:

- Not officially supported
- May break with updates
- `claude plugin list` won't show them correctly
- Use the proper CLI method instead

### Updating Plugins

After editing plugin files:

1. Update version in `plugin.json`
2. Run: `claude plugin update my-plugin@local`
3. Restart Claude Code

## See Also

- `plugin-dev:plugin-structure` - Full plugin structure documentation
- `plugin-dev:skill-development` - Writing effective SKILL.md files
