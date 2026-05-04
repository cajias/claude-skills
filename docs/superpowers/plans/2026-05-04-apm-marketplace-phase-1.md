# APM Marketplace Phase 1 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the `cajias/claude-skills` marketplace from a
hand-authored `.claude-plugin/marketplace.json` (distributed via
Homebrew) to an APM-managed marketplace driven by a root `apm.yml`,
with the regenerated `marketplace.json` as the compiled artefact.
Retire release-please. No new plugins are added in this phase.

**Architecture:** Hand-edit `apm.yml` containing a `marketplace:`
block; `apm pack` regenerates `.claude-plugin/marketplace.json`. Both
files are committed. `apm marketplace check` runs in CI to validate
the manifest. Versioning continues with semver via hand-edited
`version:` fields; tags follow `{name}-v{version}`.

**Tech Stack:** APM CLI 0.11.0+ (already installed at
`~/.local/bin/apm`), GitHub Actions, Make, Node 20 (existing
markdownlint/prettier/ls-lint toolchain retained).

---

## Pre-flight context

**Spec:**
`docs/superpowers/specs/2026-05-04-apm-marketplace-design.md`.
Re-read it before starting if you have not.

**Repo state at planning time:**

- `.claude-plugin/marketplace.json` exists, hand-authored, declares
  marketplace `name: "personal-skills"` and 4 plugins:
  `ai-zettelkasten`, `claudeception`, `isengardcli-aws-auth`,
  `semantic-search`.
- `plugins/` contains 13 plugin directories (4 exposed, 9 hidden).
- `.github/workflows/ci.yml` has a `lint` job (markdownlint).
- `.github/workflows/release-please.yml` exists and is being retired.
- `.release-please-manifest.json` and `release-please-config.json`
  exist at the repo root.
- `homebrew-tools-reference/` exists at the repo root.
- `package.json` has no release-please devDependency; it is referenced
  only by the workflow + the two root config files.
- A pre-commit hook (husky + lint-staged) runs `markdownlint --fix`
  and `prettier --write` on staged `*.md` and `*.{json,yml,yaml}`.
  Commits to docs files trigger formatting; this is expected.

**Important constraint — `apm pack` output shape:**

When the marketplace `name` is inherited from `apm.yml` top-level
(not overridden inside `marketplace:`), `apm pack` **omits** it from
the generated `marketplace.json`. The pre-migration file has
`"name": "personal-skills"` at the top level. After migration the
generated file will have **no** `name` key at the top level — this
is expected and correct per APM's Anthropic-compliance rule. Plugin
entries (`name`, `source`, `description`) must round-trip with the
same identifiers.

**Branching:** Work on a feature branch named
`apm-marketplace-phase-1`. Do not work directly on `main`.

---

## File Structure

Files this plan creates or modifies:

| Path                                   | Action              | Responsibility                                                           |
| -------------------------------------- | ------------------- | ------------------------------------------------------------------------ |
| `apm.yml`                              | Create              | Marketplace manifest (hand-edited source of truth).                      |
| `.claude-plugin/marketplace.json`      | Modify (regenerate) | Compiled artefact emitted by `apm pack`.                                 |
| `Makefile`                             | Create              | Wraps `apm pack` / `apm marketplace check` / `apm marketplace outdated`. |
| `.github/workflows/ci.yml`             | Modify              | Add `apm-marketplace` job that runs `apm marketplace check`.             |
| `.github/workflows/release-please.yml` | Delete              | Release-please retired.                                                  |
| `.release-please-manifest.json`        | Delete              | Release-please retired.                                                  |
| `release-please-config.json`           | Delete              | Release-please retired.                                                  |
| `homebrew-tools-reference/`            | Delete              | Homebrew distribution retired.                                           |
| `README.md`                            | Modify              | Replace Homebrew install with APM install; remove related links.         |

Files explicitly NOT touched: anything under `plugins/`, `skills/`,
`agents/`, `mcp-server/`, `.claude-plugin/plugin.json`,
`package.json`. The plugin internals are already valid APM-consumable
plugin format; no changes are needed in Phase 1.

---

## Task 1: Branch and snapshot baseline

**Files:**

- Create: `/tmp/marketplace-baseline.json` (snapshot, not committed)

- [ ] **Step 1: Create the feature branch**

Run from the repo root:

