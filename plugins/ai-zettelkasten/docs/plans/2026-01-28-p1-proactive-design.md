# AI Zettelkasten P1 - Proactive Features Design

> Proactive suggestion hook, semantic clustering, and hub management.

**Date:** 2026-01-28
**Status:** Approved
**Builds on:** P0 Core Implementation

---

## Overview

P1 adds proactive knowledge capture and automatic organization:

1. **Proactive Suggest Hook** - Detect extractable knowledge during Edit/Write and prompt user
2. **Semantic Clustering** - Auto-generate hub notes from related permanent notes
3. **`/zhubs` Skill** - Browse and manage hub notes

---

## 1. Proactive Suggest Hook

### Purpose
Catch knowledge in-the-moment before it's lost by analyzing Edit/Write operations.

### Hook Registration

```json
{
  "PreToolCall": [{
    "matcher": "Edit|Write",
    "hooks": [{
      "type": "command",
      "command": "uvx --from ai-zettelkasten zk-suggest"
    }]
  }]
}
```

### Flow

1. Hook receives tool call context (file path, content being written)
2. Analyzes content for knowledge patterns
3. If extractable knowledge detected, outputs suggestion:
   ```
   💡 Worth capturing: "S3 Vectors metadata has 50 key limit"
   Type: fact | Tags: aws, s3-vectors
   [y] Add  [n] Skip  [e] Edit
   ```
4. Claude sees output and asks user for y/n/e
5. On "y": Creates fleeting note via extractor

### Detection Heuristics

**Patterns to detect:**
- Comments containing "NOTE:", "IMPORTANT:", "because", "chose"
- Configuration values with explanatory comments
- Error handling with specific error messages
- Test assertions that document expected behavior
- Constants with domain-specific values (limits, dimensions, etc.)

**Knowledge type inference:**
- "chose/decided/selected" → decision
- "always/never/pattern" → pattern
- "fixed/was wrong/actually" → correction
- Default → fact

### Module: `suggester.py`

```python
@dataclass
class Suggestion:
    content: str
    knowledge_type: KnowledgeType
    tags: list[str]
    confidence: float
    source_line: int

class Suggester:
    def analyze(self, file_path: str, content: str) -> list[Suggestion]:
        """Analyze content for extractable knowledge."""

    def format_suggestion(self, suggestion: Suggestion) -> str:
        """Format suggestion for CLI output."""
```

---

## 2. Semantic Clustering

### Purpose
Auto-generate hub notes by clustering semantically similar permanent notes.

### Algorithm

```python
def generate_hubs(vectors_store, vault, threshold=0.75, min_size=3):
    # 1. Fetch all permanent note embeddings
    permanent_vectors = vectors_store.query_all(
        filter={"status": "approved"}
    )

    # 2. Build similarity matrix
    embeddings = np.array([v['embedding'] for v in permanent_vectors])

    # 3. Agglomerative clustering
    clustering = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=1 - threshold,
        metric='cosine',
        linkage='average'
    )
    labels = clustering.fit_predict(embeddings)

    # 4. Generate hub notes for clusters >= min_size
    for cluster_id in np.unique(labels):
        members = [v for v, l in zip(permanent_vectors, labels) if l == cluster_id]
        if len(members) >= min_size:
            hub = create_hub_note(members)
            vault.write_hub(hub)
            vectors_store.update_members_hub(members, hub.id)
```

### Trigger Points

1. **After promotion in `/zreview`**: Recluster if new note might change clusters
2. **Manual via `/zhubs --regenerate`**: Force full reclustering

### Hub Note Format

```markdown
---
id: hub-aws-serverless
type: hub
generated: 2026-01-28T16:00:00
cluster_method: semantic
member_count: 8
tags: [aws, lambda, s3-vectors]
---

# Hub: AWS Serverless Patterns

Auto-generated hub connecting 8 related notes.

## Facts
- [[s3-vectors-embedding-dimensions]]
- [[lambda-cold-start-times]]

## Decisions
- [[chose-s3-vectors-over-aurora]]

## Patterns
- [[serverless-cost-optimization]]

## Recently Added
- [[s3-vectors-metadata-limits]] (2h ago)
```

### Hub Naming

Extract top 2-3 most common tags from cluster members:
- `["aws", "lambda", "s3"]` → `hub-aws-lambda`
- `["testing", "pytest", "mocking"]` → `hub-testing-pytest`

---

## 3. /zhubs Skill

### Usage

```
/zhubs                    # List all hubs
/zhubs <hub-name>         # View specific hub
/zhubs --regenerate       # Force reclustering
```

### List View

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 Knowledge Hubs
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. hub-aws-serverless (8 notes)
   Tags: aws, lambda, s3-vectors, bedrock
   Recent: S3 Vectors Metadata Limits (2h ago)

2. hub-testing-patterns (5 notes)
   Tags: pytest, tdd, mocking
   Recent: Mock Boto3 Clients (1d ago)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[1-2] View hub  [r] Regenerate  [q] Quit
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Detail View

Shows all member notes grouped by knowledge type with similarity scores.

---

## Implementation Tasks

### New Files

| File | Purpose |
|------|---------|
| `src/ai_zettelkasten/suggester.py` | Proactive suggestion detection |
| `src/ai_zettelkasten/clustering.py` | Semantic clustering algorithm |
| `skills/zhubs/SKILL.md` | /zhubs skill definition |
| `tests/test_suggester.py` | Suggester unit tests |
| `tests/test_clustering.py` | Clustering unit tests |

### Modified Files

| File | Change |
|------|--------|
| `cli.py` | Implement `suggest_main()` |
| `plugin.json` | Add PreToolCall hook |
| `pyproject.toml` | Add scikit-learn, numpy deps |
| `obsidian.py` | Add `write_hub()`, `list_hubs()` |
| `s3vectors.py` | Add `query_all()`, `update_members_hub()` |

### Dependencies

```toml
"scikit-learn>=1.4.0",
"numpy>=1.26.0",
```

### Task Order

1. P1-1: Add dependencies to pyproject.toml
2. P1-2: Suggester module + tests (TDD)
3. P1-3: Clustering module + tests (TDD)
4. P1-4: Extend obsidian.py for hubs
5. P1-5: Extend s3vectors.py for bulk queries
6. P1-6: CLI suggest_main implementation
7. P1-7: /zhubs skill
8. P1-8: Update plugin.json with PreToolCall hook
9. P1-9: Integration tests
10. P1-10: Update README

---

## Testing Strategy

### Suggester Tests
- Pattern detection for each knowledge type
- Tag extraction accuracy
- Confidence scoring
- Edge cases (empty content, no patterns)

### Clustering Tests
- Correct cluster formation with mock embeddings
- Min size threshold enforcement
- Hub naming from tags
- Incremental reclustering

### Integration Tests
- Full flow: Edit → suggestion → capture → cluster → hub
- /zhubs listing and detail views
