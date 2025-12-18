# AI Writing Detection Report Template

Generate a comprehensive detection report using this structure:

## Report Format

````markdown
# AI Writing Detection Report

## Summary

- **Confidence Level**: [High/Medium/Low/None]
- **Overall Score**: [X%]
- **Total Issues Found**: [X]
- **Definitive Markers**: [X] (if any found, confidence is automatically HIGH)
- **Word Count**: [X words]
- **Analysis Date**: [Date]

## ⚠️ Important Caveats

Before reviewing the findings, note these important limitations:

- These are **potential signs**, not definitive proof
- Many patterns existed in human writing before LLMs
- False accusations harm collaboration and trust
- Context matters - consider the full picture
- Do NOT solely rely on AI detection tools (GPTZero, etc.) - they have significant error rates
- Experts correctly identify AI ~90% of the time (10% false accusations)
- Non-experts do barely better than random chance
- **When in doubt, assume human authorship**

---

## Definitive AI Markers

[If any found, list here with HIGH prominence]

**Status**: [X definitive markers found / None found]

[If found:]

### Critical Indicators (Smoking Guns)

1. **[Type]** (Line/Location): "[Exact text]"
   - **Why definitive**: [Explanation]
   - **Confidence**: 100%

2. ...

[If none found:]

✓ No definitive technical artifacts detected

---

## Content Issues

**Found**: [X issues] | **Weight**: 20% | **Score**: [X/20]

[If found, list by subcategory:]

### 1.1 Undue Emphasis on Symbolism/Legacy ([X] found)

- **Line [X]**: "[Quote]"
  - Pattern: [Pattern name]
  - Context: [Surrounding text]
  - Severity: [High/Medium/Low]

### 1.3 Superficial Analyses ([X] found)

- **Paragraph [X]**: "[Quote]"
  - Issue: [Description]
  - Example: Inanimate object "highlighting" something

### 1.4 Promotional Language ([X] found)

- **Line [X]**: "[Quote]"
  - Reads like: [Marketing copy / Travel brochure / Advertisement]

### 1.5 Didactic Disclaimers ([X] found)

- **Location**: "[Quote]"
  - Pattern: "Important to note that..."
  - Suggestion: Delete and state directly

[Continue for other subcategories...]

---

## Language Patterns

**Found**: [X issues] | **Weight**: 15% | **Score**: [X/15]

### AI Vocabulary Density

- **Total AI words found**: [X]
- **Density**: [X per 500 words]
- **Threshold**: 5 per 500 words
- **Status**: [Above/Below threshold]

#### Breakdown by Type

**High-frequency AI verbs** ([X] occurrences):

- delve: [X times]
- leverage: [X times]
- underscore: [X times]
- [List all found]

**High-frequency AI adjectives** ([X] occurrences):

- pivotal: [X times]
- multifaceted: [X times]
- [List all found]

**High-frequency AI nouns** ([X] occurrences):

- tapestry: [X times]
- landscape (metaphorical): [X times]
- [List all found]

**High-frequency AI phrases** ([X] occurrences):

- "rich tapestry": [X times]
- "testament to": [X times]
- [List all found]

### Negative Parallelisms ([X] found)

- **Line [X]**: "[Quote]"
  - Pattern: "not just X but Y"
  - Suggestion: Rephrase to direct statement

### Weasel Words / Vague Attribution ([X] found)

- **Line [X]**: "[Quote]"
  - Issue: Claims without sources
  - Action: Cite source or remove

### Rule of Three ([X] instances)

- Three-item lists: [X times]
- Status: [Acceptable / Excessive]

---

## Style Issues

**Found**: [X issues] | **Weight**: 10% | **Score**: [X/10]

### Em Dash Usage

- **Count**: [X]
- **Density**: [X per 500 words]
- **Threshold**: 2 per 500 words
- **Status**: [Acceptable / Excessive]

### Formatting Patterns

- **Title Case Headers**: [X instances]
- **Excessive Bold**: [X paragraphs with >3 bold phrases]
- **Inline-Header Lists**: [X instances]
- **Emoji Usage**: [X instances]
- **Markdown Artifacts**: [X instances]

