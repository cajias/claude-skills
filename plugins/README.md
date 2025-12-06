# Claude Code Plugins

This directory contains Claude Code plugins that extend functionality through hooks, skills, and other capabilities.

## Available Plugins

### [PR Monitor](./pr-monitor/)

Automated GitHub pull request monitoring with event-driven hooks.

**Features:**

- Auto-detects new commits in monitored PRs
- Auto-resumes Claude Code when changes detected
- Multi-PR monitoring support
- Includes Stop hook + PR monitor skill
- Auto-cleanup on merge/close

**Installation:**

```bash
claude plugin install \
  https://github.com/cajias/claude-skills/tree/main/plugins/pr-monitor
```

## Plugin Structure

Each plugin follows this structure:

```text
plugin-name/
├── .claude-plugin/
│   └── plugin.json           # Metadata (name, version, description)
├── hooks/
│   └── hooks.json            # Hook definitions
├── scripts/
│   └── *.sh                  # Hook scripts
├── skills/
│   └── skill-name/
│       └── SKILL.md          # Skill instructions
└── README.md                 # Documentation
```

## Installation

### Via Plugin Manager (Recommended)

```bash
claude plugin install \
  https://github.com/cajias/claude-skills/tree/main/plugins/PLUGIN_NAME
```

Then restart Claude Code.

### Manual Installation

```bash
# Copy plugin to Claude plugins directory
mkdir -p ~/.claude/plugins/PLUGIN_NAME
cp -r plugins/PLUGIN_NAME/* ~/.claude/plugins/PLUGIN_NAME/

# Restart Claude Code
```

## Creating a Plugin

1. **Create plugin directory:**

   ```bash
   mkdir -p plugins/my-plugin/.claude-plugin
   mkdir -p plugins/my-plugin/hooks
   mkdir -p plugins/my-plugin/scripts
   mkdir -p plugins/my-plugin/skills/my-skill
   ```

2. **Add plugin.json:**

   ```json
   {
     "name": "my-plugin",
     "version": "1.0.0",
     "description": "Description of what the plugin does",
     "author": "Your Name",
     "license": "MIT"
   }
   ```

3. **Add hooks (optional):**

   ```json
   {
     "hooks": {
       "Stop": [
         {
           "matcher": "",
           "hooks": [
             {
               "type": "command",
               "command": "${CLAUDE_PLUGIN_ROOT}/scripts/Stop.sh"
             }
           ]
         }
       ]
     }
   }
   ```

4. **Add skills (optional):**
   Create `skills/skill-name/SKILL.md` with YAML frontmatter and instructions.

5. **Add documentation:**
   Create `README.md` with installation and usage instructions.

## Plugin Types

### Hook-Based Plugins

Plugins that extend Claude Code with event-driven automation:

- Stop hooks (run when Claude would idle)
- PreToolUse/PostToolUse hooks
- Notification hooks
- Session lifecycle hooks

### Skill-Based Plugins

Plugins that bundle specialized skills:

- Domain-specific workflows
- Multi-step procedures
- Tool integrations

### Hybrid Plugins

Plugins that combine hooks + skills:

- Example: PR Monitor (Stop hook + monitoring skill)
- Hooks provide automation
- Skills provide instructions

## Best Practices

1. **Use portable paths:**
   - Use `${CLAUDE_PLUGIN_ROOT}` in hook commands
   - Use `${CLAUDE_PROJECT_DIR}` for project-relative paths

2. **Document requirements:**
   - List required tools (gh, jq, etc.)
   - Specify version requirements
   - Include installation instructions

3. **Handle errors gracefully:**
   - Check for required tools before using
   - Provide clear error messages
   - Fail safely if dependencies missing

4. **Security considerations:**
   - Hooks execute with user privileges
   - Validate and sanitize all inputs
   - Document what the plugin can access
   - Warn about sensitive operations

5. **Test thoroughly:**
   - Test hook execution manually
   - Verify skill instructions work
   - Test on different systems
   - Include troubleshooting guide

## Publishing

1. **Commit plugin to repository**
2. **Tag releases:** Use semantic versioning (v1.0.0)
3. **Update main README** with new plugin
4. **Share repository URL** for installation

## Resources

- [Claude Code Hooks Documentation](https://code.claude.com/docs/en/hooks.md)
- [Claude Code Plugins Guide](https://code.claude.com/docs/en/plugins.md)
- [Claude Code Skills Documentation](https://code.claude.com/docs/en/skills.md)
- [GitHub CLI Manual](https://cli.github.com/manual/)

## License

All plugins in this directory are licensed under MIT License unless otherwise specified.
