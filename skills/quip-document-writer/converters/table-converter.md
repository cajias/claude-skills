# Table Converter - Markdown to HTML

This document provides the rules and patterns for converting markdown tables to HTML format when
Quip's markdown parser fails.

## Why Convert Tables to HTML?

Quip's markdown parser can lose or misalign table cell data during bulk imports. When verification
shows table corruption, converting to HTML provides more control over structure and content.

## Basic Table Conversion

### Simple Table

**Markdown:**

```markdown
| Header 1 | Header 2 | Header 3 |
| -------- | -------- | -------- |
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |
```

**HTML:**

```html
<table>
  <thead>
    <tr>
      <th>Header 1</th>
      <th>Header 2</th>
      <th>Header 3</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Cell 1</td>
      <td>Cell 2</td>
      <td>Cell 3</td>
    </tr>
    <tr>
      <td>Cell 4</td>
      <td>Cell 5</td>
      <td>Cell 6</td>
    </tr>
  </tbody>
</table>
```

## Table Alignment

### Left, Center, Right Alignment

**Markdown:**

```markdown
| Left | Center | Right |
| :--- | :----: | ----: |
| L1   |   C1   |    R1 |
| L2   |   C2   |    R2 |
```

**HTML:**

```html
<table>
  <thead>
    <tr>
      <th style="text-align: left;">Left</th>
      <th style="text-align: center;">Center</th>
      <th style="text-align: right;">Right</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="text-align: left;">L1</td>
      <td style="text-align: center;">C1</td>
      <td style="text-align: right;">R1</td>
    </tr>
    <tr>
      <td style="text-align: left;">L2</td>
      <td style="text-align: center;">C2</td>
      <td style="text-align: right;">R2</td>
    </tr>
  </tbody>
</table>
```

## Tables with Rich Content

### Tables with Links

**Markdown:**

```markdown
| Name   | Link                       |
| ------ | -------------------------- |
| GitHub | [Link](https://github.com) |
| Quip   | [Link](https://quip.com)   |
```

**HTML:**

```html
<table>
  <thead>
    <tr>
      <th>Name</th>
      <th>Link</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>GitHub</td>
      <td><a href="https://github.com">Link</a></td>
    </tr>
    <tr>
      <td>Quip</td>
      <td><a href="https://quip.com">Link</a></td>
    </tr>
  </tbody>
</table>
```

### Tables with Code

**Markdown:**

```markdown
| Function      | Example          |
| ------------- | ---------------- |
| Print         | `print("hello")` |
| String format | `f"value: {x}"`  |
```

**HTML:**

```html
<table>
  <thead>
    <tr>
      <th>Function</th>
      <th>Example</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Print</td>
      <td><code>print("hello")</code></td>
    </tr>
    <tr>
      <td>String format</td>
      <td><code>f"value: {x}"</code></td>
    </tr>
  </tbody>
</table>
```

### Tables with Bold/Italic

**Markdown:**

```markdown
| Status       | Description       |
| ------------ | ----------------- |
| **Active**   | Currently running |
| _Pending_    | Waiting to start  |
| **_Failed_** | Execution failed  |
```

**HTML:**

```html
<table>
  <thead>
    <tr>
      <th>Status</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Active</strong></td>
      <td>Currently running</td>
    </tr>
    <tr>
      <td><em>Pending</em></td>
      <td>Waiting to start</td>
    </tr>
    <tr>
      <td>
        <strong><em>Failed</em></strong>
      </td>
      <td>Execution failed</td>
    </tr>
  </tbody>
</table>
```

### Tables with Line Breaks

When cells need multiple lines:

**HTML:**

```html
<table>
  <thead>
    <tr>
      <th>Item</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Feature A</td>
      <td>
        Line 1 of description<br />
        Line 2 of description<br />
        Line 3 of description
      </td>
    </tr>
  </tbody>
</table>
```

### Tables with Lists

**HTML:**

```html
<table>
  <thead>
    <tr>
      <th>Category</th>
      <th>Items</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Features</td>
      <td>
        <ul>
          <li>Feature 1</li>
          <li>Feature 2</li>
          <li>Feature 3</li>
        </ul>
      </td>
    </tr>
  </tbody>
</table>
```

## Empty Cells and Special Cases

### Empty Cells

Preserve empty cells with `&nbsp;` or leave truly empty:

**HTML:**

```html
<table>
  <thead>
    <tr>
      <th>Col 1</th>
      <th>Col 2</th>
      <th>Col 3</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Data</td>
      <td></td>
      <td>More data</td>
    </tr>
    <tr>
      <td>&nbsp;</td>
      <td>Data</td>
      <td>&nbsp;</td>
    </tr>
  </tbody>
</table>
```

### Special Characters

Escape special HTML characters:

| Character | HTML Entity |
| --------- | ----------- |
| `<`       | `&lt;`      |
| `>`       | `&gt;`      |
| `&`       | `&amp;`     |
| `"`       | `&quot;`    |
| `'`       | `&apos;`    |

**Example:**

```html
<table>
  <tbody>
    <tr>
      <td>x &lt; 5</td>
      <td>x &gt; 10</td>
      <td>A &amp; B</td>
    </tr>
  </tbody>
</table>
```

## Conversion Algorithm

### Step-by-Step Process

