# AI Zettelkasten v2.0 - Design Document

> A Claude Code plugin implementing true Zettelkasten methodology with semantic search, proactive knowledge capture, and automatic hub generation.

**Date:** 2026-01-28
**Status:** Approved
**Author:** cajias + Claude

---

## Overview

### Goals

1. **Personal knowledge management** - Build a second brain from Claude Code sessions
2. **Project documentation** - Capture learnings specific to each codebase
3. **Proactive retrieval** - Surface relevant knowledge during conversations
4. **True Zettelkasten workflow** - Atomic notes, dense linking, structure notes (hubs)

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Curation level | High-touch (review all) | Build trust, ensure quality |
| Linking strategy | Semantic clusters → auto-hubs | Zettelkasten-native, leverages S3 Vectors |
| Folder structure | Type-based | Visible workflow stages |
| Retrieval triggers | Topic detection | Proactive but not overwhelming |
| Implementation | MVP first | Core workflow, then proactive features |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     AI ZETTELKASTEN v2.0                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  CAPTURE                    PROCESS                    RETRIEVE     │
│  ───────                    ───────                    ────────     │
│                                                                     │
│  ┌──────────┐              ┌──────────┐              ┌──────────┐  │
│  │ Stop Hook│──────────────│ Review   │──────────────│ Proactive│  │
│  │ Extract  │   fleeting/  │ Queue    │  permanent/  │ Surface  │  │
│  └──────────┘              └──────────┘              └──────────┘  │
│       │                         │                         │        │
│  ┌──────────┐              ┌──────────┐              ┌──────────┐  │
│  │ /zadd    │──────────────│ Promote  │──────────────│ Topic    │  │
│  │ Manual   │              │ + Link   │              │ Detection│  │
│  └──────────┘              └──────────┘              └──────────┘  │
│       │                         │                         │        │
│  ┌──────────┐              ┌──────────┐              ┌──────────┐  │
│  │ Proactive│              │ Cluster  │              │ /zsearch │  │
│  │ Suggest  │              │ → Hubs   │              │ Query    │  │
│  └──────────┘              └──────────┘              └──────────┘  │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  STORAGE                                                            │
│  ───────                                                            │
│  ┌─────────────────────┐    ┌─────────────────────┐                │
│  │ Obsidian Vault      │    │ S3 Vectors          │                │
│  │ ├── fleeting/       │    │ • knowledge-index   │                │
│  │ ├── permanent/      │◄──►│ • Titan embeddings  │                │
│  │ ├── hubs/           │    │ • Metadata filters  │                │
│  │ └── projects/       │    └─────────────────────┘                │
│  └─────────────────────┘                                            │
└─────────────────────────────────────────────────────────────────────┘
```

**Key flows:**
- **Capture**: Stop hook extracts OR `/zadd` manual OR proactive suggestion → goes to `fleeting/`
- **Process**: `/zreview` approves → promotes to `permanent/` → auto-links → clusters generate `hubs/`
- **Retrieve**: Topic detection surfaces relevant notes during conversation

---

## Obsidian Vault Structure

### Folder Structure

```
knowledge-base/
├── fleeting/                    # Unreviewed extractions
│   ├── 2026-01-28-001.md
│   └── 2026-01-28-002.md
├── permanent/                   # Approved atomic notes
│   ├── s3-vectors-dimensions.md
│   └── mermaid-over-ascii.md
├── hubs/                        # Auto-generated semantic clusters
│   ├── aws-serverless.md
│   └── testing-patterns.md
└── projects/                    # Project-specific knowledge
    ├── omega/
    │   └── agent-core-patterns.md
    └── claude-skills/
        └── plugin-architecture.md
```

### Note Formats

#### Fleeting Note (auto-generated)

```markdown
---
id: fleeting-2026-01-28-001-a3f2c1
type: fleeting
status: pending
extracted: 2026-01-28T14:30:00
source_session: /Users/cajias/Projects/omega
knowledge_type: fact
confidence: 0.85
tags: [aws, s3-vectors, embeddings]
---

# S3 Vectors Embedding Dimensions

Bedrock Titan uses 1536 dimensions for embeddings. The S3 Vectors
index must be created with `dimension=1536` to match.

## Context
Discovered while setting up the ai-zettelkasten infrastructure.

## Source
Session working on ai-zettelkasten plugin, 2026-01-28
```

#### Permanent Note (after review)

```markdown
---
id: perm-s3-vectors-dims-b4e8d2
type: permanent
promoted: 2026-01-28T15:00:00
knowledge_type: fact
tags: [aws, s3-vectors, embeddings, bedrock]
links:
  - "[[titan-embedding-models]]"
  - "[[s3-vectors-setup]]"
hubs:
  - "[[hub-aws-serverless]]"
scope: global
---

# S3 Vectors Embedding Dimensions

Bedrock Titan uses **1536 dimensions** for embeddings. When creating
an S3 Vectors index, you must specify `dimension=1536` to match.

