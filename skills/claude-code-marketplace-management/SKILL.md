---
name: claude-code-marketplace-management
description: |
  How to discover and add Claude Code plugin marketplaces. Use when: (1) user asks
  about claudemarketplaces.com or similar discovery sites, (2) user wants to add a
  plugin marketplace, (3) confusion between marketplace directories and actual
  marketplaces, (4) user runs /plugin marketplace commands. Covers the distinction
  between discovery directories and installable marketplaces.
author: Claude Code
version: 1.0.0
date: 2026-01-26
---

# Claude Code Marketplace Management

## Problem
Users may confuse marketplace discovery directories (like claudemarketplaces.com) with
actual plugin marketplaces that can be added to Claude Code. The discovery site is for
browsing; the marketplaces listed on it are what you actually add.

## Context / Trigger Conditions
- User asks "how do I add this marketplace?" referring to claudemarketplaces.com
- User wants to discover available Claude Code plugins
- User is looking for plugin marketplaces to install
- User runs `/plugin marketplace` commands

## Solution

### Understanding the Hierarchy

1. **Discovery Directory** (e.g., claudemarketplaces.com)
   - A website that catalogs available marketplaces
   - You browse it, not install it
   - Automatically discovers GitHub repos with `.claude-plugin/marketplace.json`

2. **Plugin Marketplace** (e.g., `anthropics/claude-code`)
   - A GitHub repository containing Claude Code plugins
   - Added to Claude Code with a command
   - Contains multiple plugins you can then install

3. **Plugin**
   - Individual tools/skills within a marketplace
   - Installed after adding the marketplace

### Adding a Marketplace

```bash
/plugin marketplace add <owner>/<repo>
```

Examples:
- `/plugin marketplace add anthropics/claude-code` - Official Anthropic plugins
- `/plugin marketplace add wshobson/agents` - Community agent marketplace
- `/plugin marketplace add payloadcms/payload` - Payload CMS marketplace

### Listing Available Marketplaces

Browse claudemarketplaces.com to discover marketplaces by:
- Category (Development, AI, Security, etc.)
- GitHub stars (popularity)
- Plugin count
- Recently published

### Managing Marketplaces

```bash
# List added marketplaces
/plugin marketplace list

# Remove a marketplace
/plugin marketplace remove <owner>/<repo>
```

## Verification
After adding a marketplace, you should see:
```
Successfully added marketplace: <marketplace-name>
```

Then the plugins from that marketplace become available to install.

## Example

User: "How do I add claudemarketplaces.com?"

Answer: "claudemarketplaces.com is a discovery directory, not a marketplace itself.
Browse it to find marketplaces, then add them with:
`/plugin marketplace add <owner>/<repo>`

For example, to add the official Anthropic marketplace:
`/plugin marketplace add anthropics/claude-code`"

## Notes
- Marketplaces must have a valid `.claude-plugin/marketplace.json` file
- Only marketplaces with 5+ GitHub stars appear on claudemarketplaces.com
- The directory updates daily via automated GitHub search
- Always review marketplace code before installing (security best practice)

## References
- [Claude Code Marketplaces Directory](https://claudemarketplaces.com/)
- [About Claude Code Marketplaces](https://claudemarketplaces.com/about)
