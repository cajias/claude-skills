#!/usr/bin/env python3
"""
Claudeception - Skill Extraction Hook

Called on UserPromptSubmit to analyze recent conversation exchanges
for skill-worthy knowledge and create new SKILL.md files.

Instead of using heuristic pattern matching, this outputs an analysis prompt
for the LLM to decide what skills to extract. The LLM responds with JSON
containing skill data, which is then processed on subsequent invocations.

Environment Variables:
- CLAUDECEPTION_SKILLS_DIR: Where to save skills (default: ~/.claude/my-claude-skills/skills)
- CLAUDECEPTION_DRY_RUN: Set to "true" to skip file creation (for testing)
- CLAUDECEPTION_DEBUG: Set to "true" for verbose logging (default: true)
- CLAUDECEPTION_LOG_FILE: Log file path (default: ~/.claude/claudeception.log)
- CLAUDECEPTION_MAX_EXCHANGES: Number of recent exchanges to analyze (default: 5)

Input: Session JSON via stdin OR skill JSON from LLM
Output: Analysis prompt OR new SKILL.md files
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any


# Configuration
SKILLS_DIR = Path(os.environ.get('CLAUDECEPTION_SKILLS_DIR',
                                  os.path.expanduser('~/.claude/my-claude-skills/skills')))
DRY_RUN = os.environ.get('CLAUDECEPTION_DRY_RUN', 'false').lower() == 'true'
DEBUG = os.environ.get('CLAUDECEPTION_DEBUG', 'true').lower() == 'true'
LOG_FILE = Path(os.environ.get('CLAUDECEPTION_LOG_FILE',
                                os.path.expanduser('~/.claude/claudeception.log')))
MAX_EXCHANGES = int(os.environ.get('CLAUDECEPTION_MAX_EXCHANGES', '5'))


SKILL_TEMPLATE = '''---
name: {name}
description: |
  {description}
author: Claude Code (extracted by Claudeception)
version: 1.0.0
date: {date}
tags: {tags}
---

# {title}

## Problem / Use Case

{problem}

## When to Use This Skill

{triggers}

## Solution / Approach

{solution}

## Verification

{verification}

## Notes

- Extracted automatically by Claudeception from session on {date}
- Confidence: {confidence}
- Review and refine this skill for accuracy

'''


def log(message: str) -> None:
    """Append message to log file and stderr."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"{timestamp} - {message}"

    # Always write to log file
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(f"{log_entry}\n")
    except Exception as e:
        print(f"Log error: {e}", file=sys.stderr)

    # Also write to stderr (gets captured by hook wrapper)
    if DEBUG:
        print(log_entry, file=sys.stderr)