## Key Points
- Titan model ID: `amazon.titan-embed-text-v1`
- Dimension mismatch causes silent failures
- Cosine distance metric recommended

## Related
- [[titan-embedding-models]] - Full Titan model specs
- [[s3-vectors-setup]] - Infrastructure setup pattern
```

#### Hub Note (auto-generated from clusters)

```markdown
---
id: hub-aws-serverless
type: hub
generated: 2026-01-28T16:00:00
cluster_method: semantic
member_count: 12
tags: [aws, serverless, lambda, s3-vectors]
---

# Hub: AWS Serverless Patterns

Auto-generated hub connecting 12 related notes about AWS serverless.

## Core Concepts
- [[s3-vectors-embedding-dimensions]]
- [[lambda-cold-start-patterns]]
- [[bedrock-titan-configuration]]

## Decisions
- [[chose-s3-vectors-over-aurora]]

## Patterns
- [[serverless-cost-optimization]]

## Recently Added
- [[s3-vectors-metadata-limits]] (2026-01-28)
```

---

## Skills

### `/zadd` - Manual Capture

```
/zadd <content>                      # Quick add as fact
/zadd --type decision <content>      # Specify type
/zadd --project omega <content>      # Project-scoped
/zadd --now <content>                # Skip review, go straight to permanent
```

**Behavior:**
1. Parse content and auto-detect type if not specified
2. Auto-generate tags from content using keyword extraction
3. Create fleeting note in `fleeting/`
4. Generate embedding and store in S3 Vectors with `status: pending`
5. Suggest related existing notes: "Found 2 related notes - link them during review?"

### `/zreview` - Review Queue

```
/zreview                # Review all pending
/zreview --today        # Today's extractions only
/zreview --type fact    # Filter by type
```

**Behavior:**
1. Fetch all notes with `status: pending` from `fleeting/`
2. For each note, show:
   - Content preview
   - Suggested links (semantic similarity > 0.7)
   - Suggested hub assignment
3. Actions: `[a]pprove` `[e]dit` `[d]iscard` `[s]kip` `[l]ink`
4. On approve:
   - Move to `permanent/`
   - Create bidirectional links for approved suggestions
   - Update S3 Vectors metadata: `status: approved`
   - Trigger cluster recalculation if hub membership changes

### `/zsearch` - Semantic Search

```
/zsearch <query>                    # Natural language search
/zsearch <query> --type pattern     # Filter by type
/zsearch <query> --project omega    # Filter by project
/zsearch <query> --recent 7d        # Time filter
```

**Behavior:**
1. Generate embedding for query via Bedrock Titan
2. Query S3 Vectors with filters
3. Return top 5-10 results ranked by similarity
4. Show: title, type, tags, similarity score, preview

### `/zhubs` - Browse & Manage Hubs

```
/zhubs                      # List all hubs
/zhubs aws-serverless       # View specific hub
/zhubs --regenerate         # Force cluster recalculation
```

**Behavior:**
1. List hubs with member counts and recent activity
2. View hub shows all member notes grouped by type
3. Regenerate runs clustering algorithm on all permanent notes

---

## Hooks

### Stop Hook (Enhanced)

**Trigger:** End of every Claude Code session

**Behavior:**
1. Analyze conversation for extractable knowledge
2. For each extraction:
   - Create fleeting note in `fleeting/`
   - Generate embedding, store in S3 Vectors
   - Check for high-similarity existing notes (>0.85)
   - If near-duplicate found, flag for merge review
3. Output summary: "Extracted 3 items → review queue"

### Proactive Suggestion Hook (New - P1)

**Trigger:** During conversation when Claude detects:
- A decision being made
- A problem being solved after investigation
- A pattern being applied
- A mistake being corrected

**Behavior:**
1. Claude notices extractable moment in conversation
2. Suggests inline:
   ```
   💡 This looks worth capturing:

   "S3 Vectors metadata has 50 key limit per vector"
   Type: fact | Tags: aws, s3-vectors, limits

   [y] Add to fleeting  [n] Skip  [e] Edit first
   ```
3. On `[y]`: Create fleeting note immediately, continue conversation
4. Non-blocking - doesn't interrupt flow

### Topic Detection Hook (P2)

**Trigger:** Monitors conversation for topic keywords/concepts

**Behavior:**
1. Every few messages, extract key topics from recent conversation
2. Query S3 Vectors for semantically related notes
3. If relevant notes found (similarity > 0.75), surface them
4. Only triggers when genuinely relevant (avoids noise)

### Hook Registration

```json
{
  "hooks": {
    "Stop": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "uvx --from ai-zettelkasten extract-knowledge"
      }]
    }],
    "PreToolCall": [{
      "matcher": "Edit|Write",
      "hooks": [{
        "type": "command",
        "command": "uvx --from ai-zettelkasten proactive-suggest"
      }]
    }]
  }
}
```

---

## S3 Vectors Schema

### Vector Metadata (50 keys max)

```python
{
    "key": "perm-s3-vectors-dims-b4e8d2",
    "data": {"float32": [...]},  # 1536-dim Titan embedding
    "metadata": {
        # Core fields
        "type": "permanent",           # fleeting | permanent | hub
        "knowledge_type": "fact",      # fact | decision | pattern | correction
        "status": "approved",          # pending | approved | archived

        # Content
        "title": "S3 Vectors Embedding Dimensions",
        "content_preview": "Bedrock Titan uses 1536...",

        # Organization
        "scope": "global",             # global | project
        "project": "",
        "tags": "aws,s3-vectors,embeddings",
        "hub_ids": "hub-aws-serverless",

        # Linking
        "link_count": "3",
        "linked_ids": "perm-123,perm-456",

        # Timestamps
        "created": "2026-01-28T14:30:00",
        "promoted": "2026-01-28T15:00:00",
        "last_accessed": "2026-01-28T16:00:00",

        # Obsidian reference
        "obsidian_path": "permanent/s3-vectors-dimensions.md"
    }
}
```

---

## Semantic Clustering

### Algorithm

**Trigger:** New note promoted, `/zhubs --regenerate`, or weekly maintenance

```python
def generate_hubs(threshold=0.75, min_cluster_size=3):
    # 1. Fetch all permanent note embeddings
    vectors = s3vectors.query_vectors(
        filter={"type": {"$eq": "permanent"}},
        topK=1000,
        returnMetadata=True
    )

    # 2. Compute pairwise cosine similarity matrix
    embeddings = [v['embedding'] for v in vectors]
    similarity_matrix = cosine_similarity(embeddings)

    # 3. Agglomerative clustering
    clusters = cluster_by_similarity(
        similarity_matrix,
        threshold=threshold,
        min_size=min_cluster_size
    )

    # 4. Generate/update hub notes
    for cluster in clusters:
        hub = generate_hub_note(cluster)
        write_to_obsidian(f"hubs/{hub.id}.md", hub)
        update_member_metadata(cluster.members, hub.id)
