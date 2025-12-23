---
description: Evaluate and improve README files with iterative refinement
argument-hint: [mode: generate|improve|evaluate]
---

# README Generator

## Objective

Generate or improve README files through iterative analysis and refinement. Analyze project
codebase, create or enhance README content following best practices, evaluate quality, and apply
improvements until quality threshold is met or maximum iterations reached.

## Command Arguments

Parse `$ARGUMENTS` to determine the operation mode:

- **No arguments or "improve"** (default): Enhance existing README iteratively
- **"generate"**: Create README from scratch by analyzing codebase
- **"evaluate"**: Evaluate quality and return feedback only (no changes)

**Usage Examples:**

```text
/dev:review-readme              # Improve existing README
/dev:review-readme improve      # Same as above (explicit)
/dev:review-readme generate     # Generate from scratch
/dev:review-readme evaluate     # Evaluate only, no changes
```

## Prerequisites

Before starting, ensure:

1. You have access to the project repository and its files
2. You can read and analyze code in the project's primary language(s)
3. You understand the project's purpose and key features
4. You have access to the configuration in `config/readme-generator/default.config.json`

## Reading the README

Use `@README.md` to reference and read the existing README file in the project root.

## Gathering Project Context

Use `!` bash execution to gather project context:

```bash
# Check project structure
!ls -la

# Look for package manifests
!find . -maxdepth 2 -name "package.json" -o -name "setup.py" -o -name "Cargo.toml" -o -name "go.mod" -o -name "pom.xml"

# Read package metadata (example for Node.js)
!cat package.json

# Check for other relevant files
!ls -la src/ lib/ docs/
```

## Configuration

The command supports extensive configuration via `config/readme-generator/default.config.json`:

### Core Settings

| Setting           | Default | Description                                    |
| ----------------- | ------- | ---------------------------------------------- |
| `max_iterations`  | 5       | Maximum improvement cycles                     |
| `score_threshold` | 85      | Target quality score (0-100)                   |
| `mode`            | improve | `generate`, `improve`, or `sections`           |
| `preserve_custom` | true    | Keep custom sections not in standard templates |

### Section Control

| Setting                | Description                        |
| ---------------------- | ---------------------------------- |
| `sections_to_generate` | List of sections to create/improve |
| `preserve_sections`    | Sections to leave unchanged        |
| `require_sections`     | Sections that must be present      |

### Quality Settings

| Setting                 | Default | Description                        |
| ----------------------- | ------- | ---------------------------------- |
| `require_code_examples` | true    | Usage must include code examples   |
| `require_installation`  | true    | Installation section required      |
| `min_section_length`    | 50      | Minimum characters per section     |
| `check_links`           | true    | Validate all links                 |
| `strict_mode`           | false   | More rigorous quality requirements |

## Core Algorithm

```pseudocode
function generate_readme(project_path, config):
    iteration = 0
    current_readme = read_existing_readme() or ""
    all_changes = []

    # Phase 1: Gather context
    context = analyze_project(project_path)

    while iteration < config.max_iterations:
        iteration++

        # Phase 2: Generate or improve README
        if iteration == 1 and current_readme == "":
            # Generate from scratch
            current_readme = generate_initial_readme(context, config)
        else:
            # Apply improvements from evaluation
            if evaluation_feedback:
                current_readme = apply_improvements(current_readme, evaluation_feedback)

        # Phase 3: Evaluate quality
        evaluation = evaluate_readme(current_readme, context, config)

        # Phase 4: Check if complete
        if evaluation.score >= config.score_threshold and evaluation.critical_issues == 0:
            return {
                status: "complete",
                readme: current_readme,
                score: evaluation.score,
                iterations: iteration,
                changes: all_changes
            }

        # Phase 5: Generate improvement plan
        evaluation_feedback = generate_improvement_plan(evaluation)
        all_changes.append({
            iteration: iteration,
            issues: evaluation.issues,
            planned_improvements: evaluation_feedback
        })

        # Log iteration
        log_iteration(iteration, evaluation.score, evaluation.issues)

    # Max iterations reached
    return {
        status: "max_iterations",
        readme: current_readme,
        score: evaluation.score,
        iterations: iteration,
        changes: all_changes,
        remaining_issues: evaluation.issues
    }
```

## Step-by-Step Workflow

### Phase 1: Context Gathering and Analysis

**Goal**: Understand the project to generate relevant README content

1. **Read existing README** (if present):

   ```bash
   # Check for README
   find . -maxdepth 1 -iname "README*" -type f
   ```

