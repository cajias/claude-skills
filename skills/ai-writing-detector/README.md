# AI Writing Detector

Detect signs of AI-generated writing in text documents with detailed analysis and reporting.

## Overview

This skill analyzes text for patterns commonly found in AI-generated content, providing a
comprehensive detection report with confidence scoring. Unlike the **ai-writing-humanizer** skill
which iteratively fixes issues, this skill focuses on **detection and reporting** to help you
understand the scope and nature of AI writing patterns present.

## What It Does

1. **Scans** for technical artifacts (definitive AI markers)
2. **Analyzes** content structure and language patterns
3. **Counts** AI vocabulary density and frequency-based indicators
4. **Calculates** confidence score across multiple categories
5. **Reports** detailed findings with specific line references
6. **Warns** about false positives and context considerations

## When to Use

Use this skill when you need to:

- Audit text for AI-generated content
- Understand the extent of AI patterns in a document
- Get a detailed breakdown of specific AI writing indicators
- Verify whether edited text still contains AI patterns
- Review submissions that may be AI-generated
- Assess content before publication

**Note**: This is an analysis tool, not a content moderation weapon. Use it responsibly with
awareness of its limitations.

## Key Features

### Comprehensive Pattern Detection

- **Technical Artifacts** (Definitive): Chatbot markers, model tokens, placeholder text
- **Content Issues**: Undue emphasis, superficial analysis, promotional language
- **Language Patterns**: AI vocabulary, negative parallelisms, weasel words
- **Style Issues**: Formatting quirks, em dash overuse, markdown artifacts

### Weighted Confidence Scoring

- Definitive markers: 50% weight
- Content issues: 20% weight
- Language patterns: 15% weight
- Style issues: 10% weight
- Behavioral indicators: 5% weight

### Context-Aware Analysis

- Adjusts thresholds for technical documentation
- Considers academic writing conventions
- Recognizes legitimate marketing language
- Accounts for genre-specific patterns

### False Positive Protection

- Explicitly warns about unreliable indicators
- Notes that perfect grammar is NOT an AI sign
- Explains that fancy vocabulary suggests human authorship
- Reminds about 10% expert false positive rate

## Quick Start

### Basic Usage

```text
Use the AI Writing Detector skill to analyze this text for AI-generated content:

[Paste your text here]
```

### Request Specific Report

```text
Analyze this article for AI writing patterns and provide a detailed detection report:

[Your text]
```

### Compare Before/After

```text
I've edited this text. Can you check if AI patterns are still present?

[Your edited text]
```

## Detection Categories

### 1. Technical Artifacts (DEFINITIVE)

#### Critical - Smoking Gun Evidence

- ChatGPT markers: `turn0search0`, citation formats
- Knowledge cutoff disclaimers
- Chatbot artifacts: "I hope this helps", "As an AI"
- Placeholder text: `[Insert Name]`, `2025-xx-xx`
- Model tokens: `<|endoftext|>`

#### If ANY found → HIGH confidence automatically

### 2. Content Issues

#### Patterns in content structure and claims

- Undue emphasis on symbolism/legacy
- Promotional/travel brochure language
- Didactic disclaimers: "It's important to note"
- Section summaries and conclusions
- "Challenges and Future Prospects" formula
- Superficial analyses with empty phrases

### 3. Language Patterns

#### AI vocabulary and linguistic quirks

- High-frequency AI words: delve, leverage, pivotal, seamless, testament
- Negative parallelisms: "not just X but Y"
- Weasel words: "experts believe" (uncited)
- Rule of three overuse
- Density threshold: >5 AI words per 500 words

### 4. Style and Formatting

#### Formatting and stylistic markers

- Title Case Headers
- Excessive bold text (>3 per paragraph)
- Em dash overuse (>2 per 500 words)
- Inline-header lists: "1. **Topic:** Description"
- Markdown in plain text context

## Confidence Levels

### High (70-100%)

- **Definitive marker found**, OR
- Very high AI vocabulary density (>10 per 500 words), OR
- Multiple patterns across all categories

**Action**: Strong indicators of AI generation

### Medium (40-69%)

- Multiple patterns in 2-3 categories
- Moderate AI vocabulary density (5-10 per 500 words)
- No definitive markers

