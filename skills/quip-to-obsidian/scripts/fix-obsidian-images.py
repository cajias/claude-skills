#!/usr/bin/env python3
"""
Convert Quip markdown image references to Obsidian-compatible format.

This script performs two operations:
1. Updates /blob/THREAD_ID/BLOB_ID references to local attachment paths
2. Converts reference-style image links to inline format for Obsidian

Usage:
    python3 fix-obsidian-images.py --directory /path/to/obsidian/folder
    python3 fix-obsidian-images.py --directory /path/to/folder --attachments-dir attachments
    python3 fix-obsidian-images.py --directory /path/to/folder --use-wikilinks
"""

import argparse
import os
import re
from pathlib import Path


def get_relative_path(from_file: Path, to_dir: Path) -> str:
    """Calculate relative path from a file to a directory."""
    from_dir = from_file.parent
    return os.path.relpath(to_dir, from_dir)


def update_blob_references(content: str, attachments_rel_path: str) -> str:
    """Replace /blob/THREAD/BLOB references with local attachment paths."""
    # Pattern: /blob/THREAD_ID/BLOB_ID
    blob_pattern = r'/blob/([A-Za-z0-9]+)/([A-Za-z0-9_-]+)'

    def replace_blob(match):
        thread_id = match.group(1)
        blob_id = match.group(2)
        # Assume PNG extension (most common), actual extension determined at download time
        return f'{attachments_rel_path}/{thread_id}_{blob_id}.png'

    return re.sub(blob_pattern, replace_blob, content)


def convert_reference_to_inline(content: str, use_wikilinks: bool = False) -> str:
    """Convert reference-style image links to inline format.

    Converts:
        ![alt text][ref]
        [ref]: path/to/image.png
    To:
        ![alt text](path/to/image.png)
    Or (with wikilinks):
        ![[path/to/image.png|alt text]]
    """
    # Extract all reference definitions: [ref]: url
    ref_pattern = r'^\[([^\]]+)\]:\s*(.+)$'
    references = {}
    for match in re.finditer(ref_pattern, content, re.MULTILINE):
        ref_id = match.group(1)
        ref_url = match.group(2).strip()
        references[ref_id] = ref_url

    # Replace image references that point to local attachments
    # Pattern: ![alt text][ref] with optional trailing text
    img_pattern = r'!\[([^\]]*)\]\[(\d+)\]([^\s\[\n]*)?'

    def replace_image(match):
        alt_text = match.group(1)
        ref_id = match.group(2)
        # Ignore trailing text like "[Image editable link]"

        if ref_id in references:
            url = references[ref_id]
            # Only convert if it's a local attachment
            if 'attachments/' in url or url.endswith('.png') or url.endswith('.jpg'):
                if use_wikilinks:
                    # Obsidian wikilink format
                    if alt_text:
                        return f'![[{url}|{alt_text}]]'
                    return f'![[{url}]]'
                else:
                    # Standard markdown inline format
                    return f'![{alt_text}]({url})'

        # Keep original if not a local attachment
        return match.group(0)

    new_content = re.sub(img_pattern, replace_image, content)

    # Also handle empty alt text images: ![][ref]
    empty_img_pattern = r'!\[\]\[(\d+)\]([^\s\[\n]*)?'

    def replace_empty_image(match):
        ref_id = match.group(1)

        if ref_id in references:
            url = references[ref_id]
            if 'attachments/' in url or url.endswith('.png') or url.endswith('.jpg'):
                if use_wikilinks:
                    return f'![[{url}]]'
                else:
                    return f'![]({url})'

        return match.group(0)

    new_content = re.sub(empty_img_pattern, replace_empty_image, new_content)

    return new_content


def process_markdown_file(filepath: Path, attachments_dir: Path, use_wikilinks: bool = False) -> bool:
    """Process a single markdown file. Returns True if file was modified."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Calculate relative path to attachments from this file's directory
    attachments_rel_path = get_relative_path(filepath, attachments_dir)

    # Step 1: Update blob references to local paths
    content = update_blob_references(content, attachments_rel_path)

    # Step 2: Convert reference-style to inline format
    content = convert_reference_to_inline(content, use_wikilinks)

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def main():
    parser = argparse.ArgumentParser(
        description='Convert Quip markdown images to Obsidian-compatible format'
    )
    parser.add_argument(
        '--directory', '-d',
        required=True,
        help='Root directory containing markdown files'
    )
    parser.add_argument(
        '--attachments-dir', '-a',
        default='attachments',
        help='Name of attachments directory (default: attachments)'
    )
    parser.add_argument(
        '--use-wikilinks', '-w',
        action='store_true',
        help='Use Obsidian wikilink format ![[image]] instead of ![](image)'
    )
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Show what would be changed without modifying files'
    )

    args = parser.parse_args()

    root_dir = Path(args.directory).resolve()
    attachments_dir = root_dir / args.attachments_dir

    if not root_dir.exists():
        print(f"Error: Directory not found: {root_dir}")
        return 1

    print(f"=== Obsidian Image Converter ===")
    print(f"Directory: {root_dir}")
    print(f"Attachments: {attachments_dir}")
    print(f"Format: {'Wikilinks' if args.use_wikilinks else 'Standard Markdown'}")
    print(f"Dry run: {args.dry_run}")
    print()

    updated = 0
    scanned = 0

    for md_file in root_dir.rglob('*.md'):
        scanned += 1

        if args.dry_run:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            if '/blob/' in content or re.search(r'!\[[^\]]*\]\[\d+\]', content):
                print(f"[WOULD UPDATE] {md_file}")
                updated += 1
        else:
            if process_markdown_file(md_file, attachments_dir, args.use_wikilinks):
                print(f"[UPDATED] {md_file}")
                updated += 1

    print()
    print(f"=== Conversion Complete ===")
    print(f"Files scanned: {scanned}")
    print(f"Files {'would be ' if args.dry_run else ''}updated: {updated}")

    return 0


if __name__ == '__main__':
    exit(main())
