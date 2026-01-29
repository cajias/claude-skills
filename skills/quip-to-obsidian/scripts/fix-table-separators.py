#!/usr/bin/env python3
"""
Fix markdown table separator lines to match header column count.
"""

import re
import sys
from pathlib import Path


def count_columns(line: str) -> int:
    """Count the number of columns in a table row."""
    # Remove leading/trailing pipes and count remaining pipes + 1
    stripped = line.strip()
    if stripped.startswith('|'):
        stripped = stripped[1:]
    if stripped.endswith('|'):
        stripped = stripped[:-1]
    return stripped.count('|') + 1


def is_separator_line(line: str) -> bool:
    """Check if line is a table separator."""
    stripped = line.strip()
    return bool(re.match(r'^\|[\s\-:|]+\|$', stripped))


def make_separator(num_cols: int) -> str:
    """Create a proper separator line."""
    return '|' + '---|' * num_cols


def fix_tables(content: str) -> str:
    """Fix table separator lines to match header columns."""
    lines = content.split('\n')
    fixed_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check if this is a table header (followed by separator)
        if i + 1 < len(lines) and is_separator_line(lines[i + 1]):
            header_cols = count_columns(line)
            sep_cols = count_columns(lines[i + 1])

            # Add header
            fixed_lines.append(line)
            i += 1

            # Fix separator if needed
            if header_cols != sep_cols:
                fixed_lines.append(make_separator(header_cols))
            else:
                fixed_lines.append(lines[i])
            i += 1
        else:
            fixed_lines.append(line)
            i += 1

    return '\n'.join(fixed_lines)


def process_file(filepath: Path) -> bool:
    """Process a single file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = fix_tables(content)

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python fix-table-separators.py <directory>")
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
