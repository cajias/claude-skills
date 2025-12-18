# Validation Prompt Template

Use this prompt template to verify sections after uploading to Quip.

---

## Section Verification Prompt

```text
Please verify that section "[Section Title]" was uploaded correctly to Quip.

**Section Number**: [X] of [Y]
**Quip Document**: [document_id or URL]

**Verification Checklist**:

1. **Section Header**:
   - [ ] Header appears with correct text
   - [ ] Header level is correct (H2 for main sections)
   - [ ] Header formatting preserved

2. **Numbered Lists**:
   - [ ] All numbered lists render as actual numbered lists
   - [ ] No literal "1.", "2.", "3." text visible
   - [ ] Nesting preserved correctly
   - [ ] All items present and in correct order

3. **Bullet Lists**:
   - [ ] All bullet lists have actual bullet points
   - [ ] No literal "-" or "*" characters visible
   - [ ] Nesting preserved correctly
   - [ ] All items present

4. **Tables**:
   - [ ] Table structure intact
   - [ ] All rows present
   - [ ] All columns present
   - [ ] Cell data in correct positions
   - [ ] No data loss or corruption
   - [ ] Alignment applied correctly

5. **Code Blocks**:
   - [ ] Code blocks preserved
   - [ ] Syntax highlighting applied (if supported)
   - [ ] Indentation correct
   - [ ] No special character escaping issues

6. **Links**:
   - [ ] All links present
   - [ ] Link text correct
   - [ ] URLs correct
   - [ ] Links clickable

7. **Formatting**:
   - [ ] Bold text rendered correctly
   - [ ] Italic text rendered correctly
   - [ ] Inline code rendered correctly
   - [ ] No formatting artifacts

8. **Images/Diagrams**:
   - [ ] Placeholders present
   - [ ] Placeholder format correct
   - [ ] All information preserved

9. **Content Completeness**:
   - [ ] All paragraphs present
   - [ ] No text cut off
   - [ ] Spacing and layout reasonable
   - [ ] Special characters rendered correctly

**If any items FAIL, report**:
- Which item(s) failed
- Specific issue description
- Recommended fix strategy

**Proceed to next section only if all critical items PASS.**
```

---

## Quick Verification (Numbered Lists Only)

For faster verification when you trust bullet lists and tables:

```text
Quick verification for section "[Section Title]":

**Critical Check - Numbered Lists**:
- [ ] All numbered lists render as formatted lists (not "1.", "2.", etc.)
- [ ] Nested numbered lists work correctly
- [ ] Mixed lists (numbers + bullets) work correctly

**Status**: [PASS / FAIL]

If PASS, proceed to next section.
If FAIL, apply HTML conversion fix and re-upload.
```

## Table-Specific Verification

When section contains tables:

```text
Table verification for section "[Section Title]":

**Table [X] of [Y] in this section**:

Original table (from markdown):
[Show first 3 rows of source table]

Rendered table (in Quip):
[Show first 3 rows as they appear in Quip]

**Cell-by-cell comparison**:
- Row 1: [✓ / ✗ describe issue]
- Row 2: [✓ / ✗ describe issue]
- Row 3: [✓ / ✗ describe issue]
...

**Structural check**:
- [ ] Row count matches
- [ ] Column count matches
- [ ] No empty cells where data should be
- [ ] No data in wrong columns

**Status**: [PASS / NEEDS MANUAL FIX / CONVERT TO HTML]

If NEEDS MANUAL FIX: Flag for manual review
If CONVERT TO HTML: Apply HTML table conversion and re-upload
```

## List-Specific Verification

When section has complex list structures:

```text
List verification for section "[Section Title]":

**Numbered Lists**:
- List 1 (lines [X-Y]): [✓ / ✗]
- List 2 (lines [A-B]): [✓ / ✗]

**Bullet Lists**:
- List 1 (lines [P-Q]): [✓ / ✗]
- List 2 (lines [R-S]): [✓ / ✗]

**Nested Lists**:
- Nest level 1: [✓ / ✗]
- Nest level 2: [✓ / ✗]
- Nest level 3: [✓ / ✗]

**Mixed Lists**:
- Numbers inside bullets: [✓ / ✗]
- Bullets inside numbers: [✓ / ✗]

**Details on failures**:
[Describe any issues found]

**Fix applied**:
[Describe fix if auto-fixed]

**Status**: [PASS / FIXED / NEEDS MANUAL FIX]
```

## Content-Specific Verification

### For Technical Documentation

```text
Technical content verification for section "[Section Title]":

**Code Blocks**:
- [ ] All code blocks preserved
- [ ] Language tags correct
- [ ] No syntax breaking
- [ ] Indentation preserved

**API Endpoints**:
- [ ] All endpoints listed
- [ ] HTTP methods correct
- [ ] Parameters preserved

**Commands**:
- [ ] All commands intact
- [ ] Special characters not escaped incorrectly
- [ ] Copy-paste would work

**Status**: [PASS / FAIL]
```

