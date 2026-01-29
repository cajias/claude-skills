---
name: ai-writing-detector
description: |
  Use when:
  (1) User asks to "review for AI writing" or "check for LLM signs"
  (2) User wants to "detect AI-generated text" or "humanize this document"
  (3) User wants to identify and fix signs of AI/LLM-generated writing
  (4) User mentions Wikipedia AI writing guidelines
author: cajias
version: 1.0.0
date: 2025-01-27
---

# AI Writing Detector Skill

## Problem

AI-generated text often contains telltale signs that reduce credibility and readability. Users need a systematic way to identify and fix these patterns.

## Context/Trigger

This skill activates when the user asks to:
- "review for AI writing"
- "check for LLM signs"
- "detect AI-generated text"
- "humanize this document"
- Any variation asking to identify and fix signs of AI/LLM-generated writing

Based on Wikipedia's comprehensive guide: https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing

## Important Caveats

- These are **potential signs**, not definitive proof
- Many patterns existed in human writing before LLMs
- False accusations harm collaboration and trust
- Context matters - consider the full picture
- Do NOT solely rely on AI detection tools (GPTZero, etc.) - they have significant error rates

## Detection Categories

### 1. CONTENT ISSUES

#### 1.1 Undue Emphasis on Symbolism/Legacy/Importance
**Pattern**: Puffing up importance with vague statements about broader significance.

**Red flags**:
- "marking a pivotal moment in..."
- "represents a significant shift toward..."
- "highlighting the enduring legacy of..."
- "reflects the transformative power of..."
- "contributes to the broader history of..."
- "plays a role in the ecosystem"
- "vital not only for X but also for Y"

**Fix**: Remove vague importance claims. State specific, verifiable facts instead.

#### 1.2 Undue Emphasis on Notability/Attribution
**Pattern**: Hitting readers over the head with claims of notability.

**Red flags**:
- "has been featured in *Wired*, *Refinery29*, and other prominent media outlets"
- "maintains an active social media presence"
- "independent coverage" (echoing Wikipedia guidelines)
- Listing media outlets without context of what they said

**Fix**: Remove media listing unless relevant. Cite specific claims, not general coverage.

#### 1.3 Superficial Analyses
**Pattern**: Attaching "-ing" phrases claiming significance without evidence.

**Red flags**:
- "highlighting its significance as..."
- "underscoring its role in..."
- "reflecting the influence of..."
- "emphasizing the importance of..."
- "illustrating X's lasting influence"
- Inanimate subjects "highlighting" or "underscoring" things

**Fix**: Remove editorial commentary. Let facts speak for themselves.

#### 1.4 Promotional/Advertisement Language
**Pattern**: Sounds like a travel brochure or product pitch.

**Red flags**:
- "Nestled within the breathtaking region of..."
- "offers visitors a fascinating glimpse into..."
- "seamlessly connecting..."
- "showcasing the state's rich heritage"
- "communicates a powerful emotional presence"
- "dependable, value-driven experiences"

**Fix**: Use neutral, factual language. Remove superlatives and marketing speak.

#### 1.5 Didactic Disclaimers
**Pattern**: Telling the reader what's "important to remember."

**Red flags**:
- "It's important to note that..."
- "It is crucial to differentiate..."
- "It's important to remember..."
- "However, it should be noted..."

**Fix**: Remove meta-commentary. Just state the information.

#### 1.6 Section Summaries
**Pattern**: Restating what was just said.

**Red flags**:
- "In summary,..."
- "Conclusion" sections that just repeat content
- Paragraphs ending with restatement of their main point

**Fix**: Remove redundant summaries. Trust the reader.

#### 1.7 "Challenges and Future Prospects" Formula
**Pattern**: Rigid outline with challenges section followed by optimistic conclusion.

**Red flags**:
- "Despite its [positive words], X faces challenges..."
- "Future investments in X could enhance..."
- "Despite these challenges, X continues to..."
- Separate "Challenges" and "Future Prospects" sections

**Fix**: Integrate challenges naturally. Remove speculation about future.

#### 1.8 Treating Titles as Proper Nouns
**Pattern**: Article titles introduced as if they were standalone real-world entities.

