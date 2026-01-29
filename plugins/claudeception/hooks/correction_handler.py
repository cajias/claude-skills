#!/usr/bin/env python3
"""
Claudeception v4.0 - Correction Handler

UserPromptSubmit hook that detects user corrections and records them
as signals with high weight (x3) for breakthrough scoring.

Runs on every user prompt submission.
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
    from correction_detector import detect_correction
    from session_state import init_session, record_signal, get_session_state, log
except ImportError as e:
    # Fallback
    def log(msg):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_file = Path(os.path.expanduser('~/.claude/claudeception.log'))
        try:
            with open(log_file, 'a') as f:
                f.write(f"{timestamp} - [correction-handler] {msg}\n")
        except Exception:
            pass
        print(f"[correction-handler] {msg}", file=sys.stderr)

    def detect_correction(msg, prev=""):
        return {'is_correction': False, 'confidence': 0}

    def init_session(sid, meta=None):
        pass

    def record_signal(stype, data=None):
        pass

    def get_session_state():
        return None


def process_user_prompt(data: dict) -> None:
    """Process a UserPromptSubmit event and check for corrections."""

    prompt = data.get('prompt', '')
    session_id = data.get('session_id', '')

    if not prompt:
        log("No prompt in input")
        return

    log(f"Processing prompt: {prompt[:100]}...")

    # Ensure session is initialized
    if session_id:
        try:
            state = get_session_state()
            if not state or state.get('session_id') != session_id:
                init_session(session_id, {'source': 'correction_handler'})
        except Exception:
            init_session(session_id, {'source': 'correction_handler'})

    # Detect correction
    result = detect_correction(prompt)

    if result.get('is_correction'):
        confidence = result.get('confidence', 0)
        correction_type = result.get('correction_type', 'unknown')
        insight = result.get('extracted_insight', '')

        log(f"CORRECTION DETECTED: type={correction_type}, confidence={confidence:.2f}")
        log(f"  Insight: {insight[:200]}")

        # Record as high-weight signal
        record_signal('correction', {
            'prompt': prompt[:500],
            'correction_type': correction_type,
            'confidence': confidence,
            'extracted_insight': insight,
            'matched_patterns': result.get('matched_patterns', [])
        })

        # Output extraction prompt for the correction
        if confidence >= 0.7:
            output_correction_extraction_prompt(prompt, result)
    else:
        log(f"No correction detected in prompt")

    # Also record the exchange (for context)
    record_signal('exchange', {
        'user_prompt': prompt[:500],
        'is_correction': result.get('is_correction', False)
    })


def output_correction_extraction_prompt(prompt: str, correction_result: dict) -> None:
    """
    Output a prompt asking Claude to extract knowledge from the correction.
    This helps capture what the user is teaching.
    """
    correction_type = correction_result.get('correction_type', 'unknown')
    insight = correction_result.get('extracted_insight', '')

    extraction_prompt = f'''
================================================================================
CLAUDECEPTION - CORRECTION DETECTED
================================================================================

A user correction was detected. This may represent valuable learning.

**Correction Type:** {correction_type}
**User Said:** {prompt[:500]}
**Extracted Insight:** {insight}

If this correction teaches something reusable (not project-specific),
consider extracting it as a skill or noting it for future behavior.

Key questions:
1. What was Claude doing wrong?
2. What is the correct behavior?
3. Would this help in future similar situations?
4. Is this about a tool/API/framework behavior (extract) or project preference (note but don't extract)?

================================================================================
'''
    # Print to stdout so Claude sees it
    print(extraction_prompt)


def main():
    """Main entry point for UserPromptSubmit hook."""
    log("Correction handler started")

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


if __name__ == '__main__':
    sys.exit(main())