```bash
cd /Users/rc/Projects/workspace/claude-skills
git checkout main
git pull
git checkout -b apm-marketplace-phase-1
```

Expected: branch `apm-marketplace-phase-1` is created and checked
out. `git status` reports a clean tree.

- [ ] **Step 2: Snapshot the existing marketplace.json**

Run:

```bash
cp .claude-plugin/marketplace.json /tmp/marketplace-baseline.json
```

This snapshot is used in Task 3 to validate the round-trip. Do NOT
commit it.

- [ ] **Step 3: Verify APM CLI version**

Run:

```bash
apm --version
```

Expected output contains `Agent Package Manager (APM) CLI version
0.11.0` or higher. If APM is not on PATH, install with
`curl -sSL https://aka.ms/apm-unix | sh` and re-check.

No commit at the end of Task 1.

---

## Task 2: Create root `apm.yml`

**Files:**

- Create: `apm.yml`

- [ ] **Step 1: Write the marketplace manifest**

Create `apm.yml` at the repo root with exactly this content:

```yaml
name: claude-skills
version: 0.1.0
description: APM marketplace for Claude Code plugins and OpenProse programs
author: Raul Cajias

marketplace:
  owner:
    name: cajias
    url: https://cajias.io
  metadata:
    homepage: https://github.com/cajias/claude-skills
    pluginRoot: ./plugins
  build:
    tagPattern: "{name}-v{version}"
  plugins:
    - name: ai-zettelkasten
      source: ./plugins/ai-zettelkasten
      version: 0.1.0
      description: >-
        Automatic knowledge extraction from Claude sessions using
        Stop hooks. Captures facts, decisions, patterns to Obsidian
        and S3 Vectors.
      tags: [knowledge-management, hooks]
    - name: claudeception
      source: ./plugins/claudeception
      version: 0.1.0
      description: >-
        Extracts reusable skills from Claude Code sessions at session
        end. Analyzes for non-obvious discoveries and creates SKILL.md
        files.
      tags: [skills, learning]
    - name: isengardcli-aws-auth
      source: ./plugins/isengardcli-aws-auth
      version: 0.1.0
      description: >-
        Enforces AWS authentication via isengardcli. Blocks direct
        aws/cdk/deploy commands. Uses environment variables (DEV,
        GAMMA, PROD) with color-coded warnings.
      tags: [aws, authentication, hooks]
    - name: semantic-search
      source: ./plugins/semantic-search
      version: 0.1.0
      description: >-
        Semantic search over Obsidian Zettelkasten notes using
        LanceDB and sentence-transformers for local embeddings.
      tags: [search, embeddings, obsidian]
```

Plugin descriptions are taken verbatim from the existing
`marketplace.json` (line-wrapped via `>-` block scalars to keep them
valid YAML; YAML collapses the wrapped lines back to single
descriptions).

- [ ] **Step 2: Validate the manifest schema**

Run:

```bash
apm marketplace check --offline
```

Expected exit code: 0. Output should list 4 plugins as `ok` with
`local-path` markers. If any entry fails schema validation, fix the
YAML and re-run. `--offline` skips network reachability for
local-path entries (which is all of them in this phase).

- [ ] **Step 3: Commit `apm.yml`**

```bash
git add apm.yml
git commit -m "chore: add apm.yml marketplace manifest"
```

No `marketplace.json` change yet — that comes in Task 3.

---

## Task 3: Regenerate `marketplace.json` via `apm pack`

**Files:**

- Modify: `.claude-plugin/marketplace.json` (regenerated)

- [ ] **Step 1: Dry-run the build to preview**

Run:

```bash
apm pack --dry-run
```

Expected output: a resolution table listing the 4 plugins as
`local-path` with their resolved `source` paths. No file is written
on dry-run. If the table is empty or shows errors, stop and read the
output.

- [ ] **Step 2: Generate the file**

Run:

```bash
apm pack
```

Expected output ends with: `[+] Built marketplace.json (4 plugins)
-> .claude-plugin/marketplace.json`. The file at
`.claude-plugin/marketplace.json` is rewritten.

- [ ] **Step 3: Diff against the baseline snapshot**

Run:

```bash
diff /tmp/marketplace-baseline.json .claude-plugin/marketplace.json
```

**Expected diff** (cosmetic — these are acceptable):

