# AI Writing Pattern Database

Comprehensive reference guide for all patterns checked by the AI Writing Humanizer skill.

## Category 1: Inflated Symbolism & Meaning (PRIORITY: HIGH)

These phrases artificially inflate importance or add unwarranted gravitas:

| Pattern                       | Type   | Replacement Suggestions                    |
| ----------------------------- | ------ | ------------------------------------------ |
| `stands as a testament`       | phrase | "shows", "demonstrates", "illustrates"     |
| `serves as a testament`       | phrase | "shows", "demonstrates"                    |
| `is a testament`              | phrase | "shows", "proves"                          |
| `plays a vital role`          | phrase | "contributes to", "helps with", "is part of" |
| `plays a significant role`    | phrase | "contributes to", "affects"                |
| `plays a crucial role`        | phrase | "is important for", "affects"              |
| `plays a pivotal role`        | phrase | "influences", "shapes"                     |
| `underscores its importance`  | phrase | (delete - unnecessary editorializing)      |
| `underscores the significance`| phrase | (delete - unnecessary editorializing)      |
| `continue(s) to captivate`    | phrase | "interest", "attracts"                     |
| `leaves a lasting impact`     | phrase | "influenced", "changed", "affected"        |
| `watershed moment`            | phrase | "turning point", "important event"         |
| `key turning point`           | phrase | "turning point", "change"                  |
| `deeply rooted`               | phrase | "based on", "connected to", "traditional"  |
| `profound heritage`           | phrase | "history", "traditions"                    |
| `steadfast dedication`        | phrase | "commitment", "dedication"                 |
| `solidifies`                  | word   | "confirms", "establishes", "strengthens"   |
| `embodies`                    | word   | "represents", "shows"                      |
| `epitomizes`                  | word   | "represents", "shows"                      |

## Category 2: Promotional/Travel Brochure Language (PRIORITY: HIGH)

Text reads like marketing copy or tourism website:

| Pattern                   | Type   | Replacement Suggestions                |
| ------------------------- | ------ | -------------------------------------- |
| `rich cultural heritage`  | phrase | "history", "traditions", "culture"     |
| `rich history`            | phrase | "long history", "history"              |
| `rich tapestry`           | phrase | "mix", "combination", "variety"        |
| `rich cultural tapestry`  | phrase | "diverse culture", "cultural mix"      |
| `breathtaking`            | word   | "impressive", "notable", "striking"    |
| `stunning`                | word   | "impressive", "notable", "attractive"  |
| `must-visit`              | word   | "notable", "popular", "well-known"     |
| `must-see`                | word   | "notable", "popular", "well-known"     |
| `stunning natural beauty` | phrase | "natural scenery", "landscape"         |
| `scenic beauty`           | phrase | "scenery", "views", "landscape"        |
| `enduring legacy`         | phrase | "influence", "impact", "lasting effect" |
| `lasting legacy`          | phrase | "influence", "continued impact"        |
| `dynamic hub`             | phrase | "center", "active area"                |
| `vibrant community`       | phrase | "active community", "community"        |
| `coastal charm`           | phrase | "coastal character", "seaside atmosphere" |
| `captivates visitors`     | phrase | "attracts visitors", "interests visitors" |
| `captivates residents`    | phrase | "appeals to residents"                 |
| `hidden gem`              | phrase | "lesser-known", "overlooked"           |
| `world-class`             | word   | "high-quality", "excellent", "notable" |

## Category 3: Editorializing & Commentary (PRIORITY: HIGH)

These phrases break neutral encyclopedic tone:

