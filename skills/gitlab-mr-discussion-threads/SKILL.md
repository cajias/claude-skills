---
name: gitlab-mr-discussion-threads
description: |
  Reply to GitLab MR code review discussion threads using glab CLI. Use when:
  (1) need to respond to specific code review comments, (2) want threaded replies
  not top-level MR comments, (3) `glab mr note` only adds top-level comments.
  Covers: getting discussion IDs, replying to threads, deleting comments.
author: Claude Code
version: 1.0.0
date: 2026-01-27
---

# GitLab MR Discussion Thread Management

## Problem

When responding to MR code review feedback, you need to reply to specific discussion
threads (not add top-level comments). The `glab mr note` command only adds top-level
comments, not threaded replies to existing discussions.

## Context / Trigger Conditions

- Need to respond to code review comments on an MR
- Want replies to appear in the correct discussion thread
- Using `glab mr note` but comments appear at top level instead of threaded
- Need to manage (delete/edit) comments on discussion threads

## Solution

### 1. List Discussion Threads

Get all resolvable discussions with their IDs:

```bash
# Get unresolved discussions
glab api "projects/ENCODED_PROJECT_PATH/merge_requests/MR_NUMBER/discussions?per_page=100" \
  | jq '.[] | select(.notes[0].resolvable == true and .notes[0].resolved == false) | {disc_id: .id, note_id: .notes[0].id, body: .notes[0].body[0:60]}'

# Get all resolvable discussions (resolved and unresolved)
glab api "projects/ENCODED_PROJECT_PATH/merge_requests/MR_NUMBER/discussions?per_page=100" \
  | jq '.[] | select(.notes[0].resolvable == true) | {disc_id: .id, note_id: .notes[0].id, resolved: .notes[0].resolved}'
```

**Note:** Project path must be URL-encoded (e.g., `org/group/repo` → `org%2Fgroup%2Frepo`)

### 2. Reply to a Discussion Thread

Use the discussion ID to add a threaded reply:

```bash
glab api "projects/ENCODED_PROJECT_PATH/merge_requests/MR_NUMBER/discussions/DISCUSSION_ID/notes" \
  -X POST \
  -f "body=Your reply message here"
```

### 3. Delete a Comment

Delete a note by its ID:

```bash
glab api "projects/ENCODED_PROJECT_PATH/merge_requests/MR_NUMBER/notes/NOTE_ID" -X DELETE
```

### 4. Batch Operations

Delete multiple comments:

```bash
notes_to_delete=(123456 123457 123458)
for note_id in "${notes_to_delete[@]}"; do
  glab api "projects/ENCODED_PATH/merge_requests/MR/notes/${note_id}" -X DELETE && echo "Deleted $note_id"
done
```

### 5. Pagination

For MRs with many discussions (>100), paginate:

```bash
# Page 1
glab api "projects/PATH/merge_requests/MR/discussions?per_page=100&page=1"

# Page 2
glab api "projects/PATH/merge_requests/MR/discussions?per_page=100&page=2"
```

## Why `glab mr note` Doesn't Work for Threads

The `glab mr note` command only supports:

- Adding top-level comments to MRs
- No `--discussion-id` or `--reply-to` flag exists

For threaded replies, `glab api` is the only option.

## Verification

After posting a reply:

1. Visit the MR in GitLab UI
2. Navigate to the discussion thread
3. Verify your reply appears nested under the original comment

## Example

Reply to a code review comment about missing pagination:

```bash
# 1. Find the discussion ID
glab api "projects/my-org%2Fmy-repo/merge_requests/414/discussions?per_page=100" \
  | jq '.[] | select(.notes[0].body | contains("paginate"))'

# Output: { "id": "bb8314529ff79b8fa2e037b107a89d2cca06e2dc", ... }

# 2. Reply to that discussion
glab api "projects/my-org%2Fmy-repo/merge_requests/414/discussions/bb8314529ff79b8fa2e037b107a89d2cca06e2dc/notes" \
  -X POST \
  -f "body=Addressed - now paginates through all results using nextToken."
```

## Permission Configuration

To avoid repeated prompts, add to `~/.claude/settings.json`:

```json
{
  "permissions": {
    "allow": ["Bash(glab api*)"]
  }
}
```

## Notes

- Discussion IDs are long hex strings (e.g., `bb8314529ff79b8fa2e037b107a89d2cca06e2dc`)
- Note IDs are numeric (e.g., `878884`)
- System-generated notes (commits, assignments) cannot be deleted (403 Forbidden)
- Only your own comments can be deleted

## See Also

- `gitlab-ci-debugging` - For CI/CD pipeline issues
- `gitlab-group-exploration` - For exploring GitLab groups and projects