```

### Hub Title Generation

- Extract most common tags across cluster members
- Use first 2-3 tags to name: `hub-{tag1}-{tag2}`
- Example: Notes about AWS Lambda, cold starts → `hub-aws-lambda-performance`

---

## MVP Scope

### Priority P0 (Core)

- [ ] Enhanced Stop Hook - Extract → fleeting notes + S3 Vectors
- [ ] `/zadd` with suggestions - Manual capture + related note hints
- [ ] `/zreview` full workflow - Review → approve → promote → link
- [ ] `/zsearch` - Semantic search with filters

### Priority P1 (Proactive)

- [ ] Proactive Suggest Hook - Inline "capture this?" prompts
- [ ] Semantic Clustering - Auto-generate hubs from clusters
- [ ] `/zhubs` - Browse and manage hubs

### Priority P2 (Advanced)

- [ ] Topic Detection - Surface relevant notes mid-conversation

---

## File Structure

```
ai-zettelkasten/
├── .claude-plugin/
│   └── plugin.json              # Hook registrations, metadata
├── skills/
│   ├── zadd/SKILL.md
│   ├── zreview/SKILL.md
│   ├── zsearch/SKILL.md
│   └── zhubs/SKILL.md
├── agents/
│   └── knowledge-extractor.md
├── hooks/
│   ├── extract_knowledge.py
│   ├── proactive_suggest.py
│   └── topic_detect.py
├── src/ai_zettelkasten/
│   ├── __init__.py
│   ├── s3vectors.py             # S3 Vectors client wrapper
│   ├── embeddings.py            # Bedrock Titan wrapper
│   ├── clustering.py            # Semantic clustering logic
│   └── obsidian.py              # Obsidian file operations
├── infra/
│   ├── lib/infra-stack.ts
│   └── bin/infra.ts
├── pyproject.toml
└── README.md
```

---

## Dependencies

```toml
[project]
name = "ai-zettelkasten"
version = "2.0.0"
requires-python = ">=3.11"
dependencies = [
    "boto3>=1.35.0",
    "rich>=13.0.0",
    "pyyaml>=6.0",
    "numpy>=1.26.0",
    "scikit-learn>=1.4.0",
]

[project.scripts]
extract-knowledge = "ai_zettelkasten.hooks.extract_knowledge:main"
proactive-suggest = "ai_zettelkasten.hooks.proactive_suggest:main"
topic-detect = "ai_zettelkasten.hooks.topic_detect:main"
```

---

## Migration from v0.5.0

| Current (v0.5.0) | Enhanced (v2.0) |
|------------------|-----------------|
| Single daily extraction file | Individual atomic notes |
| No linking | Auto-suggested + manual links |
| No organization | Type-based folders + hubs |
| Passive only | Proactive suggestions |
| Basic search skill | Full semantic search |
| Review skill placeholder | Working review workflow |

### Migration Steps

1. Existing extractions in `knowledge-base/extractions/` can be batch-processed
2. Each `## [HH:MM]` section becomes a fleeting note
3. Run through `/zreview` to promote to permanent
4. Re-embed all notes for S3 Vectors consistency
