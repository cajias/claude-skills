---
name: md-to-pdf
description: Convert a directory of markdown files to PDF with Mermaid diagram rendering
argument-hint: "<directory-path>"
allowed-tools:
  - Bash
  - Read
  - Write
  - Glob
  - AskUserQuestion
---

# Markdown to PDF Converter

Convert a directory of markdown files into a single PDF document with properly rendered Mermaid diagrams.

## Workflow

1. **Validate input**: Confirm the directory exists and contains markdown files
2. **Ask for output location**: Prompt user where to save the PDF
3. **Check dependencies**: Ensure weasyprint and pandoc are installed (auto-install weasyprint via pipx if missing)
4. **Combine markdown files**: Merge all .md files in alphabetical order, stripping YAML frontmatter
5. **Render Mermaid diagrams**: Download diagrams from mermaid.ink API as PNG images
6. **Generate PDF**: Use pandoc with `--pdf-engine=weasyprint` to create the final PDF
7. **Open PDF**: Display the result to the user

## Implementation

### Step 1: Validate Input

Check if the provided path is a directory with markdown files:

```bash
ls -la "<directory>" && ls "<directory>"/*.md 2>/dev/null | head -5
```

If no directory provided or no .md files found, inform the user.

### Step 2: Ask Output Location

Use AskUserQuestion to ask where to save the PDF:

- Same directory as source (default)
- Custom path

### Step 3: Check Dependencies

```bash
# Check for pandoc
which pandoc || echo "pandoc not found - please install with: brew install pandoc"

# Check for weasyprint, install if missing
which weasyprint || pipx install weasyprint
```

### Step 4: Run the Conversion

Execute the main conversion script:

```bash
python3 "$CLAUDE_PLUGIN_ROOT/scripts/md-to-pdf.py" "<source-directory>" "<output-path>"
```

The script handles:

- Combining markdown files alphabetically
- Downloading Mermaid diagrams from mermaid.ink
- Generating the styled PDF with pandoc's weasyprint engine

### Step 5: Open Result

```bash
open "<output-path>"
```

## Error Handling

- If weasyprint installation fails, suggest manual installation
- If mermaid.ink API fails, keep original code blocks
- If pandoc fails, show the error message

## Example Usage

```text
/md-to-pdf /path/to/documentation
```

This will:

1. Find all .md files in /path/to/documentation
2. Ask where to save the PDF
3. Generate the PDF with rendered diagrams
4. Open the result
