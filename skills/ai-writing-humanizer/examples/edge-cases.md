# Edge Cases and Tricky Scenarios

This document covers challenging situations where AI writing patterns may be acceptable, ambiguous,
or require special handling.

## Case 1: Legitimate Technical Terms

### Scenario

Technical documentation uses terms that appear in the buzzword list.

**Text**:

"The Kubernetes ecosystem includes robust monitoring tools that leverage the cluster API to
optimize resource allocation."

**Issue**: "ecosystem", "robust", "leverage", "optimize" all flagged as buzzwords.

### Analysis

- "Kubernetes ecosystem" is an established technical term
- "cluster API" is a specific API name
- "optimize resource allocation" is technically accurate

### Resolution

**Option A (Strict)**: Replace all buzzwords

"The Kubernetes environment includes strong monitoring tools that use the cluster API to improve
resource allocation."

**Option B (Context-Aware)**: Keep technical terms, replace only general buzzwords

"The Kubernetes ecosystem includes strong monitoring tools that use the cluster API to improve
resource allocation."

### Recommendation

Use Option B for technical documentation. Keep established technical terms ("Kubernetes
ecosystem") but still replace generic buzzwords ("robust" → "strong", "leverage" → "use").

---

## Case 2: Cited Weasel Words

### Scenario

Weasel words appear with proper citations.

**Text**:

"According to a 2024 Stanford study (Chen et al.), experts say the approach shows promise."

**Issue**: "experts say" flagged as weasel wording.

### Analysis

The phrase has a proper citation, making it acceptable.

### Resolution

**Do not flag** when:

- Citation precedes or follows the claim
- Specific source named
- Verifiable reference provided

**Do flag** when:

"Experts say the approach shows promise." (no citation)

### Recommendation

Check for citations within 1-2 sentences before flagging weasel words.

---

## Case 3: Intentional Rule of Three

### Scenario

Three-item lists used for emphasis or completeness.

**Text**:

"The system checks for accuracy, completeness, and consistency—the three pillars of data quality."

**Issue**: Three-item list flagged.

### Analysis

This is intentional structure referencing "three pillars" explicitly.

### Resolution

**Do not flag** when:

- List is explained or referenced ("three pillars", "three types")
- Grammatical requirement (serial comma)
- Only occurrence in document

**Do flag** when:

- Multiple three-item lists throughout document
- Lists appear formulaic or repetitive
- No clear reason for exactly three items

### Recommendation

Flag only if multiple three-item lists appear without variation.

---

## Case 4: Academic Hedging

### Scenario

Academic writing requires uncertainty qualifiers.

**Text**:

"The results may suggest a potential correlation, though the data could indicate alternative
explanations."

**Issue**: Multiple hedge words ("may", "potential", "could") in close proximity.

### Analysis

Academic writing legitimately requires hedging to avoid overclaiming.

### Resolution

**Do not flag** when:

- Expressing genuine scientific uncertainty
- Following academic conventions
- Appropriate use of tentative language

**Do flag** when:

- Hedge words used unnecessarily
- Hedging replaces clear statements
- Excessive hedging undermines message

### Recommendation

For academic writing, increase hedge word threshold or skip this category.

---

## Case 5: Em Dashes for Clarity

### Scenario

Em dashes used appropriately for parenthetical information.

**Text**:

"The system—which was developed in 2023—processes data in real-time. The algorithm—based on neural
networks—achieves 95% accuracy. Results—both in testing and production—confirm the approach."

**Issue**: 3 em dashes in short text (flagged for overuse).

### Analysis

All em dashes provide parenthetical information, not emphasis.

### Resolution

**Acceptable use**:

- Parenthetical clauses (like parentheses)
- Abrupt topic changes
- Emphasis (sparingly)

**Problematic use**:

- Multiple in short text
- Used where commas would work
- Creating dramatic pauses artificially

### Recommendation

Review each em dash individually. Suggest alternatives (commas, parentheses) for some but not all.

---

## Case 6: "Important to Note" with Actual Importance

### Scenario

Editorializing phrase used to genuinely highlight critical information.

**Text**:

"The medication is generally safe. It's important to note that pregnant women should not take this
medication."

**Issue**: "It's important to note" flagged as editorializing.

### Analysis

This genuinely introduces critical safety information.

### Resolution

**Better phrasing**:

"The medication is generally safe. Pregnant women should not take this medication."

OR

"The medication is generally safe. Warning: Pregnant women should not take this medication."

### Recommendation

Always delete "it's important to note" but ensure the critical information remains prominent.
Consider adding "Warning:", "Note:", or restructuring for emphasis.

---

## Case 7: "Leverage" in Financial Context

### Scenario

"Leverage" used in its literal financial meaning.

**Text**:

"The company can leverage its assets to secure better loan terms, leveraging a debt-to-equity
ratio of 2:1."

**Issue**: Both instances of "leverage" flagged as buzzwords.

### Analysis

First use is legitimate financial term. Second use could be replaced.

### Resolution

**Better phrasing**:

"The company can leverage its assets to secure better loan terms, using a debt-to-equity ratio
of 2:1."

Keep financial/legal technical meaning, replace generic usage.

### Recommendation

For domain-specific terminology, check context. Keep legitimate uses, replace generic buzzword
usage.

---

## Case 8: Participle Ending with Substantive Information

### Scenario

Participle ending adds meaningful information, not just commentary.

**Text**:

"The company released earnings of $2.1 million, exceeding analyst expectations by 15%."

**Issue**: ", exceeding" flagged as participle ending.

### Analysis

The participle clause adds factual, quantifiable information.

### Resolution

**Keep as is** or **rephrase without participle**:

"The company released earnings of $2.1 million, which exceeded analyst expectations by 15%."

OR

"The company released earnings of $2.1 million. This exceeded analyst expectations by 15%."

### Recommendation

Distinguish between:

- **Substantive participles**: Add facts → Consider keeping or rephrasing
- **Commentary participles**: Add opinion → Delete

---

## Case 9: "Continues to" in Historical Context

### Scenario

"Continues to" describes ongoing situation factually.

**Text**:

"The building, constructed in 1850, continues to serve as the town hall."

**Issue**: "continues to" flagged as section conclusion pattern.

### Analysis

This is factual statement about ongoing use, not editorial wrap-up.

### Resolution

**Acceptable**:

- Factual ongoing situations
- Historical context
- Comparative statements

**Problematic**:

- Generic conclusions ("continues to be relevant")
- Vague futures ("continues to evolve")
- Editorial wrap-ups

### Recommendation

Check if "continues to" is followed by specific fact or vague generality.

---

## Case 10: "Rich History" in Historical Writing

### Scenario

Historical writing describes genuinely extensive history.

**Text**:

"The city has a rich history spanning 2,000 years, including periods under Roman, Byzantine, and
Ottoman rule."

**Issue**: "rich history" flagged as promotional language.

### Analysis

The extensive history justifies the descriptor.

### Resolution

**Better alternatives**:

"The city has a long history spanning 2,000 years..."

OR

"The city's 2,000-year history includes periods under Roman, Byzantine, and Ottoman rule."

### Recommendation

Replace "rich history" even when justified—more specific descriptions are always better.

---

## Case 11: Multiple Issues in One Sentence

### Scenario

Single sentence contains multiple overlapping patterns.

**Text**:

"In today's ever-evolving landscape, it's important to note that the cutting-edge platform
leverages AI to facilitate seamless collaboration, ensuring optimal results."

**Issues**:

1. Filler opening ("In today's ever-evolving landscape")
2. Editorializing ("it's important to note that")
3. Buzzwords ("cutting-edge", "leverages", "facilitate", "seamlessly", "optimal")
4. Participle ending (", ensuring optimal results")

### Resolution

**Step-by-step**:

1. Delete filler: "It's important to note that the cutting-edge platform..."
2. Delete editorializing: "The cutting-edge platform..."
3. Replace buzzwords: "The modern platform uses AI to enable smooth collaboration"
4. Delete participle: "The modern platform uses AI to enable smooth collaboration."

**Final**: "The modern platform uses AI to enable smooth collaboration."

### Recommendation

Address issues in priority order: critical > high > medium > low. Each fix may naturally resolve
others.

---

## Case 12: False Positive - Natural Human Writing

### Scenario

Naturally written text flagged due to coincidental pattern match.

**Text**:

"The artist's work embodies the spirit of the era."

**Issue**: "embodies" flagged as inflated symbolism.

### Analysis

"Embodies" is appropriate and precise in this context about art.

### Resolution

**Context check**:

- Is the word used precisely and meaningfully?
- Does replacement improve clarity?
- Would a human writer naturally use this word here?

In this case: **Do not change**. "Embodies" is appropriate for describing artistic representation.

### Recommendation

Not all flagged patterns need fixing. Use judgment. When in doubt, err on side of keeping
well-chosen words.

---

## Case 13: Negative Parallelism with Necessary Contrast

### Scenario

Negative parallelism used to make important distinction.

**Text**:

"The treatment is not curative, but palliative, focusing on symptom management rather than
disease elimination."

**Issue**: Negative parallelism pattern flagged.

### Analysis

This makes a medically important distinction between curative and palliative treatment.

### Resolution

**Keep but refine**:

"The treatment is palliative, not curative. It focuses on symptom management rather than disease
elimination."

OR simply:

"The treatment is palliative, focusing on symptom management rather than disease elimination."

### Recommendation

Negative parallelism is acceptable when making necessary technical or factual distinctions. Just
ensure it's not used for artificial drama.

---

## Case 14: Buzzwords in Brand Names

### Scenario

Buzzwords appear in product or company names.

**Text**:

"The RobustDB database system leverages OptimizeEngine to facilitate queries."

**Issue**: "RobustDB", "leverages", "OptimizeEngine", "facilitate" flagged.

### Analysis

"RobustDB" and "OptimizeEngine" are product names (hypothetically). Should not be changed.

### Resolution

**Do not change proper nouns**, but fix surrounding buzzwords:

"The RobustDB database system uses OptimizeEngine to enable queries."

### Recommendation

Preserve:

- Product names
- Company names
- Software/framework names
- Trademarked terms

Replace everything else.

---

## Case 15: Cultural/Literary References

### Scenario

Flagged phrase is literary allusion or cultural reference.

**Text**:

"The project stands as a testament to the team's dedication, echoing the cathedral builders of
medieval Europe."

**Issue**: "stands as a testament" flagged.

### Analysis

This is intentional literary reference and metaphor.

### Resolution

**For creative writing**: May be acceptable

**For encyclopedic writing**: Still remove

"The project demonstrates the team's dedication, recalling the cathedral builders of medieval
Europe."

### Recommendation

Genre matters. Creative/literary writing has more flexibility. Encyclopedic/technical writing
should still avoid these patterns.

---

## Case 16: Lists with Natural Three-Item Structure

### Scenario

Three items represent actual complete category.

**Text**:

"The three branches of US government are executive, legislative, and judicial."

**Issue**: Three-item list flagged.

### Analysis

Three items is the correct, complete list—not an AI pattern.

### Resolution

**Do not flag** when:

- Representing actual triplet (three branches, three laws, three phases)
- Explicitly stated as three ("the three types", "three main factors")
- Factually accurate enumeration

**Do flag** when:

- Multiple unrelated three-item lists
- Could be two or four items equally well
- Appears formulaic

### Recommendation

Check if three items is factually necessary or just stylistic choice.

---

## General Guidelines for Edge Cases

### When to Keep Flagged Patterns

1. **Technical terminology** in appropriate context
2. **Proper nouns** and brand names
3. **Domain-specific language** (finance, medicine, law)
4. **Cited claims** (weasel words with proper attribution)
5. **Necessary qualifiers** (academic hedging, medical disclaimers)
6. **Factual descriptions** (ongoing situations, historical spans)
7. **Intentional literary devices** (in creative writing)

### When to Still Flag/Replace

1. **Generic buzzwords** even in technical writing
2. **Promotional language** even when describing impressive things
3. **Editorializing** even when introducing important information
4. **Participle endings** unless adding substantive facts
5. **Filler phrases** always (no exceptions)
6. **Chatbot artifacts** always (no exceptions)

### Decision Framework

Ask these questions:

1. **Does the word/phrase add meaning?** If no → remove
2. **Is it technically precise?** If yes and technical → keep
3. **Would replacement lose information?** If yes → consider keeping
4. **Is it a proper noun?** If yes → keep
5. **Does it match the genre?** (Creative vs technical vs encyclopedic)
6. **Is there a clearer alternative?** If yes → replace
7. **When in doubt**: Provide both flagged version and explanation of why it might be acceptable

### Confidence Levels for Edge Cases

- **High confidence**: Clear pattern, clear fix
- **Medium confidence**: Pattern present but context matters
- **Low confidence**: Ambiguous, requires human judgment

For low confidence cases, flag but note the ambiguity.

---

## Summary

Edge cases require:

- **Context awareness**: Genre, domain, purpose
- **Judgment**: Not all patterns are always problems
- **Precision**: Distinguish technical from buzzword usage
- **Flexibility**: Different standards for different types of writing
- **Clarity goal**: Even in edge cases, aim for clearer communication

The goal is improving clarity and naturalness, not rigid adherence to rules.
