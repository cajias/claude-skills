# False Positive Examples

This document provides examples of text that might SEEM like AI but is actually human-written, to
help avoid false accusations.

## ⚠️ Critical Reminder

- **10% false positive rate even among experts**
- **Non-experts perform barely better than random chance**
- **When in doubt, assume human authorship**
- **Context and multiple indicators matter more than single patterns**

---

## Example 1: Formal Academic Writing

### Text

```text
The framework constitutes a comprehensive approach to analyzing institutional effectiveness. The
methodology leverages established theoretical paradigms while incorporating robust empirical data.
This research underscores the crucial importance of longitudinal studies in understanding complex
organizational dynamics.
```

### Why It Might Flag

- Uses "comprehensive", "leverage", "paradigm", "robust", "underscores", "crucial" (AI vocabulary)
- Formal, structured style
- Academic tone

### Why It's Likely Human

- **Legitimate academic context**: This is standard scholarly writing
- **Discipline-appropriate**: Social science research uses these terms correctly
- **No chatbot artifacts**: No "I hope this helps" or similar
- **No definitive markers**: No technical AI artifacts
- **Appropriate formality**: Academic papers should be formal

### Verdict

**Not AI** - This is legitimate academic writing. Do not flag based on vocabulary alone in
academic contexts.

---

## Example 2: Technical Documentation

### Text

```text
The Kubernetes ecosystem provides a robust platform for container orchestration. Organizations can
leverage this infrastructure to streamline deployment pipelines, ensuring seamless scaling across
distributed systems. The architecture embodies cloud-native principles, offering a holistic
solution for microservices management.
```

### Why It Might Flag

- Uses "ecosystem", "robust", "leverage", "streamline", "seamless", "embodies", "holistic" (AI
  buzzwords)
- High density of technical jargon
- Promotional-sounding

### Why It's Likely Human

- **Technical context**: Terms like "Kubernetes ecosystem" are standard in DevOps
- **Correct usage**: "Leverage" and "robust" are appropriate in technical documentation
- **Specific references**: Names actual technology (Kubernetes, microservices)
- **No artifacts**: No chatbot markers

### Verdict

**Not AI** - Technical documentation legitimately uses these terms. Context matters.

---

## Example 3: Perfectly Grammatical Writing

### Text

```text
The committee met on Tuesday. They discussed the budget. All members voted in favor. The motion
passed unanimously.
```

### Why It Might Flag

- Perfect grammar
- Zero errors
- Clean, simple structure

### Why It's Actually Human

- **Skilled writers exist**: Perfect grammar is not an AI indicator
- **Simple style**: LLMs actually tend toward floridity, not simplicity
- **Direct communication**: No buzzwords or inflated language

### Verdict

**Not AI** - Perfect grammar is NOT an AI indicator. Many humans write grammatically.

---

## Example 4: Formal Business Letter

### Text

```text
Dear Mr. Johnson,

I am writing to confirm our meeting scheduled for next Tuesday at 2:00 PM. Please find attached
the agenda and relevant documents for your review.

Should you have any questions prior to our meeting, please do not hesitate to contact me.

Sincerely,
Sarah Williams
```

### Why It Might Flag

- Formal structure
- "Please do not hesitate to contact me" (sounds formulaic)
- Letter format

### Why It's Human

- **Standard business format**: This is how professional letters are written
- **Pre-LLM convention**: These formulas existed for decades before AI
- **Genre appropriate**: Formal letters should be formal

### Verdict

**Not AI** - Business letter conventions predate LLMs. Formality is not AI.

---

## Example 5: Marketing Copy (Intentional)

### Text

```text
Experience the breathtaking beauty of coastal Maine. Our world-class resort offers visitors a
fascinating glimpse into New England's rich cultural heritage. Nestled within stunning natural
surroundings, the property seamlessly blends modern luxury with historic charm.
```

### Why It Might Flag

- "breathtaking", "world-class", "fascinating glimpse", "rich cultural heritage", "nestled",
  "seamlessly" (promotional language)
- Travel brochure style
- High AI vocabulary density

### Why It Might Be Human

- **Intentional marketing copy**: This is SUPPOSED to sound promotional
- **Professional copywriting**: Humans write marketing materials too
- **Genre convention**: Travel brochures used this style before AI

### Verdict

**Possibly Either** - Consider whether promotional tone is appropriate for context. If this is
marketing material, the style is intentional and acceptable. If this is encyclopedic content,
it's inappropriate regardless of author.

---

## Example 6: Literary/Creative Writing

### Text

```text
The city stretched before her like a vast tapestry of lights and shadows. Each neighborhood formed
a distinct thread in the broader landscape of urban life. The confluence of cultures created a
mosaic of experiences, a testament to human diversity.
```

### Why It Might Flag

- Uses "tapestry", "landscape", "confluence", "mosaic", "testament" (AI nouns)
- Metaphorical language
- Flowery prose

### Why It's Human

- **Literary devices**: Metaphors are legitimate in creative writing
- **Authorial style**: Some writers favor elaborate language
- **Pre-LLM technique**: Metaphorical writing existed for centuries

### Verdict

**Not AI** - Metaphors and literary devices are not AI indicators. These are stylistic choices.

---

## Example 7: Using Conjunctions

