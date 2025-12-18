# AI Writing Detector Skill

## Objective

Detect signs of AI-generated writing in text documents and provide detailed analysis reports with
confidence scoring. This skill focuses on **detection and reporting** rather than fixing, making it
complementary to the **ai-writing-humanizer** skill.

## Prerequisites

Before starting, ensure:

1. You have access to the pattern databases in `patterns/` directory
2. You have access to the prompt templates in `prompts/` directory
3. You understand the 6 major detection categories
4. You can perform pattern matching and frequency analysis

## Important Caveats

**Always** include these warnings when using this skill:

- These are **potential signs**, not definitive proof (except technical artifacts)
- Many patterns existed in human writing before LLMs
- **False accusations harm collaboration and trust**
- Context matters - consider the full picture
- **Do NOT solely rely on AI detection tools** - they have significant error rates
- **Experts correctly identify AI ~90% of time** (10% false positives)
- **Non-experts do barely better than random chance**
- **When in doubt, assume human authorship**

## Core Detection Algorithm

```pseudocode
function detect_ai_writing(input_text):
    # Step 1: Scan for definitive markers
    definitive_markers = scan_technical_artifacts(input_text)
    if definitive_markers.length > 0:
        confidence = "HIGH"
        # Continue analysis for full report

    # Step 2: Count AI vocabulary
    ai_vocab = count_ai_vocabulary(input_text)
    vocab_density = calculate_density(ai_vocab, word_count)

    # Step 3: Analyze content structure
    content_issues = analyze_content_patterns(input_text)

    # Step 4: Examine language patterns
    language_patterns = analyze_language(input_text)

    # Step 5: Review style and formatting
    style_issues = analyze_style(input_text)

    # Step 6: Calculate confidence score
    confidence_score = calculate_weighted_score({
        definitive_markers: 50%,
        content_issues: 20%,
        language_patterns: 15%,
        style_issues: 10%,
        behavioral: 5%
    })

    # Step 7: Generate report
    report = generate_detection_report({
        confidence: confidence_score,
        definitive_markers: definitive_markers,
        content_issues: content_issues,
        language_patterns: language_patterns,
        style_issues: style_issues,
        false_positive_warnings: check_context(input_text),
        recommendations: generate_recommendations(confidence_score)
    })

    return report
```

## Step-by-Step Workflow

### Phase 1: Input Processing and Initialization

#### Step 1.1: Accept Input Text

Accept text from one of these sources:

- Direct text input from user
- File path to read
- Clipboard content
- URL to fetch (if supported)

#### Step 1.2: Initialize Analysis State

```json
{
  "text": "...",
  "word_count": 0,
  "findings": {
    "definitive_markers": [],
    "content_issues": [],
    "language_patterns": [],
    "style_issues": [],
    "behavioral_indicators": []
  },
  "metadata": {
    "analysis_date": "2025-12-18",
    "skill_version": "1.0.0"
  }
}
```

#### Step 1.3: Load Pattern Databases

Load all pattern files:

- `patterns/content-patterns.json` (categories 1.1-1.9)
- `patterns/language-patterns.json` (categories 2.1-2.6)
- `patterns/style-patterns.json` (categories 3.1-3.7)
- `patterns/artifact-patterns.json` (category 4.1-4.11)
- `patterns/false-positives.json` (category 6.1-6.10)

### Phase 2: Technical Artifact Detection (Definitive Markers)

#### Step 2.1: Scan for ChatGPT Artifacts

From `patterns/artifact-patterns.json`, section 4.1:

- `turn0search0`, `turn0image0`, `turn\d+search\d+`
- `:contentReference[oaicite:\d+]{index=\d+}`
- `[oai_citation:\d+‡...]`

**If found**: Set confidence to HIGH immediately. This is definitive proof.

#### Step 2.2: Scan for Other AI System Markers

- **Grok**: `<grok_card>` tags
- **UTM parameters**: `utm_source=chatgpt.com`, `utm_source=claude.ai`
- **Model tokens**: `<|endoftext|>`, `<|im_end|>`

#### Step 2.3: Check for Knowledge Cutoff Disclaimers

- "as of my last knowledge update"
- "as of my knowledge cutoff"
- "my training data ends/cuts off"
- "based on my training"

#### Step 2.4: Check for Prompt Refusals

- "as an AI language model, I can't"
- "as an AI, I don't/cannot/can't"
- "I'm (just) an AI"
- "as a language model"