2. **Analyze project structure**:

   ```bash
   # Identify project type and structure
   ls -la
   find . -name "package.json" -o -name "setup.py" -o -name "Cargo.toml" -o -name "go.mod" -o -name "pom.xml"
   ```

3. **Identify key files**:
   - Package manifests (package.json, setup.py, Cargo.toml, etc.)
   - Configuration files
   - Main entry points (main.py, index.js, main.go, etc.)
   - Documentation files

4. **Extract project metadata**:
   - Project name
   - Version
   - Description
   - Dependencies
   - Scripts/commands
   - License

5. **Analyze codebase features**:
   - Read main source files
   - Identify key classes, functions, or modules
   - Look for exported APIs
   - Find usage patterns in tests or examples

6. **Identify ecosystem and tools**:
   - Programming language(s)
   - Build tools
   - Package manager
   - Testing framework
   - CI/CD setup

### Phase 2: Initial Generation or Improvement

**Goal**: Create or enhance README content following best practices

#### For New README Generation (`mode: generate`)

1. **Create structure using template**:

   ```markdown
   # Project Name

   Brief description

   ## Highlights

   - Key feature 1
   - Key feature 2
   - Key feature 3

   ## Installation

   ### Via Package Manager

   [installation commands]

   ## Usage

   ### Basic Example

   [code example]

   ## API / Configuration

   [if applicable]

   ## Contributing

   [guidelines]

   ## License

   [license info]
   ```

2. **Populate each section**:
   - **Highlights**: Extract from codebase analysis, package description
   - **Installation**: Based on package manager and ecosystem
   - **Usage**: Create examples from API analysis or entry points
   - **API**: Document exported functions/classes if library
   - **Configuration**: Document config files or environment variables

#### For README Improvement (`mode: improve`)

1. **Preserve existing structure**:
   - Keep custom sections not in preserve_sections list
   - Maintain existing formatting style
   - Preserve code examples that work

2. **Identify gaps**:
   - Missing required sections
   - Incomplete sections (too short or vague)
   - Missing code examples
   - Outdated information

3. **Enhance content**:
   - Add missing sections
   - Expand thin sections with detail
   - Add code examples where missing
   - Update outdated commands or examples

#### For Targeted Section Update (`mode: sections`)

1. **Focus on specified sections only**:
   - Only modify sections in `sections_to_generate`
   - Leave all other sections unchanged

### Phase 3: README Evaluation

**Goal**: Assess README quality against comprehensive criteria

1. **Evaluate against Core Questions** (from banesullivan/README):

   Every README should answer these fundamental questions for the reader:

   ```text
   Core Questions:
   - [ ] Does this solve my problem? (Clear problem statement and value proposition)
   - [ ] Can I use this code? (Installation, usage examples, prerequisites)
   - [ ] Who made this? (Authors, contributors, license)
   - [ ] How can I learn more? (Documentation links, related projects, support)
   ```

2. **Check essential sections**:

   ```text
   Critical (must have):
   - [ ] Highlights or Description
   - [ ] Installation instructions
   - [ ] Usage examples

   Recommended (should have):
   - [ ] API documentation (for libraries)
   - [ ] Configuration (for tools)
   - [ ] Contributing guidelines
   - [ ] License information
   ```

3. **Validate content quality**:

   For each section, check:
   - Is content present and non-empty?
   - Is content length adequate (>= min_section_length)?
   - Is content clear and well-formatted?
   - Does it contain specific, actionable information?

4. **Assess quality attributes**:

   ```text
   Cognitive Funneling:
   - [ ] Broad to specific organization (overview → details)
   - [ ] Logical flow from problem to solution to usage
   - [ ] Progressive disclosure of complexity

   Caveats Upfront:
   - [ ] Limitations mentioned early (not buried at end)
   - [ ] Prerequisites clearly stated before installation
   - [ ] Platform/version requirements prominent

   Tone Assessment:
   - [ ] Inviting and approachable language
   - [ ] Friendly without being unprofessional
   - [ ] Encouraging to potential users/contributors

   Visual Elements:
   - [ ] Screenshots for UI/visual projects
   - [ ] GIFs/demos for interactive features
   - [ ] Diagrams for architecture/workflows (when helpful)
   - [ ] Code examples properly highlighted
   ```

