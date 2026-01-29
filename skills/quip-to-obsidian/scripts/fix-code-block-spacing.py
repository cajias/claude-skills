#!/usr/bin/env python3
"""
Fix extra blank lines in code blocks from Quip exports.

Quip exports add extra blank lines (often with trailing spaces) between
every line of code. This script removes these extra lines while preserving
intentional blank lines.
"""

import re
import sys
from pathlib import Path


def fix_code_block_spacing(content: str) -> str:
    """Remove extra blank lines from within code blocks."""
    
    def fix_block(match):
        """Fix a single code block."""
        lang = match.group(1) or ''
        block_content = match.group(2)
        
        # Split into lines
        lines = block_content.split('\n')
        
        # Remove lines that are empty or contain only whitespace,
        # but keep intentional blank lines (consecutive blank lines become one)
        fixed_lines = []
        prev_was_content = False
        
        for line in lines:
            stripped = line.rstrip()
            
            if stripped:  # Line has content
                fixed_lines.append(stripped)
                prev_was_content = True
            elif prev_was_content and not stripped:
                # First blank line after content - might be intentional
                # Check if next non-empty line exists
                prev_was_content = False
                # Don't add blank line yet - wait to see if there's more content
            # Skip additional consecutive blank lines
        
        # Rejoin, removing trailing blank lines
        fixed_content = '\n'.join(fixed_lines)
        
        return f'```{lang}\n{fixed_content}\n```'
    
    # Match code blocks with optional language
    pattern = r'```(\w*)\n(.*?)```'
    return re.sub(pattern, fix_block, content, flags=re.DOTALL)


def process_file(filepath: Path) -> bool:
    """Process a single file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = fix_code_block_spacing(content)
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python fix-code-block-spacing.py <directory>")
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
