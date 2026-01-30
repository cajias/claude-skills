---
name: ztagfix
description: Interactive tag remediation workflow for consolidating orphan tags, fixing safety redundancy, and pruning over-tagged notes
---

# /ztagfix - Tag Remediation

Interactive workflow to fix tag issues identified by `/ztagaudit`.

## Usage

```
/ztagfix                      # Full remediation workflow
/ztagfix safety               # Just safety tag consolidation
/ztagfix orphans              # Just orphan tag consolidation
/ztagfix prune                # Just over-tagged notes pruning
```

## Workflow Steps

### Step 1: Run Audit

First, run `/ztagaudit` to generate current metrics. Review the report at `knowledge-base/.reports/tag-audit-{date}.md`.

### Step 2: Safety Tag Consolidation

Consolidate redundant safety-related tags:

```bash
# Preview changes
isengardcli run --account 806230523044 -- bash -c '
export OBSIDIAN_VAULT=/Users/cajias/Documents/obsidian-vault-work
zk-tag-consolidate --from guardrails,ai-risks --to safety --dry-run
'

# Apply after review
isengardcli run --account 806230523044 -- bash -c '
export OBSIDIAN_VAULT=/Users/cajias/Documents/obsidian-vault-work
zk-tag-consolidate --from guardrails,ai-risks --to safety
'
```

### Step 3: Orphan Tag Consolidation

Consolidate orphan tags to broader categories based on the tag taxonomy:

| Orphan Tags | Target | Command |
|-------------|--------|---------|
| `discipline`, `exit-criteria`, `planning`, `goals`, `tracking` | `methodology` | `zk-tag-consolidate -f discipline,exit-criteria,planning,goals,tracking -t methodology` |
| `cloudformation`, `cdk`, `deployment`, `devops` | `infrastructure` | `zk-tag-consolidate -f cloudformation,cdk,deployment,devops -t infrastructure` |
| `team-coordination`, `communication` | `workflows` | `zk-tag-consolidate -f team-coordination,communication -t workflows` |
| `adr` | `documentation` | `zk-tag-consolidate -f adr -t documentation` |
| `validation` | `testing` | `zk-tag-consolidate -f validation -t testing` |
| `secrets` | `security` | `zk-tag-consolidate -f secrets -t security` |
| `cost-management` | `monitoring` | `zk-tag-consolidate -f cost-management -t monitoring` |
| `debugging` | `code-quality` | `zk-tag-consolidate -f debugging -t code-quality` |

Run each with `--dry-run` first, then apply.

### Step 4: Prune Over-Tagged Notes

For notes with 7+ tags:

1. Review the over-tagged notes list from the audit
2. For each note, consider:
   - Is the primary categorization via hub assignment?
   - Are any tags redundant with the hub?
   - Are any tags too specific?
3. Manually edit each note to reduce to 4-6 tags

**Pruning principles:**
- Keep tags that enable cross-hub discovery
- Remove tags redundant with hub assignment
- Keep technology tags (e.g., `typescript`, `git`)
- Remove overly specific tags

### Step 5: Re-audit

Run `/ztagaudit` again to verify improvements.

### Step 6: Sync

Run `/zsync` to update S3 Vectors with tag changes.

## Tag Taxonomy Reference

See `[[hubs/tag-taxonomy|Tag Taxonomy]]` for:
- Approved tag categories
- Deprecated tags and their replacements
- Tagging guidelines

## Human Review Gates

**IMPORTANT**: This workflow includes human review at each step:

1. Review audit report before proceeding
2. Review `--dry-run` output before applying consolidation
3. Manually review over-tagged notes before pruning
4. Review final audit to confirm improvements

## Success Criteria

| Metric | Before | Target |
|--------|--------|--------|
| Orphan tags | ~37 | <10 |
| Unique tags | ~57 | 25-35 |
| Over-tagged notes | ~3 | 0 |
| Safety cluster tags | 3 | 1 |

## Related

- `/ztagaudit` - Generate tag health report
- `/ztagsuggest` - AI-assisted tag suggestions
- `[[hubs/tag-taxonomy|Tag Taxonomy]]` - Tag governance doc
