# List Converter - Markdown to HTML

This document provides the rules and patterns for converting markdown lists to HTML format for
Quip upload.

## Why Convert Lists to HTML?

Quip's markdown parser often fails to render numbered lists correctly, showing literal `1.` `2.`
characters as plain text instead of formatted lists. Converting to HTML before upload ensures
reliable rendering.

## Bullet List Conversion

### Simple Bullet Lists

Bullet lists usually work in markdown, but HTML provides more reliability.

**Markdown:**

```markdown
- First item
- Second item
- Third item
```

**HTML:**

```html
<ul>
  <li>First item</li>
  <li>Second item</li>
  <li>Third item</li>
</ul>
```

### Nested Bullet Lists

**Markdown:**

```markdown
- First item
  - Nested item 1
  - Nested item 2
- Second item
```

**HTML:**

```html
<ul>
  <li>
    First item
    <ul>
      <li>Nested item 1</li>
      <li>Nested item 2</li>
    </ul>
  </li>
  <li>Second item</li>
</ul>
```

## Numbered List Conversion (CRITICAL)

Numbered lists MUST be converted to HTML to prevent rendering failures.

### Simple Numbered Lists

**Markdown:**

```markdown
1. First item
2. Second item
3. Third item
```

**HTML (REQUIRED):**

```html
<ol>
  <li>First item</li>
  <li>Second item</li>
  <li>Third item</li>
</ol>
```

### Nested Numbered Lists

**Markdown:**

```markdown
1. First item
   1. Nested first
   2. Nested second
2. Second item
```

**HTML (REQUIRED):**

```html
<ol>
  <li>
    First item
    <ol>
      <li>Nested first</li>
      <li>Nested second</li>
    </ol>
  </li>
  <li>Second item</li>
</ol>
```

### Numbered Lists with Custom Start

**Markdown:**

```markdown
5. Fifth item
6. Sixth item
7. Seventh item
```

**HTML:**

```html
<ol start="5">
  <li>Fifth item</li>
  <li>Sixth item</li>
  <li>Seventh item</li>
</ol>
```

## Mixed List Conversion

### Bullets Inside Numbered Lists

**Markdown:**

```markdown
1. First numbered item
   - Bullet A
   - Bullet B
2. Second numbered item
```

**HTML (REQUIRED):**

```html
<ol>
  <li>
    First numbered item
    <ul>
      <li>Bullet A</li>
      <li>Bullet B</li>
    </ul>
  </li>
  <li>Second numbered item</li>
</ol>
```

### Numbers Inside Bullet Lists

**Markdown:**

```markdown
- First bullet
  1. Numbered A
  2. Numbered B
- Second bullet
```

**HTML:**

```html
<ul>
  <li>
    First bullet
    <ol>
      <li>Numbered A</li>
      <li>Numbered B</li>
    </ol>
  </li>
  <li>Second bullet</li>
</ul>
```

### Complex Mixed Nesting

**Markdown:**

```markdown
1. Level 1 numbered
   - Level 2 bullet
     1. Level 3 numbered
     2. Level 3 numbered
   - Level 2 bullet
2. Level 1 numbered
```

**HTML:**

```html
<ol>
  <li>
    Level 1 numbered
    <ul>
      <li>
        Level 2 bullet
        <ol>
          <li>Level 3 numbered</li>
          <li>Level 3 numbered</li>
        </ol>
      </li>
      <li>Level 2 bullet</li>
    </ul>
  </li>
  <li>Level 1 numbered</li>
</ol>
```

## Lists with Rich Content

### Lists with Code Blocks

**Markdown:**

```markdown
1. First item with code:
   (code block in python)
   print("Hello")

1. Second item
```

**HTML:**

```html
<ol>
  <li>
    First item with code:
    <pre><code class="language-python">print("Hello")</code></pre>
  </li>
  <li>Second item</li>
</ol>
```

### Lists with Multiple Paragraphs

**Markdown:**

```markdown
1. First item with paragraph

   This is a continuation paragraph.

2. Second item
```

**HTML:**

```html
<ol>
  <li>
    <p>First item with paragraph</p>
    <p>This is a continuation paragraph.</p>
  </li>
  <li>Second item</li>
</ol>
```

### Lists with Links

**Markdown:**

```markdown
1. Check [documentation](https://example.com)
2. Review [API reference](https://api.example.com)
```

**HTML:**

```html
<ol>
  <li>Check <a href="https://example.com">documentation</a></li>
  <li>Review <a href="https://api.example.com">API reference</a></li>
</ol>
```

