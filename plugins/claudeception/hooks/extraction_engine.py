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
    from session_state import (
        calculate_breakthrough_score,
        clear_session,
        get_signal_summary,
        get_transcript_start_line,
        record_compaction,
    )

    HAS_SESSION_STATE = True
except ImportError:
    HAS_SESSION_STATE = False

    def get_transcript_start_line():
        return 0

    def record_compaction(line_count):
        pass


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
        if correction.get("confidence", 0) >= 0.3:
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


def read_transcript(transcript_path: str, start_line: int = 0) -> tuple[list[dict], int]:
    """Read session transcript from a specific line.

    Args:
        transcript_path: Path to the transcript JSONL file
        start_line: Line number to start reading from (0-indexed)

    Returns:
        Tuple of (messages list, total line count)
    """
    messages = []
    total_lines = 0

    try:
        with open(transcript_path) as f:
            for i, line in enumerate(f):
                total_lines = i + 1
                if i < start_line:
                    continue  # Skip lines before start_line

                stripped = line.strip()
                if not stripped:
                    continue

                try:
                    msg = json.loads(stripped)
                    messages.append(msg)
                except json.JSONDecodeError:
                    # Not JSON, might be plain text - store as raw
                    messages.append({"type": "raw", "content": stripped})

        log(f"Read {len(messages)} messages from transcript (lines {start_line}-{total_lines})")
    except FileNotFoundError:
        log(f"Transcript file not found: {transcript_path}")
    except Exception as e:
        log(f"Error reading transcript: {e}")

    return messages, total_lines


def extract_conversation_text(messages: list[dict], max_chars: int = 50000) -> str:
    """Extract readable conversation text from transcript messages.

    Args:
        messages: List of transcript message dicts
        max_chars: Maximum characters to return

    Returns:
        Formatted conversation text
    """
    conversation_parts = []
    total_chars = 0

    for msg in messages:
        if total_chars >= max_chars:
            break

        # Handle different message formats
        role = msg.get("role", msg.get("type", "unknown"))
        content = ""

        if "content" in msg:
            content = msg["content"]
            if isinstance(content, list):
                # Handle content blocks (Claude API format)
                text_parts = []
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            text_parts.append(block.get("text", ""))
                        elif block.get("type") == "tool_use":
                            text_parts.append(f"[Tool: {block.get('name', 'unknown')}]")
                        elif block.get("type") == "tool_result":
                            result = str(block.get("content", ""))[:500]
                            text_parts.append(f"[Tool Result: {result}]")
                    elif isinstance(block, str):
                        text_parts.append(block)
                content = "\n".join(text_parts)
            elif not isinstance(content, str):
                content = str(content)

        elif "message" in msg:
            content = str(msg["message"])

        if content:
            # Format based on role
            if role in ("user", "human"):
                formatted = f"\n[USER]: {content}\n"
            elif role in ("assistant", "ai"):
                formatted = f"\n[ASSISTANT]: {content}\n"
            else:
                formatted = f"\n[{role.upper()}]: {content}\n"

            remaining = max_chars - total_chars
            if len(formatted) > remaining:
                formatted = formatted[:remaining] + "..."

            conversation_parts.append(formatted)
            total_chars += len(formatted)

    return "".join(conversation_parts)


def analyze_transcript_for_knowledge(conversation_text: str) -> dict:
    """Analyze conversation text for extractable knowledge patterns.

    Returns analysis metadata to guide LLM extraction prompt.
    """
    analysis = {
        "has_debugging": False,
        "has_error_resolution": False,
        "has_workaround": False,
        "has_discovery": False,
        "has_pattern_learning": False,
        "key_topics": [],
        "error_patterns": [],
        "tools_used": set(),
    }

    text_lower = conversation_text.lower()

    # Detect debugging sessions
    debug_indicators = ["debug", "error", "exception", "traceback", "stack trace", "failed", "not working"]
    analysis["has_debugging"] = any(ind in text_lower for ind in debug_indicators)

    # Detect error resolution
    resolution_indicators = ["fixed", "solved", "resolved", "working now", "that worked", "solution"]
    if analysis["has_debugging"] and any(ind in text_lower for ind in resolution_indicators):
        analysis["has_error_resolution"] = True

    # Detect workarounds
    workaround_indicators = ["workaround", "instead", "alternative", "hack", "trick", "bypass"]
    analysis["has_workaround"] = any(ind in text_lower for ind in workaround_indicators)

    # Detect discoveries
    discovery_indicators = ["found", "discovered", "realized", "turns out", "actually", "the issue was"]
    analysis["has_discovery"] = any(ind in text_lower for ind in discovery_indicators)

    # Detect pattern learning
    pattern_indicators = ["pattern", "best practice", "should always", "remember to", "learned", "gotcha"]
    analysis["has_pattern_learning"] = any(ind in text_lower for ind in pattern_indicators)

    # Extract error patterns (look for common error formats)
    error_patterns = re.findall(r"(?:error|exception|failed)[\s:]+([^\n]{10,100})", text_lower)
    analysis["error_patterns"] = list(set(error_patterns[:5]))  # Dedupe and limit

    # Extract tools used
    tool_matches = re.findall(r"\[Tool:\s*([^\]]+)\]", conversation_text)
    analysis["tools_used"] = list(set(tool_matches))

    # Extract key topics (capitalized multi-word terms)
    topic_matches = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b", conversation_text)
    analysis["key_topics"] = list(set(topic_matches[:10]))

    return analysis