#### Step 2.5: Check for Placeholder Text

- `[Entertainer's Name]`, `[Your Name]`, `[Insert ...]`
- Date placeholders: `2025-xx-xx`
- `[TBD]`

#### Step 2.6: Check for Collaborative Artifacts

- "would you like me to"
- "shall I continue/proceed/elaborate"
- "let me know if you'd like"
- "I hope this helps"
- "feel free to ask"

#### Step 2.7: Record Definitive Findings

```json
{
  "definitive_markers": [
    {
      "type": "Collaborative Artifact",
      "pattern": "I hope this helps",
      "location": "line 45",
      "context": "...explain the concept. I hope this helps with your project.",
      "confidence": "definitive",
      "severity": "critical"
    }
  ]
}
```

**Result**: If ANY definitive marker found, set overall confidence to HIGH (≥70%).

### Phase 3: AI Vocabulary Analysis

#### Step 3.1: Count High-Frequency AI Verbs

From `patterns/language-patterns.json`, section 2.1:

Count occurrences of:

- delve, underscore, highlight, emphasize, showcase, leverage, navigate, foster, spearhead,
  bolster, fortify, grapple, hone, underpin, broaden, elevate, streamline, harness

#### Step 3.2: Count High-Frequency AI Adjectives

- crucial, pivotal, intricate, nuanced, comprehensive, multifaceted, robust, innovative, seamless,
  holistic, groundbreaking, cutting-edge, meticulous, versatile, dynamic

#### Step 3.3: Count High-Frequency AI Nouns

- tapestry, landscape (metaphorical), paradigm, realm, synergy, trajectory, cornerstone, catalyst,
  beacon, testament, hallmark, confluence, nexus, mosaic, bedrock

#### Step 3.4: Count High-Frequency AI Phrases

- "rich tapestry", "broader landscape", "key/integral/pivotal role", "a testament to", "poised to",
  "at the forefront"

#### Step 3.5: Calculate Density

```javascript
total_ai_words = verbs + adjectives + nouns + phrases;
words_per_500 = (total_ai_words / word_count) * 500;

// Thresholds
if (words_per_500 > 10) {
  vocab_flag = "HIGH";
} else if (words_per_500 > 5) {
  vocab_flag = "MEDIUM";
} else {
  vocab_flag = "ACCEPTABLE";
}
```

#### Step 3.6: Generate Vocabulary Report

```json
{
  "ai_vocabulary": {
    "total_count": 18,
    "density_per_500": 10.1,
    "threshold": 5,
    "status": "HIGH",
    "breakdown": {
      "verbs": ["leverage: 2", "streamline: 1", "foster: 1"],
      "adjectives": ["pivotal: 3", "cutting-edge: 1", "robust: 2"],
      "nouns": ["paradigm: 1", "ecosystem: 2"],
      "phrases": ["testament to: 1", "crucial role: 1"]
    }
  }
}
```

### Phase 4: Content Pattern Analysis

#### Step 4.1: Check Undue Emphasis (1.1)

From `patterns/content-patterns.json`:

- "marking a pivotal moment"
- "represents a significant shift"
- "highlighting the enduring legacy"
- "reflects the transformative power"
- "vital not only for X but also for Y"

#### Step 4.2: Check Notability Emphasis (1.2)

- Media outlets listed without context
- "maintains an active social media presence"

#### Step 4.3: Check Superficial Analyses (1.3)

- "highlighting its significance as"
- "underscoring its role in"
- "emphasizing the importance of"
- Inanimate subjects doing "highlighting" or "underscoring"

#### Step 4.4: Check Promotional Language (1.4)

- "nestled within the breathtaking"
- "offers visitors a fascinating glimpse"
- "seamlessly connecting"
- "showcasing the [adj] rich heritage"

#### Step 4.5: Check Didactic Disclaimers (1.5)

- "It's important to note that"
- "It is crucial to differentiate"
- "However, it should be noted"

**Action**: Flag for deletion

#### Step 4.6: Check Section Summaries (1.6)

- "In summary," at paragraph ends
- Generic concluding statements

#### Step 4.7: Check Challenges/Future Formula (1.7)

- Pattern: "Despite its [positive], X faces challenges..."
- Pattern: "Future investments could enhance..."
- Structural: Check for separate "Challenges" AND "Future Prospects" sections

