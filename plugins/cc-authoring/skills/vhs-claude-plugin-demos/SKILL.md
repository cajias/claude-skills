---
name: vhs-claude-plugin-demos
description: |
  Make a hero GIF demo of a Claude Code plugin using VHS (charmbracelet/vhs).
  Use when: (1) writing a plugin README and want a terminal-demo GIF, (2) recording
  a screencast of a CLI that is ALSO wrapped by Claude Code slash commands, (3) the
  plugin has both slash commands (e.g. `/kb-query`) and an underlying shell CLI
  (e.g. `kb search`), (4) seeing HuggingFace/transformers progress-bar spam in
  recordings, (5) the CLI requires CWD inside a data dir but uv/poetry project
  lives elsewhere. Covers the slash-vs-CLI verb mismatch trap, deterministic /tmp
  scratch setup, hidden env-var blocks, and `uv run --project` for split CWD.
author: Claude Code
version: 1.0.0
date: 2026-04-15
---

# VHS Demos for Claude Code Plugins

## Problem

You want to make a hero GIF for a Claude Code plugin's README using VHS. The plugin exposes slash commands like `/kb-init`, `/kb-ingest`, `/kb-query`. You want to record those.

But: **VHS records terminals.** Slash commands run inside Claude Code's TUI, not in a plain shell. Recording the TUI is fragile — model latency varies, permission prompts interrupt, output is hard to time deterministically. And many Claude Code plugins wrap an underlying shell CLI where **the slash-command verb often differs from the CLI verb** (e.g. `/kb-query` is actually `kb search` under the hood, `/kb-compile` is mechanical-only while the LLM orchestration lives in the slash command).

## Trigger Conditions

- Writing a README for a Claude Code plugin and need a demo GIF
- Considering recording slash commands directly with VHS
- Discovering the slash-command name doesn't match the CLI verb
- Sharing your shell with sentence-transformers / huggingface_hub (output spam)
- The CLI requires CWD inside a data dir but the uv/poetry project root is elsewhere

## Solution

**1. Demo the shell CLI, not the slash commands.** Slash commands are wrappers. The underlying CLI gives a clean, deterministic, fast terminal recording. VHS is a TTY recorder; the TUI is too unpredictable.

**2. Verify CLI verbs first — don't trust the slash-command names.** Before writing the tape, run `<cli> --help` and `<cli> <subcmd> --help` for each step. The slash-command verb may not match. Common mismatches:

- `/kb-query` → `kb search`
- `/kb-compile` (orchestrates the LLM) → `kb compile --write-note ...` (mechanical only)

**3. Use a /tmp scratch dir for re-render determinism.** Set up the demo working area inside the tape so re-renders produce identical output:

```
Hide
Type "rm -rf /tmp/vhs-demo && mkdir -p /tmp/vhs-demo && cd /tmp/vhs-demo" Enter
Show
```

**4. Silence noisy ML libraries inside a `Hide` block:**

```
Hide
Type "export HF_HUB_DISABLE_PROGRESS_BARS=1" Enter
Type "export TRANSFORMERS_VERBOSITY=error" Enter
Type "export TOKENIZERS_PARALLELISM=false" Enter
Show
```

Without this, sentence-transformers will dump progress bars and download chatter into the recording.

**5. Split CWD from uv project context with `uv run --project`.** If your CLI needs CWD inside a wiki/data dir (e.g. needs to find a `.kb-config.yml`) but `uv` needs the project root for dependency resolution, alias it inside `Hide`:

```
Hide
Type "alias kb='uv run --project /abs/path/to/uv/project kb'" Enter
Show
```

Visible commands then look clean: `kb init`, `kb ingest`, etc., while uv silently resolves from the project root.

**6. Tape config defaults that work for plugin READMEs:**

```
Output docs/demos/<plugin>.gif
Set Shell zsh
Set FontSize 14
Set Width 1000
Set Height 600
Set Theme "Dracula"
Set TypingSpeed 60ms
```

1000×600 produces ~300-500 KB for a 25-40s demo — well under GitHub's image display limits and renders crisply on a README.

**7. Pacing.** `Sleep 1500ms` after commands whose output the viewer needs to read. `Sleep 500ms` between fast setup commands. Total target: 25-40s rendered.

## Verification

- `vhs path/to/demo.tape` produces a `.gif` under 3 MB
- `file demo.gif` reports `GIF image data, version 89a, <W> x <H>`
- Open the GIF and confirm: no HF progress bars, no permission prompts, the final command produces a meaningful result (not empty output)
- Re-run `vhs path/to/demo.tape` from a clean state — the `/tmp` scratch reset means output should be byte-identical (or close — embedding scores may vary slightly)

## Example Tape Skeleton

```
Output docs/demos/my-plugin.gif
Set Shell zsh
Set FontSize 14
Set Width 1000
Set Height 600
Set Theme "Dracula"
Set TypingSpeed 60ms

Hide
Type "rm -rf /tmp/vhs-demo && mkdir -p /tmp/vhs-demo && cd /tmp/vhs-demo" Enter
Type "export HF_HUB_DISABLE_PROGRESS_BARS=1 TRANSFORMERS_VERBOSITY=error TOKENIZERS_PARALLELISM=false" Enter
Type "alias kb='uv run --project /abs/path/to/plugin/core kb'" Enter
Type "clear" Enter
Show

Type "kb init my-wiki && cd my-wiki" Enter
Sleep 1s

Type 'kb ingest --mode text --source "Functional options is a Go pattern..."' Enter
Sleep 1500ms

Type 'kb compile --write-note --title "Functional options" --knowledge-type pattern --tags code-quality,api-design --confidence high --source "ingest-001" --body "..."' Enter
Sleep 1500ms

Type "kb index --full" Enter
Sleep 2s

Type 'kb search "Go patterns" --limit 3' Enter
Sleep 3s
```

## Notes

- VHS install: `brew install vhs` (~25 MB with deps: ttyd, libuv, libwebsockets, json-c)
- **The `Hide`/`Show` blocks are essential** — without them, env-var setup and aliases pollute the visible recording
- If your plugin has a dry-run command (e.g. `/kb-test`), prefer that — fewer side effects
- Asset convention: `docs/demos/<plugin>.tape` + `docs/demos/<plugin>.gif`. Commit BOTH (tape for reproducibility, gif for the README)
- The renamed-verb gotcha generalizes: any Claude Code plugin whose slash commands wrap a CLI may diverge in naming. Always run `<cli> --help` first
- For embedded `kb` style CLIs that need a config file in CWD: use a directory-aware alias rather than `pushd`/`popd` inside the tape — it's cleaner and won't show up in recordings
- The first invocation of an embedding model (sentence-transformers, etc.) downloads ~100 MB and is slow. Pre-warm it BEFORE recording (run `kb index --full` once outside the tape) so the recording shows fast inference

## References

- VHS: <https://github.com/charmbracelet/vhs>
- VHS tape syntax: <https://github.com/charmbracelet/vhs#vhs-command-reference>
- HF env vars: <https://huggingface.co/docs/huggingface_hub/package_reference/environment_variables>
- uv `--project` flag: <https://docs.astral.sh/uv/reference/cli/#uv-run>