---

## Confidence Breakdown

| Category              | Weight | Issues Found | Score | Weighted |
| --------------------- | ------ | ------------ | ----- | -------- |
| Definitive markers    | 50%    | [X]          | [X]   | [X]      |
| Content issues        | 20%    | [X]          | [X]   | [X]      |
| Language patterns     | 15%    | [X]          | [X]   | [X]      |
| Style issues          | 10%    | [X]          | [X]   | [X]      |
| Behavioral indicators | 5%     | [X]          | [X]   | [X]      |
| **TOTAL**             | 100%   | -            | -     | **[X%]** |

### Confidence Assessment

**Level**: [High / Medium / Low / None]

**Reasoning**:

- [Explain why this confidence level]
- [List key factors]
- [Note any ambiguous patterns]

---

## False Positive Warnings

⚠️ The following patterns were detected but may NOT indicate AI generation:

- [List any patterns that could be human]
- [Note context-dependent findings]
- [Explain legitimate uses]

**Example**:

- Technical terms like "ecosystem" and "leverage" found, but used in proper technical context
- Formal academic style detected, consistent with scholarly writing conventions

---

## Context Considerations

**Document Type**: [Inferred type: Technical / Academic / Marketing / Creative / Other]

**Contextual Notes**:

- [How context affects interpretation]
- [Adjustments made to thresholds]
- [Genre-specific considerations]

---

## Recommendations

[Based on confidence level:]

### If High Confidence:

**Conclusion**: Strong indicators of AI generation detected.

**Next Steps**:

1. Review definitive markers carefully
2. If content needs use, consider running through ai-writing-humanizer skill
3. Verify any citations or references
4. Consider rewriting flagged sections

### If Medium Confidence:

**Conclusion**: Multiple AI patterns present, but not definitive.

**Next Steps**:

1. Review flagged sections in context
2. Consider whether patterns are stylistic choices
3. If concerned, run through ai-writing-humanizer skill
4. May benefit from human review and light editing

### If Low Confidence:

**Conclusion**: Few AI indicators found.

**Next Steps**:

1. Patterns may be coincidental or stylistic
2. Consider document purpose and context
3. No immediate action needed
4. If still concerned, focus on specific flagged items

### If No Confidence:

**Conclusion**: No significant AI indicators detected.

**Assessment**: Text shows characteristics consistent with human writing.

---

## Optional: Fix Suggestions

[If requested, provide specific suggestions for each flagged item:]

### Line [X]: "[Original text]"

**Issue**: [Description]

**Suggested fix**: "[Rewritten version]"

**Rationale**: [Why this change]

---

## References

- Pattern Database: patterns/\*.json
- Detection Methodology: Based on Wikipedia's Signs of AI Writing
- Analysis Tool: AI Writing Detector Skill v1.0.0
````

## Notes for Report Generation

1. **Be specific**: Always include line numbers or paragraph references
2. **Provide context**: Quote surrounding text for each finding
3. **Explain reasoning**: Don't just list patterns, explain why they matter
4. **Show calculations**: Display how confidence score was computed
5. **Be balanced**: Include false positive warnings and caveats
6. **Consider context**: Adjust interpretation based on document type
7. **Be actionable**: Provide clear next steps based on findings
8. **Preserve nuance**: Note when patterns may be legitimate
9. **Emphasize uncertainty**: Make clear these are indicators, not proof
10. **Link to humanizer**: Suggest ai-writing-humanizer skill for fixes if needed

## Relationship to AI Writing Humanizer

This skill (detector) and ai-writing-humanizer are complementary:

- **Detector**: Single-pass analysis, detailed report, no changes
- **Humanizer**: Iterative fixing, applies changes, loop until clean

**Workflow Integration**:

1. Use **detector** to audit text and understand scope
2. Review detection report and decide if changes needed
3. Use **humanizer** to fix detected issues
4. Use **detector** again to verify fixes successful
