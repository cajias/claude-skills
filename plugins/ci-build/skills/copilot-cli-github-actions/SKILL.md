---
name: copilot-cli-github-actions
description: |
  Run GitHub Copilot CLI headlessly inside GitHub Actions (Claude/GPT models
  billed via Copilot instead of a metered provider API key). Use when:
  (1) building a workflow or composite action that calls `copilot -p` in CI;
  (2) deciding between GITHUB_TOKEN and a PAT for Copilot CLI auth in Actions;
  (3) Copilot CLI in CI fails auth confusingly even though GITHUB_TOKEN is
  present in the env; (4) the CLI hangs or exits without acting because tool
  permissions were not pre-approved (missing --allow-tool/--no-ask-user);
  (5) choosing the flag/env var to select a Claude model in Copilot CLI;
  (6) installing a Claude Code plugin/skill marketplace into Copilot CLI
  (copilot plugin marketplace add / plugin install).
author: Claude Code
version: 1.0.3
date: 2026-07-19
---

# GitHub Copilot CLI in GitHub Actions

## Problem

Running an agentic Claude task in CI normally needs an `ANTHROPIC_API_KEY`
secret with metered billing. Copilot CLI can run the same kind of task under
an existing Copilot subscription, but its CI auth model, non-interactive
flags, and tool-permission syntax are spread across several doc pages and
changed materially in July 2026.

## Context / Trigger Conditions

- Writing a workflow/composite action that runs `copilot -p "..."` on a runner
- Auth errors in CI despite `GITHUB_TOKEN` being set (see gotcha below)
- The CLI prompting for tool confirmation in a non-interactive job
- Needing a specific Claude model rather than the default

## Solution

**Install** (Node 22+ required):

```yaml
- uses: actions/setup-node@v4
  with:
    node-version: 22
- run: npm install -g @github/copilot
```

**Auth — two options.** Token env-var precedence is
`COPILOT_GITHUB_TOKEN` > `GH_TOKEN` > `GITHUB_TOKEN`.

1. Built-in `GITHUB_TOKEN` (no secrets; available since 2026-07-02): declare
   the permission in the workflow and it just works — *if* the org/repo
   "Copilot in GitHub Actions" policy is enabled.

   ```yaml
   permissions:
     copilot-requests: write
   ```

2. Fine-grained PAT with the "Copilot Requests" permission, stored as a
   secret and exported as `COPILOT_GITHUB_TOKEN`. Use when the policy is off
   or usage should bill a specific user's seat.

**Gotcha:** Actions always injects `GITHUB_TOKEN` into the env, and the CLI
will pick it up (lowest precedence) even when it has no Copilot entitlement,
producing a confusing auth error (github/copilot-cli#3396). When using a PAT,
set `COPILOT_GITHUB_TOKEN` explicitly — it outranks the ambient token.

**Programmatic mode:** `copilot -p "PROMPT"` plus pre-approved tools, either
`--allow-all-tools` (docs: required for programmatic use) or granular allows
with `--no-ask-user`:

```bash
copilot -p "$(cat prompt.md)" \
  --allow-tool=read \
  --allow-tool=write \
  --allow-tool='shell(grep:*),shell(find:*),shell(cat:*),shell(git:*)' \
  --deny-tool='shell(git push)' \
  --deny-tool='shell(gh:*)' \
  --no-ask-user
```

Patterns are `Kind(argument)`; prefix matching on word boundaries
(`shell(git:*)` matches `git push`, not `gitea`); deny always beats allow,
even under `--allow-all`.

**Model selection:** `--model=MODEL` or `COPILOT_MODEL` env var.
`claude-sonnet-4.6` is the default as of 2026-07; `claude-haiku-4.5` for
cheap/fast; `auto` lets Copilot choose.

**Plugins & skills:** Copilot CLI plugin marketplaces are format-compatible
with Claude Code plugin marketplaces (the official docs register
`anthropics/claude-code` as their example). In CI:

```bash
copilot plugin marketplace add OWNER/REPO
copilot plugin install PLUGIN@MARKETPLACE-NAME
```

MARKETPLACE-NAME is the `name` field in the repo's
`.claude-plugin/marketplace.json`, not OWNER/REPO. Reference the plugin's
skill by name in the `-p` prompt afterward. Also: there is no GitHub-owned
setup action for the CLI (marketplace "setup" listings are 1–20 star
community wrappers) — the docs' official install is
`npm install -g @github/copilot`.

**Output pattern:** have the agent write its result to a file
(`$RUNNER_TEMP/report.md`), `test -s` it, and let deterministic shell steps
do the GitHub side effects (`gh issue create`, `$GITHUB_STEP_SUMMARY`).
Denying `shell(gh:*)` to the agent keeps all GitHub mutations in reviewable
bash instead of model-driven calls.

## Verification

Used to build the `ponytail-audit` composite action in
custom-github-actions (2026-07-19). Flags/auth verified against the official
docs and changelog the same day; not yet exercised in a live CI run.

## Notes

- Billing: each run consumes Copilot premium requests per the model
  multiplier; GITHUB_TOKEN auth bills the repo owner, PAT bills that user's
  seat.
- Copilot CLI does not read Claude Code `.claude/skills/`; inline skill
  instructions into the prompt.
- actionlint (as of mid-2026) does not know the `copilot-requests` permission
  scope and reports `unknown permission scope "copilot-requests"` — a false
  positive; the permission is current per GitHub docs. Expect it locally and
  from reviewdog/actionlint CI checks until the schema updates.
- Treat repo content the agent reads as untrusted (prompt injection): never
  `--allow-tool='shell(*)'` with a token in env — allowlist read-only
  commands so `curl` is denied. Use `persist-credentials: false` on
  checkout, or the ambient token lands in `.git/config` where an
  allowlisted `cat` can read it into model output.

## References

- <https://docs.github.com/en/copilot/how-tos/copilot-cli/automate-copilot-cli/automate-with-actions>
- <https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference>
- <https://github.blog/changelog/2026-07-02-copilot-cli-no-longer-needs-a-personal-access-token-in-github-actions/>
- <https://github.com/github/copilot-cli/issues/3396>
