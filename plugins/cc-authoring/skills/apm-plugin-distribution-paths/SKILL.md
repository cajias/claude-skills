---
name: apm-plugin-distribution-paths
description: |
  Canonical authoring layout for an APM (microsoft/apm)
  package, plus the decision matrix for whether you need a `marketplace:` block.
  Use when: (1) you've run `apm init` and are unsure where SKILL.md / agent .md
  / command .md files belong (answer: under `.apm/`, NOT at repo root); (2)
  you've authored CC-native files at `commands/agents/skills/` at repo root and
  wonder if that's "right" (it works as fallback layout #3 "Claude plugin", but
  it's not the canonical authoring path); (3) you're trying to choose between
  the three layouts APM recognizes (one-skill repo, multi-primitive `.apm/`,
  Claude plugin); (4) `apm targets` fails with "No such command" in CLI 0.12.1
  (subcommand doesn't exist); (5) `apm validate` fails with "No such command"
  in CLI 0.12.1 (use APM's packaging command in dry-run mode instead); (6) wondering whether
  `apm compile -t claude` will generate output for a hand-authored CC-native
  plugin (it won't; it's a no-op for layout #3); (7) wondering if you need a
  `marketplace:` block in apm.yml (you don't, for a single-plugin repo).
  Covers the canonical `.apm/` source layout, the source-to-plugin remap
  table, the three-layout choice, and the four distribution paths.
author: Claude Code
version: 2.0.0
date: 2026-05-09
---

# APM Plugin Distribution Paths

A common confusion when packaging a Claude Code plugin with APM is "where do
my files go?" and "do I need a `marketplace:` block?" The answers are both
non-obvious and easy to get wrong:

- **Where files go**: under `.apm/` (source) — *not* at repo root. The root
  `commands/agents/skills/` paths are *build output* (deployed copies),
  not the canonical authoring location.
- **Marketplace**: not needed for a single-plugin repo. `apm install
  owner/repo` works against bare `apm.yml` + `.apm/` content.

This skill captures the canonical layout, the alternatives APM tolerates,
and the four distribution paths.

## Problem

You've run `apm init` on a repo, authored a SKILL.md and a slash command,
and you don't know whether they go at:

- `skills/<name>/SKILL.md` and `commands/<name>.md` (root)
- `.apm/skills/<name>/SKILL.md` and `.apm/commands/<name>.md`
- `.claude/skills/<name>/SKILL.md` and `.claude/commands/<name>.md`
- `plugins/<name>/skills/<name>/SKILL.md` (under a marketplace pluginRoot)

All four "work" in the sense that something installs, but only one is
canonical and gets the full benefit of APM's multi-target compile.

## Context / Trigger Conditions

Any of these point here:

- The APM "Your First Package" guide shows files at `.apm/skills/<name>/SKILL.md`
  but you've put them at root `skills/<name>/SKILL.md` because that's the
  Claude Code plugin layout. Both work; only one is canonical.
- You're reading the existing `apm-marketplace-authoring-gotchas` skill and
  it implies every APM-published plugin needs a marketplace block. (It
  doesn't — that skill is about authoring a *marketplace*, not about a
  single plugin.)
- `apm targets` exits 2 with `Error: No such command 'targets'` (despite
  the dependencies guide referencing the command — it's not shipped in 0.12.1).
- `apm validate` exits 2 with `Error: No such command 'validate'`.
  Validation is folded into APM's packaging command run with `--dry-run`.
- `apm compile -t claude --dry-run` exits 0 with `[x] No APM content found
  to compile` — confirms you have no `.apm/` source content (only deployed
  copies at root). For canonical authoring, the message should disappear.

## Solution

### The mental model (one-liner)

From the official anatomy doc:

> `apm.yml` is your `package.json`. `.apm/` is your `src/`. `apm_modules/`
> is your `node_modules/`. Output under `.github/`, `.claude/`, `.cursor/`,
> etc. is your `dist/` — generated, tool-specific, not the source of truth.

**Source under `.apm/`. Tool-specific dirs (`.claude/`, `.github/`, etc.)
are build output.** That single rule resolves most layout confusion.

### The three layouts APM recognizes

Per the official getting-started guide:

| # | Layout | When to use |
|---|---|---|
| 1 | **One skill** — `SKILL.md` at root + optional `agents/`/`assets/`/`scripts/` | Single-skill repo, no other primitives |
| 2 | **Multiple primitives** — `.apm/skills/`, `.apm/agents/`, `.apm/instructions/`, `.apm/commands/` | **Canonical** for any package shipping > 1 primitive |
| 3 | **Claude plugin** — existing `plugin.json` at repo root with `commands/agents/skills/` siblings | Pre-existing CC plugin you want APM to consume *as-is* without restructuring |

Layout 3 is a *consumption fallback*, not a recommended authoring path. APM
"can consume it directly without restructuring" — that wording is the
giveaway. Use it only if migrating an existing CC plugin and you don't want
the multi-target benefit.

### Canonical `.apm/` source → plugin-bundle remap

APM's packaging step reads from `.apm/` and emits a plugin bundle under
`build/<name>-<version>/`. The remap table:

| `.apm/` source path | Plugin output path |
|---|---|
| `.apm/agents/<name>.agent.md` | `agents/<name>.agent.md` |
| `.apm/skills/<name>/SKILL.md` | `skills/<name>/SKILL.md` |
| `.apm/prompts/<name>.prompt.md` | `commands/<name>.md` (suffix stripped) |
| `.apm/prompts/<name>.md` | `commands/<name>.md` |
| `.apm/instructions/<name>.instructions.md` | `instructions/<name>.instructions.md` |
| `.apm/hooks/*.json` | `hooks.json` (merged) |
| `.apm/commands/<name>.md` | `commands/<name>.md` |

Two notable conventions:

- **Agents get the `.agent.md` suffix** under `.apm/agents/`. A bare
  `<name>.md` doesn't get picked up the same way.
- **Slash commands have two valid source locations**: `.apm/commands/*.md`
  (preserved as-is) or `.apm/prompts/*.md` (any `.prompt.md` suffix is
  stripped on output). Prefer `.apm/commands/` for Claude-Code-flavored
  slash commands; prefer `.apm/prompts/` for portable prompt-style content
  that consumers might invoke as Copilot prompts.

### Migration: from layout 3 (root) to layout 2 (canonical `.apm/`)

If you currently have a CC-native repo at root and want to move to
canonical APM authoring:

```bash
# 1. Create the .apm tree
mkdir -p .apm/skills .apm/agents .apm/commands

# 2. Move skills as-is (directory layout preserved)
git mv skills/* .apm/skills/

# 3. Move and rename agents (.md → .agent.md)
for f in agents/*.md; do
  base=$(basename "$f" .md)
  git mv "$f" ".apm/agents/${base}.agent.md"
done
rmdir agents

# 4. Move commands as-is
git mv commands/* .apm/commands/
rmdir commands

# 5. Optionally remove plugin.json (APM's packaging step synthesizes it from apm.yml)
git rm .claude-plugin/plugin.json
rmdir .claude-plugin

# 6. Verify
# (run APM's packaging step in --dry-run mode here) → exit 0; should now list all primitives from .apm/
apm install --dry-run # would deploy to .claude/, .github/, etc.
```

After migration, the deployed copies under `.claude/` (or `.github/`, etc.)
are *build output*. They can be:

- **Gitignored**: typical for greenfield APM packages.
- **Committed as deployed copies**: what `microsoft/apm` itself does
  (dogfooding) — useful for repos where the in-repo agent also consumes
  the deployed copy. Source is still authoritative; deployed is byte-identical.

### The four distribution paths

Once your source is canonical, here's how others consume it:

| Path | Consumer command | Requires |
|---|---|---|
| **APM Package** (canonical) | `apm install owner/repo` | `apm.yml` + `.apm/` source ✓ default |
| **Marketplace Plugin** | `apm install owner/repo/plugins/<name>` | Content under `./plugins/<name>/` (multi-plugin repos) |
| **CC `/plugin marketplace add`** | `/plugin marketplace add owner/repo` | `marketplace:` block in `apm.yml` so APM's packaging step emits `marketplace.json` |
| **Manual install** | `git clone` + copy | Just the file layout |

The first row is what `apm init` aims at. Add a `marketplace:` block only if
your audience is non-APM CC users who'd use `/plugin marketplace add`, or if
you host multiple plugins in one repo.

### Subcommand reality (APM 0.12.1)

Real subcommands (verified by `apm --help`):

```text
apm init                       # Scaffold apm.yml
apm install                    # Resolve deps + deploy local .apm/ content
apm compile [-t <target>]      # Translate .apm/* sources to native formats
# APM's packaging step, optional --dry-run  # Validate schema + build plugin bundle
# APM's marketplace-check command           # Runs git ls-remote (often fails for local-only)
apm policy
apm preview
```

Non-existent in 0.12.1 (referenced in older docs/skills):

- `apm targets` — auto-detection runs *during* install/compile/pack.
  To preview compile output, use `apm compile -t <target> --dry-run`.
- `apm validate` — schema validation is APM's packaging step run with `--dry-run`.

### Minimum viable `apm.yml` (matches `apm init -y`)

```yaml
name: <package-name>
version: 1.0.0
description: <one line>
author: <handle>          # or {name, url} object form
dependencies:
  apm: []                 # plugins THIS package consumes
  mcp: []
includes: auto            # walks .apm/ tree and deploys what it finds
scripts: {}
```

The `includes: auto` field is what makes `apm install` walk `.apm/` and
deploy locally-authored primitives. Setting `includes: []` (or omitting)
disables local-content deployment.

## Verification

After authoring at `.apm/skills/<name>/SKILL.md` and friends:

```bash
# (run APM's packaging step with --dry-run) # Schema validation; exit 0
apm install --dry-run                  # Preview deployment; exit 0
apm compile -t claude --dry-run        # Should now show content (not the
                                       # "No APM content found" message
                                       # you'd see for layout 3)
```

Then test the consumer flow from a different directory:

```bash
cd /tmp/test-consumer
echo 'name: test
version: 0.0.1
dependencies:
  apm:
    - owner/repo' > apm.yml
apm install --dry-run                  # Should resolve your package
```

If APM's packaging step (with `--dry-run`) lists fewer primitives than expected after
migration, check that agent files use `.agent.md` (not bare `.md`) and that
commands moved to `.apm/commands/` (not the deployed `commands/` at root).

## Example

The reference example is `microsoft/apm-sample-package`, which uses
layout 2:

```text
apm-sample-package/
├── apm.yml
└── .apm/
    ├── prompts/
    │   ├── design-review.prompt.md
    │   └── accessibility-audit.prompt.md
    ├── instructions/
    │   └── design-standards.instructions.md
    ├── agents/
    │   └── design-reviewer.agent.md
    └── skills/
        └── style-checker/SKILL.md
```

Consumers `apm install microsoft/apm-sample-package#v1.0.0` and the deploy
step writes:

- `.apm/skills/style-checker/SKILL.md` → `.claude/skills/style-checker/SKILL.md`
- `.apm/agents/design-reviewer.agent.md` → `.claude/agents/design-reviewer.agent.md`
- `.apm/prompts/design-review.prompt.md` → `.claude/commands/design-review.md`

## Notes

- `apm.lock.yaml` should be **tracked** (committed) for reproducibility,
  not gitignored. `apm_modules/` should be gitignored. `build/` (where
  APM's packaging step writes) should also be gitignored.
- The `microsoft/apm` repo itself dogfoods layout 2 — `.apm/skills/python-architecture/SKILL.md`
  is the source; `.github/skills/python-architecture/SKILL.md` is the
  deployed copy that the in-repo Copilot agent loads. Use this as a real
  reference.
- `marketplace:` block and `dependencies:` block can coexist — your repo
  can both consume other plugins AND be a marketplace. They're orthogonal.
- This is APM 0.12.1 reality. Future versions may add `apm targets` /
  `apm validate` as first-class subcommands; re-verify with `apm --help`.
- For marketplace-specific authoring traps (CI staleness, `pluginRoot`
  rewriting, prettier conflicts, husky/markdownlint MD040, etc.), see the
  complementary skill `apm-marketplace-authoring-gotchas`.
- **Common mistake** (the one that prompted this skill's v2.0): assuming
  CC's plugin layout (`commands/agents/skills/` at root) is the canonical
  APM authoring layout. It isn't — it's layout 3, the "I already have a
  Claude plugin" fallback. Layout 2 (`.apm/`) is the source-of-truth path
  and the only one that works for multi-target compile.

## References

- APM "Your First Package": <https://microsoft.github.io/apm/getting-started/first-package/>
- APM Anatomy of a Package: <https://microsoft.github.io/apm/introduction/anatomy-of-an-apm-package/>
- APM dependencies guide: <https://microsoft.github.io/apm/guides/dependencies/>
- APM compilation guide: <https://microsoft.github.io/apm/guides/compilation/>
- APM pack & distribute: <https://microsoft.github.io/apm/guides/pack-distribute/>
- Reference package: <https://github.com/microsoft/apm-sample-package>
- Self-dogfooding repo: <https://github.com/microsoft/apm> (`.apm/` + `.github/` side-by-side)
- Companion skill: `apm-marketplace-authoring-gotchas`