### Lists with Bold/Italic

**Markdown:**

```markdown
1. **Important** item
2. _Emphasized_ item
3. **_Bold and italic_** item
```

**HTML:**

```html
<ol>
  <li><strong>Important</strong> item</li>
  <li><em>Emphasized</em> item</li>
  <li>
    <strong><em>Bold and italic</em></strong> item
  </li>
</ol>
```

## Conversion Algorithm

### Step-by-Step Process

1. **Identify list type**: Numbered (starts with `\d+\.`) or bullet (starts with `-` or `*`)
2. **Determine nesting level**: Count leading spaces (usually 2-4 spaces per level)
3. **Parse list items**: Extract text content for each item
4. **Handle rich content**: Process inline formatting, links, code blocks
5. **Build HTML structure**: Create nested `<ol>` or `<ul>` elements
6. **Generate output**: Format with proper indentation

### Detection Patterns

**Numbered list pattern:**

```regex
^\s*(\d+)\.\s+(.+)$
```

**Bullet list pattern:**

```regex
^\s*[-*]\s+(.+)$
```

**Nesting level calculation:**

```python
def get_nesting_level(line):
    leading_spaces = len(line) - len(line.lstrip())
    return leading_spaces // 2  # Assuming 2 spaces per indent level
```

## Implementation Example (Python)

```python
import re

def convert_list_to_html(markdown_text):
    """Convert markdown list to HTML."""
    lines = markdown_text.split('\n')
    html_lines = []
    stack = []  # Track open tags

    for line in lines:
        # Skip empty lines
        if not line.strip():
            continue

        # Detect numbered list
        numbered_match = re.match(r'^(\s*)(\d+)\.\s+(.+)$', line)
        if numbered_match:
            indent, num, content = numbered_match.groups()
            level = len(indent) // 2

            # Close/open tags as needed
            while len(stack) > level:
                tag = stack.pop()
                html_lines.append('  ' * len(stack) + f'</{tag}>')

            if not stack or stack[-1] != 'ol':
                html_lines.append('  ' * level + '<ol>')
                stack.append('ol')

            html_lines.append('  ' * level + f'  <li>{content}</li>')
            continue

        # Detect bullet list
        bullet_match = re.match(r'^(\s*)[-*]\s+(.+)$', line)
        if bullet_match:
            indent, content = bullet_match.groups()
            level = len(indent) // 2

            # Close/open tags as needed
            while len(stack) > level:
                tag = stack.pop()
                html_lines.append('  ' * len(stack) + f'</{tag}>')

            if not stack or stack[-1] != 'ul':
                html_lines.append('  ' * level + '<ul>')
                stack.append('ul')

            html_lines.append('  ' * level + f'  <li>{content}</li>')

    # Close remaining tags
    while stack:
        tag = stack.pop()
        html_lines.append('  ' * len(stack) + f'</{tag}>')

    return '\n'.join(html_lines)
```

## Testing Conversion

### Verification Checklist

After converting to HTML, verify:

- [ ] All list items are present
- [ ] Nesting structure is correct
- [ ] Rich content (links, formatting) is preserved
- [ ] No extra whitespace or line breaks
- [ ] Opening and closing tags are balanced
- [ ] Indentation is consistent

### Common Mistakes to Avoid

1. **Forgetting to close nested tags**: Always close inner lists before closing outer lists
2. **Incorrect nesting level**: Count spaces carefully
3. **Missing list items**: Don't skip items when parsing
4. **Broken rich content**: Preserve inline HTML and markdown
5. **Inconsistent indentation**: Use 2 spaces per level consistently

## When to Use HTML vs Markdown

| Scenario                  | Use HTML | Use Markdown |
| ------------------------- | -------- | ------------ |
| Numbered lists            | ✅ Yes   | ❌ No        |
| Nested numbered lists     | ✅ Yes   | ❌ No        |
| Mixed lists               | ✅ Yes   | ❌ No        |
| Simple bullet lists       | Optional | ✅ Yes       |
| Lists with code blocks    | ✅ Yes   | Optional     |
| Lists with paragraphs     | ✅ Yes   | Optional     |
| Simple content, no issues | Optional | ✅ Yes       |

## Summary

- **Always convert numbered lists to HTML** to prevent rendering failures
- Bullet lists can stay as markdown, but HTML is more reliable
- Preserve rich content (links, formatting, code) during conversion
- Test the conversion before uploading to Quip
- Verify the rendered output matches expectations
