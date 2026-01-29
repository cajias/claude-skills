#!/usr/bin/env python3
"""Claudeception v4.0 - Extraction Engine.

Stop hook that performs skill extraction at end of session.
Uses breakthrough scoring, TF-IDF duplicate detection, and taxonomy classification.

This is the main extraction logic that runs when a session ends.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


# Configuration
LOG_FILE = Path(os.environ.get("CLAUDECEPTION_LOG_FILE", os.path.expanduser("~/.claude/claudeception.log")))
DEBUG = os.environ.get("CLAUDECEPTION_DEBUG", "true").lower() == "true"
DRY_RUN = os.environ.get("CLAUDECEPTION_DRY_RUN", "false").lower() == "true"
METRICS_DIR = Path(os.path.expanduser("~/.claude/claudeception-metrics"))
EVENTS_DIR = METRICS_DIR / "events"

# Breakthrough score threshold for extraction
BREAKTHROUGH_THRESHOLD = 0.15

# Import modules
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

try:
    from session_state import calculate_breakthrough_score, clear_session, get_signal_summary

    HAS_SESSION_STATE = True
except ImportError:
    HAS_SESSION_STATE = False

try:
    from duplicate_detector import should_reject_duplicate

    HAS_DUPLICATE_DETECTOR = True
except ImportError:
    HAS_DUPLICATE_DETECTOR = False

try:
    from taxonomy_classifier import classify_skill, get_target_directory

    HAS_TAXONOMY = True
except ImportError:
    HAS_TAXONOMY = False


def log(message: str) -> None:
    """Append message to log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - [extraction-engine] {message}"
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(f"{log_entry}\n")
    except Exception:
        pass
    if DEBUG:
        print(log_entry, file=sys.stderr)


def ensure_directories() -> None:
    """Ensure required directories exist."""
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    EVENTS_DIR.mkdir(parents=True, exist_ok=True)


def emit_event(event: dict[str, Any]) -> None:
    """Write event to daily JSONL log."""
    ensure_directories()
    today = datetime.now().strftime("%Y-%m-%d")
    events_file = EVENTS_DIR / f"{today}.jsonl"
    try:
        with open(events_file, "a") as f:
            f.write(json.dumps(event) + "\n")
        log(f"Emitted {event.get('event_type', 'unknown')} event")
    except Exception as e:
        log(f"Error writing event: {e}")


