---
name: ztriage
description: |
  Triage fleeting notes in the Zettelkasten. Categorize notes by quality,
  identify atomic extracts needing enrichment, find duplicates, and prepare
  notes for review. Batch processing for efficient curation.
version: 1.0.0
---

# /ztriage - Triage Fleeting Notes

Analyze and categorize fleeting notes to identify what needs enrichment, review, or archiving.

## Usage

```bash
/ztriage                    # Triage all fleeting notes
/ztriage --category atomic  # Show only atomic (single-paragraph) notes
/ztriage --duplicates       # Find potential duplicates
```

## Implementation

When this skill is invoked:

1. **Scan fleeting directory** for all notes:

```python
from pathlib import Path
import os

vault_path = Path(os.environ.get("OBSIDIAN_VAULT", ""))
fleeting_path = vault_path / "knowledge-base" / "fleeting"

notes = list(fleeting_path.glob("*.md"))
# Exclude archived notes
notes = [n for n in notes if ".archive" not in str(n)]
```

2. **Categorize notes by quality tier**:

```text
Quality Tiers:
- Tier 1 (Full): >20 lines, has sections (##), has Related links
- Tier 2 (Partial): 10-20 lines, some structure
- Tier 3 (Atomic): <10 lines, single paragraph - NEEDS ENRICHMENT
```

3. **Identify note patterns**:

```python
categories = {
    "named_patterns": [],    # descriptive-name.md
    "flee_extracts": [],     # flee-YYYYMMDD-*.md
    "aws_tools": [],         # aws-proserve-*.md
    "duplicates": [],        # potential duplicates by title similarity
}

for note in notes:
    if note.stem.startswith("flee-"):
        categories["flee_extracts"].append(note)
    elif note.stem.startswith("aws-proserve"):
        categories["aws_tools"].append(note)
    else:
        categories["named_patterns"].append(note)
```

4. **Display triage summary**:

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Fleeting Triage Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total: 162 notes

By Category:
  • Named patterns: 55 (descriptive filenames)
  • Atomic extracts: 100 (flee-* IDs)
  • Tool notes: 7 (aws-proserve-*)

By Quality:
  • Tier 1 (Full): 12 - Ready for review
  • Tier 2 (Partial): 43 - May need enrichment
  • Tier 3 (Atomic): 107 - NEED ENRICHMENT

Potential Duplicates: 3

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Actions:
  [e]nrich atomic notes (/zenrich)
  [r]eview full notes (/zreview)
  [d]uplicates check (/zdupes)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

5. **For duplicate detection**, use TF-IDF similarity:

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Extract titles
titles = [note.stem.replace("-", " ") for note in notes]

# Compute similarity
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(titles)
similarities = cosine_similarity(tfidf_matrix)

# Find pairs > 0.7 similarity
duplicates = []
for i, j in combinations(range(len(notes)), 2):
    if similarities[i, j] > 0.7:
        duplicates.append((notes[i], notes[j], similarities[i, j]))
```

## Output

Produces a categorized summary enabling informed decisions about next actions:
- Run `/zenrich` for atomic notes needing structure
- Run `/zreview` for full notes ready for promotion
- Run `/zdupes` for duplicate resolution
