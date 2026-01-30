---
name: zlink-audit
description: Audit Zettelkasten links for quality issues and fix violations of ZK principles
---

# Zettelkasten Link Audit

Comprehensive audit and repair of wiki-links in the Zettelkasten to ensure they follow best practices.

## When to Use

- After bulk link operations (zk-suggest-links --apply)
- When the knowledge graph feels "too connected"
- Before promoting fleeting notes to permanent
- Periodically as maintenance

## Issues to Check

### 1. Broken Links
Links pointing to non-existent files:
```python
# Check if target exists
if target not in valid_slugs:
    print(f"BROKEN: {file} -> {target}")
```

### 2. Self-References
Notes that link to themselves (always invalid):
```python
if slug in links:
    print(f"SELF-REF: {file}")
```

### 3. Duplicate Links
Same target linked multiple times in one note:
```python
from collections import Counter
counts = Counter(links)
dupes = [t for t, c in counts.items() if c > 1]
```

### 4. Flee-* References
Permanent notes should NOT link to fleeting IDs:
```bash
grep -l '\[\[flee-' *.md
```

### 5. Over-Connection
Zettelkasten best practice: 3-5 meaningful links per note, max 7
```python
if link_count > 7:
    print(f"OVER-CONNECTED: {file} has {link_count} links")
```

### 6. Empty Related Sections
Notes with `## Related` but no actual links

## Healthy Metrics

| Metric | Healthy Range |
|--------|---------------|
| Links per note | 3-5 average |
| Max links | 7 or fewer |
| Broken links | 0 |
| Self-references | 0 |
| Duplicates | 0 |

## Fix Strategy

1. **Broken links**: Remove the line containing the broken link
2. **Self-references**: Remove self-referential lines
3. **Duplicates**: Keep first occurrence, remove rest
4. **Flee-* refs**: Either promote the fleeting note or remove the link
5. **Over-connection**: Prune by relationship priority:
   - SOLVES (keep) > CONTRADICTS > ENABLES > ELABORATES > SUPPORTS > APPLIES > ABSTRACTS > SEQUENCE (remove first)

## Audit Script

```python
import os, re
from collections import Counter

valid_slugs = {f.replace('.md', '') for f in os.listdir('.') if f.endswith('.md')}

for f in os.listdir('.'):
    if not f.endswith('.md'): continue
    slug = f.replace('.md', '')

    with open(f) as file:
        content = file.read()

    links = re.findall(r'\[\[([^\]|]+)', content)

    # Check all issues
    for target in links:
        if target not in valid_slugs:
            print(f"BROKEN: {f} -> {target}")

    if slug in links:
        print(f"SELF-REF: {f}")

    dupes = [t for t, c in Counter(links).items() if c > 1]
    if dupes:
        print(f"DUPLICATE: {f} has {dupes}")
```

## Related Commands

- `zk-suggest-links --all` - Generate link suggestions
- `zk-suggest-links --apply` - Apply suggestions (may over-connect!)
- `/zfix-links` - Fix broken wiki-links using fuzzy matching