def to_kebab_case(text: str) -> str:
    """Convert text to kebab-case."""
    text = re.sub(r"[^a-zA-Z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text.strip().lower())
    text = re.sub(r"-+", "-", text)
    return text[:50]


SKILL_TEMPLATE = """---
name: {name}
description: |
  {description}
author: Claude Code (extracted by Claudeception v4.0)
version: 1.0.0
date: {date}
tags: {tags}
level: {level}
breakthrough_score: {breakthrough_score}
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

## Extraction Context

- Extracted automatically by Claudeception v4.0
- Breakthrough score: {breakthrough_score}
- Classification: {level}
- Confidence: {confidence}
- Corrections detected: {corrections_count}

"""


def create_skill(
    skill_data: dict, target_dir: Path, breakthrough_score: float, level: str, corrections_count: int
) -> bool:
    """Create a skill file from extracted data."""
    name = skill_data.get("name", "")
    if not name:
        name = to_kebab_case(skill_data.get("title", "unnamed-skill"))
    name = to_kebab_case(name)

    if not name or len(name) < 3:
        name = f"skill-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    skill_dir = target_dir / name
    skill_file = skill_dir / "SKILL.md"

    # Check if exists
    if skill_file.exists():
        log(f"Skill already exists: {name}")
        return False

    # Check duplicates with TF-IDF
    if HAS_DUPLICATE_DETECTOR:
        should_reject, reason = should_reject_duplicate(skill_data)
        if should_reject:
            log(f"Duplicate rejected: {reason}")
            emit_event(
                {
                    "event_type": "skill_rejected",
                    "timestamp": datetime.now().isoformat(),
                    "skill_name": name,
                    "reason": "duplicate",
                    "details": reason,
                }
            )
            return False

    # Prepare template
    template_data = {
        "name": name,
        "title": skill_data.get("title", "Untitled Skill"),
        "description": skill_data.get("description", "No description"),
        "problem": skill_data.get("problem", "Not specified"),
        "triggers": skill_data.get("triggers", "- Not specified"),
        "solution": skill_data.get("solution", "Not specified"),
        "verification": skill_data.get("verification", "- Verify the approach works"),
        "tags": str(skill_data.get("tags", [])),
        "confidence": skill_data.get("confidence", 0.5),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "level": level,
        "breakthrough_score": f"{breakthrough_score:.2f}",
        "corrections_count": corrections_count,
    }

    content = SKILL_TEMPLATE.format(**template_data)

    if DRY_RUN:
        log(f"[DRY RUN] Would create skill: {name} at {target_dir}")
        return True

    try:
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file.write_text(content)
        log(f"Created skill: {name} at {skill_file}")

        emit_event(
            {
                "event_type": "skill_created",
                "timestamp": datetime.now().isoformat(),
                "skill_name": name,
                "level": level,
                "breakthrough_score": breakthrough_score,
                "target_dir": str(target_dir),
            }
        )

        return True
    except Exception as e:
        log(f"Error creating skill: {e}")
        return False


def extract_skills_from_session(session_data: dict, signal_summary: dict) -> int:
    """Extract skills from session based on accumulated signals.

    Returns number of skills created.
    """
    cwd = session_data.get("cwd", "")
    session_id = session_data.get("session_id", "")
    session_data.get("transcript_path", "")

    log(f"Extracting skills from session {session_id}")
    log(f"Signal summary: {json.dumps(signal_summary, indent=2)}")

    breakthrough_score = signal_summary.get("breakthrough_score", 0)
    corrections = signal_summary.get("corrections", [])
    errors = signal_summary.get("errors", [])

    # Check if session meets extraction threshold
    if breakthrough_score < BREAKTHROUGH_THRESHOLD:
        log(f"Breakthrough score {breakthrough_score:.2f} below threshold {BREAKTHROUGH_THRESHOLD}")
        emit_event(
            {
                "event_type": "extraction_skipped",
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "reason": "below_threshold",
                "breakthrough_score": breakthrough_score,
            }
        )
        return 0

    log(f"Breakthrough score {breakthrough_score:.2f} meets threshold!")

    # Build skill proposals from corrections and errors
    skills_created = 0
    skills_to_create = []

    # Corrections are high-value signals (lowered threshold v4.2.1)
    for correction in corrections:
        if correction.get("confidence", 0) >= 0.5:
            insight = correction.get("extracted_knowledge", "") or correction.get("extracted_insight", "")
            if insight:
                skills_to_create.append(
                    {
                        "name": to_kebab_case(insight[:30]),
                        "title": insight[:60],
                        "description": f"Learned from user correction: {insight}",
                        "problem": correction.get("prompt", "")[:200],
                        "triggers": f"When making similar mistakes to: {correction.get('correction_type', 'unknown')}",
                        "solution": insight,
                        "verification": "- Apply the corrected approach and verify user acceptance",
                        "tags": ["correction", "learned", correction.get("correction_type", "pattern")],
                        "confidence": correction.get("confidence", 0.7),
                        "source": "correction",
                    }
                )

    # Errors with resolutions could be skills
    error_groups = {}
    for error in errors:
        tool = error.get("tool", "unknown")
        if tool not in error_groups:
            error_groups[tool] = []
        error_groups[tool].append(error)

    for tool, tool_errors in error_groups.items():
        if len(tool_errors) >= 2:  # Multiple errors with same tool = learning opportunity
            skills_to_create.append(
                {
                    "name": f"{tool.lower()}-error-handling",
                    "title": f"Handling {tool} Errors",
                    "description": f"Patterns for handling common {tool} errors",
                    "problem": f"Encountered {len(tool_errors)} errors with {tool}",
                    "triggers": f"When using {tool} and encountering errors",
                    "solution": "Review error patterns and apply appropriate fixes",
                    "verification": f"- {tool} operations complete successfully",
                    "tags": ["error-handling", tool.lower(), "debugging"],
                    "confidence": 0.6,
                    "source": "error_pattern",
                }
            )

    log(f"Proposed {len(skills_to_create)} skills from signals")

    # Create skills
    for skill_data in skills_to_create:
        # Classify skill
        if HAS_TAXONOMY:
            level = classify_skill(skill_data, cwd)
            target_dir = get_target_directory(level, cwd)
        else:
            level = "user"
            target_dir = Path(os.path.expanduser("~/.claude/my-claude-skills/skills"))

        if target_dir is None:
            log(f"Skill '{skill_data.get('name')}' classified as skip")
            continue

        if create_skill(skill_data, target_dir, breakthrough_score, level, len(corrections)):
            skills_created += 1

    return skills_created


def read_transcript(transcript_path: str) -> list[dict]:
    """Read session transcript."""
    messages = []
    try:
        with open(transcript_path) as f:
            for line in f:
                try:
                    msg = json.loads(line.strip())
                    messages.append(msg)
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        log(f"Error reading transcript: {e}")
    return messages


def main() -> int:
    """Main entry point for Stop hook."""
    log("=" * 70)
    log("Extraction engine started (Stop hook)")

    # Read session data from stdin
    session_data = {}
    if not sys.stdin.isatty():
        try:
            input_str = sys.stdin.read()
            if input_str:
                session_data = json.loads(input_str)
                log(f"Received session data: {list(session_data.keys())}")
        except json.JSONDecodeError:
            log("Could not parse stdin as JSON")
        except Exception as e:
            log(f"Error reading stdin: {e}")

    # Get session state with accumulated signals
    signal_summary = {}
    if HAS_SESSION_STATE:
        try:
            signal_summary = get_signal_summary() or {}
            log("Retrieved signal summary")
        except Exception as e:
            log(f"Error getting signal summary: {e}")

    # Add breakthrough score if not present
    if "breakthrough_score" not in signal_summary and HAS_SESSION_STATE:
        try:
            signal_summary["breakthrough_score"] = calculate_breakthrough_score()
        except Exception:
            signal_summary["breakthrough_score"] = 0

    # Extract skills
    skills_created = 0
    if session_data or signal_summary:
        skills_created = extract_skills_from_session(session_data, signal_summary)

    # Emit summary event
    emit_event(
        {
            "event_type": "session_extraction_complete",
            "timestamp": datetime.now().isoformat(),
            "session_id": session_data.get("session_id", "unknown"),
            "breakthrough_score": signal_summary.get("breakthrough_score", 0),
            "skills_created": skills_created,
            "corrections_count": len(signal_summary.get("corrections", [])),
            "errors_count": len(signal_summary.get("errors", [])),
        }
    )

    # Clear session state
    if HAS_SESSION_STATE:
        try:
            clear_session()
            log("Cleared session state")
        except Exception as e:
            log(f"Error clearing session: {e}")

    log(f"Extraction complete: {skills_created} skills created")
    log("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
