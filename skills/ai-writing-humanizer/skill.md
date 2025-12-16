# AI Writing Humanizer Skill

## Objective

Review text against Wikipedia's "Signs of AI Writing" guidelines using an iterative loop-until-clean
approach. Analyze text for AI writing patterns, propose changes, apply them, and re-analyze until
no patterns remain or maximum iterations reached.

## Prerequisites

Before starting, ensure:

1. You have access to the pattern database in `patterns/patterns.json`
2. You have access to the prompt templates in `prompts/` directory
3. You understand the 15 pattern categories and their priorities
4. You can perform text analysis and pattern matching

## Configuration

The skill supports extensive configuration via `config/default.config.json`:

### Mode Options

| Mode          | Description                                   |
| ------------- | --------------------------------------------- |
| `interactive` | Review each change before applying            |
| `batch`       | Auto-apply changes above confidence threshold |
| `report-only` | Analyze without making changes                |

### Priority Levels

| Priority   | Auto-fix Default       | Examples                      |
| ---------- | ---------------------- | ----------------------------- |
| `critical` | Yes                    | Chatbot artifacts             |
| `high`     | Yes                    | Buzzwords, inflated symbolism |
| `medium`   | No (requires approval) | Em dash overuse, transitions  |
| `low`      | No (requires approval) | Hedge words, formatting       |

### Custom Patterns

Add project-specific patterns by creating a custom patterns file and setting `custom_patterns_file`
in config.

### Technical Terms Allowlist