#### Step 4.8: Check Titles as Proper Nouns (1.8)

- "The 'Effects of X on Y' refers to..."
- "The 'List of X' is a curated compilation..."

#### Step 4.9: Check Negative Outlines (1.9)

- "No X. No Y. Just Z."
- "Not a X, not a Y — just Z"

#### Step 4.10: Record Content Findings

```json
{
  "content_issues": [
    {
      "subcategory": "1.5 - Didactic Disclaimers",
      "location": "paragraph 2, line 12",
      "pattern": "It's important to note that",
      "context": "...the findings. It's important to note that further research is needed.",
      "severity": "high",
      "action": "delete"
    }
  ]
}
```

### Phase 5: Language Pattern Analysis

#### Step 5.1: Check Negative Parallelisms (2.2)

From `patterns/language-patterns.json`:

- "constitutes not only X but Y"
- "It's not just about X; it's about Y"
- Pattern: `(not just|not only|more than just) .+ (but|but also|rather)`

**Action**: Rephrase to direct statement

#### Step 5.2: Check Rule of Three (2.3)

Count three-item lists: `\w+, \w+, and \w+`

- Flag if appears >3 times in same section
- Note: Three-item lists are NOT inherently AI, only flag excessive use

#### Step 5.3: Check Weasel Words (2.4)

- "has been described as" (without citation)
- "experts believe" (unnamed)
- "studies show" (uncited)
- "research suggests" (unspecified)
- "is widely considered" (no source)

**Action**: Cite source or remove

#### Step 5.4: Check Elegant Variation (2.5)

Manual review required:

- Check if subject is called by multiple different titles
- Example: "John Smith", then "the protagonist", then "the key figure"

#### Step 5.5: Check False Ranges (2.6)

- Pattern: "from X to Y" used for dramatic effect
- Example: "from the Big Bang to the cosmic web" (meaningless range)

#### Step 5.6: Record Language Findings

```json
{
  "language_patterns": [
    {
      "subcategory": "2.2 - Negative Parallelism",
      "location": "paragraph 3",
      "pattern": "not just X but Y",
      "context": "It's not just a tool, but a comprehensive solution",
      "severity": "high",
      "action": "rephrase"
    }
  ]
}
```

### Phase 6: Style and Formatting Analysis

#### Step 6.1: Check Title Case Headers (3.1)

- Detect if headers use Title Case When They Should Use Sentence case
- Example: "The Impact Of Technology On Society" → "The impact of technology on society"

#### Step 6.2: Check Excessive Boldface (3.2)

- Count bold phrases per paragraph
- Flag if >3 bold phrases per paragraph on average

#### Step 6.3: Check Inline-Header Lists (3.3)

- Pattern: `^\d+\.\s+\*\*[^*]+\*\*:\s+`
- Example: "1. **Historical Context:** The world..."
- Pattern: `^[-*]\s+\*\*[^*]+\*\*:\s+`

#### Step 6.4: Check Em Dash Usage (3.5)

Count em dashes (—):

- Calculate: `count / (word_count / 500)`
- Flag if >2 per 500 words

#### Step 6.5: Check Markdown Artifacts (3.7)

- `**bold**` in plain text
- `*italic*` in plain text
- `# headers` in plain text
- Bullet syntax `- item` in plain text

#### Step 6.6: Record Style Findings

```json
{
  "style_issues": [
    {
      "subcategory": "3.5 - Em Dash Overuse",
      "count": 8,
      "density": "4.5 per 500 words",
      "threshold": "2 per 500 words",
      "severity": "medium",
      "status": "excessive"
    }
  ]
}
```

### Phase 7: Confidence Score Calculation

#### Step 7.1: Calculate Category Scores

**Definitive Markers** (50% weight):

```javascript
if (definitive_markers.length > 0) {
  definitive_score = 50; // Maximum
} else {
  definitive_score = 0;
}
```

**Content Issues** (20% weight):

```javascript
content_score = Math.min((content_issues.length / 10) * 20, 20);
```

**Language Patterns** (15% weight):

```javascript
// Based on vocabulary density
if (vocab_density > 15) {
  language_score = 15;
} else {
  language_score = (vocab_density / 15) * 15;
}
```

**Style Issues** (10% weight):

```javascript
style_score = Math.min((style_issues.length / 5) * 10, 10);
```

**Behavioral Indicators** (5% weight):