5. **Check trust signals**:

   ```text
   - [ ] Build/CI status badges (passing tests)
   - [ ] Version/release badges
   - [ ] License badge
   - [ ] Related projects or alternatives mentioned
   - [ ] Comparison with similar tools (when appropriate)
   - [ ] Active maintenance indicators (recent commits, issues)
   ```

6. **Evaluate code examples**:

   ```text
   For usage examples:
   - [ ] Syntax is valid for the language
   - [ ] Examples are complete and runnable
   - [ ] Examples cover common use cases
   - [ ] Examples include expected output (when helpful)
   ```

7. **Check installation instructions**:

   ```text
   - [ ] At least one installation method documented
   - [ ] Commands are accurate for the ecosystem
   - [ ] Prerequisites mentioned (if any)
   - [ ] Multiple installation methods (when applicable)
   ```

8. **Validate links and references**:

   ```text
   - [ ] All markdown links have valid syntax
   - [ ] Links point to accessible resources
   - [ ] Badges have correct URLs
   - [ ] References to files/paths are accurate
   ```

9. **Assess structure and formatting**:

   ```text
   - [ ] Consistent heading hierarchy
   - [ ] Code blocks have language tags
   - [ ] Lists are properly formatted
   - [ ] No broken formatting
   ```

10. **Calculate quality score**:

```text
Score = (
  essential_sections_score * 0.4 +
  content_quality_score * 0.3 +
  examples_score * 0.2 +
  formatting_score * 0.1
)

Where each component is 0-100
```

<!-- markdownlint-disable MD029 -->

11. **Categorize issues by priority**:

<!-- markdownlint-enable MD029 -->

- **Critical**: Missing essential sections, broken examples
- **High**: Incomplete sections, missing examples, broken links
- **Medium**: Thin content, minor formatting issues
- **Low**: Style inconsistencies, optional improvements

### Phase 4: Generate Improvement Plan

**Goal**: Create actionable plan to address evaluation issues

1. **Prioritize issues**:
   - Address critical issues first
   - Group related issues together
   - Consider dependencies between fixes

2. **Create improvement actions**:

   For each issue, specify:
   - What needs to be added/changed
   - Where in the document
   - Why it's important
   - Specific content to add (when possible)

3. **Example improvement plan**:

   ```json
   {
     "critical": [
       {
         "issue": "Missing Installation section",
         "action": "Add Installation section after Highlights",
         "content": "Include npm install command and prerequisites"
       }
     ],
     "high": [
       {
         "issue": "Usage section has no code examples",
         "action": "Add code examples to Usage section",
         "content": "Show basic import and function call example"
       }
     ],
     "medium": [
       {
         "issue": "API section is incomplete",
         "action": "Document main exported functions",
         "content": "Add parameter descriptions and return types"
       }
     ]
   }
   ```

### Phase 5: Apply Improvements

**Goal**: Update README with planned improvements

1. **Process improvements by priority**:
   - Apply critical fixes first
   - Then high priority
   - Then medium and low if within iteration limit

2. **Make surgical edits**:
   - Preserve existing content when possible
   - Add new sections in appropriate locations
   - Enhance existing sections without complete rewrites
   - Maintain consistent formatting style

3. **Validate changes**:
   - Ensure new content fits naturally
   - Check that code examples are syntactically correct
   - Verify links and references are valid
   - Maintain document flow and coherence

### Phase 6: Re-Evaluation Loop

**Goal**: Verify improvements and iterate if needed

1. **Re-run evaluation**:
   - Evaluate updated README
   - Calculate new quality score
   - Identify remaining issues

2. **Check completion criteria**:

   ```text
   Complete if:
   - Score >= score_threshold, AND
   - critical_issues == 0, AND
   - high_priority_issues <= acceptable_threshold

   OR

   - iteration >= max_iterations
   ```

3. **Continue or finish**:
   - If complete: Return final README and summary
   - If not complete: Generate new improvement plan and continue
   - If max iterations: Return best attempt with remaining issues

### Phase 7: Final Report

**Goal**: Provide comprehensive summary of work done

1. **Summarize changes**:

   ```markdown
   ## README Generation Summary

   **Status**: Complete / Max Iterations Reached
   **Final Score**: 92/100
   **Iterations**: 3

   ### Changes Made

   #### Iteration 1

   - Added Installation section with npm and manual methods
   - Created Usage section with basic example
   - Added API documentation for main functions

   #### Iteration 2

   - Enhanced Usage section with advanced examples
   - Added Configuration section
   - Fixed broken links to documentation

   #### Iteration 3

   - Improved code examples with expected output
   - Added troubleshooting subsection
   - Enhanced Contributing guidelines

   ### Final Quality Breakdown

   - Essential Sections: 100/100
   - Content Quality: 90/100
   - Code Examples: 95/100
   - Formatting: 85/100

   ### Remaining Issues (if any)

   None - All critical and high-priority issues resolved.
   ```

