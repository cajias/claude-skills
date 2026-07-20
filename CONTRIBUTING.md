# Contributing

Thanks for contributing to `claude-skills` — a Claude-native marketplace of skills and plugins for
[Claude Code](https://docs.claude.com/en/docs/claude-code). Before you write any code, run through the plugin setup
below: this repo depends on plugins that Claude Code will not install for you, and it will not tell you when they are
missing.

## Plugin marketplace setup

### Why missing plugins fail silently

`.claude/settings.json` enables 17 plugins, but `enabledPlugins` is only a `name@marketplace -> bool` map. It carries no
information about where a marketplace comes from. Resolution happens against **your own** local marketplace registry.

If you have not added the marketplace a plugin comes from, that plugin simply does not load. There is no error, no
warning, and no entry in the logs — the plugin's skills and slash commands are just absent, as if they were never
configured. Cloning the repo is not enough; you have to register the marketplaces yourself.

### Marketplaces you need to add

Run these four commands once, from anywhere. All four sources are public GitHub repos and need no authentication.

```bash
claude plugin marketplace add cajias/claude-skills
claude plugin marketplace add DietrichGebert/ponytail
claude plugin marketplace add mksglu/context-mode
claude plugin marketplace add uditgoenka/autoresearch
```

They map to the enabled plugins like this:

| Marketplace     | Plugin provided |
| --------------- | --------------- |
| `claude-skills` | `dev`           |
| `ponytail`      | `ponytail`      |
| `context-mode`  | `context-mode`  |
| `autoresearch`  | `autoresearch`  |

### Plugins that need no setup

13 of the 17 enabled plugins come from `claude-plugins-official`, which ships with Claude Code. Nothing to install for
these: `code-review`, `feature-dev`, `pr-review-toolkit`, `code-simplifier`, `commit-commands`, `superpowers`,
`skill-creator`, `hookify`, `claude-code-setup`, `typescript-lsp`, `pyright-lsp`, `context7`, and `ralph-loop`.

That leaves the 4 non-official marketplaces above as the only manual step.

### Heads-up: `claude-skills` is a local directory for maintainers

On the maintainer's machine, the `claude-skills` marketplace is registered as a **local directory** source:

```bash
claude-skills -> Source: Directory (~/Projects/workspace/claude-skills)
```

That absolute path exists only on that machine. If you clone this repo and rely on the checked-in settings alone,
`dev@claude-skills: true` points at a marketplace name that resolves to nothing on your system, and the `dev` plugin —
including its `/dev:review-readme` skill — silently never loads.

Use the GitHub form instead, which is a drop-in replacement:

```bash
claude plugin marketplace add cajias/claude-skills
```

The marketplace name comes from the manifest (`.claude-plugin/marketplace.json` declares `"name": "claude-skills"`), not
from how you added it, so the existing `dev@claude-skills` key resolves identically. **Do not edit
`.claude/settings.json`** to work around this. Maintainers can keep the local directory source for live editing; only
onboarding needs the GitHub form.

### Verify your setup

After adding the marketplaces, restart Claude Code and run:

```bash
claude plugin list
```

You should see all 17 plugins listed as enabled, including the four non-official ones:

```text
dev@claude-skills           enabled
ponytail@ponytail           enabled
context-mode@context-mode   enabled
autoresearch@autoresearch   enabled
```

If a plugin is missing from the output entirely, its marketplace is not registered — re-run the matching
`claude plugin marketplace add` command above. As a functional smoke test, the `/dev:review-readme` skill should be
available once `dev@claude-skills` resolves.
