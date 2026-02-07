---
name: notion-ingest
description: >-
  [DEPRECATED - Use ai-zettelkasten instead] Ingest Notion documents into
  Zettelkasten as atomic notes. Writes to BOTH ChromaDB (vector search) AND
  Obsidian (markdown files with wikilinks). Analyzes structure, proposes
  atomization, creates interlinked notes with proper Luhmann-style IDs.
---

> **DEPRECATED:** This plugin has been superseded by **ai-zettelkasten**.
> Please migrate to `ai-zettelkasten` for continued updates.
> This plugin is no longer maintained.

# Notion Document Ingestion

When user provides a Notion URL or page ID, or says "ingest from notion",
follow this process to atomize the document into Zettelkasten notes.

## Trigger Phrases

- `/notion-ingest <url or page_id>`
- "ingest notion page"
- "import from notion"
- "add notion doc to zettelkasten"

## Dual-Storage Architecture

Notes are stored in **two places**:

| Storage      | Purpose                                             | Tool                                |
| ------------ | --------------------------------------------------- | ----------------------------------- |
| **ChromaDB** | Vector search, semantic queries, metadata filtering | `mcp__chroma__chroma_add_documents` |
| **Obsidian** | Human-readable markdown, wikilinks, graph view      | `mcp__obsidian__write_note`         |

Both must be updated together to keep the systems in sync.

## Step 1: Fetch Content

Extract page ID from URL if needed. Notion URLs have format:
`https://www.notion.so/Page-Title-{page_id}`

The page_id is the 32-character hex string at the end (may have hyphens).

```text
# Get page metadata
mcp__MCP_DOCKER__API-retrieve-a-page(page_id)

# Get page content blocks
mcp__MCP_DOCKER__API-get-block-children(block_id=page_id, page_size=100)
```

Parse the block children to extract:

- Headings (heading_1, heading_2, heading_3) → Section structure
- Paragraphs → Body content
- Bulleted/numbered lists → Supporting points
- To-do blocks → Potential tasks
- Quotes → Key citations
- Links → Source references

## Step 2: Analyze Structure

Count and categorize:

```text
Block Types:
- Headings: {count} (section boundaries)
- Paragraphs: {count}
- Lists: {count}
- TODOs: {count} (potential tasks)
- Quotes: {count}
- Links: {count} (potential sources)
```

Identify:

1. **Main sections** by heading_2 blocks (these become atomic notes)
2. **Key concepts** that deserve their own notes
3. **Research items** from TODO blocks
4. **Sources** from URLs/citations
5. **Personal reflections** vs external content

## Step 3: Propose Atomization

Present to user before creating:

```text
Proposed Structure for: "{document_title}"
Source: {notion_url}

INDEX NOTE:
  ID: {topic}-1
  Title: {document_title}
  Type: index-note

ATOMIC NOTES ({count}):
  {topic}-1a: {section_1_title} (literature-note)
  {topic}-1b: {section_2_title} (literature-note)
  {topic}-1c: {section_3_title} (permanent-note)
  ...

RESEARCH TASKS ({count}):
  task-{topic}-1: {todo_1}
  task-{topic}-2: {todo_2}
  ...

LINKS:
  {topic}-1 (parent)
  ├── {topic}-1a (child) ←→ task-{topic}-1 (related)
  ├── {topic}-1b (child)
  └── {topic}-1c (child) ←→ {topic}-1a (related)

Proceed? [y/n] or suggest changes:
```

## Step 4: ID Generation

Follow Luhmann-style branching:

- Ask: "What topic prefix should we use?" (e.g., `llm`, `design`, `learn`)
- Check existing IDs with that prefix
- Generate: `{prefix}-{next_number}` for index
- Children: `{prefix}-{number}a`, `{prefix}-{number}b`, etc.
- Tasks: `task-{topic}-{number}`

## Step 5: Create Notes in ChromaDB

After user approval, create all documents in ChromaDB for vector search:

```python
# For each note, create with chroma_add_documents:
{
  "id": "{generated_id}",
  "document": "{title}\n\n{body}\n\nTags: {tags}\nSource: {source}",
  "metadata": {
    "title": "{title}",
    "category": "{category}",  # index-note, literature-note, permanent-note, fleeting-note, kanban-task
    "topic": "{topic}",
    "tags": "{comma,separated,tags}",
    "source": "{source_citation}",
    "sourceUrl": "{url}",
    "dateAdded": "{ISO_date}",
    "parentIds": "{comma,separated,ids}",
    "childIds": "{comma,separated,ids}",
    "relatedIds": "{comma,separated,ids}"
  }
}
```

## Step 5b: Create Notes in Obsidian

**IMPORTANT:** Also create each note in Obsidian for browsable markdown with wikilinks.

**Obsidian Vault:** `/Users/rc/Documents/Obsidian Vault`
**Folder:** `Zettelkasten/`

Use `mcp__obsidian__write_note` for each note:

```python
mcp__obsidian__write_note(
  path="Zettelkasten/{id} {title}.md",
  content="""# {title}

{body_as_markdown}

## Connections

- Parent: [[{parent_id} {parent_title}]]
- Related: [[{related_id} {related_title}]], ...
""",
  frontmatter={
    "id": "{id}",
    "title": "{title}",
    "category": "{category}",
    "topic": "{topic}",
    "tags": ["{tag1}", "{tag2}"],  # Array format for Obsidian
    "source": "{source}",
    "sourceUrl": "{url}",
    "dateAdded": "{ISO_date}",
    "parentIds": ["{parent_id}"],
    "status": "todo"  # For tasks only
  }
)
```

**Obsidian-specific formatting:**

- Use `[[note-name]]` wikilinks for connections (Obsidian resolves these)
- Include filename pattern: `{id} {title}.md` for readability
- Use YAML arrays for tags (not comma-separated strings)
- Add `status` field for kanban tasks

## Step 6: Establish Links

Ensure bidirectional links:

1. Index note's `childIds` contains all atomic note IDs
2. Each atomic note's `parentIds` contains index note ID
3. Tasks' `relatedIds` link to relevant concept notes
4. Related concepts link to each other via `relatedIds`

## Step 7: Connection Discovery

After creating notes, run semantic search to find connections to existing notes:

```text
chroma_query_documents(
  collection_name="zettelkasten",
  query_texts=["{new_note_content}"],
  n_results=5
)
```

For each new note, suggest connections:

```text
Potential connections for {id}:
[1] {existing_id}: "{title}" (similarity: 0.XX)
[2] {existing_id}: "{title}" (similarity: 0.XX)

Create links? [1,2] or [n]one:
```

## Category Assignment Guidelines

| Content Type                | Category        |
| --------------------------- | --------------- |
| Overview/TOC of a topic     | index-note      |
| Summary of external source  | literature-note |
| Your own developed ideas    | permanent-note  |
| Quick thoughts, unprocessed | fleeting-note   |
| Action items from TODOs     | kanban-task     |
| Large initiatives           | epic            |

## Tag Extraction

Auto-extract tags from:

- Explicit tags in document
- Key terms (capitalized concepts, technical terms)
- Topic area
- Status indicators (draft, review, etc.)

Default tags by category:

- literature-note: `source:{author}`, `year:{year}`
- kanban-task: `todo` (status tag)
- fleeting-note: `unprocessed`

## Example Session

```text
User: /notion-ingest https://notion.so/My-Notes-abc123def456
```
