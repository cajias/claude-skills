#!/usr/bin/env python3
"""
Comprehensive fix for Quip table formatting issues.

Fixes:
1. Empty leading columns: ||Header| -> |Header|
2. Row numbers in first column: |1|Cell| -> |Cell|
3. Extra separator columns: |---|---|---| (removes first if empty header)
4. Empty row separators: ||||||| -> removes line
5. Escaped characters in tables: \( -> (
"""

import re
import sys
from pathlib import Path


def is_table_line(line: str) -> bool:
    """Check if line is part of a markdown table."""
    stripped = line.strip()
    return stripped.startswith('|') and stripped.endswith('|') and '|' in stripped[1:-1]


def is_separator_line(line: str) -> bool:
    """Check if line is a table separator (|---|---|)."""
    stripped = line.strip()
    return bool(re.match(r'^\|[\s\-:|]+\|$', stripped))


def is_empty_table_line(line: str) -> bool:
    """Check if line is an empty table row (just pipes)."""
    stripped = line.strip()
    return bool(re.match(r'^\|+$', stripped))


def fix_table_line(line: str) -> str:
    """Fix a single table line."""
    original = line

    # Skip non-table lines
    if not is_table_line(line):
        return line

    # Remove empty table lines (just pipes)
    if is_empty_table_line(line):
        return ''

    # Fix double leading pipe: ||Content| -> |Content|
    while line.strip().startswith('||'):
        line = re.sub(r'^\s*\|\|', '|', line)

    # Fix separator line with extra column
    if is_separator_line(line):
        # |---|---|---| with extra first column
        line = re.sub(r'^\|---\|', '|', line)
    else:
        # Fix numbered first column: |1|Content| -> |Content|
        # But preserve |#| as header
        if not re.match(r'^\s*\|#\|', line):
            line = re.sub(r'^\|(\d+)\|', '|', line)

    # Unescape parentheses in tables: \( -> ( and \) -> )
    line = line.replace('\\(', '(').replace('\\)', ')')

    # Unescape asterisks if over-escaped: \* -> *
    # Only in table context, be conservative

    return line


def fix_content(content: str) -> str:
    """Fix all tables in content."""
    lines = content.split('\n')
    fixed_lines = []

    for line in lines:
        # An empty table row (just pipes, e.g. ||||) should be removed entirely,
        # but genuine blank lines (paragraph separators) must be preserved.
        if is_table_line(line) and is_empty_table_line(line):
            continue
        fixed_lines.append(fix_table_line(line))

    return '\n'.join(fixed_lines)


def process_file(filepath: Path) -> bool:
    """Process a single file. Returns True if modified."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"[ERROR] Could not read {filepath}: {e}")
        return False

    new_content = fix_content(content)

    if new_content != content:
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
        except Exception as e:
            print(f"[ERROR] Could not write {filepath}: {e}")
            return False
    return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python fix-quip-tables-v2.py <directory>")
        sys.exit(1)

    root_dir = Path(sys.argv[1]).resolve()

    if not root_dir.exists():
        print(f"Error: Directory not found: {root_dir}")
        sys.exit(1)

    print(f"=== Quip Table Fixer v2 ===")
    print(f"Directory: {root_dir}")
    print()

    updated = 0
    scanned = 0

    for md_file in root_dir.rglob('*.md'):
        scanned += 1
        if process_file(md_file):
            print(f"[FIXED] {md_file.relative_to(root_dir)}")
            updated += 1

    print()
    print(f"=== Complete ===")
    print(f"Files scanned: {scanned}")
    print(f"Files fixed: {updated}")


if __name__ == '__main__':
    main()