### Text

```text
The project failed. And that was a turning point. But the team learned valuable lessons. However,
they needed more time.
```

### Why It Might Flag

- Starts sentences with conjunctions: "And", "But", "However"

### Why It's Human

- **Grammatically acceptable**: Starting sentences with conjunctions is not wrong
- **Common in modern writing**: Journalists and writers do this regularly
- **Pre-dates AI**: This style existed long before LLMs

### Verdict

**Not AI** - Conjunction usage is NOT an AI indicator.

---

## Example 8: Specialized Vocabulary

### Text

```text

The differential diagnosis includes several esoteric conditions: acanthosis nigricans, xanthomas,
and eruptive xanthomatosis. The etiology remains obscure, though iatrogenic factors cannot be
discounted.
```

### Why It Might Flag

- Complex medical terminology
- Unusual, low-frequency words

### Why It's Human

- **LLMs avoid rare words**: AI models favor statistically common words
- **Technical accuracy**: Medical writing requires precise terminology
- **Specialist knowledge**: Experts use field-specific vocabulary

### Verdict

**Not AI** - Low-frequency, specialized vocabulary actually suggests HUMAN authorship.

---

## Example 9: Bland, Simple Prose

### Text

```text
The cat sat on the mat. It was gray. The room was quiet. The man read a book.
```

### Why It Might Flag

- Simple, "robotic" style
- Monotonous structure
- Lack of complexity

### Why It's Human

- **LLMs are effusive**: AI models actually produce flowery, elaborate text
- **Hemingway exists**: Some authors favor minimalism
- **Stylistic choice**: Simplicity can be deliberate

### Verdict

**Not AI** - Bland prose is NOT an AI indicator. LLMs tend toward floridity, not simplicity.

---

## Key Takeaways for Avoiding False Positives

### ❌ Do NOT Flag Based On

1. **Perfect grammar** - Skilled writers exist
2. **Formal style** - Appropriate in many contexts
3. **Technical terms** - Necessary in specialized fields
4. **Metaphors** - Literary devices are legitimate
5. **Conjunctions** - Common in modern writing
6. **Complex vocabulary** - Actually suggests human authorship
7. **Simple style** - Minimalism is a choice
8. **Lists and structure** - Common in all writing
9. **One pattern alone** - Need multiple indicators

### ✅ DO Flag Based On

1. **Definitive technical artifacts** - Chatbot markers, model tokens
2. **Extreme AI vocabulary density** - 10+ AI words per 500 words
3. **Multiple categories matching** - Content + Language + Style issues
4. **Context mismatch** - Chatbot artifacts in formal document
5. **Pattern clustering** - Many issues in short span
6. **Lack of human markers** - No unusual words, no personality, no errors

### Context Adjustment Guidelines

| Context                 | Adjustment                                          |
| ----------------------- | --------------------------------------------------- |
| Academic paper          | Higher threshold for formal vocabulary              |
| Technical docs          | Allow technical jargon like "ecosystem", "leverage" |
| Marketing material      | Promotional language may be intentional             |
| Creative writing        | Metaphors are expected                              |
| Business communication  | Formality is standard                               |
| Personal blog           | Informal style with personality suggests human      |
| Encyclopedia entry      | Neutral tone doesn't indicate AI                    |

### Red Flags That Override Context

Even with contextual adjustments, these are still problematic:

- Chatbot artifacts ("I hope this helps")
- Knowledge cutoff statements
- Placeholder text
- Model tokens
- Broken hallucinated references

---

## Testing Your Detection Skills

### Exercise: Human or AI?

Each example below - try to determine if it's human or AI before checking the answer.

#### Text A

```text
The algorithm facilitates the processing of large datasets, leveraging machine learning techniques
to optimize performance across diverse use cases.
```

**Your guess**: \_\_\_\_\_\_

**Answer**: Could be either - but probably **Human** if from a computer science paper. This is
standard technical writing. Need more context and additional indicators.

#### Text B

```text
The algorithm processes large datasets using machine learning to improve performance in different
situations. I hope this explanation helps clarify how it works!
```

**Your guess**: \_\_\_\_\_\_

**Answer**: **AI** - The chatbot artifact "I hope this explanation helps" is definitive.

#### Text C

```text
The study examined three variables: age, income, and education level.
```

**Your guess**: \_\_\_\_\_\_

**Answer**: **Human** - Rule of three is not an indicator. Three-item lists are standard in
research.

#### Text D

```text
In today's ever-evolving landscape, it's important to note that experts believe this paradigm shift
represents a pivotal moment, leveraging cutting-edge solutions to foster innovation.
```

**Your guess**: \_\_\_\_\_\_

**Answer**: **Likely AI** - Multiple AI patterns: filler opening, didactic disclaimer, weasel
words, AI vocabulary (paradigm, pivotal, leveraging, cutting-edge, foster). High density of issues
in one sentence suggests AI.

---

## Conclusion

**Remember**: The goal is accurate detection, not witch hunts.

- Require multiple indicators across categories
- Consider context and purpose
- Prioritize definitive markers over vocabulary
- When uncertain, assume human authorship
- False accusations harm collaboration more than missing some AI text

Use this skill responsibly and with appropriate humility about detection accuracy.
