# README Generator Skill

Generate and iteratively improve README files through automated analysis and refinement.

## Overview

This skill implements an intelligent loop-until-clean approach to create high-quality README files.
It generates or improves README content, evaluates it against best practices, applies improvements,
and re-evaluates until quality standards are met.

## What It Does

1. **Analyzes** project codebase and existing documentation
2. **Generates** or updates README content following best practices
3. **Evaluates** README against comprehensive quality criteria
4. **Identifies** missing sections, unclear explanations, and improvement opportunities
5. **Applies** improvements iteratively
6. **Re-evaluates** until quality threshold met or max iterations reached

## When to Use

Use this skill when you need to:

- Create a comprehensive README for a new project
- Improve an existing README that lacks important sections
- Ensure README follows best practices and templates
- Standardize README quality across multiple projects
- Update documentation after significant code changes
- Prepare project for open source release or public visibility

## Key Features

### Intelligent Context Gathering

- Automatically analyzes project structure and files
- Identifies programming languages and frameworks
- Detects installation methods (npm, pip, gem, etc.)
- Discovers key features from code and comments
- Extracts usage patterns and API examples

### Comprehensive Evaluation

- Based on banesullivan/README template and best practices
- Checks for essential sections (Highlights, Installation, Usage, etc.)
- Validates code examples and commands
- Ensures proper formatting and structure
- Verifies completeness and clarity

### Iterative Refinement

- Generates initial README from project analysis
- Evaluates against quality criteria
- Applies targeted improvements
- Re-evaluates until quality threshold met
- Tracks all changes for transparency

### Flexible Configuration

- **Generate from scratch**: Create complete README for new projects
- **Improve existing**: Enhance current README with missing sections
- **Target sections**: Focus improvements on specific sections only
- **Preserve sections**: Protect certain sections from modification

## Quick Start

### Generate New README

```text
Use the README Generator skill to create a comprehensive README for this project.
```

### Improve Existing README

```text
Use the README Generator to improve the existing README file, focusing on adding
missing sections and improving clarity.
```

### Target Specific Sections

```text
Use the README Generator to improve just the Installation and Usage sections
of the README.
```

## Workflow Phases

### Phase 1: Context Gathering

- Read existing README (if any)
- Analyze project structure and key files
- Identify programming language and ecosystem
- Detect build tools and package managers
- Extract features from code and comments

### Phase 2: Initial Generation/Update

- Generate missing sections
- Follow banesullivan/README template structure
- Include essential sections:
  - Highlights (key features and value proposition)
  - Installation (multiple methods when applicable)
  - Usage (basic examples and common patterns)
  - API/Configuration (when applicable)
  - Contributing guidelines
  - License information

### Phase 3: Evaluation Loop

- Evaluate README against quality criteria
- Check for completeness (all essential sections present)
- Validate clarity and accuracy
- Verify code examples and commands
- Assess formatting and structure
- Generate improvement suggestions

### Phase 4: Improvement Application

- Apply high-priority improvements
- Fix missing or incomplete sections
- Clarify confusing explanations
- Add missing code examples
- Improve formatting and structure

### Phase 5: Re-Evaluation

- Re-evaluate improved README
- Check for remaining issues
- Verify improvements didn't introduce problems
- Continue until quality threshold met or max iterations reached

### Phase 6: Final Report

- Summary of all changes made
- Final quality score
- Sections added or improved
- Recommendations for manual review

## Configuration Options

The skill supports extensive configuration via `config/default.config.json`:

### Core Settings

- **max_iterations**: Maximum improvement cycles (default: 5)
- **score_threshold**: Target quality score to reach (default: 85)
- **mode**: `generate` (from scratch), `improve` (existing), or `sections` (targeted)

### Section Control

- **sections_to_generate**: List of sections to create/improve
  - `highlights` - Key features and benefits
  - `installation` - Setup instructions
  - `usage` - Basic usage examples
  - `api` - API documentation
  - `configuration` - Configuration options
  - `contributing` - Contribution guidelines
  - `license` - License information

- **preserve_sections**: Sections to leave unchanged
  - Useful for protecting manually curated content
  - Common examples: `contributing`, `license`, `credits`

### Quality Criteria

- **require_code_examples**: Ensure usage section has runnable examples
- **require_installation**: Verify installation instructions present
- **min_section_length**: Minimum content length for sections
- **check_links**: Validate all links are accessible
- **check_badges**: Verify badge URLs and status

## Evaluation Criteria

The skill evaluates README quality based on:

### Core Questions (from banesullivan/README)

Every README should answer these fundamental questions:

- ✓ **Does this solve my problem?** Clear problem statement and value proposition
- ✓ **Can I use this code?** Installation, usage examples, prerequisites
- ✓ **Who made this?** Authors, contributors, license
- ✓ **How can I learn more?** Documentation links, related projects, support

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

- ✓ **Cognitive Funneling**: Broad to specific organization (overview → details)
- ✓ **Caveats Upfront**: Limitations and prerequisites mentioned early
- ✓ **Inviting Tone**: Friendly, approachable language
- ✓ **Visual Elements**: Screenshots, GIFs, diagrams where appropriate

### Trust Signals

- ✓ **Badges**: Build status, version, license
- ✓ **Related Projects**: Alternatives and comparisons
- ✓ **Active Maintenance**: Recent commits and issue activity

### Quality Checks (All Priorities)

- ✓ Code examples are syntactically valid
- ✓ Installation commands are accurate
- ✓ Links are valid and accessible
- ✓ Formatting is consistent
- ✓ Language is clear and concise
- ✓ Structure follows logical flow

## Success Criteria

README passes evaluation when:

- ✓ All essential sections present and complete
- ✓ Code examples are valid and runnable
- ✓ Installation instructions are clear and tested
- ✓ Usage examples cover common scenarios
- ✓ Formatting is consistent and professional
- ✓ Quality score meets or exceeds threshold
- ✓ No critical issues remain

## Examples

See the `examples/` directory for:

- **example-workflow.md**: Complete walkthrough with sample project

## Limitations

- **Code analysis**: Limited to static analysis, cannot run tests
- **Context windows**: Very large projects may require focused analysis
- **Language-specific**: Best suited for projects with clear structure
- **Manual review**: Some improvements may still require human judgment
- **Existing content**: Preserves most existing content unless clearly incorrect

## Related Skills

- **AI Writing Humanizer**: For improving writing style and tone
- **GitHub Issue Grooming**: For organizing project issues
- **Software Effort Estimation**: For codebase analysis

## References

- [banesullivan/README](https://github.com/banesullivan/README) - README template and best
  practices
- [Art of README](https://github.com/hackergrrl/art-of-readme) - README writing guide
- [README Template](https://github.com/banesullivan/README/blob/main/TEMPLATE.md) - Starting
  template

## Version

1.0.0 - Initial release with iterative generation and evaluation workflow