### For Documentation with Images

```text
Image placeholder verification for section "[Section Title]":

**Images in this section**: [X]

Image 1:
- [ ] Placeholder present
- [ ] Filename correct
- [ ] Alt text preserved
- [ ] Path recorded

Image 2:
- [ ] Placeholder present
- [ ] Filename correct
- [ ] Alt text preserved
- [ ] Path recorded

...

**All images accounted for**: [YES / NO]
**Ready for manual upload**: [YES / NO]
```

## Batch Verification (Multiple Sections)

For verifying several sections at once:

```text
Batch verification for sections [X] through [Y]:

| Section | Title                | Lists | Tables | Images | Status |
| ------- | -------------------- | ----- | ------ | ------ | ------ |
| 1       | [Title]              | ✓     | ✓      | ✓      | PASS   |
| 2       | [Title]              | ✗     | ✓      | N/A    | FAIL   |
| 3       | [Title]              | ✓     | ✗      | ✓      | FAIL   |
| 4       | [Title]              | ✓     | ✓      | ✓      | PASS   |

**Sections requiring fixes**: [2, 3]

**Section 2 issue**: Numbered list rendered as plain text
**Section 2 fix**: Convert to HTML and re-upload

**Section 3 issue**: Table missing cells in column 3
**Section 3 fix**: Convert to HTML table

**Re-verification needed after fixes**: YES
```

## Final Document Verification

After all sections uploaded:

```text
Final document verification:

**Document Structure**:
- [ ] All sections present (expected: [X], found: [Y])
- [ ] Section order correct
- [ ] Table of contents accurate (if applicable)
- [ ] No duplicate sections
- [ ] No missing sections

**Content Quality**:
- [ ] All headers render correctly
- [ ] All lists render correctly
- [ ] All tables readable
- [ ] All links work
- [ ] All code blocks preserved
- [ ] All formatting intact

**Placeholders**:
- [ ] All image placeholders present
- [ ] All diagram placeholders present
- [ ] Manual task list complete

**Overall Document**:
- [ ] Readable end-to-end
- [ ] Professional appearance
- [ ] No obvious errors
- [ ] Ready for manual tasks (images, diagrams)

**Status**: [APPROVED / NEEDS REVIEW / HAS ISSUES]

**Issues found**: [None / List issues]

**Manual tasks ready**: [YES / NO / PARTIAL]
```

## Regression Verification

If re-uploading sections after fixes:

```text
Regression verification for section "[Section Title]" (attempt [N]):

**Previous issue**: [Describe what failed before]

**Fix applied**: [Describe fix]

**Re-verification**:
- [ ] Previous issue resolved
- [ ] No new issues introduced
- [ ] Content still complete
- [ ] Formatting still correct

**Comparison with previous attempt**:
- What changed: [Describe]
- What stayed the same: [Describe]
- Improvement: [YES / NO / PARTIAL]

**Status**: [PASS / FAIL / NEEDS ANOTHER FIX]

**Next action**:
[If PASS: Move to next section]
[If FAIL: Try alternative fix]
[If NEEDS ANOTHER FIX: Describe next approach]
```

## Red Flags to Watch For

These issues commonly indicate verification failure:

```text
**Red Flags Checklist**:

- [ ] Seeing literal "1." or "2." in what should be numbered lists
- [ ] Seeing literal "-" or "*" in what should be bullet lists
- [ ] Table has fewer rows than expected
- [ ] Table has fewer columns than expected
- [ ] Empty cells where data should be
- [ ] Data appears in wrong columns
- [ ] Links not clickable
- [ ] Code blocks showing escaped characters like &lt; or &gt;
- [ ] Headers not rendering as headers
- [ ] Text cut off mid-sentence
- [ ] Formatting completely lost
- [ ] Special characters displaying as � or other garbage

**If ANY red flags present**: FAIL verification and apply fix.
```

## Tips for Effective Verification

1. **Don't rush**: Take time to actually look at the rendered content
2. **Compare side-by-side**: Have source markdown open while checking Quip
3. **Focus on critical elements**: Numbered lists and tables fail most often
4. **Trust but verify**: Even simple sections can have issues
5. **Use checklist**: Don't skip items even if they seem obvious
6. **Document issues**: Note exactly what failed for fixing
7. **Test before proceeding**: Fix issues before moving to next section

## Verification Levels

### Level 1: Critical Only

- Numbered lists render correctly
- Tables structurally intact
- No obvious content loss

### Level 2: Standard (Recommended)

- All lists render correctly
- Tables have all data in correct positions
- Links work
- Code blocks preserved
- Images/diagrams have placeholders

### Level 3: Thorough

- Everything from Level 2, plus:
- Cell-by-cell table comparison
- Character-by-character code block check
- Click every link
- Verify every formatting element
- Check special characters render correctly

Choose level based on document importance and time available.
