# Common Issues and Troubleshooting

This guide covers common problems encountered when transferring markdown to Quip and their
solutions.

## Issue 1: Numbered Lists Render as Plain Text

### Symptoms

- Lists show literal "1.", "2.", "3." as text
- Numbers are not formatted as actual list items
- Indentation is lost

### Example

**Expected**:

1. First item
2. Second item
3. Third item

**Actual (in Quip)**:

```text
1. First item
2. Second item
3. Third item
```

### Cause

Quip's markdown parser fails to recognize numbered list syntax during bulk uploads.

### Solution

Convert numbered lists to HTML before uploading:

```html
<ol>
  <li>First item</li>
  <li>Second item</li>
  <li>Third item</li>
</ol>
```

### Prevention

**Always pre-process numbered lists** before upload. Never upload markdown numbered lists directly.

## Issue 2: Table Data Corruption

### Symptoms

- Cell values appear in wrong columns
- Empty cells where data should be
- Rows or columns missing
- Data duplicated across cells

### Example

**Original Markdown**:

| Name  | Age | City     |
| ----- | --- | -------- |
| Alice | 30  | New York |
| Bob   | 25  | Boston   |

**Actual (in Quip)**:

| Name  | Age      | City |
| ----- | -------- | ---- |
| Alice | New York |      |
| Bob   | 25       |      |

### Cause

Quip's table parser can misinterpret cell boundaries, especially with:

- Special characters in cells
- Long cell content
- Uneven column widths
- Complex formatting in cells

### Solution

1. **First attempt**: Re-upload with cleaner formatting
2. **If still fails**: Convert table to HTML

```html
<table>
  <thead>
    <tr>
      <th>Name</th>
      <th>Age</th>
      <th>City</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Alice</td>
      <td>30</td>
      <td>New York</td>
    </tr>
    <tr>
      <td>Bob</td>
      <td>25</td>
      <td>Boston</td>
    </tr>
  </tbody>
</table>
```

### Prevention

- Verify tables immediately after upload
- Use HTML for complex tables
- Keep cell content simple when possible

## Issue 3: API Authentication Fails

### Symptoms

- HTTP 401 Unauthorized
- Error: "Invalid token"
- Cannot access document

### Cause

- Token expired
- Token doesn't have required permissions
- Token not properly set in environment

### Solution

1. **Verify token is valid**:

   ```bash
   curl -H "Authorization: Bearer $QUIP_API_TOKEN" \
     https://platform.quip.com/1/users/current
   ```

2. **Get new token**: Visit <https://quip.com/dev/token>

3. **Check permissions**: Ensure token has document edit access

4. **Set environment variable**:

   ```bash
   export QUIP_API_TOKEN="your-new-token-here"
   ```

### Prevention

- Check token before starting transfer
- Keep token secure and don't commit to source control
- Set token expiration reminders

## Issue 4: Rate Limiting

### Symptoms

- HTTP 429 Too Many Requests
- Uploads fail after several sections
- "Rate limit exceeded" error

### Cause

Quip API rate limits (typically 300 requests/hour for free tier, 600/hour for paid).

### Solution

1. **Wait before retrying**:

   ```bash
   sleep 60  # Wait 1 minute
   ```

2. **Reduce upload frequency**: Add delays between sections

   ```python
   import time
   time.sleep(5)  # 5 seconds between uploads
   ```

3. **Batch content**: Combine smaller sections to reduce API calls

### Prevention

- Add delays between section uploads (3-5 seconds)
- Monitor rate limit headers in API responses
- Upgrade to paid Quip plan for higher limits

## Issue 5: Content Too Large (413 Error)

### Symptoms

- HTTP 413 Payload Too Large
- Section upload fails
- Large sections don't appear

### Cause

Quip has payload size limits (typically ~100 KB per request).

### Solution

1. **Split section into smaller chunks**:

   ```python
   def split_section(content, max_size=50000):
       # Split by paragraphs
       paragraphs = content.split('\n\n')
       chunks = []
       current_chunk = ""

       for para in paragraphs:
           if len(current_chunk) + len(para) < max_size:
               current_chunk += para + "\n\n"
           else:
               chunks.append(current_chunk)
               current_chunk = para + "\n\n"

       if current_chunk:
           chunks.append(current_chunk)

       return chunks
   ```

2. **Upload chunks sequentially**:

   ```bash
   for chunk in chunks:
       upload_to_quip(chunk)
       sleep 3
   ```

### Prevention

- Keep sections under 50 KB when possible
- Split large sections at logical boundaries
- Test with smaller content first

## Issue 6: Nested Lists Don't Render Correctly

### Symptoms

- Nested items appear at wrong indent level
- List structure flattened
- Bullet/number types wrong for nested levels

### Example

**Expected**:

1. First level
   - Second level bullet
   - Second level bullet
2. First level

**Actual (in Quip)**:

1. First level
2. Second level bullet
3. Second level bullet
4. First level

### Cause

Incorrect HTML structure or indentation parsing failure.

### Solution

Ensure proper nested HTML:

```html
<ol>
  <li>
    First level
    <ul>
      <li>Second level bullet</li>
      <li>Second level bullet</li>
    </ul>
  </li>
  <li>First level</li>
</ol>
```

**Key points**:

- Nested list goes INSIDE parent `<li>`, not after it
- Close inner list before closing parent `<li>`
- Don't put `<li>` tags at wrong nesting level

### Prevention

- Test nested list conversion before bulk upload
- Validate HTML structure
- Use consistent indentation in HTML

## Issue 7: Code Blocks Lose Formatting

### Symptoms

