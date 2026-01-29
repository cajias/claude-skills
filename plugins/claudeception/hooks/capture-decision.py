#!/usr/bin/env python3
"""Claudeception - Capture LLM Extraction Decision.

This script is called by capture-decision.sh to process Claude's response
after the extraction prompt. It detects whether Claude proposed skills
or decided to skip extraction, then emits structured events.

The script:
1. Reads pending correlation data from ~/.claude/claudeception-metrics/pending.json
2. Parses the assistant response for skill JSON or rejection phrases
3. Emits extraction_decision and skill_proposed events to the JSONL log
4. Clears the pending file after processing

Input: Assistant response via stdin
Output: JSONL events to ~/.claude/claudeception-metrics/events/YYYY-MM-DD.jsonl
"""

import json
import os
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


# Configuration
METRICS_DIR = Path(os.path.expanduser("~/.claude/claudeception-metrics"))
EVENTS_DIR = METRICS_DIR / "events"
PENDING_FILE = METRICS_DIR / "pending.json"
LOG_FILE = Path(os.path.expanduser("~/.claude/claudeception.log"))
DEBUG = os.environ.get("CLAUDECEPTION_DEBUG", "true").lower() == "true"
PLUGIN_VERSION = os.environ.get("CLAUDECEPTION_VERSION", "1.3.0")


# Rejection phrases that indicate Claude chose not to extract skills
REJECTION_PHRASES = [
    "no skill-worthy knowledge",
    "no skill-worthy",
    "nothing notable was learned",
    "no notable knowledge",
    "no skills to extract",
    "nothing to extract",
    "no reusable knowledge",
    "trivial content",
    "project-specific",
    "not worth extracting",
]


def log(message: str) -> None:
    """Append message to log file and stderr."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - [capture-decision] {message}"

    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(f"{log_entry}\n")
    except Exception as e:
        print(f"Log error: {e}", file=sys.stderr)

    if DEBUG:
        print(log_entry, file=sys.stderr)


def ensure_directories() -> None:
    """Ensure all required directories exist."""
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    EVENTS_DIR.mkdir(parents=True, exist_ok=True)


def load_pending() -> Optional[dict[str, Any]]:
    """Load pending correlation data from pending.json."""
    if not PENDING_FILE.exists():
        log("No pending.json found - nothing to correlate")
        return None

    try:
        with open(PENDING_FILE) as f:
            data = json.load(f)
        log(f"Loaded pending correlation: {data.get('correlation_id', 'unknown')}")
        return data
    except Exception as e:
        log(f"Error loading pending.json: {e}")
        return None


def clear_pending() -> None:
    """Clear the pending file after processing."""
    try:
        if PENDING_FILE.exists():
            PENDING_FILE.unlink()
            log("Cleared pending.json")
    except Exception as e:
        log(f"Error clearing pending.json: {e}")


def extract_json_from_response(response: str) -> Optional[dict[str, Any]]:
    """Extract JSON skill data from Claude's response.

    Looks for JSON in code blocks or raw JSON with 'skills' key.
    """
    # Try to find JSON in code blocks first
    json_patterns = [
        r"```json\s*\n?(.*?)\n?```",  # ```json ... ```
        r"```\s*\n?(.*?)\n?```",  # ``` ... ```
        r'\{[\s\S]*?"skills"[\s\S]*?\}',  # Raw JSON with skills key
    ]

    for pattern in json_patterns:
        matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
        for match in matches:
            try:
                # Clean up the match
                json_str = match.strip()
                if not json_str.startswith("{"):
                    # Skip if not starting with {
                    continue

                data = json.loads(json_str)

                # Verify it has skills
                if "skills" in data and isinstance(data["skills"], list):
                    log(f"Found skill JSON with {len(data['skills'])} skills")
                    return data
            except json.JSONDecodeError:
                continue

    return None


def detect_rejection(response: str) -> tuple[bool, Optional[str]]:
    """Detect if the response indicates rejection of skill extraction.

    Returns: (is_rejection, reason)
    """
    response_lower = response.lower()

    for phrase in REJECTION_PHRASES:
        if phrase in response_lower:
            log(f"Detected rejection phrase: '{phrase}'")
            return True, phrase

    return False, None


def infer_category_from_tags(tags: list[str]) -> str:
    """Infer skill category from tags."""
    tags_lower = [t.lower() for t in tags]

    category_keywords = {
        "pattern": ["pattern", "approach", "technique", "method"],
        "discovery": ["discovery", "found", "learned", "insight"],
        "workaround": ["workaround", "fix", "hack", "solution"],
        "best-practice": ["best-practice", "practice", "guideline", "standard"],
        "integration": ["integration", "connect", "api", "interface"],
    }

    for category, keywords in category_keywords.items():
        for kw in keywords:
            if any(kw in tag for tag in tags_lower):
                return category

    return "pattern"  # Default category


def emit_event(event: dict[str, Any]) -> None:
    """Emit an event to the daily JSONL log file."""
    ensure_directories()

    today = datetime.now().strftime("%Y-%m-%d")
    events_file = EVENTS_DIR / f"{today}.jsonl"

    try:
        with open(events_file, "a") as f:
            f.write(json.dumps(event) + "\n")
        log(f"Emitted {event['event_type']} event to {events_file.name}")
    except Exception as e:
        log(f"Error writing event: {e}")


def create_base_event(event_type: str, correlation_id: str, session_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Create a base event with common fields."""
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "correlation_id": correlation_id,
        "plugin_version": PLUGIN_VERSION,
        "data": data,
    }


