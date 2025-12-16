# Generate Human-Friendly Replacements

For each flagged AI writing pattern below, generate a natural human-sounding replacement.

## Flagged Issues

````json
{{ISSUES_JSON}}
```text

## Original Text

```text
{{ORIGINAL_TEXT}}
```text

## Guidelines for Replacements

### 1. Preserve Meaning

Don't lose important information. If the original text conveys a fact or detail, the replacement
must maintain it.

**Example**:

- Original: "The system stands as a testament to modern engineering"
- Bad: "The system exists"
- Good: "The system demonstrates modern engineering"

### 2. Be Specific

Replace vague with concrete. Remove abstraction layers.

**Example**:

- Original: "leveraging cutting-edge technology"
- Bad: "using technology"
- Good: "using machine learning"

### 3. Be Concise

Shorter is usually better. Remove unnecessary words.

**Example**:

- Original: "It's important to note that the data shows improvement"
- Bad: "Note that the data shows improvement"
- Good: "The data shows improvement"

### 4. Sound Natural

Read it aloud. Would a human say this? Avoid formal or robotic phrasing.

**Example**:

- Original: "The solution facilitates seamless integration"
- Bad: "The solution enables integration that is smooth"
- Good: "The solution integrates smoothly" or just "The solution integrates"

### 5. Match Tone

Keep consistent with surrounding text. Don't shift from formal to casual or vice versa.

### 6. Sometimes Delete

If a phrase adds nothing, remove it entirely.

**Example**:

- Original: "The company released earnings, highlighting its transparency"
- Good: "The company released earnings"

## Replacement Strategies by Category

### Inflated Symbolism

**Strategy**: Deflate. State directly without drama.

- "stands as a testament to X" → "shows X" or just state X directly
- "plays a vital role" → "contributes to" or "is part of"
- "underscores its importance" → (delete - the importance should be evident from facts)

### Promotional Language

**Strategy**: Neutralize. Remove marketing speak.

- "breathtaking views" → "mountain views" or just "views"
- "rich cultural heritage" → "history" or "traditions"
- "hidden gem" → "lesser-known site" or just name the place

### Editorializing

**Strategy**: Delete meta-commentary. State facts directly.

- "It's important to note that X" → "X"
- "Worth mentioning is that Y" → "Y"
- "Importantly, Z" → "Z"

### Participle Endings

**Strategy**: Trim the tail. Most -ing clauses at sentence end can be deleted.

- "The company released earnings, highlighting transparency" → "The company released earnings"
- "The study found results, demonstrating efficacy" → "The study found results"

### Weasel Words

**Strategy**: Specify or delete. Name sources or remove the claim.

- "Experts say X" → "[Dr. Smith], a [neuroscientist], said X" OR delete if unsourced
- "Studies show Y" → "[A 2023 Stanford study] found Y" OR "Y" (if established fact)

### Buzzwords

**Strategy**: Simplify. Use plain language.

- "leverage" → "use"
- "utilize" → "use"
- "delve into" → "examine"
- "cutting-edge" → "modern" or "new"
- "ecosystem" → "system" or "environment"

### Negative Parallelism

**Strategy**: Direct statement. Remove the artificial contrast.

- "It's not just X, it's Y" → "Y" or "X and Y"
- "Not only X but also Y" → "X and Y" or restructure to emphasize Y naturally

### Filler Phrases

**Strategy**: Delete entirely. Start with the actual content.

- "In today's ever-evolving world, X" → "X"
- "At the end of the day, Y" → "Y"
- "In summary, Z" → "Z" (or just end the section)

## Output Format

```json
{
  "replacements": [
    {
      "issue_id": "sequential number from issues array",
      "original": "exact original text from issue",
      "replacement": "suggested replacement (or null if delete)",
      "action": "replace|delete|rephrase",
      "confidence": "high|medium|low",
      "explanation": "brief explanation of why this replacement",
      "context_before": "text before the issue",
      "context_after": "text after the issue"
    }
  ]
}
```text

## Confidence Levels

### High Confidence

Use when replacement is straightforward and won't change meaning:

- Simple buzzword replacement ("utilize" → "use")
- Obvious filler deletion ("It's important to note that" → delete)
- Clear promotional language ("breathtaking" → "impressive")

### Medium Confidence

Use when multiple options exist or context affects choice:

- Replacements that depend on surrounding text
- Terms that might be technical jargon vs buzzwords
- Phrases where deletion vs replacement is debatable

### Low Confidence

Use when substantial rewriting needed or meaning might change:

- Complex sentence restructuring
- Negative parallelism requiring full rephrase
- Weasel words where source is unclear

## Examples

### Example 1: Simple Replacement

**Original**: "The platform leverages cutting-edge AI technology."

```json
{
  "issue_id": 1,
  "original": "leverages",
  "replacement": "uses",
  "action": "replace",
  "confidence": "high",
  "explanation": "Direct substitution of buzzword with plain language",
  "context_before": "The platform",
  "context_after": "cutting-edge AI technology."
}
```text

### Example 2: Deletion

**Original**: "It's important to note that the results were positive."

```json
{
  "issue_id": 2,
  "original": "It's important to note that",
  "replacement": null,
  "action": "delete",
  "confidence": "high",
  "explanation": "Meta-commentary adds no value; state fact directly",
  "context_before": "",
  "context_after": "the results were positive."
}
```text

### Example 3: Complex Rephrase

**Original**: "It's not just a tool, but a comprehensive ecosystem for developers."

```json
{
  "issue_id": 3,
  "original": "It's not just a tool, but a comprehensive ecosystem",
  "replacement": "The comprehensive system",
  "action": "rephrase",
  "confidence": "medium",
  "explanation": "Removed negative parallelism and buzzword 'ecosystem'; kept 'comprehensive' as meaningful descriptor",
  "context_before": "",
  "context_after": "for developers."
}
```text

### Example 4: Participle Ending Removal

**Original**: "The company released quarterly earnings, highlighting its commitment to
transparency."

```json
{
  "issue_id": 4,
  "original": ", highlighting its commitment to transparency",
  "replacement": null,
  "action": "delete",
  "confidence": "high",
  "explanation": "Participle clause adds editorializing; let the action speak for itself",
  "context_before": "The company released quarterly earnings",
  "context_after": ""
}
```text

## Special Cases

### When Technical Terms Appear as Buzzwords

Some words (like "ecosystem" or "paradigm") are legitimate technical terms in certain contexts:

- Software ecosystems (npm ecosystem, Android ecosystem)
- Scientific paradigms (paradigm shift in physics)

**Strategy**: Determine from context if used technically or as buzzword. If buzzword, replace.
If technical, consider if it's overused.

### When Multiple Patterns Overlap

Sometimes one phrase contains multiple issues:

- "In today's fast-paced world, the cutting-edge solution leverages AI"
  - Filler phrase: "In today's fast-paced world"
  - Buzzwords: "cutting-edge", "leverages"

**Strategy**: Create separate replacements for each issue, or provide one comprehensive rephrase
that addresses all issues.

### When Context Makes Pattern Acceptable

Rarely, a typically-flagged pattern is appropriate:

- Academic citation: "Studies show" when referring to multiple studies
- Genuine hedge: "may" when expressing actual uncertainty

**Strategy**: Note in explanation why you're keeping it or suggest minimal modification.

## Quality Checklist

Before submitting replacements, verify:

- [ ] Meaning preserved
- [ ] Tone consistent with original
- [ ] Grammar correct
- [ ] More concise than original (usually)
- [ ] Sounds natural when read aloud
- [ ] Context preserved (beginning and end of sentence still make sense)
- [ ] All required JSON fields populated

## Notes on Action Types

### `replace`

Direct substitution of word/phrase with alternative. Use when:

- Simple word swap (utilize → use)
- Phrase replacement with same structure

### `delete`

Complete removal with no replacement. Use when:

- Filler phrases that add nothing
- Participle endings that are redundant
- Meta-commentary that can be omitted

### `rephrase`

Restructure the sentence or clause. Use when:

- Negative parallelism needs restructuring
- Multiple patterns in one phrase
- Simple replacement would be awkward

## Output Requirements

1. Provide replacement for EVERY issue in the input
2. Maintain sequential issue_id matching input order
3. Include context (5-10 words before/after when available)
4. Provide clear, actionable explanation
5. Be consistent with confidence levels
6. Ensure valid JSON formatting
````