```javascript
// Manual assessment based on:
// - Style shift from usual writing
// - English variety mismatch
// - Date considerations
behavioral_score = 0 - 5; // Requires human judgment
```

#### Step 7.2: Calculate Total Score

```javascript
total_score =
  definitive_score +
  content_score +
  language_score +
  style_score +
  behavioral_score;

// Convert to percentage
confidence_percentage = total_score; // Already 0-100
```

#### Step 7.3: Determine Confidence Level

```javascript
if (confidence_percentage >= 70) {
  confidence_level = "HIGH";
} else if (confidence_percentage >= 40) {
  confidence_level = "MEDIUM";
} else if (confidence_percentage >= 20) {
  confidence_level = "LOW";
} else {
  confidence_level = "NONE";
}
```

### Phase 8: Context and False Positive Analysis

#### Step 8.1: Determine Document Type

Infer document type from content and structure:

- Technical documentation
- Academic paper
- Marketing material
- Creative writing
- Business communication
- Encyclopedia/reference entry

#### Step 8.2: Check False Positive Patterns

From `patterns/false-positives.json`:

- Perfect grammar detected? → NOT an AI indicator
- Bland prose detected? → NOT an AI indicator (LLMs are effusive)
- Fancy vocabulary detected? → Actually suggests HUMAN (LLMs favor common words)
- Formal style detected? → Context-dependent
- Unusual/rare words detected? → Suggests HUMAN

#### Step 8.3: Apply Context Adjustments

```javascript
adjustments = [];

if (document_type === "technical") {
  adjustments.push(
    "Technical terms like 'ecosystem' and 'leverage' may be legitimate",
  );
  // Potentially reduce language_score
}

if (document_type === "academic") {
  adjustments.push("Formal language expected in academic writing");
  // Increase vocabulary threshold tolerance
}

if (document_type === "marketing") {
  adjustments.push("Promotional language may be intentional");
  // Note that style might be genre-appropriate
}
```

#### Step 8.4: Generate False Positive Warnings

```json
{
  "false_positive_warnings": [
    "Technical terms like 'ecosystem' and 'leverage' found, but used in proper technical context",
    "Formal academic style detected, consistent with scholarly writing conventions"
  ]
}
```

### Phase 9: Report Generation

#### Step 9.1: Load Report Template

Use template from `prompts/report-prompt.md`.

#### Step 9.2: Generate Summary Section

```markdown
## Summary

- **Confidence Level**: High
- **Overall Score**: 78%
- **Total Issues Found**: 24
- **Definitive Markers**: 1
- **Word Count**: 450 words
- **Analysis Date**: 2025-12-18
```

#### Step 9.3: Include Important Caveats

Always include the standard warnings:

```markdown
## ⚠️ Important Caveats

- These are **potential signs**, not definitive proof
- Many patterns existed in human writing before LLMs
- False accusations harm collaboration and trust
- Context matters - consider the full picture
- Do NOT solely rely on AI detection tools (significant error rates)
- Experts correctly identify AI ~90% of time (10% false positives)
- Non-experts do barely better than random chance
- **When in doubt, assume human authorship**
```

#### Step 9.4: Detail Definitive Markers (if any)

```markdown
## Definitive AI Markers

**Status**: 1 definitive marker found

### Critical Indicators (Smoking Guns)

1. **Collaborative Artifact** (Line 45): "I hope this helps"
   - **Why definitive**: Chatbot signature, never in published human writing
   - **Confidence**: 100%
   - **Action**: DELETE immediately
```

#### Step 9.5: Detail Content Issues

Group by subcategory with specific locations:

```markdown
## Content Issues

**Found**: 8 issues | **Weight**: 20% | **Score**: 16/20

### 1.1 Undue Emphasis on Symbolism/Legacy (2 found)

- **Line 12**: "marking a pivotal moment"
  - Pattern: Unwarranted gravitas
  - Context: "...the announcement marking a pivotal moment in history."
  - Severity: Medium
```

#### Step 9.6: Detail Language Patterns

Include vocabulary breakdown and density calculation:

```markdown
## Language Patterns

**Found**: 12 issues | **Weight**: 15% | **Score**: 13/15

### AI Vocabulary Density

- **Total AI words found**: 18
- **Density**: 20 per 500 words
- **Threshold**: 5 per 500 words
- **Status**: SIGNIFICANTLY above threshold (4x)

#### Breakdown by Type

**High-frequency AI verbs** (5 occurrences):

- leverage: 2 times
- streamline: 1 time
- foster: 1 time
```

