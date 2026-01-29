#!/usr/bin/env python3
"""
Remove zero-width space characters (U+200B) from markdown files.

Quip exports often contain invisible zero-width space characters that can
break markdown rendering, especially before tables and code blocks.
"""

import sys
import re
from pathlib import Path


def fix_zero_width_spaces(content: str) -> str:
    """Remove zero-width space characters from content."""
    # Remove zero-width space (U+200B)
    content = content.replace('\u200B', '')
    
    # Also remove other common invisible Unicode characters from Quip
    # Zero-width non-joiner (U+200C)
    content = content.replace('\u200C', '')
    # Zero-width joiner (U+200D)
    content = content.replace('\u200D', '')
    # Word joiner (U+2060)
    content = content.replace('\u2060', '')
    # Zero-width no-break space / BOM (U+FEFF)
    content = content.replace('\uFEFF', '')
    
    return content


def process_file(filepath: Path) -> bool:
    """Process a single file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = fix_zero_width_spaces(content)
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python fix-zero-width-spaces.py <directory>")
        sys.exit(1)
    
    root_dir = Path(sys.argv[1]).resolve()
    updated = 0
    
    for md_file in root_dir.rglob('*.md'):
        if process_file(md_file):
            print(f"[FIXED] {md_file.relative_to(root_dir)}")
            updated += 1
    
    print(f"\nFiles fixed: {updated}")


if __name__ == '__main__':
    main()
