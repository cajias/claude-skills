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
    and indexes them using batch operations for efficiency.

    Usage: zk-sync [--force]

    Arguments:
        --force: Delete existing vectors and re-index everything

    Returns:
        0 on success
        1 on error
    """
    import argparse
    from concurrent.futures import ThreadPoolExecutor, as_completed

    from .obsidian import ObsidianVault, NoteType
    from .embeddings import BedrockEmbeddings
    from .s3vectors import S3VectorsStore, VectorMetadata

    # Batch configuration
    EMBEDDING_WORKERS = 10  # Parallel embedding requests
    VECTOR_BATCH_SIZE = 50  # S3 Vectors batch limit

    parser = argparse.ArgumentParser(description="Sync notes to S3 Vectors")
    parser.add_argument("--force", "-f", action="store_true", help="Re-index all notes")

    args = parser.parse_args()

    vault = ObsidianVault(VAULT)
    embeddings = BedrockEmbeddings()
    vectors = S3VectorsStore(BUCKET, INDEX)

    # Get all vectors currently in S3
    existing = vectors.query_all()

    # Build path -> key mapping for deletion
    path_to_key = {}
    for v in existing:
        path = v.get("metadata", {}).get("obsidian_path", "")
        key = v.get("key", "")
        if path and key:
            path_to_key[path] = key

    existing_paths = set(path_to_key.keys())

    # Phase 1: Collect notes to sync
    notes_to_sync = []
    keys_to_delete = []

    for note_type in [NoteType.FLEETING, NoteType.PERMANENT]:
        folder = VAULT / "knowledge-base" / note_type.value
        if not folder.exists():
            continue

        for path in folder.glob("*.md"):
            path_str = str(path)

            # Skip if already indexed (unless --force)
            if path_str in existing_paths and not args.force:
                continue

            try:
                note = vault.read_note(path)

                # Track old vectors for deletion
                if args.force and path_str in path_to_key:
                    old_key = path_to_key[path_str]
                    if old_key != note.id:
                        keys_to_delete.append(old_key)

                notes_to_sync.append((path, path_str, note))

            except Exception as e:
                console.print(f"[red]✗[/red] {path.name}: {e}")

    if not notes_to_sync:
        console.print("No notes to sync.")
        return 0

    console.print(f"Found {len(notes_to_sync)} notes to sync...")

    # Phase 2: Delete old vectors if --force
    deleted = 0
    if keys_to_delete:
        for key in keys_to_delete:
            if vectors.delete_vector(key):
                deleted += 1

    # Phase 3: Generate embeddings in parallel
    def generate_embedding(item):
        """Generate embedding for a single note."""
        path, path_str, note = item
        try:
            text = f"{note.title}\n\n{note.content}"
            embedding = embeddings.embed(text)
            metadata = VectorMetadata(
                note_type=note.note_type.value,
                knowledge_type=note.knowledge_type.value,
                status=note.status,
                title=note.title,
                tags=[str(t) for t in note.tags],  # Ensure strings
                obsidian_path=path_str,
                content_preview=note.content[:500],
            )
            return (note.id, embedding, metadata, note.title, None)
        except Exception as e:
            return (None, None, None, note.title if note else path.name, str(e))

    embedded_notes = []
    errors = 0

    with ThreadPoolExecutor(max_workers=EMBEDDING_WORKERS) as executor:
        futures = {executor.submit(generate_embedding, item): item for item in notes_to_sync}

        for future in as_completed(futures):
            note_id, embedding, metadata, title, error = future.result()
            if error:
                console.print(f"[red]✗[/red] {title}: {error}")
                errors += 1
            else:
                embedded_notes.append((note_id, embedding, metadata))
                console.print(f"[green]✓[/green] {title}")

    # Phase 4: Upload vectors in batches
    synced = 0
    for i in range(0, len(embedded_notes), VECTOR_BATCH_SIZE):
        batch = embedded_notes[i:i + VECTOR_BATCH_SIZE]
        if vectors.batch_put_vectors(batch):
            synced += len(batch)
        else:
            # Fall back to individual puts on batch failure
            for note_id, embedding, metadata in batch:
                if vectors.put_vector(note_id, embedding, metadata):
                    synced += 1
                else:
                    errors += 1

    result = f"Sync complete: {synced} indexed, {errors} errors"
    if deleted:
        result = f"Sync complete: {synced} indexed, {deleted} old vectors deleted, {errors} errors"
    console.print(f"\n{result}")
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


def dupes_main():
    """Entry point for duplicate detection.

    Scans S3 Vectors for semantically similar notes that might be duplicates.

    Usage: zk-dupes [--threshold N]

    Arguments:
        --threshold: Similarity threshold 0-100 (default: 85)

    Returns:
        0 on success
        1 on error
    """
    import argparse

    from .s3vectors import S3VectorsStore

    parser = argparse.ArgumentParser(description="Find duplicate notes")
    parser.add_argument("--threshold", "-t", type=int, default=85, help="Similarity threshold (0-100)")

    args = parser.parse_args()
    threshold = args.threshold / 100.0  # Convert to 0-1 range

    try:
        vectors = S3VectorsStore(BUCKET, INDEX)

        console.print("Fetching all vectors (with embeddings)...")
        all_vectors = vectors.query_all(include_embeddings=True)
        console.print(f"Total vectors: {len(all_vectors)}")
        console.print()

        console.print(f"Scanning for duplicates (>{args.threshold}% similarity)...")
        duplicates = []
        checked = set()

        for i, v in enumerate(all_vectors):
            key = v.get("key", "")
            if key in checked:
                continue

            vec_data = v.get("embedding") or v.get("data", {}).get("float32")
            if not vec_data:
                continue

            # Query for similar
            results = vectors.query(vec_data, top_k=5)

            for r in results:
                r_key = r.get("key", "")
                if r_key == key or r_key in checked:
                    continue

                dist = r.get("distance", 1)
                similarity = 1 - dist / 2  # Convert cosine distance to similarity

                if similarity >= threshold:
                    duplicates.append((similarity * 100, key, r_key))
                    checked.add(r_key)

            checked.add(key)

            if (i + 1) % 50 == 0:
                console.print(f"  Checked {i+1}/{len(all_vectors)}...")

        console.print()
        console.print("=" * 60)
        console.print(f"DUPLICATES (>{args.threshold}% similarity)")
        console.print("=" * 60)
        console.print()

        if not duplicates:
            console.print("[green]No duplicates found![/green]")
            console.print("Your knowledge base has good content diversity.")
        else:
            duplicates.sort(reverse=True)
            for sim, a, b in duplicates[:20]:
                console.print(f"[{sim:.1f}%]")
                console.print(f"  A: {a}")
                console.print(f"  B: {b}")
                console.print()

        console.print("=" * 60)
        console.print(f"Total: {len(duplicates)} duplicate pairs")
        console.print("=" * 60)

        return 0

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


def cluster_main():
    """Entry point for semantic clustering.

    Analyzes S3 Vectors to find semantic clusters in the knowledge base.

    Usage: zk-cluster [--seeds SEEDS]

    Arguments:
        --seeds: Comma-separated list of seed patterns (default: auto)

    Returns:
        0 on success
        1 on error
    """
    import argparse

    from .s3vectors import S3VectorsStore

    parser = argparse.ArgumentParser(description="Find semantic clusters")
    parser.add_argument("--seeds", "-s", help="Comma-separated seed patterns")

    args = parser.parse_args()

    # Default seed patterns
    default_seeds = [
        ("context", "CONTEXT MANAGEMENT"),
        ("tdd", "TDD & TESTING"),
        ("phase", "SDLC PHASES"),
        ("workflow", "WORKFLOWS"),
        ("infrastructure", "INFRASTRUCTURE"),
        ("knowledge", "KNOWLEDGE MANAGEMENT"),
        ("lint", "CODE QUALITY"),
        ("security", "SECURITY"),
    ]

    if args.seeds:
        seeds = [(s.strip(), s.strip().upper()) for s in args.seeds.split(",")]
    else:
        seeds = default_seeds

    try:
        vectors = S3VectorsStore(BUCKET, INDEX)

        console.print("Fetching all vectors (with embeddings)...")
        all_vectors = vectors.query_all(include_embeddings=True)
        console.print(f"Total vectors: {len(all_vectors)}")
        console.print()

        console.print("=" * 60)
        console.print("SEMANTIC CLUSTERS")
        console.print("=" * 60)
        console.print()

        for pattern, title in seeds:
            # Find seed vector
            seed_vec = None
            seed_key = None

            # Prefer permanent notes as seeds
            for v in all_vectors:
                key = v.get("key", "")
                if pattern in key.lower() and key.startswith("perm-"):
                    vec_data = v.get("embedding") or v.get("data", {}).get("float32")
                    if vec_data:
                        seed_vec = vec_data
                        seed_key = key
                        break

            # Fallback to any note
            if not seed_vec:
                for v in all_vectors:
                    key = v.get("key", "")
                    if pattern in key.lower():
                        vec_data = v.get("embedding") or v.get("data", {}).get("float32")
                        if vec_data:
                            seed_vec = vec_data
                            seed_key = key
                            break

            if not seed_vec:
                continue

            # Query for cluster members
            results = vectors.query(seed_vec, top_k=8)

            console.print(f"[bold]>> {title}[/bold]")

            seen = set()
            for r in results:
                key = r.get("key", "?")
                base = key.split("-", 3)[-1] if "-" in key else key
                if base in seen:
                    continue
                seen.add(base)

                dist = r.get("distance", 0)
                sim = (1 - dist / 2) * 100

                marker = "★" if key.startswith("perm-") else "○"
                console.print(f"   {marker} [{sim:5.1f}%] {key}")

            console.print()

        console.print("=" * 60)
        console.print("Legend: ★ = permanent, ○ = fleeting")
        console.print("=" * 60)

        return 0

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


def hub_check_main():
    """Entry point for hub validation.

    Compares semantic clusters with hub assignments to find mismatches.

    Usage: zk-hub-check [--threshold N]

    Arguments:
        --threshold: Minimum similarity to hub centroid (default: 60)

    Returns:
        0 on success
        1 on error
    """
    import argparse

    from .s3vectors import S3VectorsStore
    from .embeddings import BedrockEmbeddings
    from .obsidian import ObsidianVault

    parser = argparse.ArgumentParser(description="Validate hub assignments")
    parser.add_argument("--threshold", "-t", type=int, default=60, help="Similarity threshold (0-100)")

    args = parser.parse_args()
    threshold = args.threshold / 100.0

    try:
        vectors = S3VectorsStore(BUCKET, INDEX)
        embeddings = BedrockEmbeddings()
        vault = ObsidianVault(VAULT)

        console.print("Fetching all vectors...")
        all_vectors = vectors.query_all(include_embeddings=True)
        console.print(f"Total vectors: {len(all_vectors)}")
        console.print()

        # Build hub name -> embedding map by reading hub files
        hub_dir = VAULT / "knowledge-base" / "hubs"
        hub_embeddings = {}

        if hub_dir.exists():
            for hub_file in hub_dir.glob("*.md"):
                hub_name = hub_file.stem
                try:
                    content = hub_file.read_text()
                    hub_emb = embeddings.embed(f"{hub_name}\n\n{content[:1000]}")
                    hub_embeddings[hub_name] = hub_emb
                    console.print(f"[dim]Loaded hub: {hub_name}[/dim]")
                except Exception as e:
                    console.print(f"[yellow]Could not embed hub {hub_name}: {e}[/yellow]")

        if not hub_embeddings:
            console.print("[yellow]No hubs found to validate against.[/yellow]")
            return 0

        console.print()
        console.print("=" * 70)
        console.print("HUB VALIDATION REPORT")
        console.print("=" * 70)
        console.print()

        mismatches = []
        well_assigned = 0

        for v in all_vectors:
            key = v.get("key", "")
            meta = v.get("metadata", {})
            obsidian_path = meta.get("obsidian_path", "")

            # Skip non-permanent or hub files
            if not key.startswith("perm-") or "/hubs/" in obsidian_path:
                continue

            vec_data = v.get("embedding") or v.get("data", {}).get("float32")
            if not vec_data:
                continue

            # Get assigned hub from file
            assigned_hub = None
            if obsidian_path and Path(obsidian_path).exists():
                try:
                    content = Path(obsidian_path).read_text()
                    # Find ## Hub section and parse wiki link
                    in_hub_section = False
                    for line in content.split("\n"):
                        if line.strip() == "## Hub":
                            in_hub_section = True
                            continue
                        if in_hub_section and line.startswith("##"):
                            break  # New section
                        if in_hub_section and "[[" in line and "]]" in line:
                            # Parse [[hubs/hub-name|Display]] or [[hubs/hub-name]]
                            hub_ref = line.split("[[")[1].split("]]")[0]
                            hub_ref = hub_ref.split("|")[0]  # Remove alias
                            if hub_ref.startswith("hubs/"):
                                hub_ref = hub_ref[5:]  # Remove hubs/ prefix
                            if hub_ref in hub_embeddings:
                                assigned_hub = hub_ref
                            break
                except:
                    pass

            if not assigned_hub:
                continue

            # Calculate similarity to assigned hub
            import numpy as np
            vec_arr = np.array(vec_data)
            hub_arr = np.array(hub_embeddings[assigned_hub])
            similarity = np.dot(vec_arr, hub_arr) / (np.linalg.norm(vec_arr) * np.linalg.norm(hub_arr))

            # Find best matching hub
            best_hub = None
            best_sim = 0
            for hub_name, hub_emb in hub_embeddings.items():
                hub_arr = np.array(hub_emb)
                sim = np.dot(vec_arr, hub_arr) / (np.linalg.norm(vec_arr) * np.linalg.norm(hub_arr))
                if sim > best_sim:
                    best_sim = sim
                    best_hub = hub_name

            title = meta.get("title", key)

            if similarity < threshold and best_hub != assigned_hub:
                mismatches.append({
                    "title": title,
                    "assigned": assigned_hub,
                    "assigned_sim": similarity * 100,
                    "suggested": best_hub,
                    "suggested_sim": best_sim * 100,
                    "path": obsidian_path
                })
            else:
                well_assigned += 1

        # Report mismatches
        if mismatches:
            console.print(f"[yellow]⚠️  Found {len(mismatches)} potential misassignments:[/yellow]")
            console.print()

            for m in sorted(mismatches, key=lambda x: x["assigned_sim"]):
                console.print(f"[cyan]{m['title'][:50]}[/cyan]")
                console.print(f"   Current: [red]{m['assigned']}[/red] ({m['assigned_sim']:.1f}%)")
                console.print(f"   Suggest: [green]{m['suggested']}[/green] ({m['suggested_sim']:.1f}%)")
                console.print()
        else:
            console.print("[green]✓ All notes are well-assigned to their hubs![/green]")

        console.print("=" * 70)
        console.print(f"Well-assigned: {well_assigned} | Mismatches: {len(mismatches)}")
        console.print("=" * 70)

        return 0

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return 1


def orphans_main():
    """Entry point for orphan detection.

    Finds notes that don't fit well into any semantic cluster.

    Usage: zk-orphans [--threshold N]

    Arguments:
        --threshold: Max similarity to be considered orphan (default: 50)

    Returns:
        0 on success
        1 on error
    """
    import argparse
    import numpy as np

    from .s3vectors import S3VectorsStore

    parser = argparse.ArgumentParser(description="Find orphan notes")
    parser.add_argument("--threshold", "-t", type=int, default=50, help="Max similarity threshold (0-100)")

    args = parser.parse_args()
    threshold = args.threshold / 100.0

    try:
        vectors = S3VectorsStore(BUCKET, INDEX)

        console.print("Fetching all vectors (with embeddings)...")
        all_vectors = vectors.query_all(include_embeddings=True)
        console.print(f"Total vectors: {len(all_vectors)}")
        console.print()

        # Calculate average similarity for each note
        orphans = []

        for i, v in enumerate(all_vectors):
            key = v.get("key", "")
            meta = v.get("metadata", {})

            vec_data = v.get("embedding") or v.get("data", {}).get("float32")
            if not vec_data:
                continue

            # Query for similar notes
            results = vectors.query(vec_data, top_k=6)  # Top 6 includes self

            # Calculate average similarity (excluding self)
            similarities = []
            for r in results:
                if r.get("key") == key:
                    continue
                dist = r.get("distance", 2)
                sim = 1 - dist / 2
                similarities.append(sim)

            if similarities:
                avg_sim = sum(similarities) / len(similarities)
                max_sim = max(similarities)

                if max_sim < threshold:
                    orphans.append({
                        "key": key,
                        "title": meta.get("title", key),
                        "avg_sim": avg_sim * 100,
                        "max_sim": max_sim * 100,
                        "note_type": meta.get("note_type", "unknown"),
                        "path": meta.get("obsidian_path", "")
                    })

            if (i + 1) % 50 == 0:
                console.print(f"  Analyzed {i+1}/{len(all_vectors)}...")

        console.print()
        console.print("=" * 70)
        console.print(f"ORPHAN NOTES (max similarity < {args.threshold}%)")
        console.print("=" * 70)
        console.print()

        if not orphans:
            console.print("[green]✓ No orphan notes found![/green]")
            console.print("All notes have strong semantic connections to others.")
        else:
            # Sort by max similarity (most isolated first)
            orphans.sort(key=lambda x: x["max_sim"])

            for o in orphans[:20]:
                marker = "★" if o["note_type"] == "permanent" else "○"
                console.print(f"{marker} [cyan]{o['title'][:50]}[/cyan]")
                console.print(f"   Max similarity: [yellow]{o['max_sim']:.1f}%[/yellow]")
                console.print(f"   Avg similarity: {o['avg_sim']:.1f}%")
                console.print()

        console.print("=" * 70)
        console.print(f"Total orphans: {len(orphans)}")
        console.print("Legend: ★ = permanent, ○ = fleeting")
        console.print("=" * 70)

        return 0

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


def related_main():
    """Entry point for related note suggestions.

    Suggests related notes for a given note or query.

    Usage: zk-related <query|note-id> [--top N]

    Arguments:
        query: Search query or note ID
        --top: Number of suggestions (default: 10)

    Returns:
        0 on success
        1 on error
    """
    import argparse

    from .s3vectors import S3VectorsStore
    from .embeddings import BedrockEmbeddings

    parser = argparse.ArgumentParser(description="Find related notes")
    parser.add_argument("query", nargs="+", help="Search query or note ID")
    parser.add_argument("--top", "-n", type=int, default=10, help="Number of results")

    args = parser.parse_args()
    query = " ".join(args.query)

    try:
        vectors = S3VectorsStore(BUCKET, INDEX)
        embeddings = BedrockEmbeddings()

        # Check if query is a note ID
        query_vec = None
        is_note = False

        if query.startswith("perm-") or query.startswith("fleet-"):
            # Try to get vector by ID
            note = vectors.get_vector(query)
            if note:
                query_vec = note.get("data", {}).get("float32")
                is_note = True
                console.print(f"[dim]Found note: {query}[/dim]")

        if not query_vec:
            # Embed the query
            console.print(f"[dim]Embedding query: {query}[/dim]")
            query_vec = embeddings.embed(query)

        # Query for similar
        results = vectors.query(query_vec, top_k=args.top + (1 if is_note else 0))

        console.print()
        console.print("=" * 60)
        console.print(f"RELATED NOTES: {query[:40]}...")
        console.print("=" * 60)
        console.print()

        count = 0
        for r in results:
            key = r.get("key", "?")
            # Skip self if querying by note ID
            if is_note and key == query:
                continue

            meta = r.get("metadata", {})
            dist = r.get("distance", 0)
            sim = (1 - dist / 2) * 100

            title = meta.get("title", key)
            tags = meta.get("tags", "")
            preview = meta.get("content_preview", "")[:60]

            marker = "★" if key.startswith("perm-") else "○"
            console.print(f"{marker} [{sim:5.1f}%] [cyan]{title}[/cyan]")
            if tags:
                console.print(f"   Tags: [magenta]{tags}[/magenta]")
            if preview:
                console.print(f"   [dim]\"{preview}...\"[/dim]")
            console.print()

            count += 1
            if count >= args.top:
                break

        console.print("=" * 60)
        console.print(f"Showing {count} related notes")
        console.print("Legend: ★ = permanent, ○ = fleeting")
        console.print("=" * 60)

        return 0

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


def hub_review_main():
    """Entry point for comprehensive hub review.

    Analyzes semantic clusters against existing hubs to identify:
    - Gap clusters that need new hubs
    - Unassigned notes needing hub assignment
    - Misassigned notes needing reassignment
    - Hub coverage statistics

    Usage: zk-hub-review [--clusters N]

    Arguments:
        --clusters: Number of clusters to discover (default: 10)

    Returns:
        0 on success
        1 on error
    """
    import argparse
    import numpy as np
    from collections import defaultdict

    from .s3vectors import S3VectorsStore
    from .embeddings import BedrockEmbeddings

    parser = argparse.ArgumentParser(description="Comprehensive hub review")
    parser.add_argument("--clusters", "-c", type=int, default=10, help="Number of clusters")

    args = parser.parse_args()

    try:
        vectors = S3VectorsStore(BUCKET, INDEX)
        embeddings = BedrockEmbeddings()

        console.print("[bold]Hub Review Analysis[/bold]")
        console.print("=" * 70)
        console.print()

        # 1. Load existing hubs
        console.print("[dim]Loading hubs...[/dim]")
        hub_dir = VAULT / "knowledge-base" / "hubs"
        hub_data = {}

        if hub_dir.exists():
            for hub_file in hub_dir.glob("*.md"):
                hub_name = hub_file.stem
                content = hub_file.read_text()
                hub_emb = embeddings.embed(f"{hub_name}\n\n{content[:1000]}")
                hub_data[hub_name] = {
                    "embedding": hub_emb,
                    "path": str(hub_file)
                }

        console.print(f"  Found {len(hub_data)} existing hubs")

        # 2. Fetch all vectors
        console.print("[dim]Fetching vectors...[/dim]")
        all_vectors = vectors.query_all(include_embeddings=True)
        console.print(f"  Total vectors: {len(all_vectors)}")

        # 3. Categorize notes
        permanent_dir = VAULT / "knowledge-base" / "permanent"
        permanent_notes = []
        notes_with_hub = []
        notes_without_hub = []

        console.print("[dim]Analyzing note assignments...[/dim]")
        for v in all_vectors:
            key = v.get("key", "")
            meta = v.get("metadata", {})
            path = meta.get("obsidian_path", "")

            if not key.startswith("perm-") or "/hubs/" in path:
                continue

            vec_data = v.get("embedding") or v.get("data", {}).get("float32")
            if not vec_data:
                continue

            note_info = {
                "key": key,
                "title": meta.get("title", key),
                "path": path,
                "embedding": vec_data,
                "tags": meta.get("tags", "").split(",") if meta.get("tags") else []
            }

            # Check if has hub assignment
            assigned_hub = None
            if path and Path(path).exists():
                try:
                    content = Path(path).read_text()
                    in_hub_section = False
                    for line in content.split("\n"):
                        if line.strip() == "## Hub":
                            in_hub_section = True
                            continue
                        if in_hub_section and line.startswith("##"):
                            break
                        if in_hub_section and "[[" in line and "]]" in line:
                            hub_ref = line.split("[[")[1].split("]]")[0].split("|")[0]
                            if hub_ref.startswith("hubs/"):
                                hub_ref = hub_ref[5:]
                            assigned_hub = hub_ref
                            break
                except:
                    pass

            note_info["assigned_hub"] = assigned_hub
            permanent_notes.append(note_info)

            if assigned_hub:
                notes_with_hub.append(note_info)
            else:
                notes_without_hub.append(note_info)

        console.print(f"  Permanent notes: {len(permanent_notes)}")
        console.print(f"  With hub: {len(notes_with_hub)}")
        console.print(f"  Without hub: {len(notes_without_hub)}")
        console.print()

        # 4. Discover clusters using k-means
        console.print("[dim]Discovering semantic clusters...[/dim]")
        if len(permanent_notes) < args.clusters:
            console.print(f"[yellow]Not enough notes for {args.clusters} clusters[/yellow]")
            return 0

        from sklearn.cluster import KMeans

        X = np.array([n["embedding"] for n in permanent_notes])
        kmeans = KMeans(n_clusters=args.clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)

        # Group notes by cluster
        clusters = defaultdict(list)
        for i, note in enumerate(permanent_notes):
            note["cluster"] = labels[i]
            clusters[labels[i]].append(note)

        # 5. Analyze each cluster
        console.print()
        console.print("=" * 70)
        console.print("CLUSTER ANALYSIS")
        console.print("=" * 70)
        console.print()

        cluster_analysis = []

        for cluster_id in range(args.clusters):
            cluster_notes = clusters[cluster_id]
            centroid = kmeans.cluster_centers_[cluster_id]

            # Find representative keywords from titles
            all_words = []
            for n in cluster_notes:
                words = n["title"].lower().replace("-", " ").split()
                all_words.extend(words)

            # Count word frequency
            word_freq = defaultdict(int)
            stopwords = {"the", "a", "an", "to", "for", "of", "in", "on", "with", "and", "is", "are", "be"}
            for w in all_words:
                if len(w) > 2 and w not in stopwords:
                    word_freq[w] += 1

            top_words = sorted(word_freq.items(), key=lambda x: -x[1])[:5]
            cluster_label = " ".join([w[0] for w in top_words[:3]]).upper()

            # Find best matching hub
            best_hub = None
            best_sim = 0
            for hub_name, hub_info in hub_data.items():
                hub_emb = np.array(hub_info["embedding"])
                sim = np.dot(centroid, hub_emb) / (np.linalg.norm(centroid) * np.linalg.norm(hub_emb))
                if sim > best_sim:
                    best_sim = sim
                    best_hub = hub_name

            cluster_analysis.append({
                "id": cluster_id,
                "label": cluster_label,
                "size": len(cluster_notes),
                "keywords": [w[0] for w in top_words],
                "best_hub": best_hub,
                "hub_similarity": best_sim * 100,
                "notes": cluster_notes
            })

        # Sort by size
        cluster_analysis.sort(key=lambda x: -x["size"])

        # Display clusters
        gap_clusters = []
        for c in cluster_analysis:
            status = ""
            if c["hub_similarity"] < 40:
                status = "[red]⚠ GAP[/red]"
                gap_clusters.append(c)
            elif c["hub_similarity"] < 55:
                status = "[yellow]~ WEAK[/yellow]"
            else:
                status = "[green]✓[/green]"

            console.print(f"{status} [bold]{c['label']}[/bold] ({c['size']} notes)")
            console.print(f"   Keywords: {', '.join(c['keywords'])}")
            console.print(f"   Best hub: {c['best_hub']} ({c['hub_similarity']:.1f}%)")

            # Show sample notes
            sample = c["notes"][:3]
            for n in sample:
                console.print(f"   • {n['title'][:45]}")
            console.print()

        # 6. Summary and recommendations
        console.print("=" * 70)
        console.print("SUMMARY & RECOMMENDATIONS")
        console.print("=" * 70)
        console.print()

        table = Table(title="Knowledge Base Status")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", justify="right")
        table.add_column("Status", style="dim")

        table.add_row("Permanent notes", str(len(permanent_notes)), "")
        table.add_row("Notes with hub", str(len(notes_with_hub)),
                      "[green]✓[/green]" if len(notes_with_hub) > len(permanent_notes) * 0.8 else "[yellow]low[/yellow]")
        table.add_row("Notes without hub", str(len(notes_without_hub)),
                      "[green]✓[/green]" if len(notes_without_hub) < 20 else "[red]needs work[/red]")
        table.add_row("Existing hubs", str(len(hub_data)), "")
        table.add_row("Semantic clusters", str(args.clusters), "")
        table.add_row("Gap clusters", str(len(gap_clusters)),
                      "[green]✓[/green]" if len(gap_clusters) == 0 else "[yellow]new hubs needed[/yellow]")

        console.print(table)
        console.print()

        # Recommendations
        if gap_clusters:
            console.print("[bold]Suggested New Hubs:[/bold]")
            for gc in gap_clusters:
                suggested_name = "-".join(gc["keywords"][:2])
                console.print(f"  • [cyan]{suggested_name}[/cyan] ({gc['size']} notes)")
                console.print(f"    Topics: {', '.join(gc['keywords'])}")
            console.print()

        if notes_without_hub:
            console.print(f"[bold]Notes Needing Hub Assignment:[/bold] {len(notes_without_hub)}")

            # Group unassigned by best-fit cluster
            unassigned_by_cluster = defaultdict(list)
            for n in notes_without_hub:
                unassigned_by_cluster[n["cluster"]].append(n)

            for cluster_id, notes in sorted(unassigned_by_cluster.items(), key=lambda x: -len(x[1]))[:5]:
                c = next(ca for ca in cluster_analysis if ca["id"] == cluster_id)
                console.print(f"  → {c['label']}: {len(notes)} notes → assign to '{c['best_hub']}'")

        console.print()
        console.print("=" * 70)

        return 0

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return 1


def fix_ids_main():
    """Entry point for fixing note ID prefixes.

    Ensures all permanent notes have 'perm-' prefix and fleeting notes
    have 'flee-' prefix. This is important for proper categorization
    in semantic search and hub analysis.

    Usage: zk-fix-ids [--dry-run]

    Arguments:
        --dry-run: Show what would be changed without modifying files

    Returns:
        0 on success
        1 on error
    """
    import argparse
    import re

    parser = argparse.ArgumentParser(description="Fix note ID prefixes")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Show changes without applying")

    args = parser.parse_args()

    try:
        permanent_dir = VAULT / "knowledge-base" / "permanent"
        fleeting_dir = VAULT / "knowledge-base" / "fleeting"

        fixes = []

        # Check permanent notes
        if permanent_dir.exists():
            for note_file in permanent_dir.glob("*.md"):
                content = note_file.read_text()

                # Extract current ID
                match = re.search(r'^id:\s*(.+)$', content, re.MULTILINE)
                if not match:
                    continue

                current_id = match.group(1).strip()

                # Check if needs fixing
                new_id = None
                if current_id.startswith("flee-"):
                    new_id = "perm-" + current_id[5:]
                elif current_id.startswith("fleeting-"):
                    new_id = "perm-" + current_id[9:]

                if new_id:
                    fixes.append({
                        "file": note_file,
                        "old_id": current_id,
                        "new_id": new_id,
                        "type": "permanent"
                    })

        # Check fleeting notes
        if fleeting_dir.exists():
            for note_file in fleeting_dir.glob("*.md"):
                content = note_file.read_text()

                match = re.search(r'^id:\s*(.+)$', content, re.MULTILINE)
                if not match:
                    continue

                current_id = match.group(1).strip()

                new_id = None
                if current_id.startswith("perm-"):
                    new_id = "flee-" + current_id[5:]

                if new_id:
                    fixes.append({
                        "file": note_file,
                        "old_id": current_id,
                        "new_id": new_id,
                        "type": "fleeting"
                    })

        if not fixes:
            console.print("[green]✓ All note IDs have correct prefixes![/green]")
            return 0

        console.print(f"Found {len(fixes)} notes with incorrect ID prefixes:")
        console.print()

        for fix in fixes[:20]:
            console.print(f"  {fix['file'].name}")
            console.print(f"    [red]{fix['old_id']}[/red] → [green]{fix['new_id']}[/green]")

        if len(fixes) > 20:
            console.print(f"  ... and {len(fixes) - 20} more")

        console.print()

        if args.dry_run:
            console.print("[yellow]Dry run - no changes made[/yellow]")
        else:
            # Apply fixes
            for fix in fixes:
                content = fix["file"].read_text()
                new_content = content.replace(f"id: {fix['old_id']}", f"id: {fix['new_id']}", 1)
                fix["file"].write_text(new_content)

            console.print(f"[green]✓ Fixed {len(fixes)} note IDs[/green]")
            console.print()
            console.print("[dim]Run zk-sync to update S3 Vectors[/dim]")

        return 0

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


def _handle_fix_audit_mode(args, vectors, embeddings, RELATIONSHIP_TYPES):
    """Handle --fix and --audit modes for link management.

    Args:
        args: Parsed command line arguments
        vectors: S3VectorsStore instance
        embeddings: BedrockEmbeddings instance
        RELATIONSHIP_TYPES: Dict of relationship types and descriptions

    Returns:
        0 on success, 1 on error
    """
    import re
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    permanent_dir = VAULT / "knowledge-base" / "permanent"
    if not permanent_dir.exists():
        console.print("[red]Permanent notes directory not found[/red]")
        return 1

    # Build inventory of existing notes
    existing_notes = {
        note.stem: note
        for note in permanent_dir.glob("*.md")
    }

    console.print(f"[dim]Found {len(existing_notes)} existing notes[/dim]")

    # Extract all links from all notes
    all_links = set()
    links_by_file = {}

    for note in permanent_dir.glob("*.md"):
        content = note.read_text()
        # Match [[link]] or [[link|alias]]
        links = re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', content)
        links_by_file[note] = links
        all_links.update(links)

    # Identify broken links
    broken_links = []
    for link in all_links:
        # Skip vault paths (playbooks/, hubs/, etc.)
        if "/" in link:
            continue
        if link not in existing_notes:
            broken_links.append(link)

    # Count valid links
    valid_count = len(all_links) - len(broken_links)

    # Audit mode - just report
    console.print()
    console.print("=" * 70)
    console.print("[bold]LINK AUDIT REPORT[/bold]")
    console.print("=" * 70)
    console.print()
    console.print(f"Total unique links: {len(all_links)}")
    console.print(f"[green]Valid links: {valid_count}[/green]")
    console.print(f"[yellow]Broken links: {len(broken_links)}[/yellow]")
    console.print()

    if broken_links:
        console.print("[bold]Broken Links:[/bold]")
        for bl in broken_links[:20]:  # Show first 20
            console.print(f"  • [[{bl}]]")
        if len(broken_links) > 20:
            console.print(f"  ... and {len(broken_links) - 20} more")
        console.print()

    if args.audit:
        console.print("=" * 70)
        console.print("[dim]Run with --fix to repair broken links[/dim]")
        return 0

    # Fix mode - repair broken links
    if not broken_links:
        console.print("[green]✓ No broken links to fix![/green]")
        return 0

    console.print("[bold]Finding replacements for broken links...[/bold]")
    console.print()

    # Use TF-IDF to find semantic matches
    existing_texts = [name.replace("-", " ") for name in existing_notes.keys()]
    existing_names = list(existing_notes.keys())

    replacements = {}
    unfixable = []

    for broken in broken_links:
        broken_text = broken.replace("-", " ")

        # Compute similarity
        try:
            vectorizer = TfidfVectorizer()
            all_texts = [broken_text] + existing_texts
            tfidf = vectorizer.fit_transform(all_texts)
            similarities = cosine_similarity(tfidf[0:1], tfidf[1:])[0]

            best_idx = similarities.argmax()
            if similarities[best_idx] > 0.3:
                replacements[broken] = existing_names[best_idx]
                console.print(f"  [[{broken}]] → [[{existing_names[best_idx]}]] ({similarities[best_idx]*100:.0f}%)")
            else:
                unfixable.append(broken)
        except Exception:
            unfixable.append(broken)

    console.print()
    console.print(f"[green]Fixable: {len(replacements)}[/green]")
    console.print(f"[yellow]Unfixable (no good match): {len(unfixable)}[/yellow]")

    if not replacements:
        console.print("\n[yellow]No links could be automatically fixed.[/yellow]")
        return 0

    # Confirm and apply fixes
    if not args.yes:
        confirm = input(f"\nApply {len(replacements)} fixes? [y/N]: ")
        if confirm.lower() != 'y':
            console.print("[yellow]Aborted.[/yellow]")
            return 0

    console.print("\n[bold]Applying fixes...[/bold]")

    fixed_files = 0
    fixed_links = 0

    for note_path, links in links_by_file.items():
        needs_update = False
        content = note_path.read_text()
        original_content = content

        for link in links:
            if link in replacements:
                replacement = replacements[link]
                # Replace [[broken]] or [[broken|alias]] with [[replacement]]
                content = re.sub(
                    rf'\[\[{re.escape(link)}(\|[^\]]+)?\]\]',
                    f'[[{replacement}]]',
                    content
                )
                needs_update = True
                fixed_links += 1

        if needs_update and content != original_content:
            note_path.write_text(content)
            fixed_files += 1
            console.print(f"  ✓ {note_path.stem}")

    console.print()
    console.print("=" * 70)
    console.print(f"[bold]Fixed {fixed_links} links in {fixed_files} files[/bold]")
    if unfixable:
        console.print(f"[yellow]Unfixable links kept as placeholders: {len(unfixable)}[/yellow]")
    console.print("=" * 70)

    return 0


def suggest_links_main():
    """Entry point for Zettelkasten link suggestions.

    Analyzes notes and suggests meaningful links following Zettelkasten principles:
    - Links connect ideas, not just similar documents
    - Each link has a relationship type (solves, enables, contradicts, etc.)
    - Bidirectional linking - suggests backlinks too
    - Quality over quantity - only meaningful connections

    Zettelkasten Relationship Types:
    - SOLVES: Note A addresses problem described in Note B
    - ENABLES: Note A is prerequisite for Note B
    - ELABORATES: Note B expands/details concept in Note A
    - CONTRADICTS: Note B challenges or limits Note A
    - SUPPORTS: Note B provides evidence for Note A
    - APPLIES: Note B applies principle from Note A
    - ABSTRACTS: Note B generalizes from Note A
    - SEQUENCE: Note B logically follows Note A

    Usage: zk-suggest-links [note-path] [--all] [--threshold N]

    Arguments:
        note-path: Path to specific note (optional)
        --all: Analyze all permanent notes
        --threshold: Minimum similarity for candidates (default: 65)

    Returns:
        0 on success
        1 on error
    """
    import argparse
    import re

    from .s3vectors import S3VectorsStore
    from .embeddings import BedrockEmbeddings

    parser = argparse.ArgumentParser(description="Suggest Zettelkasten links")
    parser.add_argument("note_path", nargs="?", help="Path to note file")
    parser.add_argument("--all", "-a", action="store_true", help="Analyze all notes")
    parser.add_argument("--threshold", "-t", type=int, default=65, help="Similarity threshold")
    parser.add_argument("--top", "-n", type=int, default=5, help="Max suggestions per note")
    parser.add_argument("--apply", action="store_true", help="Apply suggestions to notes")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")
    parser.add_argument("--bidirectional", "-b", action="store_true", default=True,
                        help="Create backlinks in target notes (default: True)")
    parser.add_argument("--no-bidirectional", dest="bidirectional", action="store_false",
                        help="Disable bidirectional linking")
    parser.add_argument("--no-validate", action="store_true",
                        help="Skip LLM validation (faster, uses heuristics only)")
    parser.add_argument("--min-confidence", type=int, default=70,
                        help="Minimum LLM confidence to accept link (0-100, default: 70)")
    parser.add_argument("--fix", action="store_true",
                        help="Repair broken links using semantic matching")
    parser.add_argument("--audit", action="store_true",
                        help="Show link health report without making changes")

    args = parser.parse_args()
    threshold = args.threshold / 100.0

    # Zettelkasten relationship types
    RELATIONSHIP_TYPES = {
        "SOLVES": "addresses problem in",
        "ENABLES": "is prerequisite for",
        "ELABORATES": "expands on",
        "CONTRADICTS": "challenges or limits",
        "SUPPORTS": "provides evidence for",
        "APPLIES": "applies principle from",
        "ABSTRACTS": "generalizes from",
        "SEQUENCE": "logically follows",
    }

    # Inverse relationships for bidirectional linking
    INVERSE_RELATIONSHIPS = {
        "SOLVES": "SOLVES",           # Symmetric - both solve each other's context
        "ENABLES": "SEQUENCE",        # If A enables B, B follows A
        "ELABORATES": "ABSTRACTS",    # If A elaborates B, B abstracts A
        "CONTRADICTS": "CONTRADICTS", # Symmetric
        "SUPPORTS": "APPLIES",        # If A supports B, B applies A
        "APPLIES": "SUPPORTS",
        "ABSTRACTS": "ELABORATES",
        "SEQUENCE": "ENABLES",
    }

    try:
        vectors = S3VectorsStore(BUCKET, INDEX)
        embeddings = BedrockEmbeddings()

        # Handle fix/audit modes first
        if args.fix or args.audit:
            return _handle_fix_audit_mode(args, vectors, embeddings, RELATIONSHIP_TYPES)

        # Initialize validator if LLM validation enabled
        validator = None
        if not args.no_validate:
            try:
                from .validator import LinkValidator
                validator = LinkValidator(min_confidence=args.min_confidence / 100.0)
                console.print("[dim]LLM validation enabled[/dim]")
            except ImportError:
                console.print("[yellow]Warning: validator module not found, using heuristics only[/yellow]")

        # Collect notes to analyze
        notes_to_analyze = []

        if args.note_path:
            notes_to_analyze.append(Path(args.note_path))
        elif args.all:
            permanent_dir = VAULT / "knowledge-base" / "permanent"
            if permanent_dir.exists():
                notes_to_analyze = list(permanent_dir.glob("*.md"))  # All permanent notes
        else:
            console.print("[yellow]Specify a note path or use --all[/yellow]")
            return 1

        console.print(f"Analyzing {len(notes_to_analyze)} note(s)...")
        console.print()

        all_suggestions = []

        for note_path in notes_to_analyze:
            if not note_path.exists():
                console.print(f"[red]Not found: {note_path}[/red]")
                continue

            # Read note content
            content = note_path.read_text()

            # Extract title
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            title = title_match.group(1) if title_match else note_path.stem

            # Extract existing links
            existing_links = set(re.findall(r'\[\[([^\]|]+)', content))

            # Get note embedding
            note_text = f"{title}\n\n{content[:1500]}"
            note_emb = embeddings.embed(note_text)

            # Query for similar notes
            results = vectors.query(note_emb, top_k=args.top + len(existing_links) + 1)

            # Analyze candidates
            suggestions = []
            for r in results:
                key = r.get("key", "")
                meta = r.get("metadata", {})
                candidate_title = meta.get("title", key)
                candidate_path = meta.get("obsidian_path", "")

                # Skip self
                if candidate_path == str(note_path):
                    continue

                # Skip already linked
                candidate_stem = Path(candidate_path).stem if candidate_path else key
                if candidate_stem in existing_links or candidate_title in existing_links:
                    continue

                # Check similarity threshold
                dist = r.get("distance", 2)
                similarity = 1 - dist / 2
                if similarity < threshold:
                    continue

                # Determine relationship type based on knowledge types
                source_type = "pattern"  # Default
                if "knowledge_type:" in content:
                    kt_match = re.search(r'knowledge_type:\s*(\w+)', content)
                    if kt_match:
                        source_type = kt_match.group(1)

                target_type = meta.get("knowledge_type", "fact")

                # Heuristic relationship classification
                relationship = "ELABORATES"  # Default
                if source_type == "pattern" and target_type == "fact":
                    relationship = "APPLIES"
                elif source_type == "fact" and target_type == "pattern":
                    relationship = "SUPPORTS"
                elif "problem" in title.lower() or "anti-pattern" in title.lower():
                    relationship = "SOLVES"
                elif "prerequisite" in content.lower() or "before" in content.lower():
                    relationship = "ENABLES"
                elif similarity > 0.85:
                    relationship = "ELABORATES"

                # LLM validation if enabled
                validated = False
                llm_confidence = similarity  # Use similarity as fallback confidence
                if validator is not None:
                    target_content = meta.get("content_preview", "")[:500]
                    validation = validator.validate(
                        source_title=title,
                        source_content=content[:500],
                        target_title=candidate_title,
                        target_content=target_content,
                    )
                    if not validation.should_link:
                        continue  # Skip this candidate - LLM rejected
                    # Use LLM's classification
                    relationship = validation.relationship
                    llm_confidence = validation.confidence
                    validated = True

                suggestions.append({
                    "from_title": title,
                    "from_path": str(note_path),
                    "to_title": candidate_title,
                    "to_path": candidate_path,
                    "similarity": similarity * 100,
                    "relationship": relationship,
                    "relationship_desc": RELATIONSHIP_TYPES.get(relationship, "relates to"),
                    "validated": validated,
                    "confidence": llm_confidence * 100 if validated else similarity * 100,
                })

                if len(suggestions) >= args.top:
                    break

            all_suggestions.extend(suggestions)

        # Display results
        console.print("=" * 70)
        console.print("ZETTELKASTEN LINK SUGGESTIONS")
        console.print("=" * 70)
        console.print()
        console.print("[dim]Relationship types:[/dim]")
        for rtype, desc in list(RELATIONSHIP_TYPES.items())[:4]:
            console.print(f"  [cyan]{rtype}[/cyan]: A {desc} B")
        console.print()

        if not all_suggestions:
            console.print("[green]✓ No new link suggestions - notes are well-connected![/green]")
        else:
            # Group by source note
            by_source = {}
            for s in all_suggestions:
                src = s["from_title"]
                if src not in by_source:
                    by_source[src] = []
                by_source[src].append(s)

            for source_title, suggestions in by_source.items():
                console.print(f"[bold]{source_title[:50]}[/bold]")
                for s in suggestions:
                    rel = s["relationship"]
                    desc = s["relationship_desc"]
                    target = s["to_title"][:40]
                    conf = s.get("confidence", s["similarity"])
                    validated = s.get("validated", False)
                    status = "[green]✓[/green]" if validated else ""
                    console.print(f"  → [cyan]{rel}[/cyan] [[{target}]] ({conf:.0f}%) {status}")
                    console.print(f"    [dim]This note {desc} '{target}'[/dim]")
                console.print()

        console.print("=" * 70)
        console.print(f"Total suggestions: {len(all_suggestions)}")
        console.print("=" * 70)

        if not all_suggestions:
            return 0

        # Apply mode - actually add links to notes
        if args.apply:
            if not args.yes:
                confirm = input(f"\nApply {len(all_suggestions)} links to notes? [y/N]: ")
                if confirm.lower() != 'y':
                    console.print("[yellow]Aborted.[/yellow]")
                    return 0

            console.print("\n[bold]Applying links...[/bold]")

            # Group by source note for efficient file operations
            by_source_path = {}
            for s in all_suggestions:
                src_path = s["from_path"]
                if src_path not in by_source_path:
                    by_source_path[src_path] = []
                by_source_path[src_path].append(s)

            applied = 0
            errors = 0

            for src_path, suggestions in by_source_path.items():
                try:
                    note_path = Path(src_path)
                    if not note_path.exists():
                        console.print(f"[red]Not found: {src_path}[/red]")
                        errors += 1
                        continue

                    content = note_path.read_text()

                    # Build links section
                    links_to_add = []
                    for s in suggestions:
                        target_stem = Path(s["to_path"]).stem if s["to_path"] else s["to_title"]
                        rel = s["relationship"]
                        desc = s["relationship_desc"]
                        target_display = s["to_title"][:50]
                        # Format: - RELATIONSHIP [[note-name|Display Title]] - description
                        link_line = f"- {rel}: [[{target_stem}|{target_display}]]"
                        links_to_add.append(link_line)

                    # Check if ## Related section exists
                    if "## Related" in content:
                        # Append to existing section
                        # Find the section and add after it
                        lines = content.split('\n')
                        new_lines = []
                        in_related = False
                        added = False

                        for line in lines:
                            new_lines.append(line)
                            if line.strip() == "## Related":
                                in_related = True
                            elif in_related and not added:
                                # Add after section header (possibly after blank line)
                                if line.strip() == "":
                                    # Add links after blank line
                                    pass  # Will add on next non-blank or end
                                elif line.startswith("## ") or line.startswith("# "):
                                    # New section - insert before it
                                    new_lines = new_lines[:-1]  # Remove last line
                                    new_lines.append("")
                                    for link in links_to_add:
                                        new_lines.append(link)
                                    new_lines.append("")
                                    new_lines.append(line)  # Re-add section header
                                    added = True
                                    in_related = False

                        if in_related and not added:
                            # Related section is at end of file
                            new_lines.append("")
                            for link in links_to_add:
                                new_lines.append(link)
                            added = True

                        content = '\n'.join(new_lines)
                    else:
                        # Add new ## Related section before ## Hub if exists, else at end
                        related_section = "\n## Related\n\n" + "\n".join(links_to_add) + "\n"

                        if "## Hub" in content:
                            content = content.replace("## Hub", related_section + "\n## Hub")
                        elif "## See Also" in content:
                            content = content.replace("## See Also", related_section + "\n## See Also")
                        else:
                            content = content.rstrip() + "\n" + related_section

                    # Write back
                    note_path.write_text(content)
                    applied += len(suggestions)
                    console.print(f"  ✓ {note_path.stem}: +{len(suggestions)} links")

                except Exception as e:
                    console.print(f"[red]Error updating {src_path}: {e}[/red]")
                    errors += 1

            # Bidirectional linking - create backlinks in target notes
            backlinks_applied = 0
            if args.bidirectional:
                console.print("\n[bold]Creating backlinks...[/bold]")

                # Group by target for efficient backlink creation
                by_target = {}
                for s in all_suggestions:
                    target_path = s["to_path"]
                    if target_path:
                        if target_path not in by_target:
                            by_target[target_path] = []
                        by_target[target_path].append(s)

                for target_path, backlinks in by_target.items():
                    try:
                        target_note = Path(target_path)
                        if not target_note.exists():
                            continue

                        target_content = target_note.read_text()

                        # Build backlinks with inverse relationships
                        backlink_lines = []
                        for bl in backlinks:
                            source_stem = Path(bl["from_path"]).stem
                            source_title = bl["from_title"][:50]
                            fwd_rel = bl["relationship"]
                            inv_rel = INVERSE_RELATIONSHIPS.get(fwd_rel, fwd_rel)
                            backlink_lines.append(f"- {inv_rel}: [[{source_stem}|{source_title}]]")

                        # Add backlinks using same logic as forward links
                        if "## Related" in target_content:
                            lines = target_content.split('\n')
                            new_lines = []
                            in_related = False
                            added = False

                            for line in lines:
                                new_lines.append(line)
                                if line.strip() == "## Related":
                                    in_related = True
                                elif in_related and not added:
                                    if line.startswith("## ") or line.startswith("# "):
                                        new_lines = new_lines[:-1]
                                        new_lines.append("")
                                        for bl_line in backlink_lines:
                                            new_lines.append(bl_line)
                                        new_lines.append("")
                                        new_lines.append(line)
                                        added = True
                                        in_related = False

                            if in_related and not added:
                                new_lines.append("")
                                for bl_line in backlink_lines:
                                    new_lines.append(bl_line)
                                added = True

                            target_content = '\n'.join(new_lines)
                        else:
                            related_section = "\n## Related\n\n" + "\n".join(backlink_lines) + "\n"
                            if "## Hub" in target_content:
                                target_content = target_content.replace("## Hub", related_section + "\n## Hub")
                            else:
                                target_content = target_content.rstrip() + "\n" + related_section

                        target_note.write_text(target_content)
                        backlinks_applied += len(backlinks)
                        console.print(f"  ← {target_note.stem}: +{len(backlinks)} backlinks")

                    except Exception as e:
                        console.print(f"[red]Error creating backlinks in {target_path}: {e}[/red]")
                        errors += 1

            console.print()
            console.print("=" * 70)
            console.print(f"[bold]Applied {applied} links to {len(by_source_path)} notes[/bold]")
            if args.bidirectional:
                console.print(f"[bold]Created {backlinks_applied} backlinks[/bold]")
            if errors:
                console.print(f"[yellow]Errors: {errors}[/yellow]")
            console.print("=" * 70)
        else:
            console.print()
            console.print("[dim]Zettelkasten principle: Links should connect ideas meaningfully,[/dim]")
            console.print("[dim]not just because topics are similar. Review suggestions carefully.[/dim]")
            console.print()
            console.print("[cyan]Run with --apply to add these links to your notes[/cyan]")

        return 0

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return 1


def hub_assign_main():
    """Entry point for bulk hub assignment.

    Assigns unassigned permanent notes to their best-matching hubs based on
    semantic similarity. Uses embeddings to find the most relevant hub for
    each note.

    Usage: zk-hub-assign [--threshold N] [--dry-run] [--yes] [--update-vectors]

    Arguments:
        --threshold: Minimum similarity to assign (default: 50)
        --dry-run: Show what would be assigned without making changes
        --yes: Skip confirmation prompt
        --update-vectors: Also update S3 Vectors metadata with hub assignments

    Returns:
        0 on success
        1 on error
    """
    import argparse
    import numpy as np
    from collections import defaultdict
    from pathlib import Path

    from .s3vectors import S3VectorsStore, VectorMetadata
    from .embeddings import BedrockEmbeddings

    parser = argparse.ArgumentParser(description="Bulk assign notes to hubs")
    parser.add_argument("--threshold", "-t", type=int, default=50,
                        help="Minimum similarity to assign (0-100, default: 50)")
    parser.add_argument("--dry-run", "-n", action="store_true",
                        help="Show what would be changed without modifying files")
    parser.add_argument("--yes", "-y", action="store_true",
                        help="Skip confirmation prompt")
    parser.add_argument("--update-vectors", "-u", action="store_true",
                        help="Also update S3 Vectors metadata")

    args = parser.parse_args()
    threshold = args.threshold / 100.0

    try:
        vectors = S3VectorsStore(BUCKET, INDEX)
        embeddings = BedrockEmbeddings()

        console.print("[bold]Hub Assignment Tool[/bold]")
        console.print("=" * 70)
        console.print()

        # 1. Load existing hubs and their embeddings
        console.print("[dim]Loading hubs...[/dim]")
        hub_dir = VAULT / "knowledge-base" / "hubs"
        hub_data = {}

        if hub_dir.exists():
            for hub_file in hub_dir.glob("*.md"):
                hub_name = hub_file.stem
                content = hub_file.read_text()

                # Extract hub title from markdown
                title_match = __import__('re').search(r'^#\s+(.+)$', content, __import__('re').MULTILINE)
                hub_title = title_match.group(1) if title_match else hub_name

                hub_emb = embeddings.embed(f"{hub_name}\n\n{content[:1000]}")
                hub_data[hub_name] = {
                    "embedding": hub_emb,
                    "path": str(hub_file),
                    "title": hub_title
                }

        if not hub_data:
            console.print("[red]No hubs found![/red]")
            console.print("Create hubs first using /zadd or manually in knowledge-base/hubs/")
            return 1

        console.print(f"  Found {len(hub_data)} hubs")

        # 2. Fetch all vectors and find unassigned notes
        console.print("[dim]Fetching vectors...[/dim]")
        all_vectors = vectors.query_all(include_embeddings=True)
        console.print(f"  Total vectors: {len(all_vectors)}")

        # 3. Find notes without hub assignments
        console.print("[dim]Analyzing note assignments...[/dim]")
        unassigned_notes = []
        assigned_count = 0

        for v in all_vectors:
            key = v.get("key", "")
            meta = v.get("metadata", {})
            path = meta.get("obsidian_path", "")

            # Only process permanent notes, skip hubs
            if not key.startswith("perm-") or "/hubs/" in path:
                continue

            vec_data = v.get("embedding") or v.get("data", {}).get("float32")
            if not vec_data:
                continue

            # Check if note already has hub assignment
            has_hub = False
            if path and Path(path).exists():
                try:
                    content = Path(path).read_text()
                    in_hub_section = False
                    for line in content.split("\n"):
                        if line.strip() == "## Hub":
                            in_hub_section = True
                            continue
                        if in_hub_section and line.startswith("##"):
                            break
                        if in_hub_section and "[[" in line and "]]" in line:
                            has_hub = True
                            break
                except:
                    pass

            if has_hub:
                assigned_count += 1
            else:
                # Calculate best hub match
                best_hub = None
                best_sim = 0
                for hub_name, hub_info in hub_data.items():
                    hub_emb = np.array(hub_info["embedding"])
                    vec_arr = np.array(vec_data)
                    sim = np.dot(vec_arr, hub_emb) / (np.linalg.norm(vec_arr) * np.linalg.norm(hub_emb))
                    if sim > best_sim:
                        best_sim = sim
                        best_hub = hub_name

                if best_hub and best_sim >= threshold:
                    unassigned_notes.append({
                        "key": key,
                        "title": meta.get("title", key),
                        "path": path,
                        "best_hub": best_hub,
                        "hub_title": hub_data[best_hub]["title"],
                        "similarity": best_sim * 100,
                        "embedding": vec_data
                    })

        console.print(f"  Already assigned: {assigned_count}")
        console.print(f"  Unassigned (above {args.threshold}% threshold): {len(unassigned_notes)}")
        console.print()

        if not unassigned_notes:
            console.print("[green]All notes are already assigned to hubs![/green]")
            return 0

        # 4. Group by hub for display
        by_hub = defaultdict(list)
        for note in unassigned_notes:
            by_hub[note["best_hub"]].append(note)

        # 5. Display preview
        console.print("=" * 70)
        console.print("ASSIGNMENT PREVIEW")
        console.print("=" * 70)
        console.print()

        for hub_name in sorted(by_hub.keys()):
            notes = by_hub[hub_name]
            hub_title = hub_data[hub_name]["title"]
            console.print(f"[bold cyan]{hub_title}[/bold cyan] ({len(notes)} notes)")
            console.print(f"  [dim]{hub_name}[/dim]")

            # Sort by similarity
            for note in sorted(notes, key=lambda x: -x["similarity"])[:10]:
                console.print(f"    [{note['similarity']:.0f}%] {note['title'][:50]}")

            if len(notes) > 10:
                console.print(f"    ... and {len(notes) - 10} more")
            console.print()

        # Summary table
        table = Table(title="Assignment Summary")
        table.add_column("Hub", style="cyan")
        table.add_column("Notes", justify="right")
        table.add_column("Avg Similarity", justify="right")

        for hub_name in sorted(by_hub.keys()):
            notes = by_hub[hub_name]
            avg_sim = sum(n["similarity"] for n in notes) / len(notes)
            table.add_row(hub_name, str(len(notes)), f"{avg_sim:.1f}%")

        console.print(table)
        console.print()
        console.print(f"[bold]Total:[/bold] {len(unassigned_notes)} notes to assign")
        console.print()

        # 6. Dry run check
        if args.dry_run:
            console.print("[yellow]Dry run - no changes made[/yellow]")
            return 0

        # 7. Confirmation
        if not args.yes:
            console.print("Proceed with assignment? [y/N] ", end="")
            response = input().strip().lower()
            if response != "y":
                console.print("[yellow]Cancelled[/yellow]")
                return 0

        # 8. Apply assignments
        console.print()
        console.print("[dim]Applying assignments...[/dim]")

        success_count = 0
        error_count = 0
        hub_counts = defaultdict(int)

        for note in unassigned_notes:
            path = Path(note["path"])
            hub_name = note["best_hub"]

            if not path.exists():
                console.print(f"[red]Not found: {path}[/red]")
                error_count += 1
                continue

            try:
                content = path.read_text()

                # Check if ## Hub section exists
                if "## Hub" in content:
                    # Add link after ## Hub line
                    lines = content.split("\n")
                    new_lines = []
                    found_hub_section = False

                    for i, line in enumerate(lines):
                        new_lines.append(line)
                        if line.strip() == "## Hub" and not found_hub_section:
                            found_hub_section = True
                            # Add blank line and hub link
                            new_lines.append("")
                            new_lines.append(f"[[hubs/{hub_name}|{hub_data[hub_name]['title']}]]")

                    content = "\n".join(new_lines)
                else:
                    # Append ## Hub section at end
                    content = content.rstrip() + "\n\n## Hub\n\n"
                    content += f"[[hubs/{hub_name}|{hub_data[hub_name]['title']}]]\n"

                # Write updated content
                path.write_text(content)
                hub_counts[hub_name] += 1
                success_count += 1

            except Exception as e:
                console.print(f"[red]Error updating {path.name}: {e}[/red]")
                error_count += 1

        console.print()

        # 9. Optionally update S3 Vectors metadata
        if args.update_vectors and success_count > 0:
            console.print("[dim]Updating S3 Vectors metadata...[/dim]")
            vector_updates = 0

            for note in unassigned_notes:
                if not Path(note["path"]).exists():
                    continue

                try:
                    # Get current vector metadata
                    vec = vectors.get_vector(note["key"])
                    if not vec:
                        continue

                    current_meta = vec.get("metadata", {})
                    current_hub_ids = current_meta.get("hub_ids", "")

                    # Add new hub to hub_ids
                    hub_ids_list = [h for h in current_hub_ids.split(",") if h]
                    hub_id = f"hub-{note['best_hub']}" if not note['best_hub'].startswith("hub-") else note['best_hub']

                    if hub_id not in hub_ids_list:
                        hub_ids_list.append(hub_id)

                    # Update metadata
                    updated_meta = VectorMetadata(
                        note_type=current_meta.get("note_type", "permanent"),
                        knowledge_type=current_meta.get("knowledge_type", "fact"),
                        status=current_meta.get("status", "approved"),
                        title=current_meta.get("title", ""),
                        tags=current_meta.get("tags", "").split(",") if current_meta.get("tags") else [],
                        obsidian_path=current_meta.get("obsidian_path", ""),
                        content_preview=current_meta.get("content_preview", ""),
                        scope=current_meta.get("scope", "global"),
                        project=current_meta.get("project", ""),
                        hub_ids=hub_ids_list,
                        link_count=int(current_meta.get("link_count", 0)),
                        linked_ids=current_meta.get("linked_ids", "").split(",") if current_meta.get("linked_ids") else [],
                        created=current_meta.get("created"),
                        promoted=current_meta.get("promoted"),
                    )

                    if vectors.update_metadata(note["key"], updated_meta):
                        vector_updates += 1

                except Exception as e:
                    pass  # Silent fail for vector updates

            console.print(f"  Updated {vector_updates} vectors")

        # 10. Final report
        console.print()
        console.print("=" * 70)
        console.print("ASSIGNMENT COMPLETE")
        console.print("=" * 70)
        console.print()

        result_table = Table(title="Results by Hub")
        result_table.add_column("Hub", style="cyan")
        result_table.add_column("Notes Assigned", justify="right")

        for hub_name in sorted(hub_counts.keys()):
            result_table.add_row(hub_name, str(hub_counts[hub_name]))

        console.print(result_table)
        console.print()
        console.print(f"[green]Successfully assigned: {success_count}[/green]")
        if error_count:
            console.print(f"[red]Errors: {error_count}[/red]")

        console.print()
        console.print("[dim]Tip: Run zk-hub-check to validate assignments[/dim]")

        return 0 if error_count == 0 else 1

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return 1


def link_loop_main():
    """Entry point for iterative link building loop.

    Runs zk-suggest-links repeatedly until no new links are suggested,
    building a densely connected knowledge graph through convergence.

    Each iteration:
    1. Analyzes all notes for link suggestions
    2. Applies suggested links above threshold
    3. Repeats until no new suggestions (fixpoint)

    Usage: zk-link-loop [--threshold N] [--top N] [--max-iterations N]

    Arguments:
        --threshold: Minimum similarity for links (default: 70)
        --top: Max links per note per iteration (default: 3)
        --max-iterations: Safety limit (default: 10)

    Returns:
        0 on success
        1 on error
    """
    import argparse
    import time

    parser = argparse.ArgumentParser(description="Iterative link building loop")
    parser.add_argument("--threshold", "-t", type=int, default=70,
                        help="Minimum similarity for links (0-100, default: 70)")
    parser.add_argument("--top", "-n", type=int, default=3,
                        help="Max links per note per iteration (default: 3)")
    parser.add_argument("--max-iterations", "-m", type=int, default=10,
                        help="Maximum iterations before stopping (default: 10)")

    args = parser.parse_args()

    console.print("=" * 70)
    console.print("[bold]ZETTELKASTEN LINK LOOP[/bold]")
    console.print("=" * 70)
    console.print(f"Threshold: {args.threshold}%  |  Top: {args.top} links/note  |  Max iterations: {args.max_iterations}")
    console.print()

    iteration = 1
    total_added = 0

    while iteration <= args.max_iterations:
        console.print(f"[bold cyan]━━━ ITERATION {iteration} ━━━[/bold cyan]")

        # Import and run suggest_links logic inline
        from .s3vectors import S3VectorsStore
        from .embeddings import BedrockEmbeddings
        import re

        threshold = args.threshold / 100.0

        RELATIONSHIP_TYPES = {
            "SOLVES": "addresses problem in",
            "ENABLES": "is prerequisite for",
            "ELABORATES": "expands on",
            "CONTRADICTS": "challenges or limits",
            "SUPPORTS": "provides evidence for",
            "APPLIES": "applies principle from",
            "ABSTRACTS": "generalizes from",
            "SEQUENCE": "logically follows",
        }

        try:
            vectors = S3VectorsStore(BUCKET, INDEX)
            embeddings = BedrockEmbeddings()

            permanent_dir = VAULT / "knowledge-base" / "permanent"
            if not permanent_dir.exists():
                console.print(f"[red]Permanent notes directory not found: {permanent_dir}[/red]")
                return 1

            notes_to_analyze = list(permanent_dir.glob("*.md"))
            console.print(f"Analyzing {len(notes_to_analyze)} notes...")

            all_suggestions = []

            for note_path in notes_to_analyze:
                if not note_path.exists():
                    continue

                content = note_path.read_text()
                title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                title = title_match.group(1) if title_match else note_path.stem
                existing_links = set(re.findall(r'\[\[([^\]|]+)', content))

                note_text = f"{title}\n\n{content[:1500]}"
                note_emb = embeddings.embed(note_text)
                results = vectors.query(note_emb, top_k=args.top + len(existing_links) + 1)

                suggestions = []
                for r in results:
                    key = r.get("key", "")
                    meta = r.get("metadata", {})
                    candidate_title = meta.get("title", key)
                    candidate_path = meta.get("obsidian_path", "")

                    if candidate_path == str(note_path):
                        continue

                    candidate_stem = Path(candidate_path).stem if candidate_path else key
                    if candidate_stem in existing_links or candidate_title in existing_links:
                        continue

                    dist = r.get("distance", 2)
                    similarity = 1 - dist / 2
                    if similarity < threshold:
                        continue

                    source_type = "pattern"
                    if "knowledge_type:" in content:
                        kt_match = re.search(r'knowledge_type:\s*(\w+)', content)
                        if kt_match:
                            source_type = kt_match.group(1)

                    target_type = meta.get("knowledge_type", "fact")

                    relationship = "ELABORATES"
                    if source_type == "pattern" and target_type == "fact":
                        relationship = "APPLIES"
                    elif source_type == "fact" and target_type == "pattern":
                        relationship = "SUPPORTS"
                    elif "problem" in title.lower() or "anti-pattern" in title.lower():
                        relationship = "SOLVES"
                    elif "prerequisite" in content.lower() or "before" in content.lower():
                        relationship = "ENABLES"
                    elif similarity > 0.85:
                        relationship = "ELABORATES"

                    suggestions.append({
                        "from_title": title,
                        "from_path": str(note_path),
                        "to_title": candidate_title,
                        "to_path": candidate_path,
                        "similarity": similarity * 100,
                        "relationship": relationship,
                    })

                    if len(suggestions) >= args.top:
                        break

                all_suggestions.extend(suggestions)

            console.print(f"Total suggestions: {len(all_suggestions)}")

            if not all_suggestions:
                console.print("[green]✓ Convergence reached - no new links to add![/green]")
                break

            # Apply links
            by_source_path = {}
            for s in all_suggestions:
                src_path = s["from_path"]
                if src_path not in by_source_path:
                    by_source_path[src_path] = []
                by_source_path[src_path].append(s)

            applied = 0
            for src_path, suggestions in by_source_path.items():
                try:
                    note_path = Path(src_path)
                    if not note_path.exists():
                        continue

                    content = note_path.read_text()

                    links_to_add = []
                    for s in suggestions:
                        target_stem = Path(s["to_path"]).stem if s["to_path"] else s["to_title"]
                        rel = s["relationship"]
                        target_display = s["to_title"][:50]
                        link_line = f"- {rel}: [[{target_stem}|{target_display}]]"
                        links_to_add.append(link_line)

                    if "## Related" in content:
                        lines = content.split('\n')
                        new_lines = []
                        in_related = False
                        added = False

                        for line in lines:
                            new_lines.append(line)
                            if line.strip() == "## Related":
                                in_related = True
                            elif in_related and not added:
                                if line.startswith("## ") or line.startswith("# "):
                                    new_lines = new_lines[:-1]
                                    new_lines.append("")
                                    for link in links_to_add:
                                        new_lines.append(link)
                                    new_lines.append("")
                                    new_lines.append(line)
                                    added = True
                                    in_related = False

                        if in_related and not added:
                            new_lines.append("")
                            for link in links_to_add:
                                new_lines.append(link)

                        content = '\n'.join(new_lines)
                    else:
                        related_section = "\n## Related\n\n" + "\n".join(links_to_add) + "\n"
                        if "## Hub" in content:
                            content = content.replace("## Hub", related_section + "\n## Hub")
                        elif "## See Also" in content:
                            content = content.replace("## See Also", related_section + "\n## See Also")
                        else:
                            content = content.rstrip() + "\n" + related_section

                    note_path.write_text(content)
                    applied += len(suggestions)

                except Exception:
                    pass

            console.print(f"[green]Applied {applied} links to {len(by_source_path)} notes[/green]")
            total_added += applied
            iteration += 1

            # Brief pause between iterations
            time.sleep(1)

        except Exception as e:
            console.print(f"[red]Error in iteration {iteration}: {e}[/red]")
            import traceback
            traceback.print_exc()
            return 1

    console.print()
    console.print("=" * 70)
    console.print("[bold]LOOP COMPLETE[/bold]")
    console.print("=" * 70)
    console.print(f"Total iterations: {iteration - 1}")
    console.print(f"Total links added: {total_added}")
    console.print()
    console.print("[dim]Tip: Run zk-sync to update S3 Vectors with changes[/dim]")

    return 0


def link_ranked_main():
    """Entry point for similarity-ranked link building.

    Clusters notes semantically, then creates links starting from the
    highest similarity pairs. More efficient than iterative approaches.

    Process:
    1. Fetch all vectors from S3
    2. Compute pairwise similarities within similarity threshold
    3. Sort all pairs by similarity (highest first)
    4. Add links in order, respecting max links per note
    5. Skip already-linked pairs

    Usage: zk-link-ranked [--threshold N] [--max-links N] [--dry-run]

    Arguments:
        --threshold: Minimum similarity to create link (default: 70)
        --max-links: Max links per note (default: 5)
        --dry-run: Preview without applying

    Returns:
        0 on success
        1 on error
    """
    import argparse
    import re
    import numpy as np
    from collections import defaultdict

    from .s3vectors import S3VectorsStore
    from .embeddings import BedrockEmbeddings

    parser = argparse.ArgumentParser(description="Similarity-ranked link building")
    parser.add_argument("--threshold", "-t", type=int, default=70,
                        help="Minimum similarity (0-100, default: 70)")
    parser.add_argument("--max-links", "-m", type=int, default=5,
                        help="Max links per note (default: 5)")
    parser.add_argument("--dry-run", "-n", action="store_true",
                        help="Preview without applying")

    args = parser.parse_args()
    threshold = args.threshold / 100.0

    console.print("=" * 70)
    console.print("[bold]SIMILARITY-RANKED LINK BUILDER[/bold]")
    console.print("=" * 70)
    console.print(f"Threshold: {args.threshold}%  |  Max links/note: {args.max_links}")
    console.print()

    RELATIONSHIP_TYPES = {
        "SOLVES": "addresses problem in",
        "ENABLES": "is prerequisite for",
        "ELABORATES": "expands on",
        "SUPPORTS": "provides evidence for",
        "APPLIES": "applies principle from",
    }

    try:
        vectors = S3VectorsStore(BUCKET, INDEX)

        # Step 1: Fetch all vectors
        console.print("[bold]Step 1:[/bold] Fetching all vectors...")
        all_vectors = vectors.query_all(include_embeddings=True)
        console.print(f"  Found {len(all_vectors)} vectors")

        # Build lookup maps
        key_to_meta = {}
        key_to_emb = {}
        key_to_path = {}

        for v in all_vectors:
            key = v.get("key", "")
            meta = v.get("metadata", {})
            emb = v.get("embedding")

            if not emb or not key:
                continue

            # Only permanent notes
            path = meta.get("obsidian_path", "")
            if "/permanent/" not in path:
                continue

            key_to_meta[key] = meta
            key_to_emb[key] = np.array(emb)
            key_to_path[key] = path

        console.print(f"  Permanent notes with embeddings: {len(key_to_emb)}")

        # Step 2: Read existing links from files
        console.print("[bold]Step 2:[/bold] Reading existing links...")
        existing_links = defaultdict(set)  # path -> set of linked stems

        for key, path in key_to_path.items():
            try:
                note_path = Path(path)
                if note_path.exists():
                    content = note_path.read_text()
                    links = re.findall(r'\[\[([^\]|]+)', content)
                    existing_links[path] = set(links)
            except Exception:
                pass

        total_existing = sum(len(v) for v in existing_links.values())
        console.print(f"  Existing links: {total_existing}")

        # Step 3: Compute pairwise similarities
        console.print("[bold]Step 3:[/bold] Computing pairwise similarities...")
        keys = list(key_to_emb.keys())
        n = len(keys)

        # Compute all similarities above threshold
        pairs = []
        for i in range(n):
            emb_i = key_to_emb[keys[i]]
            norm_i = np.linalg.norm(emb_i)
            if norm_i == 0:
                continue

            for j in range(i + 1, n):
                emb_j = key_to_emb[keys[j]]
                norm_j = np.linalg.norm(emb_j)
                if norm_j == 0:
                    continue

                # Cosine similarity
                similarity = np.dot(emb_i, emb_j) / (norm_i * norm_j)

                if similarity >= threshold:
                    pairs.append({
                        "key_a": keys[i],
                        "key_b": keys[j],
                        "similarity": similarity,
                        "path_a": key_to_path[keys[i]],
                        "path_b": key_to_path[keys[j]],
                        "title_a": key_to_meta[keys[i]].get("title", keys[i]),
                        "title_b": key_to_meta[keys[j]].get("title", keys[j]),
                    })

        console.print(f"  Pairs above {args.threshold}%: {len(pairs)}")

        # Step 4: Sort by similarity (highest first)
        console.print("[bold]Step 4:[/bold] Sorting by similarity...")
        pairs.sort(key=lambda x: x["similarity"], reverse=True)

        # Step 5: Create links respecting max per note
        console.print("[bold]Step 5:[/bold] Creating links (highest similarity first)...")

        link_count = defaultdict(int)  # path -> number of new links added
        links_to_add = defaultdict(list)  # path -> [(target_stem, target_title, similarity)]

        for pair in pairs:
            path_a = pair["path_a"]
            path_b = pair["path_b"]
            stem_a = Path(path_a).stem
            stem_b = Path(path_b).stem
            sim = pair["similarity"]

            # Check if already linked
            if stem_b in existing_links[path_a] or stem_a in existing_links[path_b]:
                continue

            # Check max links
            can_add_a = link_count[path_a] < args.max_links
            can_add_b = link_count[path_b] < args.max_links

            if can_add_a and stem_b not in [x[0] for x in links_to_add[path_a]]:
                links_to_add[path_a].append((stem_b, pair["title_b"], sim))
                link_count[path_a] += 1

            if can_add_b and stem_a not in [x[0] for x in links_to_add[path_b]]:
                links_to_add[path_b].append((stem_a, pair["title_a"], sim))
                link_count[path_b] += 1

        total_new = sum(len(v) for v in links_to_add.values())
        console.print(f"  New links to add: {total_new}")

        # Show top pairs
        console.print()
        console.print("[bold]Top 10 highest similarity pairs:[/bold]")
        for pair in pairs[:10]:
            sim = pair["similarity"] * 100
            console.print(f"  [{sim:.1f}%] {pair['title_a'][:30]} ↔ {pair['title_b'][:30]}")

        if args.dry_run:
            console.print()
            console.print("[yellow]Dry run - no changes made[/yellow]")
            return 0

        # Step 6: Apply links
        console.print()
        console.print("[bold]Step 6:[/bold] Applying links to files...")

        applied = 0
        errors = 0

        for path, links in links_to_add.items():
            if not links:
                continue

            try:
                note_path = Path(path)
                if not note_path.exists():
                    continue

                content = note_path.read_text()

                # Build link lines (sorted by similarity within this note)
                links.sort(key=lambda x: x[2], reverse=True)
                link_lines = []
                for stem, title, sim in links:
                    link_lines.append(f"- ELABORATES: [[{stem}|{title[:50]}]]")

                # Add to ## Related section
                if "## Related" in content:
                    # Find the section and append
                    lines = content.split('\n')
                    new_lines = []
                    in_related = False
                    added = False

                    for i, line in enumerate(lines):
                        new_lines.append(line)
                        if line.strip() == "## Related":
                            in_related = True
                        elif in_related and not added:
                            if line.startswith("## ") or line.startswith("# "):
                                # Insert before next section
                                new_lines = new_lines[:-1]
                                for ll in link_lines:
                                    new_lines.append(ll)
                                new_lines.append("")
                                new_lines.append(line)
                                added = True
                                in_related = False
                            elif line.strip() == "" and i + 1 < len(lines) and (lines[i+1].startswith("## ") or lines[i+1].startswith("# ")):
                                # Empty line before next section
                                for ll in link_lines:
                                    new_lines.append(ll)
                                added = True

                    if in_related and not added:
                        # Related is at end of file
                        new_lines.append("")
                        for ll in link_lines:
                            new_lines.append(ll)

                    content = '\n'.join(new_lines)
                else:
                    # Create ## Related section
                    related_section = "\n## Related\n\n" + "\n".join(link_lines) + "\n"
                    if "## Hub" in content:
                        content = content.replace("## Hub", related_section + "\n## Hub")
                    else:
                        content = content.rstrip() + "\n" + related_section

                note_path.write_text(content)
                applied += len(links)

            except Exception as e:
                errors += 1

        console.print()
        console.print("=" * 70)
        console.print("[bold]COMPLETE[/bold]")
        console.print("=" * 70)
        console.print(f"Links applied: {applied}")
        console.print(f"Notes modified: {len([p for p, l in links_to_add.items() if l])}")
        if errors:
            console.print(f"[yellow]Errors: {errors}[/yellow]")
        console.print()
        console.print("[dim]Tip: Run zk-sync to update S3 Vectors[/dim]")

        return 0

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return 1


def merge_duplicates_main():
    """Entry point for merging duplicate notes.

    Finds duplicate pairs, merges unique content into primary note,
    and archives the duplicate.

    Primary selection:
    1. Human-named notes preferred over flee-*/perm-* IDs
    2. Notes with more links preferred

    Usage: zk-merge-dupes [--threshold N] [--dry-run]
    """
    import argparse
    import re
    import shutil
    import numpy as np

    from .s3vectors import S3VectorsStore

    parser = argparse.ArgumentParser(description="Merge duplicate notes")
    parser.add_argument("--threshold", "-t", type=int, default=90,
                        help="Minimum similarity (0-100, default: 90)")
    parser.add_argument("--dry-run", "-n", action="store_true",
                        help="Preview without applying")

    args = parser.parse_args()
    threshold = args.threshold / 100.0

    console.print("=" * 70)
    console.print("[bold]DUPLICATE MERGER[/bold]")
    console.print("=" * 70)
    console.print(f"Threshold: {args.threshold}%")
    console.print()

    try:
        vectors = S3VectorsStore(BUCKET, INDEX)

        # Fetch all vectors with embeddings
        console.print("[bold]Step 1:[/bold] Fetching vectors...")
        all_vectors = vectors.query_all(include_embeddings=True)

        key_to_meta = {}
        key_to_emb = {}
        key_to_path = {}

        for v in all_vectors:
            key = v.get("key", "")
            meta = v.get("metadata", {})
            emb = v.get("embedding")
            if not emb or not key:
                continue
            path = meta.get("obsidian_path", "")
            if "/permanent/" not in path:
                continue
            key_to_meta[key] = meta
            key_to_emb[key] = np.array(emb)
            key_to_path[key] = path

        console.print(f"  Found {len(key_to_emb)} permanent notes")

        # Find duplicate pairs
        console.print("[bold]Step 2:[/bold] Finding duplicates...")
        keys = list(key_to_emb.keys())
        n = len(keys)
        duplicates = []

        for i in range(n):
            emb_i = key_to_emb[keys[i]]
            norm_i = np.linalg.norm(emb_i)
            if norm_i == 0:
                continue
            for j in range(i + 1, n):
                emb_j = key_to_emb[keys[j]]
                norm_j = np.linalg.norm(emb_j)
                if norm_j == 0:
                    continue
                similarity = np.dot(emb_i, emb_j) / (norm_i * norm_j)
                if similarity >= threshold:
                    duplicates.append({
                        "key_a": keys[i], "key_b": keys[j],
                        "similarity": similarity,
                        "path_a": key_to_path[keys[i]],
                        "path_b": key_to_path[keys[j]],
                        "title_a": key_to_meta[keys[i]].get("title", keys[i]),
                        "title_b": key_to_meta[keys[j]].get("title", keys[j]),
                    })

        console.print(f"  Found {len(duplicates)} duplicate pairs")

        if not duplicates:
            console.print("[green]No duplicates found![/green]")
            return 0

        # Determine primary for each pair
        console.print("[bold]Step 3:[/bold] Selecting primaries...")

        def is_auto_id(filename):
            return filename.startswith("flee-") or filename.startswith("perm-")

        def get_priority(path):
            filename = Path(path).stem
            score = 0
            if not is_auto_id(filename):
                score += 100
            try:
                content = Path(path).read_text()
                score += len(re.findall(r'\[\[', content))
            except:
                pass
            return score

        processed = set()
        merge_plan = []

        for dup in sorted(duplicates, key=lambda x: x["similarity"], reverse=True):
            path_a, path_b = dup["path_a"], dup["path_b"]
            if path_a in processed or path_b in processed:
                continue

            if get_priority(path_a) >= get_priority(path_b):
                primary, secondary = path_a, path_b
            else:
                primary, secondary = path_b, path_a

            merge_plan.append({
                "primary": primary, "secondary": secondary,
                "similarity": dup["similarity"],
            })
            processed.add(secondary)

        console.print(f"  Merge plan: {len(merge_plan)} pairs")

        # Preview
        console.print()
        console.print("[bold]Merge Plan (secondary → primary):[/bold]")
        for m in merge_plan[:15]:
            sim = m["similarity"] * 100
            p, s = Path(m["primary"]).stem[:25], Path(m["secondary"]).stem[:25]
            console.print(f"  [{sim:.0f}%] {s} → {p}")
        if len(merge_plan) > 15:
            console.print(f"  ... and {len(merge_plan) - 15} more")

        if args.dry_run:
            console.print("\n[yellow]Dry run - no changes made[/yellow]")
            return 0

        # Execute merges
        console.print("\n[bold]Step 4:[/bold] Executing merges...")

        archive_dir = VAULT / "knowledge-base" / "permanent" / ".archive" / "merged-duplicates"
        archive_dir.mkdir(parents=True, exist_ok=True)

        merged, errors = 0, 0

        for m in merge_plan:
            try:
                primary_path = Path(m["primary"])
                secondary_path = Path(m["secondary"])
                if not primary_path.exists() or not secondary_path.exists():
                    continue

                primary_content = primary_path.read_text()

                # Add merge reference
                merge_note = f"\n\n## Merged From\n\n- [[{secondary_path.stem}]] (archived, {m['similarity']*100:.0f}% similar)\n"
                if "## Merged From" not in primary_content:
                    if "## Hub" in primary_content:
                        primary_content = primary_content.replace("## Hub", merge_note + "## Hub")
                    else:
                        primary_content = primary_content.rstrip() + merge_note
                    primary_path.write_text(primary_content)

                # Archive secondary
                shutil.move(str(secondary_path), str(archive_dir / secondary_path.name))
                merged += 1
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                errors += 1

        console.print()
        console.print("=" * 70)
        console.print(f"[bold]COMPLETE[/bold] - Merged: {merged}, Errors: {errors}")
        console.print(f"[dim]Archived in: {archive_dir}[/dim]")
        console.print("=" * 70)

        return 0

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return 1


def prune_links_main():
    """Entry point for pruning low-similarity links.

    Removes links from ## Related sections where the linked notes
    have similarity below the threshold.

    Usage: zk-prune-links [--threshold N] [--dry-run]
    """
    import argparse
    import re
    import numpy as np

    from .s3vectors import S3VectorsStore

    parser = argparse.ArgumentParser(description="Prune low-similarity links")
    parser.add_argument("--threshold", "-t", type=int, default=80,
                        help="Minimum similarity to keep link (0-100, default: 80)")
    parser.add_argument("--dry-run", "-n", action="store_true",
                        help="Preview without applying")

    args = parser.parse_args()
    threshold = args.threshold / 100.0

    console.print("=" * 70)
    console.print("[bold]LINK PRUNER[/bold]")
    console.print("=" * 70)
    console.print(f"Threshold: {args.threshold}% (links below this will be removed)")
    console.print()

    try:
        vectors = S3VectorsStore(BUCKET, INDEX)

        # Fetch all vectors with embeddings
        console.print("[bold]Step 1:[/bold] Fetching vectors...")
        all_vectors = vectors.query_all(include_embeddings=True)

        # Build lookup by stem
        stem_to_emb = {}
        for v in all_vectors:
            path = v.get("metadata", {}).get("obsidian_path", "")
            emb = v.get("embedding")
            if path and emb:
                stem = Path(path).stem
                stem_to_emb[stem] = np.array(emb)

        console.print(f"  Mapped {len(stem_to_emb)} notes to embeddings")

        # Process each note
        console.print("[bold]Step 2:[/bold] Scanning links...")
        permanent_dir = VAULT / "knowledge-base" / "permanent"

        total_checked = 0
        to_remove = []  # List of (file_path, line_content, similarity)

        for note_path in permanent_dir.glob("*.md"):
            content = note_path.read_text()

            if "## Related" not in content:
                continue

            lines = content.split("\n")
            in_related = False
            source_stem = note_path.stem
            source_emb = stem_to_emb.get(source_stem)

            for i, line in enumerate(lines):
                if line.strip() == "## Related":
                    in_related = True
                    continue

                if in_related and (line.startswith("## ") or line.startswith("# ")):
                    in_related = False

                if in_related and "[[" in line:
                    match = re.search(r"\[\[([^\]|]+)", line)
                    if match:
                        target_stem = match.group(1)
                        target_emb = stem_to_emb.get(target_stem)

                        total_checked += 1

                        if source_emb is not None and target_emb is not None:
                            norm_s = np.linalg.norm(source_emb)
                            norm_t = np.linalg.norm(target_emb)
                            if norm_s > 0 and norm_t > 0:
                                sim = np.dot(source_emb, target_emb) / (norm_s * norm_t)

                                if sim < threshold:
                                    to_remove.append({
                                        "path": str(note_path),
                                        "line": line.strip(),
                                        "target": target_stem,
                                        "similarity": sim,
                                    })

        console.print(f"  Checked {total_checked} links")
        console.print(f"  Found {len(to_remove)} links below {args.threshold}%")

        if not to_remove:
            console.print("[green]All links are above threshold![/green]")
            return 0

        # Show preview
        console.print()
        console.print("[bold]Links to remove:[/bold]")
        for r in sorted(to_remove, key=lambda x: x["similarity"])[:20]:
            sim = r["similarity"] * 100
            src = Path(r["path"]).stem[:20]
            tgt = r["target"][:20]
            console.print(f"  [{sim:.0f}%] {src} → {tgt}")
        if len(to_remove) > 20:
            console.print(f"  ... and {len(to_remove) - 20} more")

        if args.dry_run:
            console.print("\n[yellow]Dry run - no changes made[/yellow]")
            return 0

        # Apply removal
        console.print("\n[bold]Step 3:[/bold] Removing links...")

        # Group by file
        by_file = {}
        for r in to_remove:
            p = r["path"]
            if p not in by_file:
                by_file[p] = set()
            by_file[p].add(r["target"])

        removed = 0
        files_modified = 0

        for file_path, targets_to_remove in by_file.items():
            note_path = Path(file_path)
            content = note_path.read_text()
            lines = content.split("\n")
            new_lines = []
            in_related = False

            for line in lines:
                if line.strip() == "## Related":
                    in_related = True
                    new_lines.append(line)
                    continue

                if in_related and (line.startswith("## ") or line.startswith("# ")):
                    in_related = False

                if in_related and "[[" in line:
                    match = re.search(r"\[\[([^\]|]+)", line)
                    if match and match.group(1) in targets_to_remove:
                        removed += 1
                        continue  # Skip this line

                new_lines.append(line)

            note_path.write_text("\n".join(new_lines))
            files_modified += 1

        console.print()
        console.print("=" * 70)
        console.print(f"[bold]COMPLETE[/bold]")
        console.print(f"Links removed: {removed}")
        console.print(f"Files modified: {files_modified}")
        console.print("=" * 70)

        return 0

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return 1


def tag_consolidate_main():
    """Entry point for tag consolidation.

    Replaces specified tags with a target tag across all notes.

    Usage: zk-tag-consolidate --from TAG1,TAG2 --to TAG [--dry-run]

    Arguments:
        --from: Comma-separated list of tags to replace
        --to: Target tag to consolidate into
        --dry-run: Preview changes without modifying files

    Returns:
        0 on success
        1 on error
    """
    import argparse
    import re
    import yaml

    parser = argparse.ArgumentParser(description="Consolidate tags across knowledge base")
    parser.add_argument("--from", "-f", dest="from_tags", required=True,
                        help="Comma-separated list of tags to replace")
    parser.add_argument("--to", "-t", dest="to_tag", required=True,
                        help="Target tag to consolidate into")
    parser.add_argument("--dry-run", "-n", action="store_true",
                        help="Preview changes without modifying files")

    args = parser.parse_args()

    try:
        # Parse and validate source tags
        source_tags = [tag.strip() for tag in args.from_tags.split(",") if tag.strip()]
        target_tag = args.to_tag.strip()

        if not source_tags:
            console.print("[red]Error: At least one source tag is required[/red]")
            return 1

        if not target_tag:
            console.print("[red]Error: Target tag must not be empty[/red]")
            return 1

        if target_tag in source_tags:
            console.print(f"[yellow]Warning: Target tag '{target_tag}' is in source tags list[/yellow]")

        # Display header
        source_display = ", ".join(source_tags)
        console.print(f"[bold]Tag Consolidation:[/bold] {source_display} -> {target_tag}")
        console.print()

        # Scan directories
        directories = [
            VAULT / "knowledge-base" / "permanent",
            VAULT / "knowledge-base" / "fleeting",
        ]

        affected_files = []

        for directory in directories:
            if not directory.exists():
                continue

            for md_file in directory.glob("**/*.md"):
                try:
                    content = md_file.read_text()

                    # Extract frontmatter
                    match = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
                    if not match:
                        continue

                    frontmatter_str, body = match.groups()
                    frontmatter = yaml.safe_load(frontmatter_str)

                    if not frontmatter or "tags" not in frontmatter:
                        continue

                    tags = frontmatter.get("tags", [])
                    if not isinstance(tags, list):
                        continue

                    # Check if any source tags are present
                    found_source_tags = [tag for tag in tags if tag in source_tags]
                    if not found_source_tags:
                        continue

                    # Record old tags
                    old_tags = tags.copy()

                    # Replace source tags with target tag
                    new_tags = []
                    target_added = False
                    for tag in tags:
                        if tag in source_tags:
                            if not target_added:
                                new_tags.append(target_tag)
                                target_added = True
                            # Skip the source tag (it's being replaced)
                        else:
                            new_tags.append(tag)

                    # Deduplicate while preserving order
                    seen = set()
                    deduped_tags = []
                    for tag in new_tags:
                        if tag not in seen:
                            seen.add(tag)
                            deduped_tags.append(tag)

                    # Store change info
                    affected_files.append({
                        "path": md_file,
                        "relative_path": md_file.relative_to(VAULT / "knowledge-base"),
                        "old_tags": old_tags,
                        "new_tags": deduped_tags,
                        "replaced_count": len(found_source_tags),
                        "frontmatter": frontmatter,
                        "body": body,
                    })

                except Exception as e:
                    console.print(f"[yellow]Warning: Could not process {md_file.name}: {e}[/yellow]")
                    continue

        # Report changes
        if not affected_files:
            console.print("[green]No files contain the specified source tags.[/green]")
            return 0

        console.print("[bold]Affected files:[/bold]")
        total_replaced = 0

        for file_info in affected_files:
            console.print(f"  {file_info['relative_path']}")
            old_str = ", ".join(file_info["old_tags"])
            new_str = ", ".join(file_info["new_tags"])
            console.print(f"    Tags: [{old_str}] -> [{new_str}]")
            total_replaced += file_info["replaced_count"]

        console.print()
        console.print("[bold]Summary:[/bold]")
        console.print(f"  Files modified: {len(affected_files)}")
        console.print(f"  Tags replaced: {total_replaced}")
        console.print()

        if args.dry_run:
            console.print("[yellow][Dry run - no changes made][/yellow]")
            return 0

        # Apply changes
        for file_info in affected_files:
            try:
                # Update frontmatter tags
                file_info["frontmatter"]["tags"] = file_info["new_tags"]

                # Serialize frontmatter
                new_frontmatter_str = yaml.dump(
                    file_info["frontmatter"],
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True
                )

                # Reconstruct file content
                new_content = f"---\n{new_frontmatter_str.strip()}\n---\n{file_info['body']}"

                # Write back
                file_info["path"].write_text(new_content)

            except Exception as e:
                console.print(f"[red]Error writing {file_info['path'].name}: {e}[/red]")

        console.print("[green]Changes applied successfully.[/green]")
        return 0

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return 1


def tag_audit_main():
    """Entry point for tag audit.

    Generates a comprehensive tag audit report for the knowledge base.

    Usage: zk-tag-audit [--output FILE]

    Arguments:
        --output: Output file path (default: knowledge-base/.reports/tag-audit-{date}.md)

    Returns:
        0 on success
        1 on error
    """
    import argparse
    from collections import defaultdict
    from datetime import datetime
    from itertools import combinations

    import yaml

    parser = argparse.ArgumentParser(description="Generate tag audit report")
    parser.add_argument("--output", "-o", type=str, default=None,
                        help="Output file path (default: knowledge-base/.reports/tag-audit-{date}.md)")

    args = parser.parse_args()

    console.print("=" * 70)
    console.print("[bold]TAG AUDIT REPORT[/bold]")
    console.print("=" * 70)
    console.print()

    try:
        # Directories to scan
        permanent_dir = VAULT / "knowledge-base" / "permanent"
        fleeting_dir = VAULT / "knowledge-base" / "fleeting"

        # Data structures
        tag_counts = defaultdict(int)  # tag -> count
        tag_notes = defaultdict(list)  # tag -> list of note titles
        note_tags = {}  # note_path -> list of tags
        cooccurrence = defaultdict(int)  # (tag1, tag2) -> count

        total_notes = 0
        notes_with_tags = 0

        # Scan both directories
        for scan_dir in [permanent_dir, fleeting_dir]:
            if not scan_dir.exists():
                continue

            for note_path in scan_dir.glob("**/*.md"):
                total_notes += 1
                content = note_path.read_text()

                # Parse frontmatter
                if content.startswith("---"):
                    try:
                        end_idx = content.index("---", 3)
                        frontmatter_str = content[3:end_idx]
                        frontmatter = yaml.safe_load(frontmatter_str)

                        tags = frontmatter.get("tags", []) if frontmatter else []
                        if tags:
                            notes_with_tags += 1
                            note_title = note_path.stem
                            note_tags[str(note_path)] = {"title": note_title, "tags": tags}

                            for tag in tags:
                                tag_counts[tag] += 1
                                tag_notes[tag].append(note_title)

                            # Calculate co-occurrences
                            for tag1, tag2 in combinations(sorted(tags), 2):
                                cooccurrence[(tag1, tag2)] += 1

                    except (ValueError, yaml.YAMLError):
                        pass  # Skip notes with invalid frontmatter

        console.print(f"[bold]Step 1:[/bold] Scanned {total_notes} notes")
        console.print(f"  Notes with tags: {notes_with_tags} ({notes_with_tags * 100 // total_notes if total_notes else 0}%)")
        console.print(f"  Unique tags: {len(tag_counts)}")
        console.print()

        # Find orphan tags (used only once)
        orphan_tags = [(tag, tag_notes[tag][0]) for tag, count in tag_counts.items() if count == 1]
        orphan_tags.sort(key=lambda x: x[0])

        # Find over-tagged notes (7+ tags)
        over_tagged = [(info["title"], len(info["tags"]), info["tags"])
                       for path, info in note_tags.items() if len(info["tags"]) >= 7]
        over_tagged.sort(key=lambda x: x[1], reverse=True)

        # Sort tag frequency
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)

        # Sort co-occurrence
        sorted_cooccur = sorted(cooccurrence.items(), key=lambda x: x[1], reverse=True)[:50]

        console.print(f"[bold]Step 2:[/bold] Analysis complete")
        console.print(f"  Orphan tags: {len(orphan_tags)}")
        console.print(f"  Over-tagged notes: {len(over_tagged)}")
        console.print()

        # Generate report
        date_str = datetime.now().strftime("%Y-%m-%d")
        date_file_str = datetime.now().strftime("%Y%m%d")

        report_lines = [
            f"# Tag Audit Report - {date_str}",
            "",
            "## Summary",
            f"- Total notes scanned: {total_notes}",
            f"- Notes with tags: {notes_with_tags} ({notes_with_tags * 100 // total_notes if total_notes else 0}%)",
            f"- Unique tags: {len(tag_counts)}",
            f"- Orphan tags: {len(orphan_tags)} (tags used only once)",
            f"- Over-tagged notes: {len(over_tagged)} (7+ tags)",
            "",
            "## Tag Frequency Distribution",
            "| Tag | Count | % of Tagged Notes |",
            "|-----|-------|-------------------|",
        ]

        for tag, count in sorted_tags:
            pct = count * 100 // notes_with_tags if notes_with_tags else 0
            report_lines.append(f"| `{tag}` | {count} | {pct}% |")

        report_lines.extend([
            "",
            "## Orphan Tags (used only once)",
        ])

        if orphan_tags:
            for tag, note_title in orphan_tags:
                report_lines.append(f"- `{tag}` - {note_title}")
        else:
            report_lines.append("*No orphan tags found*")

        report_lines.extend([
            "",
            "## Over-Tagged Notes (7+ tags)",
            "| Note | Tag Count | Tags |",
            "|------|-----------|------|",
        ])

        if over_tagged:
            for title, count, tags in over_tagged:
                tags_str = ", ".join(f"`{t}`" for t in sorted(tags))
                report_lines.append(f"| {title} | {count} | {tags_str} |")
        else:
            report_lines.append("| *None* | - | - |")

        report_lines.extend([
            "",
            "## Co-occurrence Matrix (top pairs)",
            "| Tag A | Tag B | Co-occurrences |",
            "|-------|-------|----------------|",
        ])

        if sorted_cooccur:
            for (tag1, tag2), count in sorted_cooccur:
                report_lines.append(f"| `{tag1}` | `{tag2}` | {count} |")
        else:
            report_lines.append("| *None* | - | - |")

        report_content = "\n".join(report_lines)

        # Determine output path
        if args.output:
            output_path = Path(args.output)
        else:
            reports_dir = VAULT / "knowledge-base" / ".reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            output_path = reports_dir / f"tag-audit-{date_file_str}.md"

        # Write report
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report_content)

        console.print(f"[bold]Step 3:[/bold] Report saved to {output_path}")
        console.print()

        # Display summary table
        console.print("[bold]Top 10 Tags:[/bold]")
        table = Table()
        table.add_column("Tag", style="cyan")
        table.add_column("Count", style="magenta")
        table.add_column("% of Tagged", style="green")

        for tag, count in sorted_tags[:10]:
            pct = count * 100 // notes_with_tags if notes_with_tags else 0
            table.add_row(tag, str(count), f"{pct}%")

        console.print(table)
        console.print()

        # Show orphan tags if any
        if orphan_tags:
            console.print(f"[yellow]Orphan tags ({len(orphan_tags)}):[/yellow]")
            for tag, note in orphan_tags[:10]:
                console.print(f"  - {tag} (in: {note})")
            if len(orphan_tags) > 10:
                console.print(f"  ... and {len(orphan_tags) - 10} more")
            console.print()

        # Show over-tagged notes if any
        if over_tagged:
            console.print(f"[yellow]Over-tagged notes ({len(over_tagged)}):[/yellow]")
            for title, count, tags in over_tagged[:5]:
                console.print(f"  - {title} ({count} tags)")
            if len(over_tagged) > 5:
                console.print(f"  ... and {len(over_tagged) - 5} more")
            console.print()

        console.print("=" * 70)
        console.print("[bold]COMPLETE[/bold]")
        console.print(f"Report: {output_path}")
        console.print("=" * 70)

        return 0

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(extract_main())
