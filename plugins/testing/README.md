# testing

Skills for making verification actually verify. Each one addresses a way a
test or check reports green while proving nothing — a renderer test that
survives deleting the draw call, a Streamlit smoke test that only proves the
HTTP server answered, a zsh assertion block that reports every item MISSING
because of word splitting, or a Workflow script with no unit-test path at all.

## Skills

| Skill                               | Purpose                                                                                                                                                                                  |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `claude-workflow-tdd-harness`       | Dependency-free ESM harness for unit-testing Workflow scripts with `node:test` — strips `export const meta`, wraps the body in an AsyncFunction, injects mocks for the Workflow globals. |
| `mutation-verify-render-tests`      | Mutation-test pixel and scene-capture tests for graphical renderers: break the draw call, confirm the test fails, restore, confirm it passes.                                            |
| `streamlit-ui-visual-verification`  | Verify Streamlit changes in a real browser instead of an HTTP 200 smoke test; covers the server-up-does-not-mean-UI-works trap and the Playwright MCP fallback.                          |
| `zsh-done-assertion-word-splitting` | Two zsh traps that make done-assertion blocks report false all-MISSING results: no word splitting of unquoted vars, and a lowercase `path` variable clobbering `$PATH`.                  |

## Install

```bash
cp -r plugins/testing ~/.claude/plugins/
```

Skills surface automatically via Claude Code's semantic matching when you hit
one of the trigger conditions documented in each `SKILL.md`.
