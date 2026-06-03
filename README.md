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

**A curated [APM](https://github.com/microsoft/apm) marketplace of skills and plugins that expand what [Claude Code](https://docs.claude.com/en/docs/claude-code) can do.** It bundles standalone *skills* — reusable, multi-step prompts Claude invokes on the fly — alongside installable *plugins* that ship hooks, slash commands, and bundled skills for knowledge management, session mining, terminal control, and developer workflows. Install a plugin by name with `apm`, or drop a skill straight into a Claude Code project.

<!-- markdownlint-disable MD033 -->
<table>
<tr><td><b>APM marketplace</b></td><td>One <code>apm.yml</code> publishes the whole catalog; <code>apm pack</code> generates <code>.claude-plugin/marketplace.json</code> so consumers can <code>apm install cajias/claude-skills/&lt;plugin&gt;</code>.</td></tr>
<tr><td><b>Skills library</b></td><td>Hundreds of skills under <code>skills/</code>, each a self-contained <code>SKILL.md</code> + <code>README.md</code> with instructions, procedures, and examples Claude can follow.</td></tr>
<tr><td><b>Installable plugins</b></td><td>13 plugins under <code>plugins/</code> — knowledge management (Zettelkasten, Obsidian memory, semantic search), session mining, iTerm control, PR monitoring, and dev tooling.</td></tr>
<tr><td><b>Hooks &amp; automation</b></td><td>Plugins like <code>pr-monitor</code> and <code>ai-zettelkasten</code> wire Stop hooks that auto-resume Claude or extract knowledge at session end.</td></tr>
<tr><td><b>Semantic + vector search</b></td><td><code>semantic-search</code> and <code>zettelkasten</code> embed notes locally (LanceDB / ChromaDB + sentence-transformers) for offline retrieval over your knowledge base.</td></tr>
<tr><td><b>CI-enforced quality</b></td><td>GitHub Actions lint Markdown, enforce file naming, verify every skill has the required files, and assert <code>marketplace.json</code> is never stale.</td></tr>
</table>
<!-- markdownlint-enable MD033 -->

## Installation

### Via APM (recommended)

[APM](https://github.com/microsoft/apm) is the dependency manager for AI agents. Add this marketplace once, then install plugins by name:

```bash
# one-time, per consumer repo
apm marketplace add cajias/claude-skills

# install a plugin
apm install cajias/claude-skills/<plugin-name>
```

Plugin names match the `packages` in [`apm.yml`](./apm.yml) — for example `ai-zettelkasten`, `semantic-search`, `dev`, `pr-monitor`, `obsidian-memory`.

### Via Claude Code

Install a single plugin directly from this repo:

```bash
claude plugin install \
  https://github.com/cajias/claude-skills/tree/main/plugins/<plugin-name>
```

### From source

Clone the repo to browse or hack on skills and plugins locally:

```bash
git clone https://github.com/cajias/claude-skills.git
cd claude-skills
```

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
make check           # validate apm.yml schema (apm pack --dry-run)
make pack            # regenerate .claude-plugin/marketplace.json from apm.yml
make outdated        # report drift between resolved versions and upstream tags

npm run lint         # markdownlint + ls-lint
npm run format       # prettier --write across md/json/yml
npm run validate     # scripts/validate.sh
```

<p align="center">
  <img src="docs/demo.gif" alt="make help — available maintenance targets" width="100%">
</p>

> _Recording is reproducible: run `vhs docs/demo.tape` after installing [vhs](https://github.com/charmbracelet/vhs)._

## Configuration

The marketplace catalog is declared in [`apm.yml`](./apm.yml):

- **`marketplace.metadata.pluginRoot`** — `./plugins`, the common prefix for every plugin source.
- **`marketplace.build.tagPattern`** — `{name}-v{version}`, the release tag scheme.
- **`packages`** — the published plugins, each with `name`, `source`, `version`, `description`, and `tags`.

Run `make pack` after editing `apm.yml` to regenerate `.claude-plugin/marketplace.json`; CI fails if the generated file is stale.

## How it works

```text
claude-skills/
├── apm.yml                      # marketplace source of truth (packages -> plugins)
├── .claude-plugin/
│   └── marketplace.json         # generated by `apm pack`, consumed by Claude Code
├── skills/                      # standalone skills (SKILL.md + README.md each)
│   └── <skill-name>/
├── plugins/                     # installable plugins (hooks, commands, skills)
│   └── <plugin-name>/
│       └── .claude-plugin/plugin.json
├── Makefile                     # apm pack / check / outdated
└── .github/workflows/ci.yml     # lint, marketplace freshness, plugin tests
```

1. **Author** a skill under `skills/` or a plugin under `plugins/`.
2. **Register** plugins in `apm.yml` under `packages`.
3. **Pack** with `make pack` to (re)generate `marketplace.json`.
4. **Distribute** via APM (`apm marketplace add`) or Claude Code's plugin installer.
5. **CI** validates Markdown, file naming, required skill files, marketplace freshness, and runs the `semantic-search` plugin's pytest suite.

## Development

```bash
git clone https://github.com/cajias/claude-skills.git
cd claude-skills
npm install          # installs lint/format toolchain + husky hooks

# quality gates (mirror CI)
npm run lint         # markdownlint + ls-lint
npm run format:check # prettier --check
make check           # apm pack --dry-run

# the semantic-search plugin is tested with uv + pytest
cd plugins/semantic-search
uv sync
uv run ruff check src/ tests/
uv run pytest -v
```

To add a skill: create `skills/<name>/` with `SKILL.md` and `README.md` (CI enforces both). To add a plugin: create `plugins/<name>/` with `.claude-plugin/plugin.json`, register it in `apm.yml`, then run `make pack`.

## License

[MIT](./LICENSE) © Claude Skills Contributors.
