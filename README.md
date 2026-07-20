<!-- markdownlint-disable MD013 MD033 MD040 MD041 MD049 -->

```
 ██████╗██╗      █████╗ ██╗   ██╗██████╗ ███████╗    ███████╗██╗  ██╗██╗██╗     ██╗     ███████╗
██╔════╝██║     ██╔══██╗██║   ██║██╔══██╗██╔════╝    ██╔════╝██║ ██╔╝██║██║     ██║     ██╔════╝
██║     ██║     ███████║██║   ██║██║  ██║█████╗█████╗███████╗█████╔╝ ██║██║     ██║     ███████╗
██║     ██║     ██╔══██║██║   ██║██║  ██║██╔══╝╚════╝╚════██║██╔═██╗ ██║██║     ██║     ╚════██║
╚██████╗███████╗██║  ██║╚██████╔╝██████╔╝███████╗    ███████║██║  ██╗██║███████╗███████╗███████║
 ╚═════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝    ╚══════╝╚═╝  ╚═╝╚═╝╚══════╝╚══════╝╚══════╝
```

<p align="center"><em>A collection of skills that expand Claude's capabilities</em></p>

<p align="center">
  <img src="https://img.shields.io/github/languages/top/cajias/claude-skills?style=for-the-badge" alt="Language">
  <a href="https://github.com/cajias/claude-skills/actions"><img src="https://img.shields.io/github/actions/workflow/status/cajias/claude-skills/ci.yml?style=for-the-badge" alt="Build"></a>
  <a href="https://github.com/cajias/claude-skills/blob/main/LICENSE"><img src="https://img.shields.io/github/license/cajias/claude-skills?style=for-the-badge" alt="License"></a>
  <a href="https://github.com/cajias/claude-skills/stargazers"><img src="https://img.shields.io/github/stars/cajias/claude-skills?style=for-the-badge" alt="Stars"></a>
  <img src="https://img.shields.io/badge/Claude%20Code-plugin%20marketplace-C084FC?style=for-the-badge" alt="Claude Code marketplace">
</p>