2. **Provide recommendations**:
   - Suggest manual review areas
   - Note sections that may need project-specific detail
   - Recommend future updates based on project evolution

## Best Practices

### Content Generation

1. **Be specific, not generic**:
   - Use actual project name, not "Your Project"
   - Include real commands, not placeholders
   - Reference actual files and directories

2. **Show, don't just tell**:
   - Include runnable code examples
   - Show expected output
   - Demonstrate common use cases

3. **Consider the audience**:
   - Assume basic technical knowledge
   - Explain project-specific concepts
   - Link to external resources for complex topics

4. **Keep it current**:
   - Match code examples to current version
   - Ensure commands work with latest release
   - Update deprecated patterns

### Evaluation

1. **Be objective**:
   - Use clear, measurable criteria
   - Don't penalize different but valid approaches
   - Consider context (library vs application)

2. **Prioritize correctly**:
   - Missing essential sections = critical
   - Poor examples = high
   - Minor formatting = low

3. **Verify claims**:
   - Test installation commands
   - Validate code example syntax
   - Check links are accessible

### Iteration

1. **Make incremental progress**:
   - Don't try to perfect everything in one iteration
   - Focus on highest-impact improvements
   - Build on previous iterations

2. **Track changes**:
   - Log what was changed and why
   - Note score improvements
   - Document remaining issues

3. **Know when to stop**:
   - When quality threshold met
   - When no critical issues remain
   - When changes become marginal

## Common Patterns

### Pattern: Adding Installation Section

```markdown
## Installation

### Via npm

\`\`\`bash
npm install package-name
\`\`\`

### Via yarn

\`\`\`bash
yarn add package-name
\`\`\`

### Manual Installation

Clone and install:

\`\`\`bash
git clone https://github.com/user/repo.git
cd repo
npm install
\`\`\`
```

### Pattern: Creating Usage Section

```markdown
## Usage

### Basic Example

\`\`\`javascript
const package = require('package-name');

// Simple usage
const result = package.doSomething('input');
console.log(result); // Output: processed input
\`\`\`

### Advanced Example

\`\`\`javascript
// Configuration options
const result = package.doSomething('input', {
option1: true,
option2: 'value'
});
\`\`\`
```

### Pattern: API Documentation

```markdown
## API

### `functionName(param1, param2, options)`

Description of what the function does.

**Parameters:**

- `param1` (Type): Description
- `param2` (Type): Description
- `options` (Object, optional): Configuration options
  - `option1` (Boolean): Description
  - `option2` (String): Description

**Returns:** Type - Description

**Example:**

\`\`\`javascript
const result = functionName('value1', 'value2', { option1: true });
\`\`\`
```

## Error Handling

### Issue: Cannot analyze project structure

**Cause**: Unusual project layout or missing key files

**Solution**:

- Prompt user for project type and structure
- Look for additional file patterns
- Fall back to manual input for key details

### Issue: Code examples fail validation

**Cause**: Complex examples with dependencies

**Solution**:

- Simplify examples to core functionality
- Add comments explaining required setup
- Note prerequisites in example

### Issue: Score not improving between iterations

**Cause**: Conflicting requirements or incorrect fixes

**Solution**:

- Review evaluation criteria
- Check if fixes are being applied correctly
- Adjust improvement strategy
- Consider stopping if at local maximum

### Issue: README becomes too long

**Cause**: Too much detail or redundant information

**Solution**:

- Move detailed content to separate docs
- Link to external resources
- Keep main README focused on essentials
- Use collapsible sections for optional content

## Success Metrics

Track these metrics for each README generation:

- **Initial score**: Quality before improvements
- **Final score**: Quality after all iterations
- **Score improvement**: Final - Initial
- **Iterations used**: Number of improvement cycles
- **Critical issues resolved**: Count of critical fixes
- **Sections added**: New sections created
- **Examples added**: Number of code examples added
- **Time to completion**: Total time spent

## References

- [banesullivan/README](https://github.com/banesullivan/README) - README template and best practices
- [Art of README](https://github.com/hackergrrl/art-of-readme) - README writing guide

## Version

1.0.0 - Initial release