- `name` removed from the top level (was `"personal-skills"`,
  now omitted because `apm.yml` top-level `name: claude-skills`
  inherits and APM omits inherited names).
- `metadata` block added (containing `homepage` and `pluginRoot`).
- Each plugin entry may include a `tags` array (was absent from the
  hand-authored file).
- Whitespace and trailing-newline differences from
  prettier-vs-APM's writer.

**Unexpected diff** (stop and investigate):

- Any plugin missing from the new file.
- A plugin's `name`, `source`, or `description` differing in a way
  not attributable to YAML block-scalar collapsing of long
  descriptions.
- Extra unexpected top-level fields.

If the diff is unexpected, stop, capture the diff in a comment, and
flag in the PR. Do not commit until resolved.

- [ ] **Step 4: Run the full check (online)**

Run:

```bash
apm marketplace check
```

Expected exit code: 0. This validates schema + ensures local paths
resolve.

- [ ] **Step 5: Commit the regenerated file**

```bash
git add .claude-plugin/marketplace.json
git commit -m "chore: regenerate marketplace.json from apm.yml"
```

---

## Task 4: Add Makefile

**Files:**

- Create: `Makefile`

- [ ] **Step 1: Write the Makefile**

Create `Makefile` at the repo root with exactly this content (note:
recipe lines must use a TAB character, not spaces):

```make
.PHONY: pack check outdated help

pack: ## regenerate .claude-plugin/marketplace.json from apm.yml
 apm pack

check: ## validate apm.yml schema and plugin reachability
 apm marketplace check

outdated: ## report drift between resolved versions and upstream tags
 apm marketplace outdated

help: ## show available targets
 @grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) \
   | awk -F':.*?## ' '{printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
```

If your editor expands tabs to spaces, fix it. `make` requires
literal tabs at the start of recipe lines.

- [ ] **Step 2: Verify each target works**

Run:

```bash
make help
```

Expected output: a colored list of the four targets with
descriptions. If you see `Makefile:N: *** missing separator. Stop.`,
your tabs got eaten — re-create the file ensuring tab indentation.

```bash
make check
```

Expected exit code: 0 (same as `apm marketplace check`).

- [ ] **Step 3: Commit**

```bash
git add Makefile
git commit -m "chore: add Makefile wrapping apm pack/check/outdated"
```

---

## Task 5: Add CI job for `apm marketplace check`

**Files:**

- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: Read the existing workflow**

Open `.github/workflows/ci.yml`. It currently defines a single
`lint` job that runs markdownlint via `npm`. We add a sibling
`apm-marketplace` job that runs `apm marketplace check`.

- [ ] **Step 2: Append the new job**

Add the following `apm-marketplace` job to `.github/workflows/ci.yml`
under `jobs:` (sibling to the existing `lint` job). Do NOT remove or
modify the `lint` job.

```yaml
apm-marketplace:
  name: APM marketplace check
  runs-on: ubuntu-latest
  steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Install APM CLI
      run: |
        curl -sSL https://aka.ms/apm-unix | sh
        echo "$HOME/.local/bin" >> "$GITHUB_PATH"

    - name: Verify APM version
      run: apm --version

    - name: Run apm marketplace check
      run: apm marketplace check

    - name: Verify marketplace.json is up-to-date
      run: |
        apm pack
        if ! git diff --quiet .claude-plugin/marketplace.json; then
          echo "::error::marketplace.json is stale. Run 'apm pack' locally and commit the result."
          git --no-pager diff .claude-plugin/marketplace.json
          exit 1
        fi
```

The final step prevents drift: if a contributor edits `apm.yml` but
forgets to run `apm pack`, CI fails. This is the same pattern lockfile
checks use in npm/cargo CI.

- [ ] **Step 3: Validate the YAML locally**

Run:

```bash
npx --yes prettier --check .github/workflows/ci.yml
```

Expected exit code: 0. If prettier reports formatting issues, run
`npx prettier --write .github/workflows/ci.yml`.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add apm marketplace check job"
```

---

## Task 6: Retire release-please

**Files:**

- Delete: `.github/workflows/release-please.yml`
- Delete: `.release-please-manifest.json`
- Delete: `release-please-config.json`

- [ ] **Step 1: Remove the workflow and config files**

Run:

```bash
git rm .github/workflows/release-please.yml \
       .release-please-manifest.json \
       release-please-config.json