def to_kebab_case(text: str) -> str:
    """Convert text to kebab-case for skill names."""
    text = re.sub(r'[^a-zA-Z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text.strip().lower())
    text = re.sub(r'-+', '-', text)
    return text[:50]


def skill_exists(name: str) -> bool:
    """Check if a skill with this name already exists."""
    skill_path = SKILLS_DIR / name / 'SKILL.md'
    return skill_path.exists()


def find_similar_skills(keywords: List[str]) -> List[str]:
    """Find existing skills that might be similar based on keywords."""
    similar = []
    if not SKILLS_DIR.exists():
        return similar

    for skill_dir in SKILLS_DIR.iterdir():
        if skill_dir.is_dir():
            skill_file = skill_dir / 'SKILL.md'
            if skill_file.exists():
                try:
                    content = skill_file.read_text().lower()
                    matches = sum(1 for kw in keywords if kw.lower() in content)
                    if matches >= 2:
                        similar.append(skill_dir.name)
                except Exception:
                    pass
    return similar


def extract_recent_exchanges(session_data: Dict[Any, Any], max_exchanges: int = 5) -> str:
    """Extract the last N exchanges from session data."""
    conversation = ""

    if isinstance(session_data, dict):
        if 'messages' in session_data:
            messages = session_data.get('messages', [])
            recent_messages = messages[-(max_exchanges * 2):] if len(messages) > max_exchanges * 2 else messages

            for msg in recent_messages:
                if isinstance(msg, dict):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    conversation += f"[{role}]: {content}\n\n"
        elif 'conversation' in session_data:
            full_text = str(session_data['conversation'])
            chunks = full_text.split('\n\n')
            recent_chunks = chunks[-(max_exchanges * 2):] if len(chunks) > max_exchanges * 2 else chunks
            conversation = '\n\n'.join(recent_chunks)
        else:
            conversation = json.dumps(session_data)
    else:
        conversation = str(session_data)

    return conversation


def output_extraction_prompt(conversation: str):
    """
    Output a prompt for the LLM to analyze and extract skills.
    The LLM will respond with JSON containing skill data.
    """
    prompt = f'''
================================================================================
CLAUDECEPTION - SKILL EXTRACTION ANALYSIS
================================================================================

Analyze this recent conversation for **skill-worthy knowledge** that could help
future Claude sessions or users. Look for:

| Category | What to Extract | Example |
|----------|-----------------|---------|
| Pattern | Reusable approach or technique | "Use worktrees for parallel feature work" |
| Discovery | Non-obvious finding that took investigation | "CDK bundling fails with multiple lock files" |
| Workaround | Solution to a limitation or bug | "Mock MCP servers need explicit port binding" |
| Best Practice | Recommended approach for quality/safety | "Always validate webhook signatures" |
| Integration | How to connect systems/tools | "Connect Obsidian to Claude via REST API" |

**Extraction Criteria:**
- Must be **reusable** (not one-off specific to a unique codebase)
- Must be **non-obvious** (required investigation or experimentation)
- Must be **verified** (actually worked, not theoretical)
- Should benefit **future sessions** (worth remembering)

**Recent Conversation:**
--------------------------------------------------------------------------------
{conversation[:3000]}
--------------------------------------------------------------------------------

If skill-worthy knowledge was found, output JSON:

```json
{{
  "skills": [
    {{
      "name": "kebab-case-skill-name",
      "title": "Brief Descriptive Title",
      "description": "One-line summary of what this skill teaches",
      "problem": "The problem or use case this addresses",
      "triggers": "When to use this skill (conditions/scenarios)",
      "solution": "The approach, technique, or knowledge to apply",
      "verification": "How to verify it worked",
      "tags": ["tag1", "tag2"],
      "confidence": 0.8
    }}
  ]
}}
```

If nothing notable was learned, respond:
"No skill-worthy knowledge to extract from this conversation."

================================================================================
'''
    print(prompt)


def create_skill(skill_data: Dict[str, Any]) -> bool:
    """Create a new skill from extracted data."""
    name = skill_data.get('name', '')
    if not name:
        name = to_kebab_case(skill_data.get('title', 'unnamed-skill'))

    # Ensure name is valid
    name = to_kebab_case(name)
    if not name or len(name) < 3:
        name = f"skill-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    # Check for duplicates
    if skill_exists(name):
        log(f"Skill already exists: {name}")
        return False

    # Check for similar skills
    keywords = re.findall(r'\b[a-zA-Z]{4,}\b', skill_data.get('title', ''))[:5]
    similar = find_similar_skills(keywords)
    if similar:
        log(f"Similar skills exist: {similar} - skipping to avoid duplicate")
        return False

    skill_dir = SKILLS_DIR / name
    skill_file = skill_dir / 'SKILL.md'

    # Prepare template data
    template_data = {
        'name': name,
        'title': skill_data.get('title', 'Untitled Skill'),
        'description': skill_data.get('description', 'No description provided'),
        'problem': skill_data.get('problem', 'Not specified'),
        'triggers': skill_data.get('triggers', '- Not specified'),
        'solution': skill_data.get('solution', 'Not specified'),
        'verification': skill_data.get('verification', '- Verify the approach works as expected'),
        'tags': str(skill_data.get('tags', [])),
        'confidence': skill_data.get('confidence', 0.5),
        'date': datetime.now().strftime('%Y-%m-%d'),
    }

    content = SKILL_TEMPLATE.format(**template_data)

    if DRY_RUN:
        log(f"[DRY RUN] Would create skill: {name}")
        log(f"[DRY RUN] Content preview:\n{content[:500]}...")
        return True

    try:
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file.write_text(content)
        log(f"Created skill: {name} at {skill_file}")
        return True
    except Exception as e:
        log(f"Error creating skill: {e}")
        return False


def process_skill_json(data: Dict[Any, Any]) -> int:
    """Process JSON containing skill extraction data from LLM."""
    skills = data.get('skills', [])

    if not skills:
        log("No skills in JSON data")
        return 0

    log(f"\n{'='*70}")
    log(f"LLM EXTRACTED {len(skills)} SKILLS:")
    log(f"{'='*70}")

    created = 0
    for idx, skill in enumerate(skills, 1):
        log(f"\n--- Skill {idx}/{len(skills)} ---")
        log(f"  Name: {skill.get('name', 'N/A')}")
        log(f"  Title: {skill.get('title', 'N/A')}")
        log(f"  Tags: {skill.get('tags', [])}")
        log(f"  Confidence: {skill.get('confidence', 'N/A')}")
        log(f"  Problem: {skill.get('problem', 'N/A')[:100]}...")

        if create_skill(skill):
            created += 1
            log(f"  ✓ Skill created successfully")
        else:
            log(f"  ✗ Skill creation skipped/failed")

    log(f"\nCreated {created}/{len(skills)} skills")
    return created


def main():
    """Main entry point."""
    log("Claudeception extraction started")

    # Check if we have input
    if sys.stdin.isatty():
        log("No stdin input - nothing to analyze")
        return 0

    # Read input
    try:
        input_data = sys.stdin.read().strip()
    except Exception as e:
        log(f"Error reading stdin: {e}")
        return 1

    if not input_data:
        log("Empty stdin - nothing to analyze")
        return 0

    log(f"Received input ({len(input_data)} chars)")

    # Try to parse as JSON
    try:
        data = json.loads(input_data)

        # Check if this is skill extraction JSON from LLM
        if 'skills' in data:
            log("Detected skill extraction JSON from LLM")
            created = process_skill_json(data)
            log(f"Skill extraction complete: {created} skills created")
            return 0

        # Otherwise, it's session data - extract conversation and output prompt
        conversation = extract_recent_exchanges(data, MAX_EXCHANGES)

        if len(conversation) < 100:
            log(f"Conversation too short ({len(conversation)} chars) - skipping")
            return 0

        log(f"Analyzing last {MAX_EXCHANGES} exchanges ({len(conversation)} chars)")
        log(f"\n{'='*70}")
        log("CONVERSATION PREVIEW:")
        log(f"{'='*70}")
        log(conversation[:500])
        if len(conversation) > 500:
            log("... (truncated)")
        log(f"{'='*70}")

        # Output the extraction prompt for Claude to analyze
        output_extraction_prompt(conversation)
        log("Output extraction prompt for LLM analysis")
        return 0

    except json.JSONDecodeError:
        # Not JSON - treat as plain text conversation
        log("Input is not JSON - treating as plain text")
        conversation = input_data

        if len(conversation) < 100:
            log(f"Text too short ({len(conversation)} chars) - skipping")
            return 0

        output_extraction_prompt(conversation)
        log("Output extraction prompt for LLM analysis")
        return 0

    except Exception as e:
        log(f"Error in extraction: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
