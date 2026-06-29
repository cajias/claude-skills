# Claude Skills

A collection of skills to expand Claude's capabilities for specific workflows and tasks.

## What are Claude Skills?

Skills are reusable prompts and workflows that enable Claude to perform complex, multi-step tasks
efficiently. Each skill contains:

- Detailed instructions and best practices
- Step-by-step procedures
- Example usage patterns
- Tool and API integration guidance

## Installation

Clone and symlink all plugins:

```bash
git clone https://github.com/cajias/claude-skills
cd claude-skills && make install
```

Or install one plugin:

```bash
cp -r plugins/<name> ~/.claude/plugins/
```

## Available Skills

### [GitHub Issue Grooming](./skills/github-issue-grooming/)

Automate GitHub issue management workflows including:

- Setting up milestones based on project phases
- Creating native issue relationships (blocked by, blocks)
- Assigning issues to milestones
- Removing redundant labels
- Organizing issue dependencies

### [Software Effort Estimation & Codebase Valuation](./skills/software-effort-estimation/)

Generate comprehensive software effort estimation reports including:

- Automated codebase analysis (LOC, commits, contributors)
- Five independent estimation models (COCOMO II, Industry Benchmarks, Infrastructure Multiplier,
  Blended Hybrid, Team Analysis)
- Productivity multiplier analysis (LLM-assisted vs traditional development)
- Three-stage verification process with 90%+ accuracy
- Professional 15,000+ word reports with strategic recommendations
- Reproducible methodology with complete command documentation

### [AI Writing Humanizer](./skills/ai-writing-humanizer/)

Transform AI-generated text into natural human-sounding writing:

- Comprehensive pattern detection across 15 categories (200+ patterns)
- Iterative loop-until-clean approach with re-analysis after each pass
- Removes chatbot artifacts, buzzwords, promotional language, and inflated symbolism
- Interactive mode for review or batch mode for automatic fixes
- Context-aware replacements that preserve meaning
- Before/after comparisons and detailed change logs

### [Quip Document Writer](./skills/quip-document-writer/)

Transfer markdown documents to Quip with proper formatting validation:

- Section-by-section transfer approach with validation
- Automatic conversion of numbered lists to HTML to prevent rendering failures
- Smart handling of images, tables, and Mermaid diagrams
- Comprehensive verification after each section upload
- Detailed TODO lists for manual follow-up tasks
- Handles common Quip markdown import issues

### [Tell Q Agent Router](./skills/tell-q-agent-router/)

Intelligently route tasks to Amazon Q CLI agents with automatic agent selection:

- Natural language interface using "tell q to..." pattern
- Intelligent agent selection based on task analysis and keywords
- Background execution with progress monitoring
- Support for explicit agent selection when needed
- Special workflow patterns (e.g., Quip file upload)
- Seven specialized agents (AWS, docs, architecture, quality, code dev, default, omega)

### [Q Chat Integration](./skills/q-chat-integration/)

Delegate tasks to Amazon Q CLI agents with specialized tool integrations:

- Seamlessly delegate to Q using natural trigger phrases ("tell Q to...", "ask Q to...")
- Non-interactive background execution with full tool permissions
- Perfect for Quip operations, ticket creation, and diagram generation
- Intelligent context gathering and absolute path resolution
- Automatic agent routing based on task type (AWS, docs, architecture, quality)
- Progress monitoring and status reporting

## Available Plugins

### [Dev](./plugins/dev/)

Development workflow tools with slash commands for README generation and code review:

- `/dev:review-readme` command for README creation and improvement
- Intelligent codebase analysis to extract features and usage patterns
- Iterative evaluation and improvement loop until quality threshold met
- Three modes: generate from scratch, improve existing, or evaluate only
- Based on banesullivan/README template and best practices
- Configurable quality criteria and section requirements
- Detailed change tracking and quality reports

### [PR Monitor](./plugins/pr-monitor/)

Automated GitHub pull request monitoring with event-driven hooks:

- Automatically detects new commits in monitored PRs
- Auto-resumes Claude Code when changes are detected
- Supports monitoring multiple PRs simultaneously
- Includes Stop hook + PR monitor skill
- Auto-cleanup when PR is merged or closed

## Using Skills

Skills can be invoked by Claude when working on related tasks. Each skill directory contains:

- `README.md` - Skill overview and usage guide
- `SKILL.md` - The skill prompt and detailed instructions
- `examples/` - Example workflows and outputs (when applicable)

## Using Plugins

Plugins extend Claude Code with hooks, skills, and other capabilities. Each plugin directory
contains:

- `.claude-plugin/plugin.json` - Plugin metadata
- `hooks/` - Hook definitions and scripts
- `skills/` - Bundled skills
- `README.md` - Plugin documentation

**Installation:**

```bash
cp -r plugins/PLUGIN_NAME ~/.claude/plugins/
```

## Contributing

**To add a new skill:**

1. Create a new directory under `skills/`
2. Add a `README.md` with skill overview
3. Add a `SKILL.md` with detailed instructions
4. Include examples if applicable
5. Update this main README with the new skill

**To add a new plugin:**

1. Create a new directory under `plugins/`
2. Add `.claude-plugin/plugin.json` with metadata
3. Add `hooks/`, `skills/`, or other components
4. Add a `README.md` with documentation
5. Update this main README with the new plugin

## License

MIT License - See LICENSE file for details
