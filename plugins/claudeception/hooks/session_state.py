#!/usr/bin/env python3
"""Claudeception v4.0 - Session State Management Module.

This module manages session state for tracking signals during a Claude Code session.
It supports:
- Session initialization and lifecycle management
- Signal recording (errors, retries, web searches, corrections)
- Breakthrough score calculation
- Thread-safe file access with locking

State File: ~/.claude/claudeception-metrics/session-state.json

Environment Variables:
- CLAUDECEPTION_DEBUG: Set to "true" for verbose logging (default: true)
- CLAUDECEPTION_LOG_FILE: Log file path (default: ~/.claude/claudeception.log)
- CLAUDECEPTION_STATE_DIR: State directory (default: ~/.claude/claudeception-metrics)
"""

import fcntl
import json
import os
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


# Configuration
DEBUG = os.environ.get("CLAUDECEPTION_DEBUG", "true").lower() == "true"
LOG_FILE = Path(os.environ.get("CLAUDECEPTION_LOG_FILE", os.path.expanduser("~/.claude/claudeception.log")))
STATE_DIR = Path(os.environ.get("CLAUDECEPTION_STATE_DIR", os.path.expanduser("~/.claude/claudeception-metrics")))
STATE_FILE = STATE_DIR / "session-state.json"
LOCK_FILE = STATE_DIR / ".session-state.lock"

# Lock timeout in seconds
LOCK_TIMEOUT = 10.0
LOCK_RETRY_INTERVAL = 0.1


class SessionStateError(Exception):
    """Base exception for session state errors."""


class LockAcquisitionError(SessionStateError):
    """Raised when unable to acquire file lock."""


class SessionNotInitializedError(SessionStateError):
    """Raised when accessing state without an active session."""


