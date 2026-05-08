# cc-plugin-authoring

Reference skills for authoring Claude Code plugins and APM marketplaces.
Bundles hard-won gotchas — discovered while shipping real plugins — into
two skills that activate via Claude Code's semantic skill matching.

## Skills

### `apm-marketplace-authoring-gotchas`

Seven compounding gotchas hit while migrating from a hand-authored
`.claude-plugin/marketplace.json` to an APM-managed marketplace. Each
"fix" tends to surface the next, so knowing the chain ahead of time
collapses ~6 CI iterations into one.

Highlights:

- `apm marketplace check` exits 1 on local-path-only marketplaces;
  use `apm pack --dry-run` for schema validation instead.
- CI staleness check (`apm pack && git diff --quiet`) fails when the
  APM CLI version drifts between local and CI — pin the install with
  `curl -sSL https://aka.ms/apm-unix | sh -s -- @v0.12.1`.
- Prettier reformats `marketplace.json` after `apm pack` writes it —
  add it to `.prettierignore` and pass _both_ ignore files explicitly
  to prettier scripts.
- `apm.yml.marketplace.packages` is the input; `marketplace.json.plugins`
  is the compiled output — different keys, not interchangeable.
- `apm compile -t claude` is a no-op when the plugin is already in
  CC-native format (`SKILL.md` + `plugin.json`); rely on `apm pack`
  alone.

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
apm marketplace add cajias/claude-skills
apm install cc-plugin-authoring
```

After install, both skills are available via Claude Code's semantic
matching — they surface automatically when you hit one of the trigger
conditions documented in each `SKILL.md`.

## Authoring path

Authored directly in CC-native format (`SKILL.md` + `plugin.json` under
the source tree). Build path is `apm pack` only — `apm compile -t
claude` is a no-op for hand-authored layouts (see
`apm-marketplace-authoring-gotchas` § 7).
