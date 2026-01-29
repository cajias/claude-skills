---
name: gitlab-group-exploration
description: |
  Explore GitLab groups, subgroups, and projects using glab CLI API commands. Use when:
  (1) Need to list all projects in a GitLab group/namespace,
  (2) WebFetch fails for private/internal GitLab instances like code.aws.dev,
  (3) Want to get project details (descriptions, URLs, activity) programmatically,
  (4) Need to check for subgroups within a group,
  (5) Working with enterprise GitLab instances that require authentication.
  Covers glab api usage with URL-encoded paths and custom hostnames.
author: Claude Code
version: 1.0.0
date: 2026-01-26
---

# GitLab Group Exploration via glab CLI

## Problem
When working with private/internal GitLab instances (like `code.aws.dev`), web fetching often fails due to authentication requirements. You need a way to programmatically explore groups, list projects, and get details.

## Context / Trigger Conditions
- User asks to explore a GitLab group URL like `https://code.aws.dev/group/subgroup/path`
- WebFetch is blocked or returns authentication errors
- Need to list all projects in a GitLab namespace
- Want project metadata (descriptions, activity dates, URLs)
- Working with non-gitlab.com instances

## Solution

### 1. List Projects in a Group
```bash
# URL-encode the group path (replace / with %2F)
glab api groups/GROUP%2FPATH%2FHERE/projects --hostname code.aws.dev
```

### 2. Get Detailed Project Info
```bash
glab api groups/proserve%2Fproduct-and-solutions%2Ftools/projects --hostname code.aws.dev | \
  jq -r '.[] | "## \(.name)\n- Path: \(.path_with_namespace)\n- URL: \(.web_url)\n- Description: \(.description // "None")\n- Last Activity: \(.last_activity_at)"'
```

### 3. Check for Subgroups
```bash
glab api groups/GROUP%2FPATH/subgroups --hostname code.aws.dev | jq '.'
```

### 4. Get Group Details
```bash
glab api groups/GROUP%2FPATH --hostname code.aws.dev | jq '{name, description, full_path, web_url, visibility}'
```

### 5. Get Group ID (for API operations)
```bash
glab api groups/GROUP%2FPATH --hostname code.aws.dev | jq -r '.id'
```

## Key Points

- **URL Encoding**: Replace `/` with `%2F` in group paths
- **Custom Hostname**: Use `--hostname` for non-gitlab.com instances
- **Authentication**: glab uses tokens configured via `glab auth login --hostname <host>`
- **jq Filtering**: Pipe to jq for readable output

## Common Fields Available
- `name`, `path`, `path_with_namespace`
- `description`, `web_url`
- `visibility` (public, internal, private)
- `created_at`, `last_activity_at`
- `star_count`, `forks_count`
- `default_branch`

## Verification
Run `glab api groups/YOUR%2FGROUP/projects --hostname your.gitlab.host` and verify JSON output with project details.

## Example

Exploring `https://code.aws.dev/proserve/product-and-solutions/tools`:

```bash
# List all projects
glab api groups/proserve%2Fproduct-and-solutions%2Ftools/projects \
  --hostname code.aws.dev | jq '.[].name'

# Output:
# "kiro-agents"
# "dev-insights"
# "doc-updater cli"
# "gitlab-ci-common"
```

## Notes
- If glab isn't authenticated, run: `glab auth login --hostname code.aws.dev`
- For large groups, the API may paginate results (check for `x-next-page` header)
- Group IDs are needed for some operations like updating group settings

## References
- [glab CLI Documentation](https://gitlab.com/gitlab-org/cli/-/tree/main/docs)
- [GitLab Groups API](https://docs.gitlab.com/ee/api/groups.html)
- [GitLab Projects API](https://docs.gitlab.com/ee/api/projects.html)
