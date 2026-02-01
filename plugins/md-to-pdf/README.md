# md-to-pdf

Convert a directory of markdown files to PDF with Mermaid diagram rendering.

## Features

- Combines multiple markdown files into a single PDF
- Renders Mermaid diagrams using the mermaid.ink API
- Strips YAML frontmatter from files
- Alphabetical file ordering (use numeric prefixes like `00-`, `01-` for custom order)
- Professional styling with proper typography

## Prerequisites

- **pandoc**: `brew install pandoc`
- **weasyprint**: Auto-installed via `pipx` if missing

## Usage

```text
/md-to-pdf <directory-path>
```

### Example

```text
/md-to-pdf ~/Documents/my-playbook
```

This will:

1. Find all `.md` files in the directory
2. Ask where to save the PDF
3. Combine files alphabetically
4. Render any Mermaid diagrams
5. Generate and open the PDF

## How It Works

1. **File Discovery**: Finds all `.md` files, excludes README.md, CHANGELOG.md, etc.
2. **Frontmatter Stripping**: Removes YAML frontmatter (`---` blocks) from each file
3. **Mermaid Rendering**: Sends Mermaid code blocks to mermaid.ink API, downloads as PNG
4. **HTML Generation**: Uses pandoc to convert markdown to styled HTML
5. **PDF Generation**: Uses weasyprint to convert HTML to PDF

## File Ordering

Files are sorted alphabetically. To control order, use numeric prefixes:

```text
00-introduction.md
01-getting-started.md
02-advanced-topics.md
03-reference.md
```

## Excluded Files

The following files are automatically excluded:

- README.md
- CHANGELOG.md
- LICENSE.md
- PLAN.md

## Troubleshooting

### Mermaid diagrams not rendering

- Check internet connection (requires access to mermaid.ink)
- Complex diagrams may timeout; simplify if needed

### PDF generation fails

- Ensure weasyprint is installed: `pipx install weasyprint`
- Ensure pandoc is installed: `brew install pandoc`

### Missing fonts

weasyprint uses system fonts. Install additional fonts if needed for your content.