1. **Parse markdown table**: Split by lines and pipes (`|`)
2. **Extract headers**: First row after trimming spaces
3. **Detect alignment**: Parse separator row (`:----:`, `:----`, `----:`)
4. **Extract data rows**: All rows after separator
5. **Process cell content**: Convert inline markdown to HTML
6. **Build HTML structure**: Create `<table>`, `<thead>`, `<tbody>` elements
7. **Apply alignment**: Add `style` attributes where needed
8. **Generate output**: Format with proper indentation

### Detection Pattern

**Markdown table pattern:**

```regex
^\|(.+)\|$
```

**Alignment detection:**

```python
def detect_alignment(separator):
    """Detect column alignment from separator row."""
    if separator.startswith(':') and separator.endswith(':'):
        return 'center'
    elif separator.endswith(':'):
        return 'right'
    else:
        return 'left'
```

## Implementation Example (Python)

```python
import re

def convert_table_to_html(markdown_text):
    """Convert markdown table to HTML."""
    lines = [line.strip() for line in markdown_text.split('\n') if line.strip()]

    if len(lines) < 2:
        return markdown_text  # Not a valid table

    # Parse header
    header_cells = [cell.strip() for cell in lines[0].split('|')[1:-1]]

    # Parse alignment
    separator = lines[1]
    alignments = []
    for cell in separator.split('|')[1:-1]:
        cell = cell.strip()
        if cell.startswith(':') and cell.endswith(':'):
            alignments.append('center')
        elif cell.endswith(':'):
            alignments.append('right')
        else:
            alignments.append('left')

    # Parse data rows
    data_rows = []
    for line in lines[2:]:
        cells = [cell.strip() for cell in line.split('|')[1:-1]]
        data_rows.append(cells)

    # Build HTML
    html = ['<table>', '  <thead>', '    <tr>']

    for i, header in enumerate(header_cells):
        align = alignments[i] if i < len(alignments) else 'left'
        if align != 'left':
            html.append(f'      <th style="text-align: {align};">{header}</th>')
        else:
            html.append(f'      <th>{header}</th>')

    html.extend(['    </tr>', '  </thead>', '  <tbody>'])

    for row in data_rows:
        html.append('    <tr>')
        for i, cell in enumerate(row):
            align = alignments[i] if i < len(alignments) else 'left'
            cell_html = process_inline_markdown(cell)
            if align != 'left':
                html.append(f'      <td style="text-align: {align};">{cell_html}</td>')
            else:
                html.append(f'      <td>{cell_html}</td>')
        html.append('    </tr>')

    html.extend(['  </tbody>', '</table>'])

    return '\n'.join(html)

def process_inline_markdown(text):
    """Convert inline markdown to HTML."""
    # Bold: **text** or __text__
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)

    # Italic: *text* or _text_
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)

    # Code: `code`
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)

    # Links: [text](url)
    text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', text)

    return text
```

## Verification After Upload

### Checklist

After uploading a table to Quip, verify:

- [ ] All rows present
- [ ] All columns present
- [ ] Cell data in correct positions
- [ ] No data loss or corruption
- [ ] Alignment applied correctly
- [ ] Rich content (links, formatting) preserved
- [ ] Empty cells handled correctly

### Common Issues

| Issue                | Cause                      | Solution                          |
| -------------------- | -------------------------- | --------------------------------- |
| Missing cells        | Incorrect pipe parsing     | Recount columns, add empty `<td>` |
| Data in wrong column | Alignment mismatch         | Verify column count in each row   |
| Lost formatting      | Escaped HTML not processed | Convert inline markdown           |
| Extra whitespace     | Padding not trimmed        | Trim cell content                 |
| Broken links         | URL encoding issues        | Encode special characters         |

## When to Use HTML vs Markdown

| Scenario                      | Use HTML | Use Markdown |
| ----------------------------- | -------- | ------------ |
| Data corruption on upload     | ✅ Yes   | ❌ No        |
| Complex cell content          | ✅ Yes   | Optional     |
| Nested elements (lists, code) | ✅ Yes   | ❌ No        |
| Custom alignment              | ✅ Yes   | Optional     |
| Simple table, no issues       | Optional | ✅ Yes       |
| Large tables (50+ rows)       | ✅ Yes   | Optional     |

## Advanced Features

### Merged Cells (Colspan/Rowspan)

HTML supports merged cells (not available in markdown):

```html
<table>
  <tbody>
    <tr>
      <td colspan="2">Merged across 2 columns</td>
      <td>Regular cell</td>
    </tr>
    <tr>
      <td rowspan="2">Merged across 2 rows</td>
      <td>Cell 1</td>
      <td>Cell 2</td>
    </tr>
    <tr>
      <td>Cell 3</td>
      <td>Cell 4</td>
    </tr>
  </tbody>
</table>
```

### Table with Caption

```html
<table>
  <caption>
    Table 1: Sample Data
  </caption>
  <thead>
    <tr>
      <th>Column 1</th>
      <th>Column 2</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Data 1</td>
      <td>Data 2</td>
    </tr>
  </tbody>
</table>
```

### Styled Tables

Add CSS classes for consistent styling:

```html
<table class="quip-table">
  <thead>
    <tr class="header-row">
      <th>Header 1</th>
      <th>Header 2</th>
    </tr>
  </thead>
  <tbody>
    <tr class="data-row">
      <td>Data 1</td>
      <td>Data 2</td>
    </tr>
  </tbody>
</table>
```

## Summary

- Convert to HTML when markdown tables fail verification
- Preserve all cell data and structure
- Apply alignment using inline styles
- Process inline markdown (bold, italic, code, links)
- Escape special HTML characters
- Verify table after upload to Quip
- Use HTML for complex tables with nested content