```

If any file is missing (already removed), `git rm` will fail loudly
— check with `ls -la` first if needed.

- [ ] **Step 2: Search for any remaining release-please references**

Run:

```bash
grep -rni "release-please" \
  --exclude-dir=node_modules \
  --exclude-dir=.git \
  --exclude-dir=docs/superpowers \
  . || echo "no remaining references"
```

Expected: `no remaining references`. If matches show up in
`package.json`, `README.md`, or anywhere else, capture them and fix
them in this same task before committing.

The `docs/superpowers/` directory is excluded because the spec we
just wrote correctly references release-please in describing what is
being removed; that is documentation, not a live config.

- [ ] **Step 3: Commit**

```bash
git commit -m "chore: retire release-please

Versioning continues via hand-edited 'version:' fields in
apm.yml and per-plugin manifests; tags follow '{name}-v{version}'."
```

---

## Task 7: Retire Homebrew distribution

**Files:**

- Delete: `homebrew-tools-reference/` (entire directory)

- [ ] **Step 1: Remove the directory**

Run:

```bash
git rm -r homebrew-tools-reference/
```

- [ ] **Step 2: Verify no other Homebrew references remain in code**

Run:

```bash
grep -rni "homebrew\|brew tap\|brew install" \
  --include="*.md" --include="*.yml" --include="*.yaml" \
  --include="*.json" --include="*.sh" \
  --exclude-dir=node_modules \
  --exclude-dir=.git \
  --exclude-dir=docs/superpowers \
  . || echo "no remaining references"
```

If matches appear in `README.md`, leave them — Task 8 rewrites the
README. If they appear elsewhere (e.g. a CI script, a plugin
README), that is a real reference to fix; capture the file:line and
remove the reference inline before committing.

- [ ] **Step 3: Commit**

```bash
git commit -m "chore: remove homebrew-tools-reference

APM replaces Homebrew as the distribution channel."
```

---

## Task 8: Update root README install section

**Files:**

- Modify: `README.md`

- [ ] **Step 1: Read the current README install section**

Open `README.md`. The relevant section currently reads (approx.
lines 16-37):

````markdown
## Installation

### Via Homebrew (macOS/Linux)

```bash
brew tap cajias/tools
brew install claude-skills
```

After installation, skills and plugins will be available at:

```bash
$(brew --prefix)/share/claude-skills/skills/   # Skills
$(brew --prefix)/share/claude-skills/plugins/  # Plugins
```

### Manual Installation

Clone this repository to access skills and plugins directly:

```bash
git clone https://github.com/cajias/claude-skills.git
```
````

- [ ] **Step 2: Replace the install section**

Replace the entire `## Installation` section (from the heading
through the end of "Manual Installation" subsection) with this:

````markdown
## Installation

### Via APM (recommended)

