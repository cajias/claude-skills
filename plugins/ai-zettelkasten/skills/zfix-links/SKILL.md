---
name: zfix-links
description: |
  Fix broken wiki-links in Zettelkasten notes by replacing them with semantically
  similar existing notes. Audits link integrity and repairs Related sections
  with valid references.
version: 1.0.0
---

# /zfix-links - Fix Broken Wiki-Links

Audit and repair broken wiki-links by replacing them with semantically similar existing notes.

## Usage

```bash
/zfix-links                  # Fix all broken links
/zfix-links --audit          # Audit only, don't fix
/zfix-links --path permanent # Fix links in specific directory
```

## Implementation

1. **Build inventory of existing notes**:

```python
from pathlib import Path

vault_path = Path(os.environ.get("OBSIDIAN_VAULT", ""))
permanent_path = vault_path / "knowledge-base" / "permanent"

existing_notes = {
    note.stem: note
    for note in permanent_path.glob("*.md")
}

print(f"Found {len(existing_notes)} existing notes")
```

2. **Extract all wiki-links from notes**:

```python
import re

def extract_links(content):
    # Match [[link]] or [[link|alias]]
    pattern = r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]'
    return re.findall(pattern, content)

all_links = set()
for note in permanent_path.glob("*.md"):
    content = note.read_text()
    all_links.update(extract_links(content))
```

3. **Identify broken links**:

```python
broken_links = []
for link in all_links:
    # Skip vault paths (playbooks/, hubs/, etc.) - these are cross-folder refs
    if "/" in link:
        continue

    # Check if target exists
    if link not in existing_notes:
        broken_links.append(link)

print(f"Found {len(broken_links)} broken links")
```

4. **Display audit results**:

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔗 Link Audit Results
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total unique links: 504
Valid links: 276
Broken links: 228

Broken Link Categories:
  • Concept placeholders: 35 (e.g., eslint-configuration)
  • Vault paths: 45 (e.g., playbooks/..., hubs/...)
  • Typos/variations: 148 (fixable)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

5. **For semantic replacement**, match broken links to existing notes:

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def find_semantic_match(broken_link, existing_notes):
    """Find most similar existing note for a broken link."""

    # Convert link to searchable text
    broken_text = broken_link.replace("-", " ")

    # Get existing note names as text
    existing_texts = [name.replace("-", " ") for name in existing_notes.keys()]

    # Compute similarity
    vectorizer = TfidfVectorizer()
    all_texts = [broken_text] + existing_texts
    tfidf = vectorizer.fit_transform(all_texts)

    similarities = cosine_similarity(tfidf[0:1], tfidf[1:])[0]

    # Return best match if similarity > threshold
    best_idx = similarities.argmax()
    if similarities[best_idx] > 0.3:
        return list(existing_notes.keys())[best_idx]

    return None
```

6. **Fix broken links in files**:

```python
def fix_links_in_file(note_path, replacements):
    content = note_path.read_text()

    for broken, replacement in replacements.items():
        # Replace [[broken]] with [[replacement]]
        content = re.sub(
            rf'\[\[{re.escape(broken)}(\|[^\]]+)?\]\]',
            f'[[{replacement}]]',
            content
        )

    note_path.write_text(content)
```

7. **Options for unfixable links**:

```text
Options:
  [k]eep as concept placeholder (future note)
  [r]emove from Related section
  [m]anually specify replacement
```

## Output

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Link Repair Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Fixed: 182 links across 145 files
Kept as placeholders: 35 concept links
Removed: 11 vault path links

Sample replacements:
  [[ai-code-review]] → [[code-review-acceleration]]
  [[context-optimization]] → [[context-window-management-pattern]]
  [[strict-linters]] → [[linters-as-negotiation-layer]]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
