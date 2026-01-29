#!/usr/bin/env python3
"""Claudeception v4.1 - Unified Knowledge Handler.

UserPromptSubmit hook that detects both user corrections AND teaching patterns,
recording them as high-weight signals (3x) for breakthrough scoring.

This replaces correction_handler.py with unified knowledge detection.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path


# Import modules
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

try:
    from knowledge_detector import detect_knowledge
    from session_state import get_session_state, init_session, log, record_signal

    HAS_KNOWLEDGE_DETECTOR = True
except ImportError:
    HAS_KNOWLEDGE_DETECTOR = False

    # Fallback implementations
    def log(msg: str) -> None:
        """Fallback logging."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file = Path(os.path.expanduser("~/.claude/claudeception.log"))
        try:
            with open(log_file, "a") as f:
                f.write(f"{timestamp} - [knowledge-handler] {msg}\n")
        except Exception:
            pass
        print(f"[knowledge-handler] {msg}", file=sys.stderr)

    def detect_knowledge(user_message: str, assistant_response: str = ""):
        """Fallback detection."""
        from dataclasses import dataclass

        @dataclass
        class FallbackResult:
            is_correction: bool = False
            is_teaching: bool = False
            correction_confidence: float = 0.0
            teaching_confidence: float = 0.0
            total_confidence: float = 0.0
            correction_type: str = ""
            teaching_type: str = ""
            extracted_knowledge: str = ""
            has_response_knowledge: bool = False
            response_knowledge: str = ""

            def to_dict(self) -> dict:
                return {
                    "is_correction": self.is_correction,
                    "is_teaching": self.is_teaching,
                    "correction_confidence": self.correction_confidence,
                    "teaching_confidence": self.teaching_confidence,
                    "total_confidence": self.total_confidence,
                    "extracted_knowledge": self.extracted_knowledge,
                }

        return FallbackResult()

    def init_session(sid, meta=None) -> None:
        """Fallback session init."""

    def record_signal(stype, data=None) -> None:
        """Fallback signal recording."""

    def get_session_state():
        """Fallback state getter."""
        return


# Confidence threshold for extraction prompts
EXTRACTION_THRESHOLD = 0.7


def process_user_prompt(data: dict) -> None:
    """Process a UserPromptSubmit event and detect knowledge signals.

    Detects both corrections and teaching patterns in user prompts.
    """
    prompt = data.get("prompt", "")
    session_id = data.get("session_id", "")

    if not prompt:
        log("No prompt in input")
        return

    log(f"Processing prompt: {prompt[:100]}...")

    # Ensure session is initialized
    if session_id:
        try:
            state = get_session_state()
            if not state or getattr(state, "session_id", None) != session_id:
                init_session(session_id, {"source": "knowledge_handler"})
        except Exception:
            init_session(session_id, {"source": "knowledge_handler"})

    # Unified knowledge detection (corrections + teaching)
    result = detect_knowledge(prompt, assistant_response="")

    # Handle corrections (high-weight signal: 3x)
    if result.is_correction:
        log(
            f"CORRECTION DETECTED: type={result.correction_type}, "
            f"confidence={result.correction_confidence:.2f}"
        )
        log(f"  Knowledge: {result.extracted_knowledge[:200]}")

        record_signal(
            "correction",
            {
                "prompt": prompt[:500],
                "correction_type": result.correction_type,
                "confidence": result.correction_confidence,
                "extracted_knowledge": result.extracted_knowledge,
            },
        )

        # Output extraction prompt for high-confidence corrections
        if result.correction_confidence >= EXTRACTION_THRESHOLD:
            output_knowledge_extraction_prompt(prompt, result.to_dict(), "correction")

    # Handle teaching patterns (high-weight signal: 3x)
    if result.is_teaching:
        log(
            f"TEACHING DETECTED: type={result.teaching_type}, "
            f"confidence={result.teaching_confidence:.2f}"
        )
        log(f"  Knowledge: {result.extracted_knowledge[:200]}")

        record_signal(
            "teaching",
            {
                "prompt": prompt[:500],
                "teaching_type": result.teaching_type,
                "confidence": result.teaching_confidence,
                "extracted_knowledge": result.extracted_knowledge,
            },
        )

        # Output extraction prompt for high-confidence teaching
        if result.teaching_confidence >= EXTRACTION_THRESHOLD:
            output_knowledge_extraction_prompt(prompt, result.to_dict(), "teaching")

    # Log if neither detected
    if not result.is_correction and not result.is_teaching:
        log("No correction or teaching detected in prompt")

    # Record the exchange with knowledge flags
    record_signal(
        "exchange",
        {
            "user_prompt": prompt[:500],
            "is_correction": result.is_correction,
            "is_teaching": result.is_teaching,
            "total_confidence": result.total_confidence,
        },
    )


def output_knowledge_extraction_prompt(
    prompt: str, knowledge_result: dict, knowledge_type: str = "knowledge"
) -> None:
    """Output a prompt for Claude to process detected knowledge.

    Works for both corrections and teaching patterns.
    """
    extracted = knowledge_result.get("extracted_knowledge", "")
    confidence = knowledge_result.get(
        f"{knowledge_type}_confidence",
        knowledge_result.get("total_confidence", 0),
    )
    specific_type = knowledge_result.get(
        f"{knowledge_type}_type",
        knowledge_result.get("correction_type", knowledge_result.get("teaching_type", "unknown")),
    )

    type_label = knowledge_type.upper()

    extraction_prompt = f"""
================================================================================
CLAUDECEPTION - {type_label} DETECTED
================================================================================

A user {knowledge_type} was detected. This may represent valuable learning.

**Type:** {specific_type}
**Confidence:** {confidence:.2f}
**User Said:** {prompt[:500]}
**Extracted Knowledge:** {extracted}

If this {knowledge_type} teaches something reusable (not project-specific),
consider extracting it as a skill or noting it for future behavior.

Key questions:
1. What is the user teaching or correcting?
2. Is this about a tool/API/framework behavior (extract) or project preference (skip)?
3. Would this help in future similar situations?
4. Should this be user-level (all projects) or project-level (this project only)?

================================================================================
"""
    print(extraction_prompt)


def main() -> int:
    """Main entry point for UserPromptSubmit hook."""
    log("Knowledge handler started")

    # Read input from stdin
    if sys.stdin.isatty():
        log("No stdin input")
        return 0

    try:
        input_data = sys.stdin.read().strip()
        if not input_data:
            log("Empty input")
            return 0

        data = json.loads(input_data)
        log(f"Received UserPromptSubmit data: {list(data.keys())}")

        process_user_prompt(data)

    except json.JSONDecodeError as e:
        log(f"JSON decode error: {e}")
        return 1
    except Exception as e:
        log(f"Error processing prompt: {e}")
        import traceback

        log(traceback.format_exc())
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