def log(message: str, level: str = "INFO") -> None:
    """Append message to log file and stderr.

    Args:
        message: Log message
        level: Log level (DEBUG, INFO, WARNING, ERROR)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    log_entry = f"{timestamp} [{level}] [session_state] {message}"

    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(f"{log_entry}\n")
    except Exception as e:
        print(f"Log write error: {e}", file=sys.stderr)

    if DEBUG or level in ("WARNING", "ERROR"):
        print(log_entry, file=sys.stderr)


def ensure_state_directory() -> None:
    """Ensure the state directory exists."""
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        log(f"State directory ensured: {STATE_DIR}", "DEBUG")
    except Exception as e:
        log(f"Failed to create state directory: {e}", "ERROR")
        msg = f"Cannot create state directory: {e}"
        raise SessionStateError(msg)


@contextmanager
def file_lock(timeout: float = LOCK_TIMEOUT):
    """Context manager for acquiring an exclusive file lock.

    Implements advisory locking with timeout for concurrent access safety.

    Args:
        timeout: Maximum time to wait for lock acquisition

    Yields:
        Lock file handle

    Raises:
        LockAcquisitionError: If lock cannot be acquired within timeout
    """
    ensure_state_directory()

    start_time = time.monotonic()
    lock_fd = None

    try:
        # Open/create the lock file
        lock_fd = open(LOCK_FILE, "w")

        while True:
            try:
                # Try to acquire exclusive lock (non-blocking)
                fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                log("Lock acquired", "DEBUG")
                break
            except OSError:
                elapsed = time.monotonic() - start_time
                if elapsed >= timeout:
                    log(f"Lock acquisition timeout after {elapsed:.2f}s", "ERROR")
                    msg = f"Failed to acquire lock within {timeout}s"
                    raise LockAcquisitionError(msg)
                # Wait before retrying
                time.sleep(LOCK_RETRY_INTERVAL)

        yield lock_fd

    finally:
        if lock_fd:
            try:
                # Release the lock
                fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
                lock_fd.close()
                log("Lock released", "DEBUG")
            except Exception as e:
                log(f"Error releasing lock: {e}", "WARNING")


@dataclass
class SessionState:
    """Session state tracking all signals during a Claude Code session.

    Attributes:
        session_id: Unique identifier for the session
        session_start: ISO timestamp when session started
        error_count: Number of tool/operation errors
        retry_count: Number of retry attempts
        web_search_count: Number of web fetches/searches
        corrections: List of correction data (count derived via property)
        teachings: List of teaching data (count derived via property)
        exchanges: List of exchange summaries
        last_updated: ISO timestamp of last state update
        metadata: Additional session metadata
        last_compaction_line: Line number in transcript where last compaction occurred (0 = start)
        compaction_count: Number of compactions that have occurred
    """

    session_id: str
    session_start: str
    error_count: int = 0
    retry_count: int = 0
    web_search_count: int = 0
    corrections: list[dict[str, Any]] = field(default_factory=list)  # v4.1.2: Store correction content
    teachings: list[dict[str, Any]] = field(default_factory=list)  # v4.1.2: Store teaching content
    exchanges: list[dict[str, Any]] = field(default_factory=list)
    last_updated: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    last_compaction_line: int = 0  # v4.3: Track transcript position for incremental analysis
    compaction_count: int = 0  # v4.3: Track number of compactions

    @property
    def correction_count(self) -> int:
        """Derive count from list length."""
        return len(self.corrections)

    @property
    def teaching_count(self) -> int:
        """Derive count from list length."""
        return len(self.teachings)

    def __post_init__(self):
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "session_start": self.session_start,
            "error_count": self.error_count,
            "retry_count": self.retry_count,
            "web_search_count": self.web_search_count,
            "corrections": self.corrections,
            "teachings": self.teachings,
            "exchanges": self.exchanges,
            "last_updated": self.last_updated,
            "metadata": self.metadata,
            "last_compaction_line": self.last_compaction_line,
            "compaction_count": self.compaction_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionState":
        return cls(
            session_id=data.get("session_id", ""),
            session_start=data.get("session_start", ""),
            error_count=data.get("error_count", 0),
            retry_count=data.get("retry_count", 0),
            web_search_count=data.get("web_search_count", 0),
            corrections=data.get("corrections", []),
            teachings=data.get("teachings", []),
            exchanges=data.get("exchanges", []),
            last_updated=data.get("last_updated", ""),
            metadata=data.get("metadata", {}),
            last_compaction_line=data.get("last_compaction_line", 0),
            compaction_count=data.get("compaction_count", 0),
        )


def _read_state_file() -> Optional[dict[str, Any]]:
    """Read state from file (internal, assumes lock is held).

    Returns:
        State dictionary or None if file doesn't exist
    """
    if not STATE_FILE.exists():
        return None

    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        log(f"Corrupted state file, will recreate: {e}", "WARNING")
        return None
    except Exception as e:
        log(f"Error reading state file: {e}", "ERROR")
        msg = f"Cannot read state file: {e}"
        raise SessionStateError(msg)


def _write_state_file(state: dict[str, Any]) -> None:
    """Write state to file (internal, assumes lock is held).

    Args:
        state: State dictionary to write
    """
    ensure_state_directory()

    try:
        # Write to temp file first, then rename (atomic on POSIX)
        temp_file = STATE_FILE.with_suffix(".tmp")
        with open(temp_file, "w") as f:
            json.dump(state, f, indent=2)
        temp_file.rename(STATE_FILE)
        log(f"State written to {STATE_FILE}", "DEBUG")
    except Exception as e:
        log(f"Error writing state file: {e}", "ERROR")
        msg = f"Cannot write state file: {e}"
        raise SessionStateError(msg)


def init_session(session_id: str, metadata: Optional[dict[str, Any]] = None) -> SessionState:
    """Initialize state for a new session.

    Creates a fresh session state, clearing any previous state.

    Args:
        session_id: Unique identifier for the session
        metadata: Optional additional metadata to store

    Returns:
        Initialized SessionState object
    """
    log(f"Initializing session: {session_id}")

    now = datetime.now().isoformat()
    state = SessionState(
        session_id=session_id,
        session_start=now,
        last_updated=now,
        metadata=metadata or {},
    )

    with file_lock():
        _write_state_file(state.to_dict())

    log(f"Session initialized: {session_id}")
    return state


def record_signal(signal_type: str, data: Optional[dict[str, Any]] = None) -> SessionState:
    """Record a signal (error, retry, web search, correction, teaching, exchange).

    Supported signal types:
    - 'error': Increment error_count
    - 'retry': Increment retry_count
    - 'web_search': Increment web_search_count
    - 'correction': Append to corrections list (count derived from length)
    - 'teaching': Append to teachings list (count derived from length)
    - 'exchange': Add exchange summary to exchanges list

    Args:
        signal_type: Type of signal to record
        data: Additional data for the signal (required for 'exchange')

    Returns:
        Updated SessionState object

    Raises:
        SessionNotInitializedError: If no active session
        ValueError: If invalid signal type
    """
    valid_signals = {"error", "retry", "web_search", "correction", "teaching", "exchange"}
    if signal_type not in valid_signals:
        msg = f"Invalid signal type: {signal_type}. Valid: {valid_signals}"
        raise ValueError(msg)

    with file_lock():
        state_dict = _read_state_file()

        if not state_dict:
            msg = "No active session. Call init_session() first."
            raise SessionNotInitializedError(msg)

        state = SessionState.from_dict(state_dict)

        # Update counters based on signal type
        if signal_type == "error":
            state.error_count += 1
            log(f"Recorded error (total: {state.error_count})")
        elif signal_type == "retry":
            state.retry_count += 1
            log(f"Recorded retry (total: {state.retry_count})")
        elif signal_type == "web_search":
            state.web_search_count += 1
            log(f"Recorded web search (total: {state.web_search_count})")
        elif signal_type == "correction":
            if data:
                state.corrections.append(data)
                log(f"Recorded correction (total: {state.correction_count})")
            else:
                log("Correction signal received without data, skipping", "WARNING")
        elif signal_type == "teaching":
            if data:
                state.teachings.append(data)
                log(f"Recorded teaching (total: {state.teaching_count})")
            else:
                log("Teaching signal received without data, skipping", "WARNING")
        elif signal_type == "exchange":
            if data:
                state.exchanges.append(data)
                log(f"Recorded exchange (total: {len(state.exchanges)})")
            else:
                log("Exchange signal received without data, skipping", "WARNING")

        state.last_updated = datetime.now().isoformat()
        _write_state_file(state.to_dict())

        return state


def get_session_state() -> Optional[SessionState]:
    """Get the current session state.

    Returns:
        SessionState object or None if no active session
    """
    with file_lock():
        state_dict = _read_state_file()

        if not state_dict:
            log("No active session state found", "DEBUG")
            return None

        return SessionState.from_dict(state_dict)


def calculate_breakthrough_score() -> float:
    """Calculate the breakthrough score for the current session.

    Formula: (errors*2 + retries*1.5 + web_searches*1 + corrections*3 + teaching*3) / duration_minutes

    A higher score indicates more "breakthrough" activity - situations where
    Claude had to work through challenges, search for information, or
    receive user corrections/teaching. This suggests valuable learning opportunities.

    Returns:
        Breakthrough score (0.0 if session not started or zero duration)

    Raises:
        SessionNotInitializedError: If no active session
    """
    state = get_session_state()

    if not state:
        msg = "No active session. Call init_session() first."
        raise SessionNotInitializedError(msg)

    # Calculate duration in minutes
    try:
        start_time = datetime.fromisoformat(state.session_start)
        duration = datetime.now() - start_time
        duration_minutes = duration.total_seconds() / 60.0
    except (ValueError, TypeError) as e:
        log(f"Error parsing session start time: {e}", "ERROR")
        duration_minutes = 0.0

    # Avoid division by zero
    if duration_minutes <= 0:
        log("Session duration is zero or negative, returning 0.0", "DEBUG")
        return 0.0

    # Calculate weighted signal sum (corrections and teaching both have 3.0x weight)
    weighted_sum = (
        state.error_count * 2.0
        + state.retry_count * 1.5
        + state.web_search_count * 1.0
        + state.correction_count * 3.0
        + state.teaching_count * 3.0  # v4.1: Teaching signals have same weight as corrections
    )

    score = weighted_sum / duration_minutes

    log(
        f"Breakthrough score: {score:.4f} "
        f"(errors={state.error_count}, retries={state.retry_count}, "
        f"web_searches={state.web_search_count}, corrections={state.correction_count}, "
        f"teaching={state.teaching_count}, duration={duration_minutes:.2f}min)"
    )

    return score


def clear_session() -> bool:
    """Clear the session state (cleanup after extraction).

    Removes the session state file and lock file.

    Returns:
        True if cleanup was successful, False otherwise
    """
    log("Clearing session state")

    success = True

    with file_lock():
        # Remove state file
        if STATE_FILE.exists():
            try:
                STATE_FILE.unlink()
                log(f"Removed state file: {STATE_FILE}")
            except Exception as e:
                log(f"Error removing state file: {e}", "ERROR")
                success = False

    # Remove lock file (outside the lock context)
    if LOCK_FILE.exists():
        try:
            LOCK_FILE.unlink()
            log(f"Removed lock file: {LOCK_FILE}")
        except Exception as e:
            log(f"Error removing lock file: {e}", "WARNING")
            # Don't fail for lock file removal

    if success:
        log("Session cleared successfully")
    else:
        log("Session cleared with errors", "WARNING")

    return success


def get_session_duration_minutes() -> float:
    """Get the current session duration in minutes.

    Returns:
        Duration in minutes, or 0.0 if no active session
    """
    state = get_session_state()

    if not state:
        return 0.0

    try:
        start_time = datetime.fromisoformat(state.session_start)
        duration = datetime.now() - start_time
        return duration.total_seconds() / 60.0
    except (ValueError, TypeError):
        return 0.0


def get_signal_summary() -> dict[str, Any]:
    """Get a summary of all signals in the current session.

    Returns:
        Dictionary with signal counts and breakthrough score,
        or empty dict if no active session
    """
    state = get_session_state()

    if not state:
        return {}

    try:
        score = calculate_breakthrough_score()
    except SessionNotInitializedError:
        score = 0.0

    return {
        "session_id": state.session_id,
        "duration_minutes": get_session_duration_minutes(),
        "error_count": state.error_count,
        "retry_count": state.retry_count,
        "web_search_count": state.web_search_count,
        "correction_count": state.correction_count,
        "teaching_count": state.teaching_count,
        "corrections": state.corrections,  # v4.1.1: Include correction content for skill extraction
        "teachings": state.teachings,  # v4.1.1: Include teaching content for skill extraction
        "exchange_count": len(state.exchanges),
        "breakthrough_score": score,
        "last_updated": state.last_updated,
        "last_compaction_line": state.last_compaction_line,  # v4.3: For transcript reading
        "compaction_count": state.compaction_count,
    }


def record_compaction(transcript_line_count: int) -> SessionState:
    """Record a compaction event and update the transcript position marker.

    Called by PreCompact hook after extraction to mark where we left off.
    The next extraction will read from this line forward.

    Args:
        transcript_line_count: Current number of lines in the transcript

    Returns:
        Updated SessionState object

    Raises:
        SessionNotInitializedError: If no active session
    """
    with file_lock():
        state_dict = _read_state_file()

        if not state_dict:
            msg = "No active session. Call init_session() first."
            raise SessionNotInitializedError(msg)

        state = SessionState.from_dict(state_dict)

        # Update compaction tracking
        state.last_compaction_line = transcript_line_count
        state.compaction_count += 1
        state.last_updated = datetime.now().isoformat()

        # Reset signal counters for next segment (signals were already processed)
        state.error_count = 0
        state.retry_count = 0
        state.web_search_count = 0
        state.corrections = []
        state.teachings = []
        state.exchanges = []

        _write_state_file(state.to_dict())

        log(
            f"Recorded compaction #{state.compaction_count} at line {transcript_line_count}. "
            "Signal counters reset for next segment."
        )

        return state


def get_transcript_start_line() -> int:
    """Get the line number to start reading transcript from.

    Returns the line after the last compaction, or 0 if no compaction has occurred.

    Returns:
        Line number to start reading from (0-indexed)
    """
    state = get_session_state()

    if not state:
        return 0

    return state.last_compaction_line


# CLI interface for testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Claudeception Session State Manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init command
    init_parser = subparsers.add_parser("init", help="Initialize a new session")
    init_parser.add_argument("session_id", help="Session ID")

    # record command
    record_parser = subparsers.add_parser("record", help="Record a signal")
    record_parser.add_argument(
        "signal_type", choices=["error", "retry", "web_search", "correction"], help="Type of signal"
    )

    # get command
    subparsers.add_parser("get", help="Get current session state")

    # score command
    subparsers.add_parser("score", help="Calculate breakthrough score")

    # summary command
    subparsers.add_parser("summary", help="Get signal summary")

    # clear command
    subparsers.add_parser("clear", help="Clear session state")

    args = parser.parse_args()

    if args.command == "init":
        state = init_session(args.session_id)
        print(json.dumps(state.to_dict(), indent=2))
    elif args.command == "record":
        try:
            state = record_signal(args.signal_type)
            print(json.dumps(state.to_dict(), indent=2))
        except SessionNotInitializedError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.command == "get":
        state = get_session_state()
        if state:
            print(json.dumps(state.to_dict(), indent=2))
        else:
            print("No active session")
    elif args.command == "score":
        try:
            score = calculate_breakthrough_score()
            print(f"Breakthrough score: {score:.4f}")
        except SessionNotInitializedError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.command == "summary":
        summary = get_signal_summary()
        if summary:
            print(json.dumps(summary, indent=2))
        else:
            print("No active session")
    elif args.command == "clear":
        success = clear_session()
        print("Session cleared" if success else "Clear failed")
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
