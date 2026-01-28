# Dev Plugin

Development workflow tools for Claude Code - README generation, code review, and more.

## Overview

This plugin provides developer productivity commands that help with common development workflows:

- **README Generation**: Create and improve project README files
- **Code Review**: (Coming soon) Review code changes for quality
- **PR Review**: (Coming soon) Review pull requests comprehensively

## Commands

### `/dev:review-readme`

Evaluate and improve README files with iterative refinement.

**Modes:**

- `generate` - Create README from scratch by analyzing codebase
- `improve` (default) - Enhance existing README iteratively
- `evaluate` - Evaluate quality and return feedback only

**Usage:**

```text
/dev:review-readme              # Improve existing README
/dev:review-readme generate     # Generate from scratch
/dev:review-readme evaluate     # Evaluate only, no changes
```

**How it works:**

1. Analyzes your project structure and codebase
2. Reads existing README (if present) using `@README.md`
3. Gathers context with bash commands (`!ls -la`, `!cat package.json`)
4. Follows a 7-phase workflow:
   - Context gathering
   - Initial generation/improvement
   - Quality evaluation
   - Improvement planning
   - Apply improvements
   - Re-evaluation loop
   - Final report
5. Evaluates against banesullivan/README best practices
6. Iterates until quality threshold met (default: 85/100)

## Installation

### Via Plugin Manager (Recommended)

```bash
claude plugin install \
  https://github.com/cajias/claude-skills/tree/main/plugins/dev
```

After installation, restart Claude Code for the commands to become available.

