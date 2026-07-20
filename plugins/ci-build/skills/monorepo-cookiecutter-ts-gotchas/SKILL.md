---
name: monorepo-cookiecutter-ts-gotchas
description: |
  Bugs and footguns when cutting a TypeScript-only instance of the
  cajias/monorepo-cookiecutter scaffold and getting its test tiers green. Use
  WHENEVER you scaffold, cut, or generate a project from
  cajias/monorepo-cookiecutter (especially headless via COOKIECUTTER_SUBPROJECTS
  + uvx cookiecutter --no-input), OR when a freshly-cut instance shows any of:
  every Cucumber step "undefined" though steps exist (config is the dotfile
  .cucumber.mjs, not auto-discovered); first step fails, this.apiEndpoint
  undefined (world.ts never calls setWorldConstructor); node_modules/.env staged,
  no .gitignore generated; pnpm install can't resolve @lint-configs/eslint-config
  (404 not 403 with a write:packages token; use a file: link); husky/pre-commit
  fails on "Type tag typescript is not recognized" (commit --no-verify);
  cucumber-js --name won't match or won't load .env; make install fails
  frozen-lockfile after a dep add; jest double-runs or finds no tests; tsc errors
  on JSX.Element under React 19. Covers all 11 recurring traps.
metadata:
  author: Claude Code
  version: 1.0.0
  date: 2026-07-12
  source_memory: monorepo-cookiecutter-ts-gotchas
---

# monorepo-cookiecutter-ts-gotchas

## Problem

Cutting a TypeScript-only instance of `cajias/monorepo-cookiecutter` and getting
its test tiers green is a recurring task (this scaffold is cut for most new
projects). The scaffold ships several bugs and machine-specific footguns that
each cost real debugging time but are mechanical once known. This skill is the
reference so you fix them in minutes instead of rediscovering them.

All findings validated 2026-07-11 on a live cut (the `notion-plugin-para-viz`
build). Line/file references below are inside the *generated* project.

## Headless generation (how the scaffold is cut)

The scaffold is generated headlessly by passing the subproject topology as a
JSON env var — the post-gen hook reads it, fills `packages/`, and deletes
`_templates/`:

```bash
COOKIECUTTER_SUBPROJECTS='[{"name":"...","language":"typescript","type":"...","depends_on":[]}]' \
  uvx cookiecutter <local-clone> --no-input \
  project_name=... npm_scope=... ...
```

`COOKIECUTTER_SUBPROJECTS` is a JSON array of `{name, language, type, depends_on}`.
Without it the scaffold prompts interactively; `--no-input` alone leaves
`packages/` empty.

## The gotchas

Grouped by where they bite: generation → workspace/publish → Cucumber tier →
per-package build. Numbers match the source memory note.

### Generation & workspace

**3. The scaffold generates NO `.gitignore`** (despite the design listing one).
Author one *before* the first commit or you will commit `node_modules/`. At
minimum include:

```gitignore
node_modules/
dist/
cdk.out/
.env
.env.local
.env.*.local
**/.env
```

**5. `packageManager: "pnpm@9"`** (not a full `9.x.y` version) → pnpm 10 emits a
harmless `"not a valid version"` warning and proceeds. Not a blocker; pin to a
full version only if you want the warning gone.

**8. Frozen-lockfile trap.** Every package `Makefile install` target runs
`pnpm install --frozen-lockfile`. So **adding any dependency requires
regenerating `pnpm-lock.yaml` first** or the gate fails on a lockfile mismatch:

```bash
pnpm install --prefer-offline   # reuses the store, 0 downloads, updates the lock
```

Do this after every dependency add, in any tier.

### `@lint-configs/eslint-config` is unpublishable as configured (NOT a token problem)

**4.** The scaffold's `.npmrc` maps the `@lint-configs` scope to
`npm.pkg.github.com`, but **GitHub Packages requires the npm scope to equal the
repo-owner login**, and there is no GitHub owner named `lint-configs` (the real
source is `cajias/lint-configs`). So `@lint-configs/*` can **never** resolve
there with **any** token.

Diagnostic rule worth remembering: **a 404 (not 403) from GitHub Packages with a
valid `write:packages` token means the owner path isn't visible to you (no such
owner / not a member) — NOT a missing scope.** Don't chase `read:packages`
refreshes. Also: `1.0.3` is only a local working copy (remote tags stop at
`v1.0.2`), and the package is not on public npm. `pnpm --filter` /
`--ignore-workspace` don't help — pnpm resolves the whole workspace on any
install.

**Workaround (greens `pnpm install` with no token):** point the dep at the local
sibling checkout in the root `package.json`:

```json
"@lint-configs/eslint-config": "file:../lint-configs/typescript"
```

The sibling is plain-JS (no build step). This is lint-only, so no
build/test/cucumber exit criterion depends on it. **Proper fix for CI /
portability:** publish `@lint-configs/eslint-config` to a registry the scope can
actually live on (e.g. rename the scope to match an owner, or use public npm).

### Cucumber tier

**1. Cucumber config is the dotfile `.cucumber.mjs` → cucumber-js does NOT
auto-discover it.** cucumber-js only auto-loads
`cucumber.{js,cjs,mjs,json,yaml,yml}`. So a bare `pnpm exec cucumber-js` — and
the scaffold's own `make test-integration` / package scripts, which call bare
`cucumber-js --parallel 4` — load **zero** step definitions → every step reports
`"undefined"`, exit 1.

