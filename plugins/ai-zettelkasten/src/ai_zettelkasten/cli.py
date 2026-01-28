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


if __name__ == "__main__":
    sys.exit(extract_main())
