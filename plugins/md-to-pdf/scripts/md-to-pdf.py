#!/usr/bin/env python3
"""
Markdown to PDF converter with Mermaid diagram rendering.

Usage: python3 md-to-pdf.py <source-directory> <output-pdf-path>

This script:
1. Combines all .md files in a directory (alphabetically)
2. Downloads Mermaid diagrams from mermaid.ink API
3. Generates PDF using pandoc + weasyprint
"""

import sys
import os
import re
import base64
import json
import zlib
import urllib.request
import subprocess
import tempfile
from pathlib import Path


def get_markdown_files(directory: str) -> list[Path]:
    """Get all markdown files in directory, sorted alphabetically."""
    dir_path = Path(directory)
    md_files = sorted(dir_path.glob("*.md"))
    # Exclude common non-content files
    exclude = {"README.md", "CHANGELOG.md", "LICENSE.md", "PLAN.md"}
    return [f for f in md_files if f.name not in exclude]


def strip_yaml_frontmatter(content: str) -> str:
    """Remove YAML frontmatter from markdown content."""
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return content


def combine_markdown_files(files: list[Path]) -> str:
    """Combine multiple markdown files into one document."""
    combined = []
    for f in files:
        content = f.read_text(encoding="utf-8")
        content = strip_yaml_frontmatter(content)
        if content:
            combined.append(content)
            combined.append("\n\n---\n\n")  # Separator between files
    return "\n".join(combined)


def mermaid_to_url(mermaid_code: str) -> str:
    """Convert Mermaid code to mermaid.ink URL."""
    # mermaid.ink takes the config as a JSON *string*, not a nested object.
    payload = json.dumps({"code": mermaid_code, "mermaid": '{"theme":"default"}'})
    compressed = zlib.compress(payload.encode("utf-8"), 9)
    encoded = base64.urlsafe_b64encode(compressed).decode("utf-8")
    return f"https://mermaid.ink/img/pako:{encoded}"


def download_mermaid_diagram(mermaid_code: str, output_path: Path) -> bool:
    """Download Mermaid diagram as image from mermaid.ink."""
    try:
        url = mermaid_to_url(mermaid_code)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            output_path.write_bytes(response.read())
        return True
    except Exception as e:
        print(f"Warning: Failed to render diagram: {e}", file=sys.stderr)
        return False


def render_mermaid_diagrams(content: str, temp_dir: Path) -> str:
    """Replace Mermaid code blocks with rendered images."""
    mermaid_pattern = r"```mermaid\n(.*?)```"
    matches = list(re.finditer(mermaid_pattern, content, re.DOTALL))

    if not matches:
        return content

    print(f"Found {len(matches)} Mermaid diagrams to render...")

    image_paths = []
    for i, match in enumerate(matches):
        mermaid_code = match.group(1).strip()
        img_path = temp_dir / f"diagram_{i}.png"

        if download_mermaid_diagram(mermaid_code, img_path):
            image_paths.append(str(img_path))
            print(f"  Rendered diagram {i + 1}/{len(matches)}")
        else:
            image_paths.append(None)
            print(f"  Failed diagram {i + 1}/{len(matches)}")

    # Replace mermaid blocks with image references
    counter = 0
    def replace_mermaid(match):
        nonlocal counter
        img_path = image_paths[counter]
        counter += 1
        if img_path and os.path.exists(img_path):
            return f"![Diagram]({img_path})"
        return match.group(0)  # Keep original if failed

    return re.sub(mermaid_pattern, replace_mermaid, content, flags=re.DOTALL)


def markdown_to_pdf(markdown_content: str, temp_dir: Path, output_pdf: Path) -> None:
    """Convert markdown straight to PDF via pandoc's weasyprint engine."""
    md_file = temp_dir / "combined.md"
    md_file.write_text(markdown_content, encoding="utf-8")

    # Create CSS for styling
    css_content = """
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    line-height: 1.6;
    font-size: 11pt;
}
h1 { font-size: 24pt; margin-top: 1.5em; page-break-after: avoid; }
h2 { font-size: 18pt; margin-top: 1.5em; page-break-after: avoid; }
h3 { font-size: 14pt; margin-top: 1em; page-break-after: avoid; }
code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-size: 10pt; }
pre { background: #f4f4f4; padding: 12px; border-radius: 6px; font-size: 9pt; white-space: pre-wrap; }
table { border-collapse: collapse; width: 100%; margin: 1em 0; font-size: 10pt; }
th, td { border: 1px solid #ddd; padding: 6px; text-align: left; }
th { background: #f4f4f4; }
hr { margin: 1.5em 0; border: none; border-top: 1px solid #ddd; }
img { max-width: 100%; height: auto; display: block; margin: 1em auto; }
@page { margin: 20mm 15mm; }
"""
    css_file = temp_dir / "style.css"
    css_file.write_text(css_content, encoding="utf-8")

    cmd = [
        "pandoc",
        str(md_file),
        "-o", str(output_pdf),
        "--pdf-engine=weasyprint",
        "--standalone",
        f"--css={css_file}",
        "--embed-resources",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"pandoc failed: {result.stderr}")


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 md-to-pdf.py <source-directory> <output-pdf-path>")
        sys.exit(1)

    source_dir = sys.argv[1]
    output_pdf = sys.argv[2]

    # Validate source directory
    if not os.path.isdir(source_dir):
        print(f"Error: '{source_dir}' is not a directory")
        sys.exit(1)

    # Get markdown files
    md_files = get_markdown_files(source_dir)
    if not md_files:
        print(f"Error: No markdown files found in '{source_dir}'")
        sys.exit(1)

    print(f"Found {len(md_files)} markdown files:")
    for f in md_files:
        print(f"  - {f.name}")

    # Create temp directory for intermediate files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Combine markdown files
        print("\nCombining markdown files...")
        combined = combine_markdown_files(md_files)

        # Render Mermaid diagrams
        print("\nRendering Mermaid diagrams...")
        rendered = render_mermaid_diagrams(combined, temp_path)

        # Convert to PDF
        print("\nGenerating PDF...")
        markdown_to_pdf(rendered, temp_path, Path(output_pdf))

    print(f"\nPDF created: {output_pdf}")


if __name__ == "__main__":
    main()