**A Claude-native marketplace of skills and plugins that expand what [Claude Code](https://docs.claude.com/en/docs/claude-code) can do.** It bundles standalone _skills_ — reusable, multi-step prompts Claude invokes on the fly — alongside installable _plugins_ that ship hooks, slash commands, and bundled skills for knowledge management, session mining, terminal control, and developer workflows. Symlink the whole catalog into `~/.claude/plugins/`, or drop a single plugin in by hand.

<table>
<tr><td><b>Claude Code marketplace</b></td><td>A hand-authored <code>.claude-plugin/marketplace.json</code> lists every plugin so Claude Code can discover and install them natively — no extra package manager required.</td></tr>
<tr><td><b>Skills library</b></td><td>A library of standalone skills under <code>skills/</code>, each a self-contained <code>SKILL.md</code> + <code>README.md</code> with instructions, procedures, and examples Claude can follow.</td></tr>
<tr><td><b>Installable plugins</b></td><td>11 published plugins under <code>plugins/</code> — Obsidian memory, semantic search, session mining, iTerm control, PR monitoring, and dev tooling.</td></tr>
<tr><td><b>Hooks &amp; automation</b></td><td>Plugins like <code>pr-monitor</code> and <code>claudeception</code> wire lifecycle hooks that auto-resume Claude on new PR commits or extract reusable knowledge at session end.</td></tr>
<tr><td><b>Semantic + vector search</b></td><td><code>semantic-search</code> embeds your Obsidian notes locally (LanceDB + sentence-transformers) for offline retrieval over your knowledge base.</td></tr>
<tr><td><b>CI-enforced quality</b></td><td>GitHub Actions lint Markdown, enforce file naming, verify every skill has the required files, and check formatting; <code>make test-skills</code> validates every plugin under <code>plugins/</code>.</td></tr>
</table>

## Installation

Add the marketplace in Claude Code and install a plugin natively:

```text
/plugin marketplace add cajias/claude-skills
/plugin install obsidian-memory@claude-skills
```

For local development, or to install the whole catalog at once, clone the repo and symlink every plugin into `~/.claude/plugins/`:

```bash
# clone and symlink all plugins into ~/.claude/plugins/
git clone https://github.com/cajias/claude-skills
cd claude-skills && make install
```

Or install a single plugin by copying it into your plugins directory:

```bash
cp -r plugins/<plugin-name> ~/.claude/plugins/
```

## Plugins

| Plugin                                                    | What it does                                                                                                    |
| --------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| [`obsidian-memory`](./plugins/obsidian-memory/)           | Persistent memory using an Obsidian vault — stores decisions, learnings, and workflow facts.                    |
| [`semantic-search`](./plugins/semantic-search/)           | Local semantic search over Obsidian notes with LanceDB + sentence-transformers.                                 |
| [`session-mining`](./plugins/session-mining/)             | Mines Claude Code session history for learnings, patterns, and improvement opportunities.                       |
| [`claudeception`](./plugins/claudeception/)               | Extracts reusable skills from sessions at session end and writes new `SKILL.md` files.                          |
| [`pr-monitor`](./plugins/pr-monitor/)                     | Stop hook that auto-resumes Claude Code when new commits land on a monitored PR.                                |
| [`dev`](./plugins/dev/)                                   | Development workflow tools — README generation and review workflows.                                            |
| [`md-to-pdf`](./plugins/md-to-pdf/)                       | Converts markdown directories to PDF with Mermaid diagram rendering.                                            |
| [`iterm-utils`](./plugins/iterm-utils/)                   | iTerm2 utilities for Claude Code — pane and session management.                                                 |
| [`iterm-job-controller`](./plugins/iterm-job-controller/) | iTerm2 job dispatcher and session controller — dispatches jobs and monitors progress.                           |
| [`cc-plugin-authoring`](./plugins/cc-plugin-authoring/)   | Hard-won gotchas from authoring Claude Code plugins, with a reference skill.                                    |
| [`ai-writing`](./plugins/ai-writing/)                     | AI-writing toolkit — detect, analyze, fix, and humanize AI-generated text via a multi-agent humanizer workflow. |

## Featured skills

A few of the standalone skills under [`skills/`](./skills/):

- [`software-effort-estimation`](./skills/software-effort-estimation/) — codebase valuation and effort estimation across five independent models.
- [`github-issue-grooming`](./skills/github-issue-grooming/) — automates milestones, issue relationships, and label cleanup.
- [`quip-document-writer`](./skills/quip-document-writer/) — transfers markdown to Quip with formatting validation.
- [`tell-q-agent-router`](./skills/tell-q-agent-router/) — routes tasks to Amazon Q CLI agents with automatic agent selection.

## Usage

Skills are invoked automatically by Claude when a task matches; plugins add hooks and slash commands once installed. Each skill directory under `skills/` is self-describing:

```text
skills/<skill-name>/
├── SKILL.md      # the skill prompt + detailed instructions
├── README.md     # overview and usage guide
└── examples/     # example workflows and outputs (when applicable)
```

Common maintenance commands run through the `Makefile` and npm scripts:

```bash
make help            # list available targets
make install         # symlink all plugins into ~/.claude/plugins/
make validate        # validate plugin structure and marketplace sync
make test-skills     # run the skill eval harness for all plugins

npm run lint         # markdownlint + ls-lint
npm run format       # prettier --write across md/json/yml
npm run validate     # scripts/validate.sh
```

<p align="center">
  <img src="docs/demo.gif" alt="make help — available maintenance targets" width="100%">
</p>

> _Recording is reproducible: run `vhs docs/demo.tape` after installing [vhs](https://github.com/charmbracelet/vhs)._

## Configuration

The plugin catalog is declared in [`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json):

- **`name` / `owner`** — marketplace identity surfaced in Claude Code.
- **`plugins`** — the published plugins, each with `name`, `source`, `description`, and `tags`.

The catalog is edited directly and validated by `scripts/validate.sh` (run via `make validate`), which checks plugin structure, that each entry's version matches the plugin's own `plugin.json`, and that every entry in `marketplace.json` resolves to a real `plugins/` directory. Plugin directories absent from `marketplace.json` are treated as intentionally unpublished.

## How it works

```text
claude-skills/
├── .claude-plugin/
│   └── marketplace.json         # plugin catalog consumed by Claude Code
├── skills/                      # standalone skills (SKILL.md + README.md each)
│   └── <skill-name>/
├── plugins/                     # installable plugins (hooks, commands, skills)
│   └── <plugin-name>/
│       └── .claude-plugin/plugin.json
├── Makefile                     # install / validate / test-skills
└── .github/workflows/ci.yml     # lint, skill checks, plugin tests
```

1. **Author** a skill under `skills/` or a plugin under `plugins/`.
2. **Register** plugins in `.claude-plugin/marketplace.json`.
3. **Validate** with `make validate` (plugin structure + marketplace sync).
4. **Install** with `make install` to symlink plugins into `~/.claude/plugins/`.
5. **CI** validates Markdown, file naming, required skill files, and formatting, then runs the per-plugin test suites: `semantic-search` and `claudeception` (ruff + pytest), `ai-writing` (`node --test`), and `rsi-loop` (bash test scripts).

## Development

```bash
git clone https://github.com/cajias/claude-skills.git
cd claude-skills
npm install          # installs lint/format toolchain + husky hooks

# quality gates (mirror CI)
npm run lint         # markdownlint + ls-lint
npm run format:check # prettier --check
make validate        # plugin structure + marketplace sync
make test-skills     # skill eval harness for every plugin

# per-plugin test suites (mirror CI)
(cd plugins/semantic-search && uv sync && uv run ruff check src/ tests/ && uv run pytest -v)
(cd plugins/claudeception && uv sync --extra dev && uv run ruff check hooks/ cron/ && uv run pytest)
(cd plugins/ai-writing/skills/ai-writing-humanizer/workflows && node --test tests/*.test.mjs)
```

To add a skill: create `skills/<name>/` with `SKILL.md` and `README.md` (CI enforces both). To add a plugin: create `plugins/<name>/` with `.claude-plugin/plugin.json`, register it in `.claude-plugin/marketplace.json`, then run `make validate`.

## License

[MIT](./LICENSE) © Claude Skills Contributors.
