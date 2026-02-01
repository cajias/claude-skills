---
name: gitlab-mr-inline-comments
description: Use when GitLab MR comments have position null, appear as DiscussionNote instead of DiffNote, or inline code review comments show as general MR comments. Also use when glab api nested object parameters are ignored.
---

# GitLab MR Inline Comments

## Overview

GitLab's API requires **nested JSON objects** for positioned comments. The `glab api` CLI
tool's `-f "position[key]=value"` syntax sends **flat keys** instead of nested objects,
causing GitLab to silently create `DiscussionNote` (general comment) instead of `DiffNote`
(inline comment).

## Quick Reference

| Symptom                                        | Cause                                         |
| ---------------------------------------------- | --------------------------------------------- |
| `type: DiscussionNote` instead of `DiffNote`   | Position data sent as flat keys               |
| `position: null` in response                   | GitLab rejected position silently             |
| Comment appears in MR thread, not on code line | Same as above                                 |
| 201 Created but wrong note type                | API accepts request, ignores invalid position |

## The Fix

Use `--input` with JSON file and `--header "Content-Type: application/json"`:

```bash
# Create JSON with properly nested position object
cat > /tmp/comment.json << 'EOF'
{
  "body": "Your comment text",
  "position": {
    "base_sha": "abc123...",
    "start_sha": "abc123...",
    "head_sha": "def456...",
    "position_type": "text",
    "old_path": "path/to/file",
    "new_path": "path/to/file",
    "new_line": 42
  }
}
EOF

# Post with proper content type
glab api "/projects/:id/merge_requests/:iid/discussions" \
  --method POST \
  --header "Content-Type: application/json" \
  --input /tmp/comment.json
```

## Position Field Rules

| Line Type          | Required Fields                |
| ------------------ | ------------------------------ |
| Added line (`+`)   | `new_line` only                |
| Removed line (`-`) | `old_line` only                |
| Context line (``)  | Both `old_line` AND `new_line` |

## Getting SHA Values

```bash
# Get diff_refs from MR
glab api "/projects/:id/merge_requests/:iid" | jq '.diff_refs'
# Returns: base_sha, head_sha, start_sha
```

## Why glab -f Fails

```bash
# This sends FLAT keys (WRONG):
glab api "..." -f "position[base_sha]=abc"
# Results in: {"position[base_sha]": "abc"}

# API expects NESTED object:
# {"position": {"base_sha": "abc"}}
```

## Verification

Success response has:

- `type: "DiffNote"` (not `DiscussionNote` or `null`)
- `position` object with your SHA values (not `null`)
