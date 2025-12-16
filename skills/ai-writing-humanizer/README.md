# AI Writing Humanizer Skill

Transform AI-generated text into natural, human-sounding writing through iterative pattern
detection and replacement.

## Overview

This skill implements a comprehensive loop-until-clean approach to identify and remove telltale
signs of AI-generated writing. It analyzes text against 15 categories of AI writing patterns,
proposes human-friendly replacements, applies changes, and re-analyzes until the text passes all
checks.

## What It Does

1. **Analyzes** text against comprehensive AI writing pattern database
2. **Identifies** all matches with specific locations and context
3. **Proposes** human-friendly replacements for each issue
4. **Applies** changes with user approval (interactive mode) or automatically (batch mode)
5. **Re-analyzes** the modified text to verify all patterns removed
6. **Iterates** until text is clean or maximum iterations reached

## When to Use

Use this skill when you need to:

- Make AI-generated text sound more natural and human-written
- Remove promotional language and buzzwords from marketing copy
- Eliminate editorializing phrases from encyclopedic or technical writing
- Clean up chatbot artifacts from AI-generated content
- Prepare AI-assisted text for publication or professional use
- Comply with guidelines that restrict or discourage AI-generated content
- Improve text quality by removing vague, inflated, or meaningless phrases

## Pattern Categories

The skill checks for **15 comprehensive categories** of AI writing patterns:

### Critical Priority

- **Chatbot Artifacts**: Direct giveaways like "I hope this helps", "As an AI", "Certainly!"

### High Priority

- **Inflated Symbolism**: "testament", "vital role", "watershed moment"
- **Promotional Language**: "breathtaking", "rich heritage", "world-class"
- **Editorializing**: "important to note", "worth noting"
- **Buzzwords**: "delve", "leverage", "cutting-edge", "ecosystem"
- **Participle Endings**: ", highlighting...", ", ensuring..."
- **Filler Phrases**: "In today's ever-evolving world", "In conclusion"
- **Negative Parallelism**: "not just X, but Y"

### Medium Priority

- **Transition Overuse**: "moreover", "furthermore" (frequency-based)
- **Weasel Words**: "experts say", "studies show" (without citations)
- **Em Dash Overuse**: Excessive use of — in text
- **Rule of Three**: Overuse of three-item lists
- **Section Conclusions**: Generic closing statements

### Low Priority

- **Hedge Words**: Overuse of "arguably", "potentially", "perhaps"
- **Formatting Patterns**: Title case headers, excessive bolding

## Key Features

### Comprehensive Pattern Database

- **200+ specific patterns** across 15 categories
- Based on Wikipedia's "Signs of AI Writing" guidelines
- Regular expression support for flexible matching
- Frequency-based detection for context-dependent patterns
- Priority-ranked for efficient processing

### Iterative Refinement

- Analyzes text in multiple passes
- Each iteration removes more patterns
- Continues until text is clean or max iterations reached
- Tracks all changes for transparency

### Context-Aware Replacements

- Considers surrounding text when suggesting replacements
- Preserves meaning and factual accuracy
- Maintains consistent tone and style
- Provides multiple alternatives when appropriate

### Interactive and Batch Modes

- **Interactive**: Review and approve each change individually
- **Batch**: Automatically apply high-confidence changes
- **Report-only**: Analyze without making changes

## Quick Start

### Basic Usage

Provide text and request humanization:

````text
I have some AI-generated text that needs to sound more natural. Can you use the AI Writing
Humanizer skill to clean it up?

[Your text here]
```text

### Specify Mode

```text
Use the AI Writing Humanizer in batch mode to automatically fix all high-priority issues in this
text:

[Your text here]
```text

### Analysis Only

```text
Analyze this text for AI writing patterns but don't make changes yet:

[Your text here]
```text

## Workflow Phases

### Phase 1: Input Processing

- Accept text (direct input, file, or clipboard)
- Normalize formatting
- Split long documents if needed (>5000 words)

### Phase 2: Pattern Analysis

- Load pattern database
- Scan text for all pattern categories
- Record matches with locations
- Prioritize by severity

### Phase 3: Suggestion Generation

- Generate replacement for each issue
- Consider context and surrounding text
- Provide confidence levels
- Flag cases needing human judgment

### Phase 4: Change Application

- Present issues (grouped by paragraph in interactive mode)
- Apply approved changes
- Maintain detailed change log
- Update text incrementally

### Phase 5: Re-Analysis Loop

- Re-scan modified text
- Check for remaining issues
- Verify no new issues introduced
- Continue until clean or max iterations

### Phase 6: Final Report

- Summary statistics
- All changes made with explanations
- Before/after comparison
- Confidence assessment

## Configuration Options

The skill supports extensive configuration via `config/default.config.json`:

### Core Settings

- **Mode**: interactive, batch, or report-only
- **Max iterations**: Typically 3-5 passes (configurable 1-10)
- **Auto-fix priority**: Which levels to apply automatically (default: critical, high)
- **Require approval**: Which levels need manual review (default: medium, low)
- **Strict mode**: More aggressive pattern detection
- **Min confidence**: Minimum confidence score to report issues (0.0-1.0)
- **Output format**: Markdown, JSON, diff, or HTML

### Advanced Options

- **Categories to skip**: Exclude specific pattern categories from analysis
- **Custom patterns file**: Path to additional project-specific patterns
- **Preserve technical terms**: Use allowlist for established technical terminology
- **Technical terms allowlist**: See `patterns/technical-terms-allowlist.json` for terms
  like "Kubernetes ecosystem", "financial leverage" that are legitimate in context

See `config/config.schema.json` for complete configuration schema and validation.

## Success Criteria

Text passes verification when:

- ✓ No chatbot artifacts remain
- ✓ No promotional language detected
- ✓ No inflated symbolism phrases
- ✓ Reasonable punctuation usage
- ✓ No weasel wording without citations
- ✓ No superficial participle endings
- ✓ Varied sentence structure
- ✓ Grammar and coherence maintained
- ✓ Original meaning preserved

## Examples

See the `examples/` directory for:

- **example-workflow.md**: Complete walkthrough with sample text
- **before-after-samples.md**: Side-by-side comparisons
- **edge-cases.md**: Tricky scenarios and solutions

## Limitations

- **Not a content generator**: Only improves existing text, doesn't create new content
- **Context-dependent**: Some patterns are acceptable in certain contexts
- **Iterative process**: May require multiple passes for heavily AI-written text
- **Human judgment**: Some cases require manual review and decision
- **Meaning preservation**: Prioritizes keeping original meaning, which may limit changes
- **Technical terms**: May flag legitimate technical jargon as buzzwords

## Related Skills

- **GitHub Issue Grooming**: For organizing project issues
- **Software Effort Estimation**: For codebase analysis

## References

- [Wikipedia: Signs of AI Writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
- [How to Spot AI Writing (The Decoder)](https://the-decoder.com/heres-how-to-spot-ai-writing-according-to-wikipedia-editors/)
- [Words to Avoid (AiSDR)](https://aisdr.com/blog/words-to-avoid-so-you-dont-sound-like-ai/)
- [Wikipedia AI Writing Takeaways (Blake Stockton)](https://www.blakestockton.com/takeaways-from-wikipedias-signs-of-ai-writing-2/)

## Version

1.0.0 - Initial release with 15 pattern categories and iterative refinement workflow
````