| Pattern                               | Type   | Replacement Suggestions            |
| ------------------------------------- | ------ | ---------------------------------- |
| `it's important to note`              | phrase | (delete and state directly)        |
| `it is important to note`             | phrase | (delete and state directly)        |
| `it's worth noting`                   | phrase | (delete and state directly)        |
| `it is worth`                         | phrase | (delete and state directly)        |
| `importantly`                         | word   | (delete - let facts speak)         |
| `no discussion would be complete without` | phrase | (delete - just discuss it)     |
| `in this article`                     | phrase | (delete - self-referential)        |
| `as mentioned earlier`                | phrase | (delete or restructure)            |
| `needless to say`                     | phrase | (delete - if needless, don't say it) |

## Category 4: Overused Conjunctive/Transitional Phrases (PRIORITY: MEDIUM)

Not always wrong, but flag when multiple appear in same text:

| Pattern             | Flag When                             |
| ------------------- | ------------------------------------- |
| `moreover`          | >1 occurrence per 500 words           |
| `furthermore`       | >1 occurrence per 500 words           |
| `additionally`      | >1 occurrence per 500 words           |
| `in addition`       | >1 occurrence per 500 words           |
| `on the other hand` | >1 occurrence per 500 words           |
| `however`           | >2 occurrences per 500 words          |
| `in contrast`       | >1 occurrence per 500 words           |
| `nevertheless`      | >1 occurrence per 500 words           |
| `consequently`      | >1 occurrence per 500 words           |

**Replacement strategy**: Vary sentence structure, use simpler connectors ("but", "and",
"also"), or restructure to eliminate need for transition.

## Category 5: Negative Parallelism Pattern (PRIORITY: HIGH)

Pattern: "It's not X, it's Y" or "not just X, but Y" or "not only X but also Y"

These create false drama and artificial contrast.

**Detection regex**:

```regex
(not just|not only|not merely|it's not|isn't just|more than just).{1,50}(but|but also|it's|rather)
```

**Replacement strategy**: Rephrase to direct statement. Instead of "It's not just a tool, it's
a revolution" → "The tool significantly changed how people work"

## Category 6: Superficial Participle Endings (PRIORITY: HIGH)

Sentences ending with vague "-ing" clauses that add no real information:

| Pattern           | Type   | Action                    |
| ----------------- | ------ | ------------------------- |
| `, ensuring...`   | ending | Delete or make specific   |
| `, highlighting...` | ending | Delete or make specific |
| `, emphasizing...` | ending | Delete or make specific  |
| `, reflecting...` | ending | Delete or make specific   |
| `, underscoring...` | ending | Delete or make specific |
| `, demonstrating...` | ending | Delete or make specific |
| `, showcasing...` | ending | Delete or make specific   |
| `, signaling...`  | ending | Delete or make specific   |
| `, cementing...`  | ending | Delete or make specific   |
| `, solidifying...` | ending | Delete or make specific  |

**Detection regex**:

```regex
, (ensuring|highlighting|emphasizing|reflecting|underscoring|demonstrating|showcasing|signaling|cementing|solidifying)\b
```

**Example**:

- Bad: "The company released quarterly earnings, highlighting its commitment to transparency."
- Good: "The company released quarterly earnings."

## Category 7: Weasel Wording / Vague Attribution (PRIORITY: MEDIUM)

Phrases that suggest authority without providing sources:

| Pattern                  | Type   | Action                           |
| ------------------------ | ------ | -------------------------------- |
| `industry reports suggest` | phrase | Cite specific report or remove |
| `observers have noted`   | phrase | Name the observers or remove     |
| `some critics argue`     | phrase | Name the critics or remove       |
| `experts say`            | phrase | Name the experts or remove       |
| `many believe`           | phrase | Cite source or remove            |
| `it has been said`       | phrase | Cite who said it or remove       |
| `is widely considered`   | phrase | Cite sources or rephrase         |
| `is often regarded as`   | phrase | Cite sources or rephrase         |
| `according to sources`   | phrase | Name the sources                 |
| `studies show`           | phrase | Cite the studies                 |
| `research suggests`      | phrase | Cite the research                |
| `has been described as`  | phrase | Cite who described it            |

## Category 8: Em Dash Overuse (PRIORITY: MEDIUM)

AI uses em dashes (—) more frequently than human writers, especially in places where commas or
parentheses would be more natural.

**Detection**:

- Count em dashes per 500 words
- Flag if >2 em dashes per 500 words
- Flag em dashes used for emphasis rather than parenthetical information

**Replacement strategy**: Replace with commas, parentheses, or restructure sentence.

## Category 9: Rule of Three Overuse (PRIORITY: MEDIUM)

AI overuses three-part lists:

**Detection regex**: `\b(\w+),\s+(\w+),?\s+and\s+(\w+)\b` when appearing multiple times

**Examples to flag**:

- "convenient, efficient, and innovative"
- "keynote sessions, panel discussions, and networking opportunities"
- "speed, accuracy, and reliability"

**Replacement strategy**: Vary list lengths (sometimes 2, sometimes 4), or restructure entirely.

## Category 10: Formatting Patterns (PRIORITY: LOW)

| Pattern                    | Detection                              | Action              |
| -------------------------- | -------------------------------------- | ------------------- |
| Title Case in Headers      | Every main word capitalized            | Use sentence case   |
| Excessive Bold             | >3 bold phrases per section            | Reduce bolding      |
| Uniform Bullet Points      | Every item follows "**Topic:** description" | Vary formatting |
| Markdown artifacts         | `*asterisks*`, `_underscores_`         | Use proper formatting |

## Category 11: Buzzwords & Jargon (PRIORITY: HIGH)

| Word/Phrase      | Replacement                                      |
| ---------------- | ------------------------------------------------ |
| `delve`          | "explore", "examine", "look at"                  |
| `delve into`     | "explore", "examine"                             |
| `cutting-edge`   | "modern", "new", "advanced"                      |
| `revolutionary`  | "new", "significant", "innovative"               |
| `game-changing`  | "significant", "important"                       |
| `groundbreaking` | "new", "innovative", "first"                     |
| `multifaceted`   | "complex", "varied"                              |
| `leverage`       | "use", "apply"                                   |
| `utilize`        | "use"                                            |
| `facilitate`     | "help", "enable", "allow"                        |
| `optimize`       | "improve"                                        |
| `synergy`        | "cooperation", "combination"                     |
| `paradigm`       | "model", "approach", "method"                    |
| `holistic`       | "complete", "comprehensive", "overall"           |
| `seamlessly`     | "smoothly", "easily"                             |
| `robust`         | "strong", "reliable"                             |
| `scalable`       | (be specific about what scales)                  |
| `ecosystem`      | "system", "environment", "community"             |
| `empower`        | "enable", "help", "allow"                        |
| `harness`        | "use", "apply"                                   |

## Category 12: Filler Openings & Closings (PRIORITY: HIGH)

| Pattern                           | Action                                    |
| --------------------------------- | ----------------------------------------- |
| `In today's ever-evolving world`  | Delete entirely                           |
| `In the ever-evolving landscape`  | Delete entirely                           |
| `In today's fast-paced world`     | Delete entirely                           |
| `As we navigate`                  | Delete or rephrase                        |
| `In summary`                      | Delete (let content summarize itself)     |
| `In conclusion`                   | Delete                                    |
| `In essence`                      | Delete                                    |
| `Overall`                         | Often delete                              |
| `To summarize`                    | Delete                                    |
| `All in all`                      | Delete                                    |
| `At the end of the day`           | Delete                                    |
| `In a nutshell`                   | Delete                                    |

## Category 13: Chatbot Artifacts (PRIORITY: CRITICAL - Instant Flag)

These are dead giveaways of AI generation:

| Pattern                       | Type                |
| ----------------------------- | ------------------- |
| `I hope this helps`           | chatbot response    |
| `Certainly!`                  | chatbot response    |
| `Let me know if you`          | chatbot response    |
| `feel free to ask`            | chatbot response    |
| `As an AI`                    | chatbot disclosure  |
| `as a language model`         | chatbot disclosure  |
| `I don't have personal`       | chatbot disclosure  |
| `as of my last`               | knowledge cutoff    |
| `as of my knowledge cutoff`   | knowledge cutoff    |
| `up to my last training`      | knowledge cutoff    |
| `turn0search0`                | ChatGPT artifact    |
| `Based on my training`        | chatbot disclosure  |

## Category 14: Section Conclusions (PRIORITY: MEDIUM)

AI tends to add unnecessary concluding sentences to sections:

**Detection**: Last sentence of paragraph containing:

- "continues to be"
- "remains to be seen"
- "time will tell"
- "only time will tell"
- "the future holds"
- "looking ahead"
- "moving forward"

**Action**: Usually delete - let facts stand without editorial wrap-up.

## Category 15: Hedge Words Overuse (PRIORITY: LOW)

Flag when multiple hedge words appear in close proximity:

| Word         |
| ------------ |
| `arguably`   |
| `somewhat`   |
| `generally`  |
| `relatively` |
| `potentially`|
| `possibly`   |
| `perhaps`    |
| `likely`     |
| `might`      |
| `may`        |
| `could`      |

**Detection**: Flag if >3 hedge words per 200 words.

## Usage Notes

### Pattern Matching

- **Case-insensitive**: All patterns match case-insensitively unless specified
- **Word boundaries**: Word patterns use word boundaries to avoid partial matches
- **Regex patterns**: Patterns marked with `regex: true` use regular expression matching
- **Context-aware**: Consider surrounding text when determining if a match is problematic

### Priority Levels

- **CRITICAL**: Instant flags - these are clear AI artifacts
- **HIGH**: Strong indicators of AI writing - address immediately
- **MEDIUM**: Context-dependent - may be acceptable in some cases
- **LOW**: Minor indicators - flag only when combined with other patterns

### Frequency-Based Detection

Some categories use frequency thresholds:

- **Per 500 words**: Calculate occurrences per 500 words of text
- **Per 200 words**: Calculate occurrences per 200 words (for denser patterns)
- **Multiple occurrences**: Flag patterns that appear more than once in the same document

## Pattern Updates

This database is maintained based on:

- Wikipedia's "Signs of AI Writing" guidelines
- Community feedback and observations
- Analysis of AI-generated vs human-written text
- Emerging patterns in newer AI models

Version: 1.0.0
Last updated: 2025-12-16
