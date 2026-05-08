---
name: apm-marketplace-authoring-gotchas
description: |
  Eight APM-marketplace-authoring gotchas discovered during real
  migrations from hand-authored .claude-plugin/marketplace.json to
  APM-managed and from CC-native plugin authoring.
  Use when: (1) running `apm pack`, `apm marketplace check`, or `apm pack
  --dry-run` in a repo with an `apm.yml`; (2) wiring CI for an APM
  marketplace; (3) the CI staleness check (`apm pack && git diff
  --quiet`) fails despite a clean local; (4) prettier reformats
  `marketplace.json` after `apm pack` writes it; (5) APM exit code 1 on
  local-path-only marketplaces; (6) confused by `packages:` in apm.yml
  vs `plugins:` in marketplace.json; (7) commitlint rejects a commit
  with `footer-leading-blank` despite no apparent footer; (8) `apm
  compile -t claude` exits 0 with zero output and no compiled plugin
  appears; (9) husky+lint-staged pre-commit blocks the FIRST marketplace
  commit with markdownlint `MD040/fenced-code-language` errors on a
  SKILL.md file copied verbatim from `~/.claude/skills/`. The gotchas
  form a chain — fixing one usually surfaces the next.
author: Claude Code
version: 1.2.0
date: 2026-05-08
---

# APM Marketplace Authoring Gotchas

A real migration from a hand-authored `.claude-plugin/marketplace.json`
to an APM-managed marketplace took 18 commits and ~6 CI iterations
because of eight compounding behaviors. Each one looks like a
configuration mistake; each one is actually a tool quirk. Knowing
them up front collapses the discovery cycle.

## Problem

You set up `apm.yml` with a `marketplace:` block, run `apm pack`,
commit the regenerated `.claude-plugin/marketplace.json`, push, and
CI fails. You fix the obvious thing, push again, CI fails again with
a different error. After ~6 such loops you find yourself rewriting
git history. The fix sequence below short-circuits the loop.

## Context / Trigger Conditions

Any of these symptoms point here:

- `apm marketplace check` (with or without `--offline`) exits 1 even
  though every entry shows `[x]` in the table.
- CI's "verify marketplace.json is up-to-date" step fails with a diff
  showing `"source": "./plugins/foo"` vs `"source": "./foo"`.
- `npm run format:check` fails with prettier complaining about
  `marketplace.json` even though `.prettierignore` lists it.
- A schema validation error along the lines of "unknown field
  `plugins`" or vice versa.
- `commitlint` rejects a commit with `footer must have leading blank
line` even though the body has no obvious footer.

## Solution — five compounding fixes

### 1. Pin the APM CLI version in CI

`curl -sSL https://aka.ms/apm-unix | sh` (the canonical install line)
fetches the **latest** release. Local installs are easy to leave
behind. Version drift between local and CI silently changes the
output of `apm pack`, which breaks any staleness check
(`apm pack && git diff --quiet`).

The installer accepts a version tag:

```bash
curl -sSL https://aka.ms/apm-unix | sh -s -- @v0.12.1
```

