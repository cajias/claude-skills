---
name: ai-writing-fixer
description: |
  Fix AI writing patterns in text. Use when:
  (1) ai-writing-analyzer found issues to fix,
  (2) need to humanize AI-generated content,
  (3) preparing content for publication,
  (4) iteratively refining text until clean.
author: cajias
version: 1.0.0
date: 2025-01-27
tags: [writing, ai-detection, humanization, editing]
---

# AI Writing Fixer

Fix detected AI writing patterns. Run `ai-writing-analyzer` first to identify issues.

## Prerequisites

1. Analysis results from `ai-writing-analyzer`
2. Access to pattern database in `../ai-writing-humanizer/patterns/patterns.json`

## Quick Fix

```bash
# Interactive mode - review each change
humanize_text --mode interactive input.md

# Batch mode - auto-fix high-confidence issues
humanize_text --mode batch input.md

# Fix specific categories only
humanize_text --categories "buzzwords,filler-phrases" input.md
```

## Fix Strategies by Category

### Critical Priority

**Chatbot Artifacts** → Delete entirely
- "I hope this helps" → (delete)
- "As an AI language model" → (delete)
- "Feel free to ask" → (delete)

### High Priority

**Buzzwords** → Simplify
| Original | Replacement |
|----------|-------------|
| leverage | use |
| utilize | use |
| facilitate | help, enable |
| implement | build, create |
| delve into | examine, explore |
| cutting-edge | modern, current |
| ecosystem | system, environment |
| synergy | cooperation |

**Inflated Symbolism** → Deflate
| Original | Replacement |
|----------|-------------|
| stands as a testament | shows, demonstrates |
| plays a vital role | is important for |
| watershed moment | turning point |
| cornerstone of | foundation of, basis for |

**Promotional Language** → Neutralize
| Original | Replacement |
|----------|-------------|
| revolutionary | significant, notable |
| breathtaking | impressive |
| game-changing | important |
| unparalleled | excellent, strong |

**Editorializing** → Delete
- "It's important to note that" → (delete)
- "Worth mentioning is that" → (delete)
- "Interestingly," → (delete)

### Medium Priority

**Negative Parallelism** → Direct statement
- "It's not just X, but Y" → "It is both X and Y" or just "Y"
- "Not only X, but also Y" → "X and Y"

**Participle Endings** → Trim or restructure
- ", ensuring quality" → (delete or new sentence)
- ", highlighting its importance" → (delete)

**Filler Phrases** → Delete entirely
- "In today's ever-evolving world" → (delete)
- "In the realm of" → (delete)
- "When it comes to" → (delete)

### Low Priority

**Em Dash Overuse** → Replace with commas or periods
**Hedge Words** → Remove or be specific
**Transition Overuse** → Remove redundant connectors

## Iterative Workflow

```
┌─────────────────┐
│ Analyze Text    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Issues Found?   │──No──▶ Done (Clean)
└────────┬────────┘
         │ Yes
         ▼
┌─────────────────┐
│ Generate Fixes  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Apply Changes   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Iteration < 5?  │──No──▶ Done (Max iterations)
└────────┬────────┘
         │ Yes
         └──────────▶ (loop back to Analyze)
```

## Modes

### Interactive Mode
- Present each issue for review
- Options: [A]ccept, [E]dit, [S]kip, [Q]uit
- Maximum control, slower

### Batch Mode
- Auto-apply high-confidence fixes
- Skip low-confidence changes
- Present summary at end

### Report-Only Mode
- Show what would change
- No modifications made
- Good for preview

## Confidence Levels

| Confidence | Auto-apply? | Examples |
|------------|-------------|----------|
| High | Yes | Simple word swaps, deletions |
| Medium | Review | Phrase restructuring |
| Low | Skip | Complex rewrites |

## Change Application Order

Apply changes from end to beginning to preserve positions:

1. Sort issues by position (reverse)
2. Apply each fix
3. Verify grammar after change
4. Log before/after

## Verification

After all iterations:

1. **Pattern check** - Re-scan for remaining issues
2. **Grammar check** - No errors introduced
3. **Meaning check** - Original intent preserved
4. **Coherence check** - Text flows naturally

## Output

```markdown
## Humanization Report

**Status:** Clean after 3 iterations
**Changes Made:** 15

### Summary
| Category | Fixed |
|----------|-------|
| Chatbot Artifacts | 1 |
| Buzzwords | 6 |
| Inflated Symbolism | 3 |
| Participle Endings | 2 |
| Filler Phrases | 1 |
| Editorializing | 2 |

### Before/After Excerpt
**Before:** "In today's ever-evolving world, the platform stands as a testament to innovation, leveraging cutting-edge technology."

**After:** "The platform demonstrates innovation using modern technology."
```

## See Also

- `ai-writing-analyzer` - Detection without fixes
- `ai-writing-humanizer` - Full reference implementation