def process_skill_extraction(response: str, skill_data: dict[str, Any], pending: dict[str, Any]) -> None:
    """Process successful skill extraction from Claude's response."""
    correlation_id = pending.get("correlation_id", str(uuid.uuid4()))
    session_id = pending.get("session_id", "unknown")

    skills = skill_data.get("skills", [])
    skill_names = [s.get("name", "unnamed") for s in skills]
    confidence_scores = [s.get("confidence", 0.5) for s in skills]

    # Emit extraction_decision event
    decision_event = create_base_event(
        event_type="extraction_decision",
        correlation_id=correlation_id,
        session_id=session_id,
        data={
            "decision": "extract",
            "skills_proposed_count": len(skills),
            "llm_response_preview": response[:500] if len(response) > 500 else response,
            "response_parse_status": "success",
            "confidence_scores": confidence_scores,
            "extraction_categories": list({infer_category_from_tags(s.get("tags", [])) for s in skills}),
            "skip_reason": None,
        },
    )
    emit_event(decision_event)

    # Emit skill_proposed events for each skill
    for skill in skills:
        skill_name = skill.get("name", "unnamed")
        tags = skill.get("tags", [])

        proposed_event = create_base_event(
            event_type="skill_proposed",
            correlation_id=correlation_id,
            session_id=session_id,
            data={
                "skill_name": skill_name,
                "skill_title": skill.get("title", skill_name),
                "confidence": skill.get("confidence", 0.5),
                "tags": tags,
                "category": infer_category_from_tags(tags),
                "problem_preview": (skill.get("problem", "")[:200] if skill.get("problem") else ""),
                "solution_preview": (skill.get("solution", "")[:200] if skill.get("solution") else ""),
            },
        )
        emit_event(proposed_event)

    log(f"Processed extraction: {len(skills)} skills proposed ({', '.join(skill_names)})")


def process_skip_decision(response: str, reason: str, pending: dict[str, Any]) -> None:
    """Process Claude's decision to skip extraction."""
    correlation_id = pending.get("correlation_id", str(uuid.uuid4()))
    session_id = pending.get("session_id", "unknown")

    # Map rejection phrases to schema-valid skip reasons
    skip_reason_map = {
        "no skill-worthy": "no_notable_knowledge",
        "nothing notable": "no_notable_knowledge",
        "no notable": "no_notable_knowledge",
        "no skills to": "no_notable_knowledge",
        "nothing to extract": "no_notable_knowledge",
        "no reusable": "no_notable_knowledge",
        "trivial": "trivial_content",
        "project-specific": "project_specific",
    }

    schema_reason = "no_notable_knowledge"  # Default
    for phrase, mapped_reason in skip_reason_map.items():
        if phrase in reason.lower():
            schema_reason = mapped_reason
            break

    decision_event = create_base_event(
        event_type="extraction_decision",
        correlation_id=correlation_id,
        session_id=session_id,
        data={
            "decision": "skip",
            "skills_proposed_count": 0,
            "llm_response_preview": response[:500] if len(response) > 500 else response,
            "response_parse_status": "success",
            "confidence_scores": [],
            "extraction_categories": [],
            "skip_reason": schema_reason,
        },
    )
    emit_event(decision_event)

    log(f"Processed skip decision: {schema_reason}")