def build_extraction_prompt(conversation_text: str, analysis: dict, signal_summary: dict, hook_event: str) -> str:
    """Build a comprehensive extraction prompt for the LLM.

    Args:
        conversation_text: The conversation content to analyze
        analysis: Pre-analysis metadata
        signal_summary: Accumulated signals from session
        hook_event: Which hook triggered this (SessionEnd or PreCompact)

    Returns:
        Formatted prompt for Claude to analyze and extract skills
    """
    # Build context summary
    context_parts = []

    if analysis["has_error_resolution"]:
        context_parts.append("✓ Error was debugged and resolved")
    if analysis["has_workaround"]:
        context_parts.append("✓ Workaround or alternative approach found")
    if analysis["has_discovery"]:
        context_parts.append("✓ Non-obvious discovery made")
    if analysis["has_pattern_learning"]:
        context_parts.append("✓ Pattern or best practice identified")

    if analysis["error_patterns"]:
        context_parts.append(f"Error patterns seen: {', '.join(analysis['error_patterns'][:3])}")

    if analysis["tools_used"]:
        context_parts.append(f"Tools used: {', '.join(analysis['tools_used'][:5])}")

    context_summary = "\n".join(context_parts) if context_parts else "No specific patterns detected"

    # Signal summary
    signal_text = f"""
Signals accumulated:
- Errors: {signal_summary.get("error_count", 0)}
- Retries: {signal_summary.get("retry_count", 0)}
- Web searches: {signal_summary.get("web_search_count", 0)}
- User corrections: {signal_summary.get("correction_count", 0)}
- User teaching: {signal_summary.get("teaching_count", 0)}
- Breakthrough score: {signal_summary.get("breakthrough_score", 0):.2f}
"""

    # Truncate conversation if needed
    max_conv_len = 30000
    if len(conversation_text) > max_conv_len:
        # Keep beginning and end for context
        half = max_conv_len // 2
        conversation_text = (
            conversation_text[:half]
            + f"\n\n[... {len(conversation_text) - max_conv_len} characters truncated ...]\n\n"
            + conversation_text[-half:]
        )

    return f"""
================================================================================
CLAUDECEPTION - SESSION KNOWLEDGE EXTRACTION
================================================================================
Trigger: {hook_event}

**Pre-Analysis:**
{context_summary}

{signal_text}

**Session Conversation:**
--------------------------------------------------------------------------------
{conversation_text}
--------------------------------------------------------------------------------

**Your Task:**
Analyze this conversation for skill-worthy knowledge. Look for:

| Category | What to Extract | Skip If |
|----------|-----------------|---------|
| Debugging Insight | Root cause of non-obvious error | Just a typo or syntax error |
| Workaround | Solution to tool/framework limitation | Standard documented approach |
| Pattern | Reusable technique discovered | Project-specific config |
| Integration | How to connect systems | Already well-documented |
| Gotcha | Surprising behavior that caught us | Common knowledge |

**Extraction Criteria:**
- Must be REUSABLE (not one-off project-specific)
- Must be NON-OBVIOUS (required investigation)
- Must be VERIFIED (actually worked in this session)
- Should benefit FUTURE sessions

**Output Format:**
If skill-worthy knowledge found, respond with JSON:
```json
{{
  "skills": [
    {{
      "name": "kebab-case-name",
      "title": "Brief Descriptive Title",
      "description": "One-line summary for semantic matching - include error messages, tool names",
      "problem": "What problem this solves",
      "triggers": "When to use: specific symptoms, error messages, scenarios",
      "solution": "Step-by-step approach or key insight",
      "verification": "How to confirm it worked",
      "tags": ["category", "tool-name", "error-type"],
      "confidence": 0.8
    }}
  ]
}}
```

If nothing notable, respond: "No skill-worthy knowledge to extract."

================================================================================
"""


