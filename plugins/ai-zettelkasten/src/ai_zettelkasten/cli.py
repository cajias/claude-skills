"""CLI entry points for AI Zettelkasten."""
import json
import os
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from .extractor import KnowledgeExtractor


console = Console()

# Configuration from environment
BUCKET = os.environ.get("ZETTELKASTEN_BUCKET", "zettelkasten-prod")
INDEX = os.environ.get("ZETTELKASTEN_INDEX", "knowledge-index")
VAULT = Path(os.environ.get("OBSIDIAN_VAULT", os.path.expanduser("~/Documents/obsidian-vault-work")))


def extract_main():
    """Entry point for extraction hook.

    Reads JSON from stdin containing knowledge items to extract.
    Each item is processed through the knowledge extraction pipeline:
    1. Create note in Obsidian vault
    2. Generate embedding via Bedrock
    3. Store vector in S3 Vectors

    Input format (JSON on stdin):
        {
            "items": [
                {
                    "type": "fact|decision|pattern|correction",
                    "title": "Short descriptive title",
                    "content": "Full content/body",
                    "tags": ["tag1", "tag2"],
                    "confidence": 0.9
                }
            ]
        }

    Returns:
        0 on success (all items stored)
        1 on partial failure (some errors occurred)
    """
    # Check for stdin input
    if sys.stdin.isatty():
        console.print("[yellow]No input provided. Run with JSON on stdin.[/yellow]")
        return 0

    # Read and parse input
    try:
        input_data = sys.stdin.read().strip()
        if not input_data:
            console.print("[yellow]Empty input.[/yellow]")
            return 0

        data = json.loads(input_data)
    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON: {e}[/red]")
        return 1

    items = data.get("items", [])
    if not items:
        console.print("[dim]No items to extract.[/dim]")
        return 0

    # Process items
    extractor = KnowledgeExtractor(VAULT, BUCKET, INDEX)
    summary = extractor.process_items(items)

    # Display results
    console.print()
    table = Table(title="Extraction Results")
    table.add_column("Title", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Status", style="green")

    for result in summary["results"]:
        status_style = "green" if result["status"] == "stored" else "yellow"
        table.add_row(
            result["title"][:40],
            result["type"],
            f"[{status_style}]{result['status']}[/{status_style}]"
        )

    console.print(table)
    console.print(f"\n[bold]Summary:[/bold] {summary['stored']} stored, {summary['partial']} partial, {summary['errors']} errors")

    return 0 if summary["errors"] == 0 else 1


def suggest_main():
    """Entry point for proactive suggestion hook (PreToolCall).

    Called by the PreToolCall hook to detect extractable knowledge in
    Edit and Write operations. Reads tool call context from stdin and
    uses the Suggester module to analyze content for patterns worth capturing.

    Input format (JSON on stdin):
        {
            "tool_name": "Edit" or "Write",
            "tool_input": {
                "file_path": "/path/to/file",
                "content": "..." (for Write),
                "new_string": "..." (for Edit)
            }
        }

    Returns:
        0 (always succeeds silently)
    """
    # Check for stdin input
    if sys.stdin.isatty():
        return 0  # Silent exit if no input

    # Read tool call context from stdin
    try:
        input_data = sys.stdin.read().strip()
        if not input_data:
            return 0

        # PreToolCall provides tool_name and tool_input
        data = json.loads(input_data)
    except json.JSONDecodeError:
        return 0  # Silent fail for invalid input

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # Only analyze Edit and Write operations
    if tool_name not in ["Edit", "Write"]:
        return 0

    # Get the content being written
    content = ""
    file_path = ""

    if tool_name == "Write":
        content = tool_input.get("content", "")
        file_path = tool_input.get("file_path", "")
    elif tool_name == "Edit":
        content = tool_input.get("new_string", "")
        file_path = tool_input.get("file_path", "")

    if not content:
        return 0

    # Analyze for extractable knowledge
    from .suggester import Suggester

    suggester = Suggester()
    suggestions = suggester.analyze(file_path, content)

    if not suggestions:
        return 0

    # Output suggestions for Claude to present to user
    console.print()
    for suggestion in suggestions[:3]:  # Limit to top 3
        console.print(suggester.format_suggestion(suggestion))

    return 0


def index_main():
    """Entry point for indexing hook (PostToolCall on Write).

    Called after a Write operation completes to index new notes to S3 Vectors.
    Only processes writes to the knowledge-base folder in the Obsidian vault.

    Input format (JSON on stdin from PostToolCall):
        {
            "tool_name": "Write",
            "tool_input": {
                "file_path": "/path/to/file.md",
                "content": "..."
            },
            "tool_result": "..."
        }

    Returns:
        0 on success or skip
        1 on error
    """
    # Check for stdin input
    if sys.stdin.isatty():
        return 0

    try:
        input_data = sys.stdin.read().strip()
        if not input_data:
            return 0
        data = json.loads(input_data)
    except json.JSONDecodeError:
        return 0

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # Only process Write operations
    if tool_name != "Write":
        return 0

    file_path = tool_input.get("file_path", "")
    content = tool_input.get("content", "")

    # Only index files in knowledge-base folder
    kb_path = str(VAULT / "knowledge-base")
    if kb_path not in file_path:
        return 0

    # Skip non-markdown files
    if not file_path.endswith(".md"):
        return 0

    # Parse the markdown and index to S3 Vectors
    from .obsidian import ObsidianVault
    from .embeddings import BedrockEmbeddings
    from .s3vectors import S3VectorsStore, VectorMetadata

    try:
        vault = ObsidianVault(VAULT)
        note = vault.read_note(Path(file_path))

        # Generate embedding
        embeddings = BedrockEmbeddings()
        text = f"{note.title}\n\n{note.content}"
        embedding = embeddings.embed(text)

        # Store in S3 Vectors
        vectors = S3VectorsStore(BUCKET, INDEX)
        metadata = VectorMetadata(
            note_type=note.note_type.value,
            knowledge_type=note.knowledge_type.value,
            status=note.status,
            title=note.title,
            tags=note.tags,
            obsidian_path=file_path,
            content_preview=note.content[:500],
        )

        success = vectors.put_vector(note.id, embedding, metadata)
        if success:
            console.print(f"[green]📚 Indexed:[/green] {note.title}")
        else:
            console.print(f"[yellow]⚠️ Index failed:[/yellow] {note.title}")

    except Exception as e:
        # Silently skip if credentials unavailable - user can run /zsync manually
        pass

    return 0


def sync_main():
    """Entry point for manual sync of unindexed notes.

    Scans the knowledge-base folder for notes not yet in S3 Vectors
    and indexes them.

    Usage: zk-sync (no arguments needed)

    Returns:
        0 on success
        1 on error
    """
    from .obsidian import ObsidianVault, NoteType
    from .embeddings import BedrockEmbeddings
    from .s3vectors import S3VectorsStore, VectorMetadata

    vault = ObsidianVault(VAULT)
    embeddings = BedrockEmbeddings()
    vectors = S3VectorsStore(BUCKET, INDEX)

    # Get all vectors currently in S3
    existing = vectors.query_all()
    existing_paths = {v.get("metadata", {}).get("obsidian_path", "") for v in existing}

    synced = 0
    errors = 0

    # Scan fleeting and permanent folders
    for note_type in [NoteType.FLEETING, NoteType.PERMANENT]:
        folder = VAULT / "knowledge-base" / note_type.value
        if not folder.exists():
            continue

        for path in folder.glob("*.md"):
            if str(path) in existing_paths:
                continue  # Already indexed

            try:
                note = vault.read_note(path)
                text = f"{note.title}\n\n{note.content}"
                embedding = embeddings.embed(text)

                metadata = VectorMetadata(
                    note_type=note.note_type.value,
                    knowledge_type=note.knowledge_type.value,
                    status=note.status,
                    title=note.title,
                    tags=note.tags,
                    obsidian_path=str(path),
                    content_preview=note.content[:500],
                )

                if vectors.put_vector(note.id, embedding, metadata):
                    console.print(f"[green]✓[/green] {note.title}")
                    synced += 1
                else:
                    console.print(f"[yellow]✗[/yellow] {note.title}")
                    errors += 1

            except Exception as e:
                console.print(f"[red]✗[/red] {path.name}: {e}")
                errors += 1

    console.print(f"\n[bold]Sync complete:[/bold] {synced} indexed, {errors} errors")
    return 0 if errors == 0 else 1


def search_main():
    """Entry point for semantic search.

    Usage: zk-search <query> [--type TYPE] [--top N]

    Arguments:
        query: Natural language search query
        --type: Filter by knowledge type (fact, decision, pattern, correction)
        --top: Number of results (default: 5)

    Returns:
        0 on success
        1 on error
    """
    import argparse

    from .embeddings import BedrockEmbeddings
    from .s3vectors import S3VectorsStore

    parser = argparse.ArgumentParser(description="Search knowledge base")
    parser.add_argument("query", nargs="+", help="Search query")
    parser.add_argument("--type", "-t", help="Filter by knowledge type")
    parser.add_argument("--top", "-n", type=int, default=5, help="Number of results")

    args = parser.parse_args()
    query = " ".join(args.query)

    try:
        embeddings = BedrockEmbeddings()
        vectors = S3VectorsStore(BUCKET, INDEX)

        results = vectors.query(embeddings.embed(query), top_k=args.top)

        # Filter by type if specified
        if args.type:
            results = [r for r in results if r.get("metadata", {}).get("knowledge_type") == args.type]

        console.print()
        console.print("=" * 50)
        console.print(f"[bold]Search:[/bold] {query}")
        console.print("=" * 50)
        console.print()

        if not results:
            console.print("[yellow]No results found.[/yellow]")
            return 0

        for i, r in enumerate(results, 1):
            meta = r.get("metadata", {})
            distance = r.get("distance", 0)
            similarity = 1 - distance
            title = meta.get("title", "Untitled")
            ktype = meta.get("knowledge_type", "unknown")
            tags = meta.get("tags", "")
            preview = meta.get("content_preview", "")[:80]
            path = meta.get("obsidian_path", "")

            console.print(f"[bold]{i}.[/bold] [{similarity:.2f}] [cyan]{title}[/cyan]")
            console.print(f"   Type: [magenta]{ktype}[/magenta] | Tags: {tags}")
            console.print(f"   [dim]\"{preview}...\"[/dim]")
            console.print(f"   [dim]{path}[/dim]")
            console.print()

        console.print("=" * 50)
        console.print(f"{len(results)} results")
        console.print("=" * 50)

        return 0

    except Exception as e:
        console.print(f"[red]Search failed: {e}[/red]")
        return 1


if __name__ == "__main__":
    sys.exit(extract_main())
