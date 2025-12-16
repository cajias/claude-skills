# AI Writing Pattern Analysis

Analyze the following text for signs of AI-generated writing. Check against EACH category below and
report ALL matches.

## Text to Analyze

````text
{{INPUT_TEXT}}
```text

## Categories to Check

### 1. Inflated Symbolism

"testament", "vital/crucial/pivotal role", "underscores importance", "captivate", "watershed",
"profound", "steadfast", "embodies", "epitomizes"

### 2. Promotional Language

"rich heritage/history/tapestry", "breathtaking", "stunning", "must-visit/see", "enduring/lasting
legacy", "dynamic hub", "vibrant", "world-class", "hidden gem", "coastal charm"

### 3. Editorializing

"important to note", "worth noting", "no discussion complete without", "in this article",
"needless to say", "as mentioned earlier"

### 4. Transition Overuse

Count occurrences of "moreover", "furthermore", "additionally", "on the other hand", "in contrast",
"nevertheless", "consequently". Flag if frequency exceeds thresholds (>1 per 500 words, >2 for
"however")

### 5. Negative Parallelism

"not just X but Y", "not only X but also Y", "more than just", "it's not X, it's Y", "isn't just"

### 6. Participle Endings

Sentences ending with ", ensuring...", ", highlighting...", ", emphasizing...", ", reflecting...",
", demonstrating...", ", showcasing...", ", signaling...", ", cementing...", ", solidifying..."

### 7. Weasel Words

"experts say", "studies show", "widely considered", "often regarded", "observers note", "some
critics", "industry reports suggest", "many believe", "it has been said", "according to sources"

### 8. Em Dash Overuse

Count em dashes (—), flag if >2 per 500 words

### 9. Rule of Three

Multiple three-item lists with similar structure (e.g., "X, Y, and Z" appearing multiple times)

### 10. Formatting Patterns

- Title case in headers (Every Word Capitalized)
- Excessive bold (>3 bold phrases per section)
- Uniform bullets (every item follows **Topic:** description)
- Markdown artifacts (`*asterisks*`, `_underscores_`)

### 11. Buzzwords

"delve", "cutting-edge", "revolutionary", "game-changing", "leverage", "utilize", "facilitate",
"synergy", "paradigm", "holistic", "seamlessly", "robust", "ecosystem", "empower", "harness",
"groundbreaking", "multifaceted", "optimize"

### 12. Filler Phrases

"In today's ever-evolving", "As we navigate", "In summary/conclusion/essence", "At the end of the
day", "In a nutshell", "All in all", "To summarize", "Overall" (when used as filler)

### 13. Chatbot Artifacts (CRITICAL)

"I hope this helps", "Certainly!", "Let me know", "As an AI", "as a language model", "as of my
last", "I don't have personal", "turn0search0", "Based on my training"

### 14. Section Conclusions

"continues to be", "remains to be seen", "time will tell", "the future holds", "looking ahead",
"moving forward" (when used as concluding sentences)

### 15. Hedge Word Clusters

Multiple "arguably", "somewhat", "potentially", "perhaps", "possibly", "likely", "might", "may",
"could" near each other (>3 per 200 words)

## Output Format

For each issue found, report:

```json
{
  "issues": [
    {
      "category": "Category Name",
      "priority": "critical|high|medium|low",
      "pattern_matched": "exact text that matched",
      "location": "paragraph X, sentence Y",
      "context": "...surrounding text for context...",
      "suggested_action": "delete|replace|rephrase|cite_or_remove",
      "suggested_replacement": "specific replacement text or null"
    }
  ],
  "summary": {
    "total_issues": 0,
    "critical": 0,
    "high": 0,
    "medium": 0,
    "low": 0,
    "word_count": 0
  }
}
```text

## Analysis Guidelines

1. **Be thorough**: Check every sentence against all categories
2. **Report all matches**: Don't stop after finding a few issues
3. **Provide context**: Include surrounding text (1-2 sentences before/after)
4. **Consider frequency**: For frequency-based patterns, calculate per specified word counts
5. **Location accuracy**: Identify paragraph and sentence numbers clearly
6. **Priority assignment**: Follow the priority levels defined in the pattern database
7. **No false positives**: Only flag genuine matches, not similar but different constructions

## Special Considerations

### Frequency-Based Patterns

- Calculate word count first
- Count pattern occurrences
- Apply threshold formula (e.g., occurrences per 500 words)
- Only flag if threshold exceeded

### Context-Dependent Patterns

Some patterns are acceptable in certain contexts:

- Technical terms in technical writing (but still flag excessive use)
- Established phrases with proper citations
- Intentional stylistic choices (rare, but possible)

When in doubt, flag it and let the review process decide.

## Example Analysis

### Input Text

"In today's ever-evolving landscape, the platform stands as a testament to innovation. It's not
just a tool, but a revolutionary ecosystem that leverages cutting-edge technology, ensuring
seamless integration."

### Output

```json
{
  "issues": [
    {
      "category": "Filler Phrases",
      "priority": "high",
      "pattern_matched": "In today's ever-evolving landscape",
      "location": "paragraph 1, sentence 1",
      "context": "In today's ever-evolving landscape, the platform stands as a testament...",
      "suggested_action": "delete",
      "suggested_replacement": null
    },
    {
      "category": "Inflated Symbolism",
      "priority": "high",
      "pattern_matched": "stands as a testament",
      "location": "paragraph 1, sentence 1",
      "context": "...the platform stands as a testament to innovation.",
      "suggested_action": "replace",
      "suggested_replacement": "demonstrates"
    },
    {
      "category": "Negative Parallelism",
      "priority": "high",
      "pattern_matched": "not just a tool, but a revolutionary",
      "location": "paragraph 1, sentence 2",
      "context": "It's not just a tool, but a revolutionary ecosystem...",
      "suggested_action": "rephrase",
      "suggested_replacement": "The platform is a revolutionary ecosystem"
    },
    {
      "category": "Buzzwords",
      "priority": "high",
      "pattern_matched": "revolutionary",
      "location": "paragraph 1, sentence 2",
      "context": "...but a revolutionary ecosystem that leverages...",
      "suggested_action": "replace",
      "suggested_replacement": "innovative"
    },
    {
      "category": "Buzzwords",
      "priority": "high",
      "pattern_matched": "ecosystem",
      "location": "paragraph 1, sentence 2",
      "context": "...a revolutionary ecosystem that leverages cutting-edge...",
      "suggested_action": "replace",
      "suggested_replacement": "system"
    },
    {
      "category": "Buzzwords",
      "priority": "high",
      "pattern_matched": "leverages",
      "location": "paragraph 1, sentence 2",
      "context": "...ecosystem that leverages cutting-edge technology...",
      "suggested_action": "replace",
      "suggested_replacement": "uses"
    },
    {
      "category": "Buzzwords",
      "priority": "high",
      "pattern_matched": "cutting-edge",
      "location": "paragraph 1, sentence 2",
      "context": "...leverages cutting-edge technology, ensuring seamless...",
      "suggested_action": "replace",
      "suggested_replacement": "modern"
    },
    {
      "category": "Participle Endings",
      "priority": "high",
      "pattern_matched": ", ensuring",
      "location": "paragraph 1, sentence 2",
      "context": "...cutting-edge technology, ensuring seamless integration.",
      "suggested_action": "delete",
      "suggested_replacement": null
    },
    {
      "category": "Buzzwords",
      "priority": "high",
      "pattern_matched": "seamlessly",
      "location": "paragraph 1, sentence 2",
      "context": "...ensuring seamless integration.",
      "suggested_action": "replace",
      "suggested_replacement": "smooth"
    }
  ],
  "summary": {
    "total_issues": 9,
    "critical": 0,
    "high": 9,
    "medium": 0,
    "low": 0,
    "word_count": 27
  }
}
```text

## Notes

- Be consistent with JSON formatting
- Include all required fields for each issue
- Calculate word count for frequency analysis
- Group related issues when reporting (e.g., multiple instances of same pattern)
- Prioritize CRITICAL issues (chatbot artifacts) for immediate attention
````