The `patterns/technical-terms-allowlist.json` file contains established technical terminology that
should not be flagged when used in proper context (e.g., "Kubernetes ecosystem", "financial
leverage").

## Core Algorithm

```pseudocode
function humanize_text(input_text, max_iterations=5):
    iteration = 0
    current_text = input_text
    all_changes = []

    while iteration < max_iterations:
        iteration++

        # Step 1: Analyze current text
        issues = analyze_for_ai_patterns(current_text)

        # Step 2: Check if clean
        if issues.length == 0:
            return {
                status: "clean",
                text: current_text,
                iterations: iteration,
                changes_made: all_changes
            }

        # Step 3: Generate suggestions for each issue
        suggestions = generate_suggestions(issues, current_text)

        # Step 4: Get approval (interactive) or auto-apply (batch)
        approved_changes = get_approval(suggestions, mode)

        # Step 5: Apply changes
        current_text = apply_changes(current_text, approved_changes)
        all_changes.append(approved_changes)

        # Step 6: Log iteration
        log_iteration(iteration, issues, approved_changes)

    # Max iterations reached
    remaining_issues = analyze_for_ai_patterns(current_text)
    return {
        status: "max_iterations_reached",
        text: current_text,
        iterations: iteration,
        changes_made: all_changes,
        remaining_issues: remaining_issues
    }
```

## Step-by-Step Workflow

### Phase 1: Input Processing and Setup

#### Step 1.1: Accept Input

Accept text from one of these sources:

- Direct text input from user
- File path to read
- Clipboard content
- URL to fetch (if supported)

#### Step 1.2: Configure Options

Determine mode and settings:

```json
{
  "mode": "interactive|batch|report-only",
  "max_iterations": 5,
  "auto_fix_priority": ["critical", "high"],
  "require_approval_for": ["medium", "low"],
  "strict_mode": false,
  "categories_to_check": ["all"],
  "output_format": "markdown"
}
```

#### Step 1.3: Initialize State

```json
{
  "original_text": "...",
  "current_text": "...",
  "iteration": 0,
  "changes_log": [],
  "word_count": 0
}
```

### Phase 2: Pattern Analysis (First Iteration)

#### Step 2.1: Load Pattern Database

Load patterns from `patterns/patterns.json`. Organize by priority:

- Critical: Chatbot artifacts
- High: Promotional, buzzwords, inflated symbolism, etc.
- Medium: Frequency-based patterns, weasel words
- Low: Hedge words, formatting

#### Step 2.2: Analyze Text Using Analysis Prompt

Use the prompt template from `prompts/analysis-prompt.md`. For each category:

1. **Simple pattern matching** (buzzwords, filler phrases)
   - Search for exact matches (case-insensitive)
   - Record location (paragraph, sentence)
   - Capture surrounding context

2. **Regex pattern matching** (negative parallelism, participle endings)
   - Apply regex patterns
   - Extract matched groups
   - Validate matches in context

3. **Frequency-based detection** (transitions, em dashes, hedge words)
   - Count occurrences
   - Calculate frequency per threshold (e.g., per 500 words)
   - Flag if exceeds threshold

4. **Structural analysis** (rule of three, formatting)
   - Detect patterns in document structure
   - Count repeated structures
   - Flag excessive use

#### Step 2.3: Generate Analysis Report

Output format:

```json
{
  "issues": [
    {
      "id": 1,
      "category": "Chatbot Artifacts",
      "priority": "critical",
      "pattern_matched": "I hope this helps",
      "location": "paragraph 1, sentence 5",
      "context": "...all the necessary information. I hope this helps with your project.",
      "suggested_action": "delete",
      "suggested_replacement": null
    },
    {
      "id": 2,
      "category": "Buzzwords",
      "priority": "high",
      "pattern_matched": "leverage",
      "location": "paragraph 2, sentence 3",
      "context": "The system can leverage advanced algorithms to...",
      "suggested_action": "replace",
      "suggested_replacement": "use"
    }
  ],
  "summary": {
    "total_issues": 15,
    "critical": 1,
    "high": 9,
    "medium": 3,
    "low": 2,
    "word_count": 450
  }
}
```

#### Step 2.4: Present Analysis to User

Format issues for display:

```markdown
## Analysis Results - Iteration 1

Found 15 AI writing patterns:

### Critical Priority (1 issue)

- **Chatbot Artifact** (paragraph 1, sentence 5): "I hope this helps"
  → Suggested action: Delete

### High Priority (9 issues)

- **Buzzword** (paragraph 2, sentence 3): "leverage"
  → Suggested replacement: "use"
- **Inflated Symbolism** (paragraph 3, sentence 1): "stands as a testament"
  → Suggested replacement: "demonstrates"
  ...
```

### Phase 3: Suggestion Generation

#### Step 3.1: Load Suggestion Prompt

Use template from `prompts/suggestion-prompt.md`.

#### Step 3.2: Generate Context-Aware Replacements

For each issue:

1. **Analyze context**
   - Read 1-2 sentences before and after
   - Identify tone and style
   - Check for technical vs general usage

2. **Apply category-specific strategy**
   - **Inflated symbolism**: Deflate ("testament" → "shows")
   - **Promotional language**: Neutralize ("breathtaking" → "impressive")
   - **Editorializing**: Delete ("important to note" → delete)
   - **Buzzwords**: Simplify ("leverage" → "use")
   - **Participle endings**: Trim (", ensuring..." → delete)
   - **Negative parallelism**: Direct statement
   - **Filler phrases**: Delete entirely

3. **Generate replacement options**
   - Primary suggestion (highest confidence)
   - Alternative suggestions (if applicable)
   - Confidence level (high, medium, low)

4. **Validate replacement**
   - Preserves meaning
   - Grammatically correct
   - Sounds natural
   - Consistent tone

#### Step 3.3: Output Suggestions

```json
{
  "replacements": [
    {
      "issue_id": 1,
      "original": "I hope this helps",
      "replacement": null,
      "action": "delete",
      "confidence": "high",
      "explanation": "Chatbot artifact with no informational value"
    },
    {
      "issue_id": 2,
      "original": "leverage",
      "replacement": "use",
      "action": "replace",
      "confidence": "high",
      "explanation": "Buzzword with simple direct alternative"
    },
    {
      "issue_id": 3,
      "original": "It's not just a tool, but a comprehensive solution",
      "replacement": "The tool is a comprehensive solution",
      "action": "rephrase",
      "confidence": "medium",
      "explanation": "Removed negative parallelism while preserving meaning"
    }
  ]
}
```

### Phase 4: Change Application

#### Step 4.1: Present Changes for Approval (Interactive Mode)

For each issue (grouped by paragraph):

```markdown
### Paragraph 2, Sentence 3

**Current**: "The system can leverage advanced algorithms to process data."

**Issue**: Buzzword - "leverage"

**Suggested change**: Replace with "use"

**Result**: "The system can use advanced algorithms to process data."

Options:
[A] Accept this change
[E] Edit the replacement
[S] Skip this change
[Q] Quit interactive mode (apply remaining automatically)
```

#### Step 4.2: Auto-Apply Changes (Batch Mode)

Automatically apply changes based on:

- Priority level (critical and high by default)
- Confidence level (high confidence only)
- Category settings (user-configured)

#### Step 4.3: Apply Approved Changes

Apply changes in order (from end to beginning to preserve positions):

1. Sort changes by position (reverse order)
2. For each change:
   - Locate exact text
   - Apply replacement or deletion
   - Verify grammar after change
3. Update current_text
4. Log change with before/after

#### Step 4.4: Update Change Log

```json
{
  "iteration": 1,
  "changes": [
    {
      "location": "paragraph 1, sentence 5",
      "category": "Chatbot Artifacts",
      "original": "I hope this helps",
      "replacement": null,
      "action": "delete"
    },
    {
      "location": "paragraph 2, sentence 3",
      "category": "Buzzwords",
      "original": "leverage",
      "replacement": "use",
      "action": "replace"
    }
  ]
}
```

### Phase 5: Re-Analysis Loop

#### Step 5.1: Increment Iteration Counter

```pseudocode
iteration++
```

#### Step 5.2: Re-Run Pattern Analysis

Using the same analysis process as Phase 2, scan the modified text for:

1. **Remaining original issues**
   - Issues that weren't fixed
   - Issues that were skipped

2. **New issues introduced**
   - Check if replacements created new patterns
   - Verify grammar correctness

3. **Missed issues**
   - Patterns that were hidden by other patterns
   - Issues that become visible after changes

#### Step 5.3: Check Termination Conditions

```pseudocode
if (issues.length == 0) {
    # SUCCESS: Text is clean
    proceed to Phase 6
}

if (iteration >= max_iterations) {
    # MAX ITERATIONS: Stop with remaining issues
    proceed to Phase 6
}

if (no progress made) {
    # STALLED: Same issues remain
    proceed to Phase 6
}

# Otherwise, continue loop
goto Phase 3 (Suggestion Generation)
```

### Phase 6: Verification and Final Report

#### Step 6.1: Final Verification

Use prompt from `prompts/verification-prompt.md`:

1. **Pattern check**: Verify all 15 categories clean
2. **Grammar check**: Ensure no errors introduced
3. **Coherence check**: Text flows naturally
4. **Meaning check**: Original intent preserved

#### Step 6.2: Generate Final Report

```markdown
# AI Writing Humanizer Report

## Summary

- **Status**: Clean / Issues Remaining
- **Iterations**: 3
- **Total changes**: 15
- **Word count**: 450 words

## Statistics

- Critical issues fixed: 1
- High priority issues fixed: 9
- Medium priority issues fixed: 3
- Low priority issues fixed: 2

## Changes by Category

### Chatbot Artifacts (1)

- Removed "I hope this helps"

### Buzzwords (6)

- "leverage" → "use"
- "utilize" → "use"
- "cutting-edge" → "modern"
- "ecosystem" → "system"
- "facilitate" → "help"
- "delve into" → "examine"

### Inflated Symbolism (3)

- "stands as a testament" → "demonstrates"
- "plays a vital role" → "is important for"
- "watershed moment" → "turning point"

### Participle Endings (2)

- Removed ", highlighting its importance"
- Removed ", ensuring quality"

### Filler Phrases (1)

- Removed "In today's ever-evolving world"

### Editorializing (2)

- Removed "It's important to note that"
- Removed "Worth mentioning is that"

## Before and After

### Before (excerpt)

"In today's ever-evolving world, the platform stands as a testament to innovation. It's not just
a tool, but a revolutionary ecosystem that leverages cutting-edge technology, ensuring seamless
integration. I hope this helps!"

### After

"The platform demonstrates innovation. The revolutionary system uses modern technology and
integrates smoothly."

## Verification Results

✓ All critical patterns removed
✓ All high-priority patterns addressed
✓ Grammar is correct
✓ Meaning preserved
✓ Natural tone achieved

## Remaining Issues

None - text is clean.

## Recommendations

Text is ready for publication. No further iterations needed.
```

## Advanced Features

### Chunking for Long Documents

For documents >5000 words:

1. Split into logical chunks (by section/heading)
2. Process each chunk independently
3. Verify transitions between chunks
4. Combine results

### Confidence Thresholds

Adjust auto-apply based on confidence:

- **High confidence**: Simple word swaps, obvious deletions
- **Medium confidence**: Phrase replacements, minor rephrasing
- **Low confidence**: Complex restructuring, context-dependent

### Custom Pattern Addition

Allow users to add custom patterns:

```json
{
  "pattern": "synergize",
  "type": "word",
  "category": "Buzzwords",
  "priority": "high",
  "replacements": ["combine", "work together"]
}
```

### Batch Processing Multiple Files

Process multiple files sequentially or in parallel:

1. Load all files
2. Process each with same settings
3. Generate individual reports
4. Create summary report

## Configuration Options Reference

### Mode Options

**Interactive Mode**:

- Present each issue for review
- Allow editing of suggestions
- Maximum control, slower process

**Batch Mode**:

- Auto-apply high-confidence changes
- Present summary of changes
- Faster process, less control

**Report-Only Mode**:

- Analyze without changes
- Generate detailed report
- No modifications made

### Priority Settings

```json
{
  "auto_fix_priority": ["critical", "high"],
  "require_approval_for": ["medium", "low"]
}
```

### Category Filters

```json
{
  "categories_to_check": [
    "chatbot-artifacts",
    "buzzwords",
    "inflated-symbolism"
  ],
  "categories_to_skip": ["hedge-words", "formatting-patterns"]
}
```

### Strictness Levels

**Normal**: Follow standard thresholds

**Strict**: Lower thresholds, flag more aggressively

```json
{
  "strict_mode": true,
  "strict_thresholds": {
    "em_dash": 1,
    "transitions": 1,
    "hedge_words": 2
  }
}
```

## Error Handling

### Pattern Matching Errors

If pattern matching fails:

1. Log the error
2. Skip that pattern
3. Continue with other patterns
4. Note in final report

### Replacement Errors

If replacement introduces grammar errors:

1. Detect via grammar check
2. Revert that specific change
3. Mark for manual review
4. Continue with other changes

### Iteration Stalling

If same issues remain after iteration:

1. Check if issues are false positives
2. Mark for manual review
3. Terminate loop early
4. Report stalled issues

## Quality Assurance

Before finalizing:

1. **Grammar check**: Run grammar validation
2. **Spell check**: Verify spelling
3. **Coherence check**: Read full text for flow
4. **Fact check**: Verify meaning preserved
5. **Pattern check**: Final scan for missed patterns

## Success Metrics

Track these metrics:

- Issues found per iteration
- Changes applied per iteration
- Iterations required to clean
- Confidence levels of changes
- False positive rate
- User approval rate (interactive mode)

## Best Practices

1. **Start with analysis**: Run report-only first to understand scope
2. **Review critically**: Some patterns may be acceptable in context
3. **Preserve technical accuracy**: Don't over-simplify technical terms
4. **Maintain voice**: Keep consistent tone and style
5. **Verify meaning**: Always check that information is preserved
6. **Iterate as needed**: Don't stop after one pass if issues remain
7. **Document changes**: Keep detailed logs for transparency

## Limitations and Considerations

- **Not foolproof**: Some AI patterns may be missed
- **Context matters**: Some flagged patterns may be acceptable
- **Technical terms**: May flag legitimate jargon
- **False positives**: Manual review recommended for critical content
- **Meaning preservation**: Prioritizes meaning over pattern removal
- **Style consistency**: May require manual adjustment for specific style guides

## Integration Points

This skill works well with:

- Text editors and IDEs
- Content management systems
- Documentation platforms
- Markdown processors
- Writing assistants

## Version History

**1.0.0** (2025-12-16)

- Initial release
- 15 pattern categories
- 200+ specific patterns
- Iterative refinement workflow
- Interactive and batch modes
- Comprehensive verification
