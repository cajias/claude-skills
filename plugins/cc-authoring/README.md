# cc-authoring

Gotchas collected while authoring and shipping real Claude Code extensions — plugins, skills, hooks, and Workflow
scripts. Each skill captures one failure mode that cost a debugging session: an APM packaging trap, a marketplace path
that Claude Code silently ignores, a hook that can't tell the main thread from a subagent, a linter that breaks a
Workflow `meta` literal, an orchestration mode that deadlocks against plan mode. They activate through Claude Code's
semantic skill matching, so they surface when you hit the symptom rather than when you remember the skill exists.

## Skills

| Skill                                                  | Purpose                                                                                                                      |
| ------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| `apm-marketplace-authoring-gotchas`                    | Nine chained gotchas migrating a hand-authored `marketplace.json` to APM-managed.                                            |
| `apm-plugin-distribution-paths`                        | Canonical `.apm/` layout, the three layouts APM recognizes, and the source-to-plugin remap table.                            |
| `autoresearch-is-code-metric-optimizer`                | `/autoresearch` is a code-metric modify-verify-keep/discard optimizer, not a literature-research skill.                      |
| `cc-hooks-main-vs-subagent`                            | Detecting main thread vs subagent in a hook, plus `CLAUDE_CODE_ENTRYPOINT` traps under `claude -p`.                          |
| `cc-mid-session-registry-staleness`                    | Agent registry and `Workflow({name})` both serve session-start snapshots, so new files stay unresolvable.                    |
| `cc-plugin-cache-multi-version-not-recorded`           | Fixes the `Plugin not cached at (not recorded)` warning from two version subdirs in the plugin cache.                        |
| `cc-pluginroot-directory-source-ignored`               | `metadata.pluginRoot` is ignored for `source:"directory"` marketplaces; use explicit plugin paths.                           |
| `claude-print-subprocess-error-streams`                | `claude --print --output-format json` writes errors to stdout, so stderr-only wrappers raise empty errors.                   |
| `claude-workflow-authoring-gotchas`                    | Four Workflow-script traps: pure-literal `meta`, the args delivery contract, missing-arg errors, wrong-ground-truth cascade. |
| `claude-workflow-meta-markdownlint-pure-literal-break` | A lint line-wrap splits a `meta` string into a `BinaryExpression` and the loader rejects the script.                         |
| `claude-workflow-plugin-distribution`                  | Shipping a Workflow script through a plugin when no `workflows/` component exists, and where file I/O belongs.               |
| `find-skills`                                          | Discovers and installs agent skills when the user asks "how do I do X" or "is there a skill for X".                          |
| `plan-mode-orchestrator-write-deadlock`                | Escapes the deadlock where orchestrator mode forbids main-thread writes and plan mode forbids subagent writes.               |
| `skill-creator-trigger-eval-gotchas`                   | Six chained gotchas in skill-creator's trigger-eval harness, including probe shadowing that reads as 0% recall.              |
| `team-mode-orchestration-verification`                 | Verifying teammate work via the file-based task list when `TaskList` reads empty or teammates go idle.                       |
| `vhs-claude-plugin-demos`                              | Recording a hero GIF demo of a plugin with VHS, covering verb mismatch, scratch setup, and split CWD.                        |

## Install

```bash
cp -r plugins/cc-authoring ~/.claude/plugins/
```
