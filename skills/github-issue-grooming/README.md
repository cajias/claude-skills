# GitHub Issue Grooming Skill

Automate the complete workflow for organizing and structuring GitHub issues with proper relationships, milestones, and clean labeling.

## Overview

This skill enables Claude to perform comprehensive GitHub issue management, including:

- **Milestone Creation**: Automatically create phase-based milestones from issue descriptions
- **Native Relationships**: Set up GitHub's native "blocked by" and "blocks" relationships using GraphQL API
- **Milestone Assignment**: Assign issues to appropriate milestones based on phase information
- **Label Cleanup**: Remove redundant labels that duplicate milestone or relationship functionality
- **Dependency Tracking**: Add tasklist checkboxes for tracking dependencies in issue bodies

## When to Use

Use this skill when you need to:

- Organize a new project with multiple phases
- Set up issue dependencies for an existing project
- Clean up legacy label-based tracking in favor of native GitHub features
- Migrate from comment-based relationships to native GitHub relationships
- Establish clear project structure with milestones and dependencies

## Prerequisites

- GitHub CLI (`gh`) installed and authenticated
- Repository access with admin or write permissions
- Issues already created with dependency information in their descriptions

## Key Features

### 1. Native GitHub Relationships

Uses GitHub's GraphQL API to set true issue relationships:
- `addBlockedBy` mutations for dependency tracking
- Bidirectional, automatically synchronized relationships
- Visible in GitHub UI and project boards

### 2. Phase-Based Organization

Automatically creates milestones from phase information:
- Extracts phase structure from epic/parent issues
- Creates appropriately named milestones
- Assigns all issues to correct milestones

### 3. Concurrent Processing

Uses sub-agents to work on multiple phases in parallel:
- Faster processing of large issue sets
- Independent phase updates
- Scalable to repositories with 100+ issues

## Limitations

- Requires issues to have dependency information in descriptions
- GitHub GraphQL API rate limits apply
- Only works with public or accessible private repositories
- Cannot set cross-repository relationships

## Related Tools

- GitHub CLI (`gh`)
- GitHub GraphQL API
- GitHub Projects (for visualization)

## Success Metrics

After running this skill, your repository will have:

✓ Clear milestone structure matching project phases
✓ Native GitHub relationships between all dependent issues
✓ Clean label set without redundant phase/dependency labels
✓ Dependency tracking visible in GitHub UI
✓ Complete project structure ready for project boards