**Red flags**:
- "The 'Effects of X on Y' refers to..."
- "The 'List of X' is a curated compilation..."
- Treating a descriptive title as a named thing

**Fix**: Write naturally. Don't define the article title as if it's a concept.

#### 1.9 "Outlines of Negatives" Pattern
**Pattern**: Short sentences listing absent things with "no..., no..., just..."

**Red flags**:
- "No long-form profiles. No editorial insights. No coverage. Just recaps."
- "Not a career, not a body of work - just an algorithmic moment."
- "What matters is X, not Y, not Z."

**Fix**: Write in complete sentences. Explain what IS rather than what ISN'T.

---

### 2. LANGUAGE AND GRAMMAR

#### 2.1 Overused "AI Vocabulary" Words
**High-frequency AI words** (especially when multiple appear together):

| Category | Words |
|----------|-------|
| **Verbs** | delve, underscore, highlight, emphasize, showcase, leverage, navigate, foster, spearhead, bolster, fortify, grapple, hone, underpin, broaden, elevate, streamline, harness |
| **Adjectives** | crucial, pivotal, intricate, nuanced, comprehensive, multifaceted, robust, innovative, seamless, holistic, groundbreaking, cutting-edge, meticulous, versatile, dynamic |
| **Nouns** | tapestry, landscape, paradigm, realm, synergy, trajectory, cornerstone, catalyst, beacon, testament, hallmark, confluence, nexus, mosaic, bedrock |
| **Phrases** | "rich tapestry", "broader landscape", "key/integral/pivotal role", "significant/notable/remarkable", "a testament to", "poised to", "at the forefront" |

**Fix**: Replace with simpler, more specific language.

#### 2.2 Negative Parallelisms
**Pattern**: "Not only... but also..." or "It's not just about X, it's about Y"

**Red flags**:
- "constitutes not only X, but Y"
- "It's not just about the X; it's about the Y"
- Across sentences: "However, X took a path that..."

**Fix**: Simplify to direct statements.

#### 2.3 Rule of Three
**Pattern**: Everything comes in threes: "adjective, adjective, and adjective"

**Red flags**:
- "global SEO professionals, marketing experts, and growth hackers"
- "keynote sessions, panel discussions, and networking opportunities"
- Suspiciously consistent use of three-item lists

**Fix**: Vary list lengths. Use specific examples instead of categories.

#### 2.4 Vague Attributions (Weasel Words)
**Pattern**: Attributing claims to unnamed authorities.

**Red flags**:
- "has been described as..."
- "is of interest to researchers"
- "is described in scholarship as..."
- "Efforts are ongoing to..."
- "Experts believe..."

**Fix**: Name specific sources or remove the claim.

#### 2.5 Elegant Variation
**Pattern**: Using different synonyms for the same thing to avoid repetition.

**Red flags**:
- Subject called by name, then "the protagonist", then "the key figure", then "the artist"
- Artificially varying vocabulary for the same concept

**Fix**: Repeat terms when clarity requires it. Consistent terminology is fine.

#### 2.6 False Ranges
**Pattern**: "From X to Y" where X and Y aren't actually endpoints of a coherent scale.

**Red flags**:
- "from the singularity of the Big Bang to the grand cosmic web"
- "from problem-solving and tool-making to scientific discovery"
- Ranges where middle ground doesn't make sense

**Fix**: List items normally or describe the actual range if one exists.

---

### 3. STYLE AND FORMATTING

#### 3.1 Title Case in Headings
**Pattern**: Capitalizing All Main Words In Section Headings

**Fix**: Use sentence case (only capitalize first word and proper nouns).

#### 3.2 Excessive Boldface
**Pattern**: Bolding key terms, definitions, or "takeaways" throughout.

**Red flags**:
- Every concept bolded on first mention
- "Key takeaways" style formatting
- Sales-pitch-like emphasis

**Fix**: Reserve bold for article title and critical disambiguation only.

#### 3.3 Inline-Header Vertical Lists
**Pattern**: Lists with "**Header:** description" format.

**Red flags**:
- "1. **Historical Context:** The world was..."
- "- **Key Takeaway:** This shows that..."
- Numbered lists with inline bold headers