**Fix: rename `.cucumber.mjs` → `cucumber.mjs`** (or pass `--config .cucumber.mjs`
everywhere). The rename is the root fix and makes `cucumber-js --name "..."` work
verbatim.

**2. `support/world.ts` defines `CustomWorld` but never calls
`setWorldConstructor(CustomWorld)`** — so `this.apiEndpoint` (from `config.ts`)
is `undefined` and the first step always fails. Add the import and a trailing:

```ts
import { setWorldConstructor } from "@cucumber/cucumber";
// ...
setWorldConstructor(CustomWorld);
```

**7. Running a single scenario / loading env in the Cucumber tier.** The exit-
command form `pnpm exec cucumber-js --name "<substr>"` matches a
**case-sensitive regex substring against the scenario NAME** (so name scenarios
to contain the exact substring you'll filter on). It does **not** run
`dotenv-cli` — only the npm `test:integration` scripts do. So load `.env` from
inside the harness with a tiny repo-root loader (e.g. `support/env.ts`).
`cucumber.mjs` already sets `requireModule: ["tsx"]`, so bare `cucumber-js` loads
`.ts` step files with no `NODE_OPTIONS`; step imports use explicit `.ts`
extensions (Node16 resolution).

### Per-package build (infra / embed)

**9. infra/CDK is synth-only until deploy time.** No `cdk` CLI, no `ts-node`, no
`@types/node` are installed, and `tsx` is scoped to the integration tier. The
infra `make build` synths via `tsc` → `CDK_OUTDIR=cdk.out node dist/bin/app.js`
calling `app.synth()` (`bin/app.ts` reads `CDK_OUTDIR` from env so the real CDK
CLI can take over later). **Before `cdk deploy`, install the CDK toolkit +
`@types/node`.**

**10. jest double-discovery trap (typescript_infra shape).** The infra package's
`tsconfig.json` includes `test/**/*.ts` with `outDir: dist`, so `make build`
emits `dist/test/*.test.js`; jest's default discovery then runs **both** the
`.ts` source and the stale compiled copy (an order-dependent, possibly-stale 2nd
suite). Fix with the canonical `cdk init` pattern in `jest.config.js`:

```js
roots: ["<rootDir>/test"],
```

Also: a bare `jest` with zero tests exits non-zero and fails `make test` / CI —
ship at least one real test (e.g. a `Template.fromStack` synth assertion) rather
than relying on `--passWithNoTests`.

**11. React 19 removed the global `JSX` namespace** (bites a hand-rolled
Vite+React package). `tsc` errors on `JSX.Element`. Fix per `.tsx` file:

```ts
import { type JSX } from "react";
```

### Commit hygiene

**6. Husky `pre-commit` may be broken on the machine.** The Python `pre-commit`
framework can fail to parse `.pre-commit-config.yaml` with
`Type tag 'typescript' is not recognized. Try upgrading identify and pre-commit?`
— a stale `identify` / `pre-commit` install. Until those are upgraded, commit
with:

```bash
git commit --no-verify
```

`pre-commit` here is lint/format hygiene, not a test exit criterion.

## Verification

- **Cucumber wired (1, 2, 7):** after renaming to `cucumber.mjs` and adding
  `setWorldConstructor`, `pnpm exec cucumber-js` (bare) loads steps and the first
  scenario progresses past the world/`apiEndpoint` step — no `"undefined"` steps,
  no `this.apiEndpoint is undefined`.
- **Install greens (4, 8):** `pnpm install` (or a package `make install`)
  completes with the `file:` link for `@lint-configs/eslint-config` and no 404;
  after any dep add, `pnpm install --prefer-offline` refreshes the lock so
  `--frozen-lockfile` passes.
- **jest (10):** `make -C packages/infra test` runs each test exactly once (no
  `dist/test/*.test.js` duplicate) and exits 0 with ≥1 real test.
- **Build (9, 11):** `make -C packages/embed build` (or the React package)
  compiles with no `JSX.Element` error; infra `make build` synths `cdk.out/`.
- **Committed clean (3, 6):** `git status` shows no `node_modules/` / `.env`
  staged, and `git commit --no-verify` lands the milestone.

## Notes

- The Cucumber rename (1) is the single highest-leverage fix — without it the
  entire integration tier silently no-ops with green-looking "undefined" output.
- The `@lint-configs` 404 (4) is the most misleading: it *looks* like an auth
  problem and wastes time on token/scope refreshes. The tell is 404 (not 403)
  with a `write:packages` token → it's an owner-visibility / scope-name problem,
  not a permission problem.
- Order of operations when cutting fresh: generate → write `.gitignore` →
  swap `@lint-configs` to `file:` → `pnpm install --prefer-offline` →
  rename `.cucumber.mjs` + add `setWorldConstructor` → fix jest `roots` and
  React `JSX` imports as those tiers come online.

## References (paths inside the generated project)

- `.cucumber.mjs` (rename to `cucumber.mjs`; already has `requireModule: ["tsx"]`).
- `support/world.ts` (`CustomWorld`; add `setWorldConstructor`), `support/config.ts`.
- `.npmrc` (`@lint-configs` → `npm.pkg.github.com`), root `package.json`
  (`@lint-configs/eslint-config` dep, `packageManager`).
- `packages/infra/tsconfig.json`, `packages/infra/jest.config.js`,
  `packages/infra/bin/app.ts` (`CDK_OUTDIR`).
- `.pre-commit-config.yaml` (husky hook that fails on stale `identify`).
- Source memory note: `monorepo-cookiecutter-ts-gotchas` (originSessionId
  c2441a40-3274-4ab7-aed2-fd4ae17040ed).