def process_parse_error(response: str, pending: dict[str, Any]) -> None:
    """Handle cases where we couldn't parse the response."""
    correlation_id = pending.get("correlation_id", str(uuid.uuid4()))
    session_id = pending.get("session_id", "unknown")

    # Determine the parse error type
    parse_status = "empty_response" if not response.strip() else "json_parse_error"

    decision_event = create_base_event(
        event_type="extraction_decision",
        correlation_id=correlation_id,
        session_id=session_id,
        data={
            "decision": "skip",
            "skills_proposed_count": 0,
            "llm_response_preview": response[:500] if response else "",
            "response_parse_status": parse_status,
            "confidence_scores": [],
            "extraction_categories": [],
            "skip_reason": None,
        },
    )
    emit_event(decision_event)

    log(f"Recorded parse error: {parse_status}")


def read_session_transcript(transcript_path: str) -> list[dict[str, Any]]:
    """Read and parse a session transcript JSONL file."""
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


def find_extraction_responses(messages: list[dict[str, Any]]) -> list[str]:
    """Find assistant responses that contain extraction decisions."""
    extraction_responses = []

    for msg in messages:
        if msg.get("type") != "assistant":
            continue

        message = msg.get("message", {})
        content_list = message.get("content", [])

        for content in content_list:
            if not isinstance(content, dict) or content.get("type") != "text":
                continue

            text = content.get("text", "")

            # Check if this is an extraction-related response
            if (
                "CLAUDECEPTION" in text
                or '"skills"' in text
                or any(phrase in text.lower() for phrase in REJECTION_PHRASES)
            ):
                extraction_responses.append(text)

    return extraction_responses


def main() -> int:
    """Main entry point - works as Stop hook or with direct input."""
    log("=" * 70)
    log("Capture decision hook started (Stop hook mode)")

    # Load pending correlation data
    pending = load_pending()

    # Read session data from stdin (Stop hook provides session JSON)
    session_data = None
    if not sys.stdin.isatty():
        try:
            input_str = sys.stdin.read()
            if input_str:
                session_data = json.loads(input_str)
                log(
                    f"Received session data: {list(session_data.keys()) if isinstance(session_data, dict) else 'non-dict'}"
                )
        except json.JSONDecodeError:
            log("Could not parse stdin as JSON")
        except Exception as e:
            log(f"Error reading stdin: {e}")

    # Get transcript path from session data or pending
    transcript_path = None
    session_id = None

    if session_data and isinstance(session_data, dict):
        transcript_path = session_data.get("transcript_path")
        session_id = session_data.get("session_id")

    if not transcript_path and pending:
        # Fall back to pending data
        transcript_path = pending.get("transcript_path")
        session_id = pending.get("session_id")

    if not transcript_path:
        log("No transcript path available - cannot analyze session")
        clear_pending()
        return 0

    log(f"Analyzing transcript: {transcript_path}")

    # Read and analyze the transcript
    messages = read_session_transcript(transcript_path)
    if not messages:
        log("No messages found in transcript")
        clear_pending()
        return 0

    log(f"Found {len(messages)} messages in transcript")

    # Find extraction-related responses
    extraction_responses = find_extraction_responses(messages)

    if not extraction_responses:
        log("No extraction responses found in this session")
        clear_pending()
        return 0

    log(f"Found {len(extraction_responses)} extraction-related responses")

    # Create pending data if not available
    if not pending:
        pending = {
            "correlation_id": str(uuid.uuid4()),
            "session_id": session_id or "unknown",
            "timestamp": datetime.now().isoformat(),
        }

    # Process each extraction response
    for response in extraction_responses:
        # Try to extract skill JSON
        skill_data = extract_json_from_response(response)

        if skill_data:
            process_skill_extraction(response, skill_data, pending)
        else:
            # Check for rejection
            is_rejection, reason = detect_rejection(response)

            if is_rejection:
                process_skip_decision(response, reason, pending)
            # If neither, it might be the extraction prompt itself - skip

    # Clear pending after processing
    clear_pending()

    log("Capture decision hook completed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
