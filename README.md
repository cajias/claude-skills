# Claude Skills

A collection of skills to expand Claude's capabilities for specific workflows and tasks.

## What are Claude Skills?

Skills are reusable prompts and workflows that enable Claude to perform complex, multi-step tasks
efficiently. Each skill contains:

- Detailed instructions and best practices
- Step-by-step procedures
- Example usage patterns
- Tool and API integration guidance

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

## Available Plugins

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
- `skill.md` - The skill prompt and detailed instructions
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
claude plugin install \
  https://github.com/cajias/claude-skills/tree/main/plugins/PLUGIN_NAME
```

## Contributing

**To add a new skill:**

1. Create a new directory under `skills/`
2. Add a `README.md` with skill overview
3. Add a `skill.md` with detailed instructions
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