[APM](https://github.com/microsoft/apm) is the dependency manager for
AI agents. Add this marketplace once, then install plugins by name:

```bash
# one-time, per consumer repo
apm marketplace add cajias/claude-skills

# install a plugin
apm install cajias/claude-skills/<plugin-name>
```

Available plugins are listed under [Available Plugins](#available-plugins)
below.

### Manual Installation

Clone this repository to access plugins directly:

```bash
git clone https://github.com/cajias/claude-skills.git
claude plugin install \
  https://github.com/cajias/claude-skills/tree/main/plugins/<plugin-name>
```
````

- [ ] **Step 3: Verify the README still passes lint**

Run:

```bash
npx markdownlint README.md
```

Expected exit code: 0. If any lint error appears (line length,
fenced-code-language, etc.), fix inline before committing.

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs(readme): replace Homebrew install with APM"
```

---

## Task 9: Final verification

**Files:** none modified.

- [ ] **Step 1: Run the full local check matrix**

Run from the repo root:

```bash
make check
make pack
git diff --quiet .claude-plugin/marketplace.json && echo "clean" || echo "STALE — must commit"
npm run lint:md
```

Expected:

- `make check`: exit 0.
- `make pack`: prints `[+] Built marketplace.json (4 plugins) ...`.
- The `git diff --quiet` echoes `clean` (the file is unchanged
  because step 2 of Task 3 already committed the regenerated form).
- `npm run lint:md`: exit 0.

If any of these fail, fix the underlying issue before opening the PR.

- [ ] **Step 2: Walk the Phase 1 acceptance checklist**

Confirm each spec acceptance criterion. Print the result of each:

```bash
# 1. apm pack generates marketplace.json with the 4 plugins
apm pack && jq '.plugins | length' .claude-plugin/marketplace.json
# expect: 4

# 2. plugin entries match pre-migration descriptions
jq -r '.plugins[] | "\(.name): \(.description)"' .claude-plugin/marketplace.json
# expect: 4 lines, descriptions matching the pre-migration file

# 3. apm marketplace check exits 0
apm marketplace check && echo "OK"
# expect: OK

# 4. CI workflow exists
test -f .github/workflows/ci.yml && grep -q "apm marketplace check" .github/workflows/ci.yml && echo "OK"
# expect: OK

# 5. Homebrew/release-please artefacts are gone
test ! -e homebrew-tools-reference && \
  test ! -e .release-please-manifest.json && \
  test ! -e release-please-config.json && \
  test ! -e .github/workflows/release-please.yml && \
  echo "OK"
# expect: OK

# 6. README documents APM install
grep -q "apm marketplace add cajias/claude-skills" README.md && \
  ! grep -q "brew tap cajias/tools" README.md && \
  echo "OK"
# expect: OK
```

Six `OK` (or expected outputs) means Phase 1 acceptance is met.

- [ ] **Step 3: Push the branch and open a PR**

```bash
git push -u origin apm-marketplace-phase-1
gh pr create --title "APM marketplace migration (Phase 1)" --body "$(cat <<'EOF'
## Summary

Migrates the marketplace from a hand-authored
`.claude-plugin/marketplace.json` (distributed via Homebrew) to an
APM-managed marketplace driven by `apm.yml`. Retires release-please.

No new plugins are added in this phase. The 4 currently-published
plugins (`ai-zettelkasten`, `claudeception`, `isengardcli-aws-auth`,
`semantic-search`) round-trip through `apm pack` with byte-equivalent
plugin entries. Cosmetic differences in the generated
`marketplace.json` (top-level `name` omission, added `metadata`
block, added empty `tags`) are documented in the spec.

Spec: `docs/superpowers/specs/2026-05-04-apm-marketplace-design.md`

## Test plan

- [ ] CI: `lint` job passes.
- [ ] CI: `apm-marketplace` job passes.
- [ ] CI: marketplace.json staleness check passes.
- [ ] Local: `make check`, `make pack` exit 0.
- [ ] Local: `apm pack` produces no diff against committed
  `marketplace.json`.
- [ ] Manual: open `marketplace.json` in browser-like viewer
  (or jq) and confirm all 4 plugins are present with original
  descriptions.
EOF
)"
```

- [ ] **Step 4: Wait for CI**

Watch the CI run. If `apm-marketplace` fails on the staleness check
in CI, that means `apm pack` produces non-deterministic output (or
your local `apm` is a different version from the runner). Diagnose
by running `apm --version` locally vs `Install APM CLI` step output;
pin the CI install if needed.

If both jobs are green, the PR is ready for review and merge.

---

## Self-review

I checked the plan against the spec:

- **Phase 1 acceptance criteria 1-6** — all 6 are explicitly verified
  in Task 9 Step 2 with one shell snippet per criterion.
- **No placeholders** — every step has a concrete command or code
  block.
- **Type/identifier consistency** — plugin names (`ai-zettelkasten`,
  `claudeception`, `isengardcli-aws-auth`, `semantic-search`) match
  the spec; the marketplace `name: claude-skills` matches the spec;
  the `tagPattern: "{name}-v{version}"` matches the spec.
- **One known cosmetic divergence** — the existing
  `marketplace.json` top-level `name: "personal-skills"` will be
  omitted (because the `apm.yml` `name: claude-skills` inherits and
  APM omits inherited names). This is called out in the pre-flight
  context, in Task 3 Step 3 as an expected diff, and in the PR
  description.
- **The `package.json` audit** — Task 6 Step 2's grep covers
  `package.json` automatically; if it ever does contain a
  release-please reference, the grep catches it and the task fixes
  it inline.

The plan stays inside Phase 1. Phase 2 (the prose programs) is a
separate plan that gets written after Phase 1 lands.