#### Step 9.7: Detail Style Issues

```markdown
## Style Issues

**Found**: 3 issues | **Weight**: 10% | **Score**: 6/10

### Em Dash Usage

- **Count**: 6
- **Density**: 6.7 per 500 words
- **Threshold**: 2 per 500 words
- **Status**: Excessive (3x threshold)
```

#### Step 9.8: Show Confidence Breakdown Table

```markdown
## Confidence Breakdown

| Category              | Weight | Issues Found | Score | Weighted |
| --------------------- | ------ | ------------ | ----- | -------- |
| Definitive markers    | 50%    | 1            | 50    | 50       |
| Content issues        | 20%    | 8            | 16    | 16       |
| Language patterns     | 15%    | 12           | 13    | 13       |
| Style issues          | 10%    | 3            | 6     | 6        |
| Behavioral indicators | 5%     | 0            | 0     | 0        |
| **TOTAL**             | 100%   | 24           | -     | **85%**  |
```

#### Step 9.9: Include False Positive Warnings

```markdown
## False Positive Warnings

⚠️ The following patterns were detected but may NOT indicate AI generation:

- Technical terms like "ecosystem" found, but used in proper technical context
- Some formal language detected, but appropriate for document type
```

#### Step 9.10: Generate Recommendations

Based on confidence level:

```markdown
## Recommendations

### Conclusion

Strong indicators of AI generation detected.

### Next Steps

1. Review definitive markers carefully
2. Run through ai-writing-humanizer skill to fix issues
3. Verify any citations or references
4. Re-run detector after fixes to confirm improvement
```

#### Step 9.11: Optional Fix Suggestions

If requested, provide specific rewrites:

```markdown
## Optional: Fix Suggestions

### Line 12: "marking a pivotal moment in history"

**Issue**: Undue emphasis on symbolism

**Suggested fix**: "an important change in history" or "changed history"

**Rationale**: Removes inflated language while preserving meaning
```

### Phase 10: Output and Integration

#### Step 10.1: Format Final Report

Format the complete report in markdown following the template structure.

#### Step 10.2: Provide Integration Suggestions

```markdown
## Integration with AI Writing Humanizer

**Workflow suggestion**:

1. ✅ **Detection complete** (this report)
2. ⏭️ **Next**: Run text through ai-writing-humanizer skill
3. ⏭️ **Verify**: Run detector again on humanized output
4. ⏭️ **Iterate**: Continue humanizing until confidence drops to "None" or "Low"
```

#### Step 10.3: Return Report

Return the complete detection report to the user.

## Quality Assurance

Before finalizing the report:

1. **Verify accuracy**: Double-check pattern matches and line numbers
2. **Check calculations**: Ensure confidence scoring is correct
3. **Review context**: Confirm contextual adjustments are appropriate
4. **Balance tone**: Include both findings and caveats
5. **Provide value**: Make recommendations actionable

## Best Practices

1. **Prioritize definitive markers**: Focus on technical artifacts first
2. **Use multiple indicators**: Never rely on single pattern
3. **Consider context**: Adjust thresholds for document type
4. **Be humble**: Acknowledge detection uncertainty
5. **Protect against false positives**: Err on side of human authorship
6. **Provide specifics**: Always include line numbers and context
7. **Be actionable**: Offer clear next steps
8. **Link to humanizer**: Suggest complementary skill when appropriate

## Limitations and Considerations

- **Not foolproof**: Some AI patterns may be missed
- **Context dependent**: Some patterns are genre-appropriate
- **Single-pass only**: Unlike humanizer, doesn't iterate
- **Report only**: Doesn't make changes (use humanizer for that)
- **Requires judgment**: Human review recommended for important decisions
- **False positive risk**: Even experts have 10% error rate
- **Tool, not weapon**: This is for analysis, not accusation

## Success Metrics

Track these for skill improvement:

- Detection accuracy on known AI/human text
- False positive rate
- False negative rate
- User satisfaction with reports
- Integration success with humanizer skill

## Version History

**1.0.0** (2025-12-18)

- Initial release
- 6 major detection categories
- Weighted confidence scoring
- Comprehensive pattern database
- False positive protection
- Integration with ai-writing-humanizer skill
