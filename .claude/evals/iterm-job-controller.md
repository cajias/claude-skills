# Eval: iterm-job-controller

Plugin path: plugins/iterm-job-controller

## Capability Evals

[CAPABILITY EVAL: iterm-job-controller-structure]
Task: Verify plugin has all required structural files and fields
Success Criteria:

- [ ] .claude-plugin/plugin.json exists and is valid JSON
- [ ] plugin.json has name, description, and version fields
- [ ] At least one agents/ subdirectory with an agent definition file (.md)
- [ ] Each agent .md has YAML frontmatter with name and description fields
- [ ] No APM references (apm pack, apm marketplace, Agent Package Manager)
      Expected Output: All structural checks pass
      Grader: code-based (bash — see scripts/test-skills.sh)

[CAPABILITY EVAL: iterm-job-controller-skill-quality]
Task: Verify agent descriptions are specific and triggerable
Success Criteria:

- [ ] Description is specific (not generic boilerplate)
- [ ] Agent content is substantial (> 200 chars per agent .md)
- [ ] Triggering context is clear in the description
- [ ] No placeholder text (TODO, TBD) in production agents
      Expected Output: All skill quality checks pass
      Grader: manual (not implemented by scripts/test-skills.sh)

## Regression Evals

[REGRESSION EVAL: iterm-job-controller-claude-native]
Baseline: APM era (pre-migration)
Tests:

- plugin.json uses Claude-native format (not APM format): MUST PASS
- No APM CLI dependency for installation: MUST PASS
- Plugin installable by copying to ~/.claude/plugins/: MUST PASS
  Result: 3/3 must pass

## Plugin-Specific Checks

This plugin registers one agent definition under `agents/`:

### Agent: job-controller

File: `agents/job-controller.md`

What it does: Manages, monitors, and dispatches jobs across iTerm2 terminal sessions. Wraps the
iTerm2 MCP tools (`mcp__iterm2__*`) into a single specialized agent that can list panes, read
terminal output, send commands, send control characters (Ctrl+C, Ctrl+Z, Ctrl+L), and split or
create side panes.

Frontmatter fields present:

- name: job-controller
- namespace: iterm-job-controller:job-controller
- description: Control, monitor, and dispatch jobs to iTerm2 terminal sessions -
  tracks state, executes commands, monitors progress
- model: sonnet
- color: cyan
- usage: "Use via Task tool with subagent_type: 'iterm-job-controller:job-controller'"
- tools: list of 9 mcp**iterm2**\* tools

Plugin-specific assertions:

- [ ] agents/job-controller.md frontmatter declares all required mcp**iterm2**\* tools
- [ ] namespace field follows pattern `<plugin-name>:<agent-name>` (iterm-job-controller:job-controller)
- [ ] model field is set to a valid Claude model alias (sonnet)
- [ ] usage field describes how to invoke via Task tool with correct subagent_type value
- [ ] Agent body includes pane ID format documentation (t<tab>p<pane> convention)
- [ ] Agent body includes at least one concrete usage example (<example> block)
- [ ] Agent body documents iTerm2 API enable path (iterm2_enable_api fallback)
- [ ] No `skills/` directory exists (plugin uses `agents/` layout, not skills layout)

Note: This plugin has no `skills/` directory. It provides its capability via an `agents/`
definition. The `scripts/test-skills.sh` grader treats agents as a valid component type, so
the plugin passes structural validation and is reported as `[agents]`.

## Metrics Target

- pass@1: 100% for structure (deterministic)
