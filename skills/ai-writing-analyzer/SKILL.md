---
name: ai-writing-analyzer
description: |
  Detect AI writing patterns in text. Use when:
  (1) need to check if text sounds AI-generated,
  (2) reviewing content before publication,
  (3) analyzing writing for Wikipedia-style AI markers,
  (4) generating report-only analysis without changes.
author: cajias
version: 1.0.0
date: 2025-01-27
tags: [writing, ai-detection, analysis]
---

# AI Writing Analyzer

Detect AI writing patterns in text using Wikipedia's "Signs of AI Writing" guidelines.
For fixing detected issues, see `ai-writing-fixer`.

## Prerequisites

Access to the pattern database in `../ai-writing-humanizer/patterns/patterns.json`

## Pattern Categories (15 Total)

| Priority | Category | Examples |
|----------|----------|----------|
| Critical | Chatbot Artifacts | "I hope this helps", "As an AI..." |
| High | Buzzwords | "leverage", "utilize", "delve into" |
| High | Inflated Symbolism | "stands as a testament", "watershed moment" |
| High | Promotional Language | "breathtaking", "revolutionary" |
| High | Editorializing | "It's important to note", "Worth mentioning" |
| Medium | Negative Parallelism | "It's not just X, but Y" |
| Medium | Participle Endings | ", ensuring...", ", highlighting..." |
| Medium | Filler Phrases | "In today's ever-evolving world" |
| Medium | Weasel Words | "Some experts say", "It is believed" |
| Medium | Transition Overuse | "Furthermore", "Moreover" (frequency-based) |
| Low | Em Dash Overuse | More than 2 per 500 words |
| Low | Hedge Words | "somewhat", "relatively", "arguably" |
| Low | Rule of Three | Repeated triadic structures |
| Low | Formatting Patterns | Excessive bullet lists, headers |
| Low | Sentence Starters | Repetitive patterns |

## Quick Analysis

```bash
# Provide text directly
echo "Your text here" | analyze_for_ai_patterns

# Or analyze a file
cat document.md | analyze_for_ai_patterns
```

## Analysis Process

### Step 1: Load Pattern Database

```python
import json
patterns = json.load(open('patterns/patterns.json'))
```

### Step 2: Run Detection

For each category, apply appropriate detection method:

**Simple Matching** (buzzwords, filler phrases):
- Case-insensitive exact match
- Record location and context

**Regex Matching** (negative parallelism, participle endings):
- Apply regex patterns
- Validate in context

**Frequency Detection** (transitions, em dashes):
- Count occurrences per 500 words
- Flag if exceeds threshold

**Structural Analysis** (rule of three, formatting):
- Detect repeated patterns
- Count structural elements

### Step 3: Generate Report

Output format:

```json
{
  "issues": [
    {
      "id": 1,
      "category": "Buzzwords",
      "priority": "high",
      "pattern": "leverage",
      "location": "paragraph 2, sentence 3",
      "context": "...can leverage advanced algorithms..."
    }
  ],
  "summary": {
    "total_issues": 15,
    "critical": 1,
    "high": 9,
    "medium": 3,
    "low": 2,
    "ai_likelihood": "high"
  }
}
```

## Output Format

### Console Report

```markdown
## AI Writing Analysis

**AI Likelihood:** High (15 patterns detected)

### Critical (1)
- **Chatbot Artifact** [para 1]: "I hope this helps"

### High Priority (9)
- **Buzzword** [para 2]: "leverage" → consider "use"
- **Inflated Symbolism** [para 3]: "stands as a testament"
...

### Summary
| Category | Count |
|----------|-------|
| Critical | 1 |
| High | 9 |
| Medium | 3 |
| Low | 2 |
```

## Thresholds

| Pattern | Threshold | Flagged When |
|---------|-----------|--------------|
| Em dashes | 2 per 500 words | Exceeds |
| Transitions | 3 per 500 words | Exceeds |
| Hedge words | 4 per 500 words | Exceeds |
| Rule of three | 2 instances | Exceeds |

## AI Likelihood Scoring

| Score | Likelihood | Criteria |
|-------|------------|----------|
| 0-2 issues | Low | Likely human-written |
| 3-7 issues | Medium | Some AI markers |
| 8-15 issues | High | Likely AI-assisted |
| 16+ issues | Very High | Almost certainly AI |

## See Also

- `ai-writing-fixer` - Fix detected AI patterns
- `ai-writing-humanizer` - Full iterative workflow (analyze + fix)
