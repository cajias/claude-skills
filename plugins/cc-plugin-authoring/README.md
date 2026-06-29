# cc-plugin-authoring

Reference skill for authoring Claude Code plugins.
Bundles a hard-won gotcha — discovered while shipping real plugins — into
a skill that activates via Claude Code's semantic skill matching.

## Skills

### `cc-slash-command-argument-hint-yaml`

Specific YAML-parse trap when authoring slash commands. Frontmatter like
`argument-hint: [working-dir] [team-name]` parses as two adjacent flow
sequences and raises `yaml.scanner.ScannerError`. The slash command
silently never appears in `/help`, and any plugin-marketplace test
asserting the `description` field is present trips with a YAML error
that points at the wrong line.

Fix: quote the value as a single string —
`argument-hint: "<working-dir> <team-name>"`.

## Install

```bash
cp -r plugins/cc-plugin-authoring ~/.claude/plugins/
```

After install, the skill is available via Claude Code's semantic
matching — it surfaces automatically when you hit one of the trigger
conditions documented in its `SKILL.md`.