Pin the same tag in CI and locally. Behavior changes between APM
0.11 and 0.12 are real (see #4 below); this is not paranoia.

To install to a non-sudo location locally:

```bash
curl -sSL https://aka.ms/apm-unix | APM_INSTALL_DIR="$HOME/.local/bin" bash -s -- @v0.12.1
```

### 2. `apm pack --dry-run` is the schema-validation command (not `apm marketplace check`)

`apm marketplace check` runs `git ls-remote` against every package by
default. For a marketplace where every entry is `source: ./local-path`,
ls-remote fails with exit 128 ("not a remote"), so the command exits
1 even though the manifest is valid.

`--offline` is supposed to fix this but actually flips the failure
mode — every entry now gets "No cached refs (offline)" as a Detail
and the command still exits 1. (Running `apm pack` first populates
some cache and _temporarily_ flips it to exit 0, but this is racy and
unreliable.)

Use `apm pack --dry-run` for schema validation. It validates the
`marketplace:` block, refuses on schema errors, exits 0 on success,
and writes nothing.

```make
check: ## validate apm.yml schema
 apm pack --dry-run
```

For CI:

```yaml
- name: Validate apm.yml schema
  run: apm pack --dry-run

- name: Verify marketplace.json is up-to-date
  run: |
    apm pack
    if ! git diff --quiet .claude-plugin/marketplace.json; then
      echo "::error::marketplace.json is stale. Run 'apm pack' locally."
      git --no-pager diff .claude-plugin/marketplace.json
      exit 1
    fi
```

### 3. `apm pack` emits inline JSON; prettier reformats to multi-line

`apm pack` writes `"tags": ["a", "b"]` (inline). Husky/lint-staged
running prettier on commit reformats to:

```json
"tags": [
  "a",
  "b"
]
```

The diff between APM's output and the prettier-formatted committed
version is permanent — every CI run regenerates `marketplace.json`
and finds it stale.

Fix: let APM own the format of its own output.

`.prettierignore`:

```text
.claude-plugin/marketplace.json
```

**Then verify your scripts respect it.** Prettier's `--ignore-path`
flag is single-source: passing `--ignore-path .gitignore` _overrides_
the default behavior of also reading `.prettierignore`. Many
boilerplate `package.json` setups have this pitfall:

```json
"format:check": "npx prettier --check '**/*' --ignore-path .gitignore"
```

This silently ignores `.prettierignore`. Pass both files explicitly:

```json
"format:check": "npx prettier --check '**/*' --ignore-path .gitignore --ignore-path .prettierignore"
```

(The fix applies to `format` and any `lint:*` scripts that delegate
to prettier with `--ignore-path`.)

### 4. APM 0.11 uses `packages:` in apm.yml; output marketplace.json uses `plugins:`

The `marketplace:` block inside `apm.yml` lists entries under
**`packages:`**, not `plugins:`. Older marketplace-authoring docs and
example configs may show `plugins:`. APM 0.11+ rejects `plugins:` as
an unknown key.

```yaml
marketplace:
  owner:
    name: <owner>
  metadata:
    pluginRoot: ./plugins
  packages: # NOT `plugins:`
    - name: <name>
      source: ./plugins/<name>
      version: 0.1.0
```

The compiled `.claude-plugin/marketplace.json` **still** uses
`plugins:` because that's what the Anthropic spec requires. APM
renames between the two. So:

- `apm.yml.marketplace.packages[]` is the source of truth (input).
- `marketplace.json.plugins[]` is the compiled output (consumed by
  Claude Code, Copilot CLI, etc.).
- `jq '.plugins | length' .claude-plugin/marketplace.json` works (output).
- `jq '.marketplace.packages | length' apm.yml`-equivalent does not — different file, different format.

Audit any tooling that reads from one and writes to the other —
they're not interchangeable.

### 5. APM 0.11 → 0.12: pluginRoot rewriting

APM 0.12 implements the documented `pluginRoot` rewrite: with
`metadata.pluginRoot: ./plugins`, a `source: ./plugins/foo` entry is
emitted in `marketplace.json` as `source: ./foo` (relative to
pluginRoot). APM 0.11 emits it verbatim as `./plugins/foo`.

Both are functionally equivalent for consumers (the documented
rewrite prevents a double-prefix bug in some code paths), but the
**output text differs**. CI installing 0.12 + local at 0.11 →
staleness check always fails.

This is the concrete reason #1 (pin the version) matters in
practice.

### 6. commitlint `footer-leading-blank` false-positives on em-dash + "PR #N." patterns

commitlint's default conventional-commits config flags certain text
patterns at the end of a commit body as "footer" tokens. Real-world
trigger:

```text
fix(ci): pin APM CLI to v0.12.1 and regenerate marketplace.json

APM 0.12.1 emits paths relative to pluginRoot per docs; 0.11.0 emits
absolute paths. The unpinned curl-pipe in CI installed 0.12.1 while
local was at 0.11.0 — the version drift broke the staleness check on
PR #32. Pinning CI fixes the drift.
```

This rejects with `footer must have leading blank line`. The em-dash
(`—`) plus `PR #32.` triggers the footer detector even though there's
no actual footer.

Workarounds (any one is enough):

- Avoid em-dashes in commit bodies; use plain dashes (`-`) or rephrase.
- Avoid `PR #N.` references in the body; put them in a real footer:

  ```text
  Refs: #32
  ```

  with a blank line before.

- Use shorter, simpler commit bodies; reserve drama for the PR description.

This is the cheapest gotcha to avoid going forward — keep commit
bodies plain.

### 7. `apm compile -t claude` is a no-op when the plugin is already in CC native format

`apm compile -t claude` is a _translator_: it reads APM-native
authoring primitives (`agent.yaml`, `tool.yaml`, etc. under the
plugin source) and emits the Claude Code plugin format
(`SKILL.md` files + `plugin.json` under `.claude-plugin/`).

If you authored the plugin **directly in CC native format** (you
wrote the `SKILL.md` files yourself, dropped them under
`plugins/<name>/skills/`, and hand-wrote
`plugins/<name>/.claude-plugin/plugin.json`), there are no APM
source files to translate. `apm compile -t claude` finds nothing
to compile, emits no output, and exits 0. To a casual observer
this looks identical to a successful translation that produced
nothing — i.e. a broken build.

It isn't broken. It's working as designed for the wrong input.

**Detection signal:** `find plugins/<name> -name 'agent.yaml' -o -name 'tool.yaml' | head`.
If empty → CC-native authoring; `apm compile` is irrelevant for
your build path. Rely on `apm pack` alone to package the
marketplace, and don't run `apm compile -t claude` in CI.

**Two valid authoring paths, don't mix:**

| Path           | Author in                                           | Build with                                                 | Notes                                                                                 |
| -------------- | --------------------------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| **APM-native** | `agent.yaml`, `tool.yaml`, etc. under plugin source | `apm compile -t claude` (translate) → `apm pack` (package) | Required if one source must compile to multiple targets (Claude, Cursor, Copilot, …). |
| **CC-native**  | `SKILL.md` + `plugin.json` directly in CC layout    | `apm pack` only — `compile` is a no-op                     | Faster authoring, but Claude-only.                                                    |

**The trap:** if you set up CI with `apm compile -t claude && apm pack`
expecting the first command to be the build step, the build will
look successful (exit 0) but your packaged marketplace will be
empty or stale, depending on what's in `plugins/`. Symptom is
"my plugin works locally but the published marketplace shows no
skills."

Concrete origin: building the `cajias/nautilus-competition`
marketplace plugin (May 2026), which bundles existing
hand-authored skills lifted from `~/.claude/skills/` rather than
translating from APM primitives.

### 8. husky+markdownlint blocks the FIRST commit of a SKILL.md copied from `~/.claude/skills/`

When you author a skill at `~/.claude/skills/<name>/SKILL.md`, then
copy it verbatim into an APM marketplace tree at
`plugins/<plugin>/skills/<name>/SKILL.md` and try to commit, the
marketplace repo's husky + lint-staged pre-commit (running
`markdownlint --fix`) often rejects the file. The user's
`~/.claude/skills/` directory has no such gate — the trap is silent
until the FIRST marketplace commit.