**Fix**: Use proper headings or write in prose.

#### 3.4 Emoji Usage
**Pattern**: Emojis in headings or bullet points.

**Red flags**:
- "Cognitive Dissonance Pattern:"
- "Key facts:"
- "Traditional Sanskrit Name:"

**Fix**: Remove all emojis from technical/formal documents.

#### 3.5 Excessive Em Dashes
**Pattern**: Overuse of em dashes (-) in formulaic ways.

**Red flags**:
- Multiple em dashes per paragraph
- Em dashes used where commas would suffice
- Sales-pitch-like punchy clauses set off by em dashes

**Fix**: Replace most em dashes with commas, parentheses, or periods.

#### 3.6 Curly Quotes and Apostrophes
**Pattern**: Using "curly" quotes instead of "straight" quotes.

**Note**: This alone isn't proof - Word and iOS also do this.

#### 3.7 Markdown in Non-Markdown Contexts
**Pattern**: Markdown syntax appearing where it shouldn't.

**Red flags**:
- `**bold**` or `*italic*` not rendered
- `## Heading` appearing as text
- `[link](url)` syntax
- Triple backticks (```)

**Fix**: Convert to proper format for the target platform.

---

### 4. TECHNICAL ARTIFACTS

#### 4.1 ChatGPT Reference Bugs
**Definitive AI markers**:
- `turn0search0`, `turn0image0`
- `:contentReference[oaicite:0]{index=0}`
- `[oai_citation:0source.com]`
- `[attached_file:1]`
- `<grok_card>` tags
- `({"attribution":{"attributableIndex":"X-Y"}})`

**Fix**: Remove entirely. These are copy-paste artifacts.

#### 4.2 UTM Parameters
**Pattern**: URLs with `utm_source=chatgpt.com` or `utm_source=openai`

**Note**: Proves ChatGPT was used for research, not necessarily that text is AI-generated.

#### 4.3 Knowledge Cutoff Disclaimers
**Pattern**: Disclaimers about information being current "as of" a date.

**Red flags**:
- "As of my last knowledge update in January 2022..."
- "While specific information is limited..."
- "Though the details aren't widely documented, they likely..."
- "No significant controversies have been documented as of..."

**Fix**: Remove disclaimers. Verify and update information.

#### 4.4 Prompt Refusals
**Pattern**: AI declining to do something.

**Red flags**:
- "As an AI language model, I can't..."
- "I'm not able to directly..."

**Fix**: Obviously remove. Indicates zero review of output.

#### 4.5 Placeholder Text
**Pattern**: Fill-in-the-blank templates.

**Red flags**:
- `[Entertainer's Name]`
- `[Describe the specific section...]`
- `2025-xx-xx` dates
- `<!-- Add if available with citation -->`

**Fix**: Fill in or remove placeholders.

#### 4.6 Subject Lines in Body Text
**Pattern**: Email subject lines pasted into document.

**Red flags**:
- "Subject: Request for Permission to Edit..."
- "Subject: Edit Request for..."

**Fix**: Remove subject lines entirely.

#### 4.7 Collaborative Communication Artifacts
**Pattern**: AI advice/prewriting meant for user, not final content.

**Red flags**:
- "In this section, we will discuss..."
- "If you plan to add this information..."
- "Here's a template for your..."
- "Would you like me to..."
- References to "Wikipedia's guidelines" in body text

**Fix**: Remove meta-commentary. Keep only final content.

#### 4.8 Broken/Hallucinated References
**Pattern**: Citations that don't exist or are fabricated.

**Red flags**:
- DOIs that resolve to unrelated articles
- Invalid ISBN checksums
- URLs returning 404 errors (especially if never archived)
- Author names that don't match the time period
- Book citations without page numbers

**Fix**: Verify every citation. Remove or replace hallucinated ones.

#### 4.9 Verbose Edit Summaries
**Pattern**: Unusually long, formal edit summaries.

**Red flags**:
- First-person paragraph explanations
- Itemizing Wikipedia conventions
- "Refined the language... ensured neutrality... adhered to encyclopedic standards"

**Fix**: Use concise edit summaries.

#### 4.10 Abrupt Cutoffs
**Pattern**: Text ending mid-sentence or mid-thought.

**Red flags**:
- Sentences that just stop
- `<|endoftext|>` markers
- Content that seems incomplete

**Fix**: Complete or remove truncated content.

#### 4.11 Footnote Markers
**Pattern**: LLM-specific footnote syntax.

**Red flags**:
- `<-` characters indicating footnotes
- Unusual footnote numbering like `<- <-2`

**Fix**: Convert to standard citation format.

---

### 5. BEHAVIORAL INDICATORS

#### 5.1 Sudden Style Shift
**Pattern**: Writing quality dramatically changes from editor's usual style.

**Red flags**:
- Sudden flawless grammar from editor with consistent errors elsewhere
- Complete change in vocabulary sophistication
- Different sentence structure patterns

**Note**: Be careful - people improve, and non-native speakers vary.

#### 5.2 English Variety Mismatch
**Pattern**: American English from Indian user writing about Indian topic.

**Red flags**:
- LLMs default to American English
- User's location suggests different variety
- Topic's national context suggests different variety

**Note**: Non-native speakers often mix varieties naturally.

#### 5.3 Date Considerations
**Pattern**: Text added before ChatGPT launch (Nov 30, 2022).

**Fact**: Pre-November 2022 text is almost certainly human-written.

---

### 6. FALSE POSITIVES TO AVOID

**These are NOT reliable AI indicators**:
- Perfect grammar (skilled writers exist)
- "Bland" or "robotic" prose (LLMs are actually effusive, not bland)
- Fancy/academic words (LLMs statistically favor common words)
- Formal letter-like writing (humans wrote letters before LLMs)
- Use of conjunctions (normal in essays)
- Bizarre wikitext (often browser extension bugs, not AI)
- Low-frequency unusual words (AI avoids these statistically)

**Remember**:
- AI detection tools have significant error rates
- Experts correctly identify AI ~90% of the time (10% false accusations)
- Non-experts do barely better than random chance
- False accusations drive away contributors

---

## Review Process

When reviewing a document, iterate through these steps:

### Pass 1: Scan for Technical Artifacts
Look for definitive markers (turn0search, contentReference, utm_source, etc.)

### Pass 2: Check Vocabulary
Highlight overused AI words. Count occurrences.

### Pass 3: Analyze Structure
- Are there rigid "Challenges/Future Prospects" sections?
- Excessive rule-of-three patterns?
- Section summaries that just repeat content?

### Pass 4: Examine Claims
- Vague importance claims?
- Superficial analyses ("highlighting", "underscoring")?
- Weasel words and vague attributions?

### Pass 5: Review Style
- Title case headings?
- Excessive bold/em dashes?
- Emojis or markdown artifacts?

### Pass 6: Apply Fixes
For each issue found:
1. Identify the specific problematic text
2. Explain why it's an AI marker
3. Provide a concrete fix
4. Apply the fix

### Pass 7: Verify
Re-read the document to ensure:
- Fixes don't introduce new problems
- Document still makes sense
- No AI markers remain

---

## Usage Instructions

When I invoke this skill, I will:

1. **Read the target document**
2. **Perform all 7 passes** of the review process
3. **Generate a report** listing:
   - Issues found (with line references)
   - Category of each issue
   - Suggested fix for each issue
4. **Apply fixes** to the document
5. **Re-review** the updated document
6. **Repeat** until no issues remain or only false-positive-prone items remain

## Example Invocation

**User**: "Review this ADR for AI writing signs"

**Assistant**:
1. Reads the document
2. Performs systematic review using the categories above
3. Reports findings like:
   ```
   Line 45: "marking a pivotal moment" - Undue emphasis (1.1)
   Fix: Remove. State the specific significance if any.

   Line 67: "highlighting its crucial role" - Superficial analysis (1.3)
   Fix: Remove "-ing" clause. Let facts speak.

   Line 89: "comprehensive, robust, and innovative" - Rule of three + AI vocab (2.1, 2.3)
   Fix: Use specific description instead.
   ```
4. Applies fixes
5. Re-reviews until clean