### Manual Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/cajias/claude-skills.git
   cd claude-skills/plugins/dev
   ```

2. Copy to Claude plugins directory:

   ```bash
   mkdir -p ~/.claude/plugins/dev
   cp -r ./* ~/.claude/plugins/dev/
   ```

3. Restart Claude Code

## Quick Start

### Improve Existing README

Simply run the command in your project:

```text
/dev:review-readme
```

Claude will:

1. Read your current README
2. Analyze your project structure
3. Identify missing or incomplete sections
4. Iteratively improve the README
5. Provide a quality score and summary

### Generate New README

For projects without a README:

```text
/dev:review-readme generate
```

Claude will:

1. Analyze your codebase
2. Extract features and API information
3. Generate a comprehensive README
4. Follow best practices and templates
5. Include installation, usage, and examples

### Evaluate Without Changes

To get feedback without modifications:

```text
/dev:review-readme evaluate
```

Claude will:

1. Analyze your README quality
2. Check for missing sections
3. Validate code examples and links
4. Provide a quality score
5. List recommended improvements

## Configuration

The README generator is highly configurable via `config/readme-generator/default.config.json`:

### Core Settings

- **max_iterations** (default: 5): Maximum improvement cycles
- **score_threshold** (default: 85): Target quality score (0-100)
- **mode** (default: improve): `generate`, `improve`, or `sections`
- **preserve_custom** (default: true): Keep custom sections

### Section Control

- **sections_to_generate**: List of sections to create/improve
- **preserve_sections**: Sections to leave unchanged
- **require_sections**: Sections that must be present

### Quality Settings

- **require_code_examples** (default: true): Usage must include code examples
- **require_installation** (default: true): Installation section required
- **min_section_length** (default: 50): Minimum characters per section
- **check_links** (default: true): Validate all links
- **strict_mode** (default: false): More rigorous quality requirements

See `config/readme-generator/config.schema.json` for the full schema.

## Evaluation Criteria

The README generator evaluates against comprehensive quality criteria based on
[banesullivan/README](https://github.com/banesullivan/README) best practices:

### Core Questions

Every README should answer:

- ✓ Does this solve my problem?
- ✓ Can I use this code?
- ✓ Who made this?
- ✓ How can I learn more?

### Essential Sections (High Priority)

- ✓ **Highlights**: Clear value proposition and key features
- ✓ **Installation**: At least one installation method
- ✓ **Usage**: Basic usage examples with code

### Recommended Sections (Medium Priority)

- ✓ **API Documentation**: For libraries and frameworks
- ✓ **Configuration**: For configurable tools
- ✓ **Contributing**: Guidelines for contributors
- ✓ **License**: License information

### Quality Attributes

- ✓ **Cognitive Funneling**: Broad to specific organization
- ✓ **Caveats Upfront**: Limitations mentioned early
- ✓ **Inviting Tone**: Friendly, approachable language
- ✓ **Visual Elements**: Screenshots, GIFs, diagrams where appropriate

### Trust Signals

- ✓ Build status, version, and license badges
- ✓ Related projects and alternatives
- ✓ Active maintenance indicators

## Examples

See `examples/readme-workflow.md` for a complete walkthrough with a sample project.

### Example Output

```text
README Generation Summary

Status: Complete
Final Score: 92/100
Iterations: 3

Changes Made:
- Added Installation section with npm and yarn methods
- Created Usage section with 2 code examples
- Added complete API documentation
- Enhanced Contributing section
- Fixed 3 broken links

Quality Breakdown:
- Essential Sections: 100/100
- Content Quality: 90/100
- Code Examples: 95/100
- Formatting: 85/100
```

## Future Commands

The `dev` plugin will expand with additional commands:

- `/dev:review-code` - Code review with quality checks
- `/dev:review-pr` - Comprehensive PR review
- `/dev:lint` - Linting workflows
- `/dev:docs` - Documentation generation

## Limitations

- **Code analysis**: Limited to static analysis, cannot run tests
- **Context windows**: Very large projects may require focused analysis
- **Language-specific**: Best suited for projects with clear structure
- **Manual review**: Some improvements may still require human judgment

## Requirements

- Claude Code: Latest version
- Git: For repository analysis
- Project files: Access to codebase and README

## Troubleshooting

### Command Not Found

**Check plugin installed:**

```bash
ls -la ~/.claude/plugins/dev
```

**Verify plugin.json exists:**

```bash
cat ~/.claude/plugins/dev/.claude-plugin/plugin.json
```

### Poor Quality Score

If the generated README doesn't meet quality threshold:

1. Check that your project has clear structure
2. Ensure package manifests (package.json, etc.) are present
3. Verify that key source files are readable
4. Consider running with `generate` mode for fresh start
5. Adjust configuration in `config/readme-generator/default.config.json`

### Missing Sections

If certain sections are not generated:

1. Check `sections_to_generate` in config
2. Ensure required files exist (package.json, setup.py, etc.)
3. Add manual content that Claude can enhance

## Security Considerations

- Command reads project files with your user privileges
- Uses bash execution to gather project context
- Does NOT modify code or create commits
- Read-only access to repositories

**Best Practices:**

- Review generated content before committing
- Verify code examples are accurate
- Check that links point to correct resources
- Ensure license information is correct

## Related Skills

- **AI Writing Humanizer**: For improving writing style and tone
- **GitHub Issue Grooming**: For organizing project issues
- **Software Effort Estimation**: For codebase analysis

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add new commands or improve existing ones
4. Test your changes
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Author

cajias

## Documentation

- 📘 [Command Documentation](./commands/review-readme.md) - Full command instructions
- 📋 [Example Workflow](./examples/readme-workflow.md) - Complete walkthrough
- 🔧 [Configuration Schema](./config/readme-generator/config.schema.json) - Full config options

## References

- [banesullivan/README](https://github.com/banesullivan/README) - README template and best practices
- [Art of README](https://github.com/hackergrrl/art-of-readme) - README writing guide
- [Claude Code Commands](https://code.claude.com/docs/en/commands.md) - Command documentation

## Changelog

### v1.0.0 (2025-01-01)

- Initial release
- `/dev:review-readme` command with three modes (generate, improve, evaluate)
- Iterative improvement with quality scoring
- Configuration support
- Based on banesullivan/README best practices