def main() -> int:
    """Main entry point for SessionEnd/PreCompact hooks."""
    log("=" * 70)
    log("Extraction engine started")

    # Read session data from stdin
    session_data = {}
    hook_event = "unknown"
    if not sys.stdin.isatty():
        try:
            input_str = sys.stdin.read()
            if input_str:
                session_data = json.loads(input_str)
                hook_event = session_data.get("hook_event_name", "unknown")
                log(f"Triggered by: {hook_event}")
                log(f"Received session data: {list(session_data.keys())}")
        except json.JSONDecodeError:
            log("Could not parse stdin as JSON")
        except Exception as e:
            log(f"Error reading stdin: {e}")

    # Get transcript path
    transcript_path = session_data.get("transcript_path", "")
    if not transcript_path:
        log("No transcript_path in session data - cannot analyze content")
        # Fall back to signal-only extraction
        return _fallback_signal_extraction(session_data, hook_event)

    # Get session state with accumulated signals
    signal_summary = {}
    start_line = 0
    if HAS_SESSION_STATE:
        try:
            signal_summary = get_signal_summary() or {}
            start_line = signal_summary.get("last_compaction_line", 0)
            log(f"Retrieved signal summary, reading from line {start_line}")
        except Exception as e:
            log(f"Error getting signal summary: {e}")

    # Add breakthrough score if not present
    if "breakthrough_score" not in signal_summary and HAS_SESSION_STATE:
        try:
            signal_summary["breakthrough_score"] = calculate_breakthrough_score()
        except Exception:
            signal_summary["breakthrough_score"] = 0

    # Read transcript from last compaction point
    messages, total_lines = read_transcript(transcript_path, start_line)

    if not messages:
        log("No messages to analyze in transcript segment - falling back to signal extraction")
        return _fallback_signal_extraction(session_data, hook_event)

    # Extract conversation text
    conversation_text = extract_conversation_text(messages)
    log(f"Extracted {len(conversation_text)} chars of conversation text")

    if len(conversation_text) < 200:
        log("Conversation too short for meaningful analysis")
        return _finalize_extraction(session_data, signal_summary, hook_event, total_lines, 0)

    # Analyze transcript for knowledge patterns
    analysis = analyze_transcript_for_knowledge(conversation_text)
    log(
        f"Analysis: debugging={analysis['has_debugging']}, resolution={analysis['has_error_resolution']}, "
        f"discovery={analysis['has_discovery']}, workaround={analysis['has_workaround']}"
    )

    # Check if there's anything worth extracting
    has_potential = (
        analysis["has_error_resolution"]
        or analysis["has_workaround"]
        or analysis["has_discovery"]
        or analysis["has_pattern_learning"]
        or signal_summary.get("correction_count", 0) > 0
        or signal_summary.get("teaching_count", 0) > 0
        or signal_summary.get("breakthrough_score", 0) >= BREAKTHROUGH_THRESHOLD
    )

    if not has_potential:
        log("No indicators of extractable knowledge found")
        return _finalize_extraction(session_data, signal_summary, hook_event, total_lines, 0)

    # Extract skills directly from accumulated signals
    skills_created = extract_skills_from_session(session_data, signal_summary)
    log(f"Direct extraction created {skills_created} skills")

    return _finalize_extraction(session_data, signal_summary, hook_event, total_lines, skills_created)


def _fallback_signal_extraction(session_data: dict, hook_event: str) -> int:
    """Fallback to signal-only extraction when transcript unavailable."""
    log("Falling back to signal-only extraction")

    signal_summary = {}
    if HAS_SESSION_STATE:
        try:
            signal_summary = get_signal_summary() or {}
        except Exception as e:
            log(f"Error getting signal summary: {e}")

    if "breakthrough_score" not in signal_summary and HAS_SESSION_STATE:
        try:
            signal_summary["breakthrough_score"] = calculate_breakthrough_score()
        except Exception:
            signal_summary["breakthrough_score"] = 0

    skills_created = 0
    if session_data or signal_summary:
        skills_created = extract_skills_from_session(session_data, signal_summary)

    return _finalize_extraction(session_data, signal_summary, hook_event, 0, skills_created)


def _finalize_extraction(
    session_data: dict, signal_summary: dict, hook_event: str, total_lines: int, skills_created: int
) -> int:
    """Finalize extraction: emit events and handle state based on hook type."""
    # Emit summary event
    emit_event(
        {
            "event_type": "extraction_complete",
            "timestamp": datetime.now().isoformat(),
            "session_id": session_data.get("session_id", "unknown"),
            "hook_event": hook_event,
            "breakthrough_score": signal_summary.get("breakthrough_score", 0),
            "skills_created": skills_created,
            "corrections_count": signal_summary.get("correction_count", 0),
            "teaching_count": signal_summary.get("teaching_count", 0),
            "transcript_lines_analyzed": total_lines - signal_summary.get("last_compaction_line", 0),
        }
    )

    # Handle state based on hook type
    if HAS_SESSION_STATE:
        try:
            if hook_event == "PreCompact":
                # Record compaction point but keep session alive
                record_compaction(total_lines)
                log(f"Recorded compaction at line {total_lines}")
            elif hook_event == "SessionEnd":
                # Clear session completely
                clear_session()
                log("Cleared session state (session ended)")
            else:
                # Unknown hook, just clear to be safe
                clear_session()
                log(f"Cleared session state (unknown hook: {hook_event})")
        except Exception as e:
            log(f"Error finalizing session state: {e}")

    log(f"Extraction complete: hook={hook_event}, skills_created={skills_created}")
    log("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