Symptom signature:

````text
✖ npx markdownlint --fix:
plugins/<name>/skills/<name>/SKILL.md:NN MD040/fenced-code-language Fenced code blocks should have a language specified [Context: "```"]
husky - pre-commit script failed (code 1)
````

The block in the SKILL.md looks like a perfectly normal example —
example output, log dump, raw shell session, or commit-message
snippet — but the bare ` ``` ` (no language tag) trips MD040.
The `apm pack` step ran fine; the staleness check would have passed;
the plugin tests pass. The only thing blocking the commit is
markdownlint on the SKILL.md itself.

**Fix:** in any SKILL.md destined for an APM marketplace, never use
bare ` ``` ` — always tag the language. For example output, log
dumps, raw shell sessions, or commit-message snippets that aren't a
real language: use ` ```text `. For real languages, tag
accurately (`yaml`, `json`, `python`, `bash`, `make`, etc.).

**Workflow implication:** if you're using `claudeception` to extract a
skill that you intend to vend through an APM marketplace, run a
markdownlint pass against the new SKILL.md _before_ dropping it into
`plugins/<plugin>/skills/<name>/`. That saves a pre-commit round-trip:

```bash
npx --yes markdownlint-cli ~/.claude/skills/<name>/SKILL.md
```

If MD040 fires, fix the bare fences before copying. After fixing,
either re-extract via claudeception or just propagate the language
tags into the source-of-truth at `~/.claude/skills/` so future copies
inherit the fix.

Note: husky also runs prettier on the same files, so the diff coming
out of a failed-then-fixed pre-commit cycle will mix legitimate
markdownlint fixes with prettier cosmetic noise (e.g. `*foo*` →
`_foo_`). The marketplace copy will drift slightly from the
`~/.claude/skills/` source even after a clean pre-commit — that's
expected and not worth back-porting.

Concrete origin: committing the `cc-plugin-authoring` plugin to
`cajias/claude-skills` (May 2026). Three unlanguaged fences across two
SKILL.md files (one in `apm-marketplace-authoring-gotchas`, one in
`cc-slash-command-argument-hint-yaml`) blocked the first commit;
tagging them as ` ```text ` passed.

## Verification

After applying the five fixes:

```bash
# locally
apm pack --dry-run                                       # exit 0
apm pack && git diff --quiet .claude-plugin/marketplace.json  # exit 0
npm run format:check                                     # exit 0

# in CI: lint, apm-marketplace, commitlint, plugin tests all pass
```

If staleness check fails again: check `apm --version` locally vs the
version logged by CI's "Verify APM version" step. They must match.

If prettier check fails again: run `npm run format:check 2>&1 | head`
— if it lists `.claude-plugin/marketplace.json`, your script isn't
honoring `.prettierignore`. Re-check the `--ignore-path` flags.

## Notes

- The five gotchas compound in a specific order: you usually hit them
  as 4 → 3 → 2 → 5 → 1 → 6 because each "fix" exposes the next layer.
  Knowing the chain ahead of time lets you apply all five preemptively.
- The lint-staged race between two parallel commits (both run
  `git stash --keep-index`) is a separate but related concern — avoid
  parallel implementer subagents on this kind of repo.
- These observations are against APM 0.11 → 0.12 (May 2026). Future
  versions may resolve some of them; re-verify before assuming.

## References

- microsoft/apm marketplace-authoring docs:
  <https://microsoft.github.io/apm/guides/marketplace-authoring/>
- APM CLI installer source (accepts `@vX.Y.Z`):
  <https://aka.ms/apm-unix>
- Anthropic plugin marketplace spec:
  <https://docs.claude.com/en/docs/claude-code/plugin-marketplaces>
- conventional-commits footer spec (commitlint default config):
  <https://www.conventionalcommits.org/>
- Concrete migration that surfaced these: `cajias/claude-skills` PR #32
  (Phase 1 APM marketplace migration, May 2026).
