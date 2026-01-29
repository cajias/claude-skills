#!/usr/bin/env python3
"""
Auto-detect and add language hints to markdown code blocks.

Detects:
- Mermaid diagrams (sequenceDiagram, graph, flowchart, erDiagram, classDiagram)
- JSON (starts with { or [)
- YAML (key: value patterns, starts with ---)
- TypeScript/JavaScript (import, export, const, function, interface, =>, async)
- Go (package, func, import, type struct)
- Python (import, def, class, from x import)
- Shell/Bash (#!/bin/bash, $, export, echo, cd, ls)
- Cedar (permit, forbid, principal, action, resource)
- SQL (SELECT, INSERT, CREATE, FROM, WHERE)
- Directory trees (├──, └──, │)
- HTTP (GET, POST, PUT, DELETE followed by /)
"""

import re
import sys
from pathlib import Path


def detect_language(code: str) -> str:
    """Detect the language of a code block based on content."""
    code_stripped = code.strip()
    first_line = code_stripped.split('\n')[0] if code_stripped else ''

    # Mermaid diagrams
    if re.search(r'^(sequenceDiagram|graph\s|flowchart\s|erDiagram|classDiagram|pie\s|gantt|stateDiagram|gitGraph)', code_stripped, re.MULTILINE):
        return 'mermaid'
    if re.search(r'^\s*subgraph\s', code_stripped, re.MULTILINE):
        return 'mermaid'

    # JSON
    if first_line.startswith('{') or first_line.startswith('['):
        if re.search(r'["\']:\s*["\'\[\{0-9]', code_stripped):
            return 'json'

    # YAML
    if re.search(r'^[a-zA-Z_][a-zA-Z0-9_]*:\s*[^\s]', code_stripped, re.MULTILINE):
        if not re.search(r'(function|const|let|var|import|export)\s', code_stripped):
            if re.search(r'^[\s-]*[a-zA-Z_]+:', code_stripped, re.MULTILINE):
                return 'yaml'

    # Shell/Bash
    if first_line.startswith('#!/bin/bash') or first_line.startswith('#!/bin/sh'):
        return 'bash'
    if re.search(r'^(\$|export\s|echo\s|cd\s|mkdir\s|curl\s|npm\s|pip\s|docker\s)', code_stripped, re.MULTILINE):
        return 'bash'

    # Cedar policies
    if re.search(r'^(permit|forbid)\s*\(', code_stripped, re.MULTILINE):
        return 'cedar'
    if re.search(r'\b(principal|action|resource)\s+(is|==|in)\s+', code_stripped):
        return 'cedar'

    # Go
    if re.search(r'^package\s+\w+', code_stripped, re.MULTILINE):
        return 'go'
    if re.search(r'^func\s+\w+\s*\(', code_stripped, re.MULTILINE):
        return 'go'
    if re.search(r'type\s+\w+\s+struct\s*\{', code_stripped):
        return 'go'

    # TypeScript/JavaScript
    if re.search(r'^(import|export)\s+', code_stripped, re.MULTILINE):
        return 'typescript'
    if re.search(r'^(const|let|var)\s+\w+\s*[=:]', code_stripped, re.MULTILINE):
        return 'typescript'
    if re.search(r'^(interface|type)\s+\w+\s*[=\{<]', code_stripped, re.MULTILINE):
        return 'typescript'
    if re.search(r'^(async\s+)?function\s+\w+', code_stripped, re.MULTILINE):
        return 'typescript'
    if re.search(r'=>\s*[\{\(]', code_stripped):
        return 'typescript'

    # Python
    if re.search(r'^(from\s+\w+\s+import|import\s+\w+)', code_stripped, re.MULTILINE):
        return 'python'
    if re.search(r'^def\s+\w+\s*\(', code_stripped, re.MULTILINE):
        return 'python'
    if re.search(r'^class\s+\w+[\(:]', code_stripped, re.MULTILINE):
        return 'python'

    # SQL
    if re.search(r'^(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)\s', code_stripped, re.IGNORECASE | re.MULTILINE):
        return 'sql'

    # HTTP methods
    if re.search(r'^(GET|POST|PUT|DELETE|PATCH)\s+/', code_stripped, re.MULTILINE):
        return 'http'

    # Directory trees
    if re.search(r'[├└│]──', code_stripped):
        return 'text'

    # HCL/Terraform
    if re.search(r'^(resource|provider|variable|output|data)\s+"', code_stripped, re.MULTILINE):
        return 'hcl'

    # XML/HTML
    if re.search(r'^<\?xml|^<!DOCTYPE|^<html', code_stripped, re.IGNORECASE):
        return 'xml'
    if re.search(r'^<[a-zA-Z]+[^>]*>', code_stripped):
        return 'xml'

    return ''


def fix_code_blocks(content: str) -> tuple[str, int]:
    """Fix code blocks in content. Returns (new_content, count_fixed)."""
    # Pattern to match code blocks: ```lang or ``` followed by content and closing ```
    pattern = r'(```)([\w]*)\n(.*?)\n(```)'

    fixed_count = 0

    def replace_block(match):
        nonlocal fixed_count
        opening = match.group(1)
        lang = match.group(2)
        code = match.group(3)
        closing = match.group(4)

        # Only fix if no language specified
        if not lang:
            detected = detect_language(code)
            if detected:
                fixed_count += 1
                return f'{opening}{detected}\n{code}\n{closing}'

        return match.group(0)

    new_content = re.sub(pattern, replace_block, content, flags=re.DOTALL)
    return new_content, fixed_count


def process_file(filepath: Path) -> int:
    """Process a single file. Returns count of fixed blocks."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content, fixed_count = fix_code_blocks(content)

    if fixed_count > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

    return fixed_count


def main():
    if len(sys.argv) < 2:
        print("Usage: python fix-code-block-langs.py <directory>")
        sys.exit(1)

    root_dir = Path(sys.argv[1]).resolve()
    total_fixed = 0

    print(f"=== Code Block Language Fixer ===")
    print(f"Directory: {root_dir}")
    print()

    for md_file in root_dir.rglob('*.md'):
        fixed = process_file(md_file)
        if fixed > 0:
            print(f"[FIXED {fixed:2d}] {md_file.relative_to(root_dir)}")
            total_fixed += fixed

    print()
    print(f"=== Complete ===")
    print(f"Total code blocks fixed: {total_fixed}")


if __name__ == '__main__':
    main()
