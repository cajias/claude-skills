# AI Writing Detection Analysis

Analyze the following text for signs of AI-generated writing. Follow this systematic approach:

## Text to Analyze

```text
{{INPUT_TEXT}}
```

## Detection Workflow

### Step 1: Scan for Technical Artifacts (DEFINITIVE MARKERS)

Check for these **smoking gun** indicators from `patterns/artifact-patterns.json`:

- ChatGPT artifacts: `turn0search0`, `turn0image0`, citation formats
- Grok markers: `<grok_card>` tags
- UTM parameters: `utm_source=chatgpt.com`
- Knowledge cutoff disclaimers: "as of my last knowledge update"
- Prompt refusals: "as an AI language model, I can't"
- Placeholder text: `[Entertainer's Name]`, `2025-xx-xx`
- Collaborative artifacts: "Would you like me to...", "I hope this helps"
- Model tokens: `<|endoftext|>`, `<|im_end|>`
- Footnote markers: `↩` characters
- Subject lines in body: "Subject:", "Re:"

**If ANY definitive marker found**: Set confidence to HIGH and flag immediately.

### Step 2: Count AI Vocabulary Patterns

From `patterns/language-patterns.json`, count occurrences of:

**High-frequency AI verbs**:

- delve, underscore, highlight, showcase, leverage, navigate, foster, spearhead, bolster,
  fortify, grapple, hone, underpin, elevate, streamline, harness

**High-frequency AI adjectives**:

- pivotal, intricate, nuanced, multifaceted, robust, seamless, holistic, groundbreaking,
  cutting-edge, meticulous, versatile, dynamic, crucial

**High-frequency AI nouns**:

- tapestry, landscape (metaphorical), paradigm, realm, synergy, trajectory, cornerstone,
  catalyst, testament, hallmark, confluence, nexus, mosaic, bedrock

**High-frequency AI phrases**:

- rich tapestry, broader landscape, key/integral/pivotal role, a testament to, poised to, at
  the forefront

**Calculate density**: Total AI vocabulary words / (Word count / 500)

- Flag if density > 5 per 500 words (Medium confidence)
- Flag if density > 10 per 500 words (High confidence)

### Step 3: Analyze Content Structure

From `patterns/content-patterns.json`, check for:

**1.1 Undue Emphasis on Symbolism/Legacy**:

- "marking a pivotal moment"
- "represents a significant shift"
- "highlighting the enduring legacy"
- "reflects the transformative power"
- "vital not only for X but also for Y"

**1.2 Notability Emphasis**:

- Lists media outlets without context
- "maintains an active social media presence"

**1.3 Superficial Analyses**:

- "highlighting its significance as"
- "underscoring its role in"
- Inanimate objects "highlighting" or "emphasizing" things

**1.4 Promotional Language**:

- "nestled within the breathtaking"
- "offers visitors a fascinating glimpse"
- "seamlessly connecting"

**1.5 Didactic Disclaimers**:

- "It's important to note that"
- "It is crucial to differentiate"
- "However, it should be noted"

**1.6 Section Summaries**:

- "In summary," at paragraph ends
- Generic concluding statements

**1.7 Challenges/Future Prospects Formula**:

- "Despite its [positive], X faces challenges"
- "Future investments could enhance"
- Check for separate "Challenges" AND "Future Prospects" sections

**1.8 Titles as Proper Nouns**:

- "The 'Effects of X on Y' refers to"
- "The 'List of X' is a curated compilation"

**1.9 Negative Outlines**:

- "No X. No Y. Just Z."
- "Not a X, not a Y — just Z"

### Step 4: Examine Language Patterns

From `patterns/language-patterns.json`:

**2.2 Negative Parallelisms**:

- "constitutes not only X, but Y"
- "It's not just about X; it's about Y"
- "not just X but Y" / "not only X but also Y"

**2.3 Rule of Three**:

- Count three-item lists: "X, Y, and Z"
- Flag if appears >3 times per section

**2.4 Weasel Words**:

- "has been described as" (without citation)
- "experts believe" (unnamed)
- "studies show" (uncited)
- "research suggests" (unspecified)

**2.5 Elegant Variation**:

- Check if subject called by multiple different titles

**2.6 False Ranges**:

- "from X to Y" used for dramatic effect without meaningful range

### Step 5: Review Style and Formatting

From `patterns/style-patterns.json`:

- **Title Case Headers**: Every Word Capitalized
- **Excessive Bold**: >3 bold phrases per paragraph
- **Inline Headers**: "1. **Topic:** Description" format
- **Emoji Usage**: In formal contexts
- **Em Dash Overuse**: >2 per 500 words
- **Curly Quotes**: 'Smart quotes' instead of 'straight quotes'
- **Markdown Artifacts**: `**bold**`, `*italic*` in plain text

### Step 6: Calculate Confidence Score

Use this weighted scoring:

| Category              | Weight | Calculation                |
| --------------------- | ------ | -------------------------- |
| Definitive markers    | 50%    | Any found = 50 points      |
| Content issues        | 20%    | (Count / 10) \* 20         |
| Language patterns     | 15%    | (Density score / 15) \* 15 |
| Style issues          | 10%    | (Count / 5) \* 10          |
| Behavioral indicators | 5%     | Manual assessment          |
| **TOTAL**             | 100%   | Sum all weighted scores    |

**Confidence Levels**:

- **HIGH** (70-100%): Definitive markers OR very high pattern density
- **MEDIUM** (40-69%): Multiple patterns across categories
- **LOW** (20-39%): Few scattered patterns
- **NONE** (0-19%): Minimal or no AI indicators

## Important Caveats to Include

Always include these warnings in your analysis:

- ⚠️ These are **potential signs**, not definitive proof
- ⚠️ Many patterns existed in human writing before LLMs
- ⚠️ False accusations harm collaboration and trust
- ⚠️ Context matters - consider the full picture
- ⚠️ Do NOT solely rely on AI detection tools (significant error rates)
- ⚠️ Experts correctly identify AI ~90% of time (10% false positives)
- ⚠️ Non-experts do barely better than random chance

## False Positives to Avoid

From `patterns/false-positives.json`, do NOT flag these:

- Perfect grammar (skilled writers exist)
- Bland/robotic prose (LLMs are actually effusive)
- Fancy/academic words (LLMs favor common words statistically)
- Formal letter-like writing
- Use of conjunctions
- Low-frequency unusual words (AI avoids these)
- Lists and structured formatting

## Context Considerations

Adjust detection thresholds based on context:

- **Technical Documentation**: Terms like "ecosystem", "leverage" may be legitimate
- **Academic Writing**: Formal language expected, higher vocabulary threshold
- **Marketing Copy**: Promotional language may be intentional
- **Creative Writing**: Metaphors should not be automatically flagged

## Output Format

Proceed to generate report using the format specified in `prompts/report-prompt.md`.
