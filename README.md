# Claude Skills

A collection of skills to expand Claude's capabilities for specific workflows and tasks.

## What are Claude Skills?

Skills are reusable prompts and workflows that enable Claude to perform complex, multi-step tasks efficiently. Each skill contains:

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

## Using Skills

Skills can be invoked by Claude when working on related tasks. Each skill directory contains:

- `README.md` - Skill overview and usage guide
- `skill.md` - The skill prompt and detailed instructions
- `examples/` - Example workflows and outputs (when applicable)

## Contributing

To add a new skill:

1. Create a new directory under `skills/`
2. Add a `README.md` with skill overview
3. Add a `skill.md` with detailed instructions
4. Include examples if applicable
5. Update this main README with the new skill

## License

MIT License - See LICENSE file for details