**Action**: Warrants review, may need editing

### Low (20-39%)

- Few scattered patterns
- Below vocabulary threshold
- Context-dependent findings

**Action**: Patterns may be coincidental

### None (0-19%)

- Minimal or no AI indicators
- Characteristics consistent with human writing

**Action**: No concerns detected

## Important Caveats

### ⚠️ Critical Limitations

This skill comes with important limitations:

- These are **potential signs**, not definitive proof (except technical artifacts)
- Many patterns existed in human writing before LLMs
- **False accusations harm collaboration and trust**
- Context matters - consider the full picture
- **Do NOT solely rely on AI detection tools** - they have significant error rates
- **Experts correctly identify AI ~90% of time** (10% false accusations)
- **Non-experts do barely better than random chance**
- **When in doubt, assume human authorship**

### What NOT to Flag

The skill explicitly avoids these false positives:

- Perfect grammar (skilled writers exist)
- Bland/robotic prose (LLMs are actually effusive)
- Fancy/academic words (LLMs favor common words)
- Formal writing style
- Use of conjunctions
- Low-frequency unusual words
- Lists and structured formatting

## Report Structure

Each detection report includes:

1. **Summary** - Confidence level, issue count, word count
2. **Important Caveats** - Limitations and warnings
3. **Definitive Markers** - Technical artifacts (if any)
4. **Content Issues** - Detailed breakdown by subcategory
5. **Language Patterns** - AI vocabulary analysis with density
6. **Style Issues** - Formatting and punctuation patterns
7. **Confidence Breakdown** - Weighted scoring table
8. **False Positive Warnings** - Context-dependent considerations
9. **Recommendations** - Next steps based on findings
10. **Optional Fix Suggestions** - Specific rewrites (if requested)

## Examples

See the `examples/` directory for:

- **sample-report.md** - Complete detection report example
- **false-positive-examples.md** - Cases that look like AI but aren't

## Relationship to AI Writing Humanizer

These skills are complementary:

| Aspect       | ai-writing-detector         | ai-writing-humanizer     |
| ------------ | --------------------------- | ------------------------ |
| **Purpose**  | Detect and report           | Fix iteratively          |
| **Output**   | Detection report            | Cleaned text             |
| **Workflow** | Single-pass analysis        | Loop until clean         |
| **Changes**  | No modifications            | Applies changes          |
| **Use case** | Audit, review, verification | Transform and clean text |

### Recommended Workflow

1. **Detector** → Audit text and understand scope
2. Review detection report and decide if changes needed
3. **Humanizer** → Fix detected issues iteratively
4. **Detector** → Verify fixes successful and patterns removed

## Configuration

The skill uses pattern databases in `patterns/`:

- `content-patterns.json` - Content-level patterns (1.1-1.9)
- `language-patterns.json` - Language patterns (2.1-2.6)
- `style-patterns.json` - Style and formatting (3.1-3.7)
- `artifact-patterns.json` - Definitive markers (4.1-4.11)
- `false-positives.json` - Patterns to avoid flagging (6.1-6.10)

## Limitations

- **Not foolproof**: Some AI patterns may be missed
- **Context dependent**: Patterns may be legitimate in certain genres
- **Single-pass**: Unlike humanizer, doesn't iterate
- **Report only**: Doesn't make changes (use humanizer for that)
- **Requires judgment**: Human review recommended for important decisions
- **False positives**: Even experts have 10% error rate

## Best Practices

1. **Use multiple indicators**: Never rely on single pattern
2. **Consider context**: Adjust interpretation for document type
3. **Prioritize definitive markers**: Focus on technical artifacts
4. **Be humble**: Acknowledge detection uncertainty
5. **Combine with humanizer**: Use detector before and after humanizer
6. **Avoid weaponization**: This is an analysis tool, not a judgment tool
7. **Document assumptions**: Note any context-specific considerations

## References

- [Wikipedia: Signs of AI Writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
- [How to Spot AI Writing (The Decoder)](https://the-decoder.com/heres-how-to-spot-ai-writing-according-to-wikipedia-editors/)
- Existing **ai-writing-humanizer** skill in this repo

## Version

1.0.0 - Initial release with comprehensive pattern detection and confidence scoring