- Code appears as plain text
- Indentation lost
- Syntax highlighting missing
- Special characters escaped (e.g., `&lt;` instead of `<`)

### Cause

- Markdown code fence not recognized
- HTML escaping applied incorrectly
- Language identifier missing

### Solution

1. **Use proper markdown fences with language**:

   ````markdown
   ```python
   def hello():
       print("Hello, World!")
   ```
   ````

2. **If markdown fails, use HTML**:

   ```html
   <pre><code class="language-python">
   def hello():
       print("Hello, World!")
   </code></pre>
   ```

3. **For inline code**, use `<code>` tags:

   ```html
   Use <code>print()</code> to output text.
   ```

### Prevention

- Always specify language for code blocks
- Test code blocks in small section first
- Avoid special characters if possible

## Issue 8: Links Don't Work

### Symptoms

- Links appear as plain text
- Links not clickable
- URLs broken or incomplete

### Example

**Expected**: [Click here](https://example.com)

**Actual**: \[Click here\](<https://example.com>)

### Cause

- Markdown link syntax not parsed
- URLs with special characters
- Nested formatting breaks link

### Solution

1. **Use HTML links**:

   ```html
   <a href="https://example.com">Click here</a>
   ```

2. **Encode special characters in URLs**:

   ```html
   <a href="https://example.com/path?param=value&amp;other=123">Link</a>
   ```

3. **Avoid nesting formatting**:

   ```html
   <!-- Bad -->
   <a href="url">**Bold text**</a>

   <!-- Good -->
   <strong><a href="url">Bold text</a></strong>
   ```

### Prevention

- Test links after upload
- Use simple URLs when possible
- Encode special characters

## Issue 9: Images Upload Instead of Placeholder

### Symptoms

- Image upload attempted but fails
- Broken image links in document
- Missing image placeholders

### Cause

Markdown image syntax processed as actual image, but API doesn't support image upload.

### Solution

**Replace image syntax BEFORE upload**:

```markdown
<!-- Before -->

![Alt text](./images/photo.png)

<!-- After -->

[TODO: INSERT IMAGE]
Name: photo.png
Alt text: Alt text
Original path: ./images/photo.png
```

### Prevention

- Always pre-process images before upload
- Never include image markdown in uploads
- Create image upload checklist

## Issue 10: Special Characters Render Incorrectly

### Symptoms

- Characters display as `�` or other garbage
- Accented characters broken
- Unicode symbols wrong

### Example

**Expected**: "Smart quotes" and emoji 🎉

**Actual**: "Smart quotes" and emoji ?

### Cause

- Encoding mismatch
- Unicode not supported
- Character escaping issues

### Solution

1. **Ensure UTF-8 encoding**:

   ```bash
   file -I document.md  # Check encoding
   iconv -f ISO-8859-1 -t UTF-8 document.md > document-utf8.md
   ```

2. **Use HTML entities for special characters**:

   ```html
   &ldquo;Smart quotes&rdquo; &mdash; em dash
   ```

3. **Test with simple ASCII first**, then add special characters

### Prevention

- Use UTF-8 encoding from the start
- Test special characters in small section
- Consider HTML entities for critical characters

## Issue 11: Sections Appear Out of Order

### Symptoms

- Sections uploaded in wrong order
- Document structure broken
- Headers appear after content

### Cause

- Asynchronous upload without waiting
- API processing delay
- Upload order not sequential

### Solution

1. **Upload sequentially, not in parallel**:

   ```python
   for section in sections:
       upload_section(section)
       time.sleep(3)  # Wait for processing
   ```

2. **Verify section before proceeding**:

   ```python
   upload_section(section)
   time.sleep(3)
   if verify_section(section):
       continue
   else:
       retry_upload(section)
   ```

### Prevention

- Always upload sections in order
- Wait between uploads
- Verify before proceeding

## Issue 12: Verification Failures

### Symptoms

- Can't verify uploaded content
- API returns stale data
- Changes not visible immediately

### Cause

Quip caching or processing delay.

### Solution

1. **Wait longer before verification**:

   ```python
   upload_section(content)
   time.sleep(5)  # Increased wait time
   verify_section()
   ```

2. **Add cache-busting to API calls**:

   ```bash
   curl "https://platform.quip.com/1/threads/$ID?t=$(date +%s)"
   ```

3. **Verify in Quip UI** if API verification fails

### Prevention

- Allow adequate processing time (3-5 seconds minimum)
- Use Quip UI for final verification
- Don't rely solely on immediate API verification

## Quick Troubleshooting Checklist

When something goes wrong:

- [ ] Check API token is valid
- [ ] Verify not hitting rate limits
- [ ] Ensure content size under limits
- [ ] Confirm numbered lists converted to HTML
- [ ] Verify images replaced with placeholders
- [ ] Check for special characters needing escaping
- [ ] Ensure sequential upload with delays
- [ ] Test with smaller section first
- [ ] Review API response for error details
- [ ] Check Quip UI to see actual rendering

## Getting Help

If issues persist:

1. **Check Quip API documentation**: <https://quip.com/dev/automation/documentation>
2. **Review API response errors**: Look for specific error codes
3. **Test with minimal example**: Isolate the problem
4. **Compare working vs failing content**: Find patterns
5. **Contact Quip support**: For API-specific issues

## Summary

Most common issues:

1. ⭐ **Numbered lists** → Always convert to HTML
2. ⭐ **Tables** → Verify and convert to HTML if needed
3. ⭐ **Authentication** → Check token validity
4. **Rate limits** → Add delays between uploads
5. **Large content** → Split into smaller chunks

**Prevention is key**: Pre-process content, upload sequentially, verify each section, fix issues
before proceeding.
