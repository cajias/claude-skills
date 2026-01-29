#!/usr/bin/env python3
"""
Claudeception v4.1 - Unified Knowledge Detection Module

Detects knowledge signals from both user messages and Claude responses:

1. Teaching patterns in user messages:
   - Explicit instructions: "remember that..."
   - Standing rules: "always do X", "never do Y"
   - Preferences: "I prefer X over Y", "I like when you..."
   - Memory requests: "for future reference..."
   - Pattern teaching: "the pattern is..."

2. Knowledge synthesis in Claude responses:
   - Key insights: "Key insight: ..."
   - Insight blocks: "★ Insight ───"
   - Important notes: "IMPORTANT:", "NOTE:"

3. Correction detection (integrated from correction_detector.py):
   - Direct negation: "no, that's wrong"
   - Wrong assessment: "incorrect", "that's wrong"
   - Clarification: "actually I meant..."

This module provides unified detection for the v4.1 breakthrough scoring system.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# Import correction detection from existing module
from correction_detector import detect_correction, CorrectionType


class TeachingType(Enum):
    """Types of teaching patterns in user messages."""
    EXPLICIT_INSTRUCTION = "explicit_instruction"
    STANDING_RULE = "standing_rule"
    PROHIBITION = "prohibition"
    PREFERENCE = "preference"
    MEMORY_REQUEST = "memory_request"
    PATTERN_TEACHING = "pattern_teaching"
    UNKNOWN = "unknown"


class ResponseKnowledgeType(Enum):
    """Types of knowledge synthesis in Claude responses."""
    KEY_INSIGHT = "key_insight"
    INSIGHT_BLOCK = "insight_block"
    IMPORTANT_NOTE = "important_note"
    SYNTHESIS = "synthesis"
    UNKNOWN = "unknown"


@dataclass
class TeachingResult:
    """Result of teaching pattern detection."""
    is_teaching: bool
    confidence: float
    teaching_type: str
    extracted_knowledge: str
    matched_patterns: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "is_teaching": self.is_teaching,
            "confidence": self.confidence,
            "teaching_type": self.teaching_type,
            "extracted_knowledge": self.extracted_knowledge,
            "matched_patterns": self.matched_patterns,
        }


@dataclass
class ResponseKnowledgeResult:
    """Result of response knowledge synthesis detection."""
    has_knowledge: bool
    confidence: float
    knowledge_type: str
    extracted_knowledge: str
    matched_patterns: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "has_knowledge": self.has_knowledge,
            "confidence": self.confidence,
            "knowledge_type": self.knowledge_type,
            "extracted_knowledge": self.extracted_knowledge,
            "matched_patterns": self.matched_patterns,
        }


@dataclass
class KnowledgeResult:
    """Unified result combining all knowledge detection signals."""
    # Teaching detection
    is_teaching: bool = False
    teaching_confidence: float = 0.0
    teaching_type: str = ""
    teaching_knowledge: str = ""

    # Correction detection (from existing module)
    is_correction: bool = False
    correction_confidence: float = 0.0
    correction_type: str = ""
    correction_insight: str = ""

    # Response knowledge detection
    has_response_knowledge: bool = False
    response_confidence: float = 0.0
    response_knowledge_type: str = ""
    response_knowledge: str = ""

    # Combined
    total_confidence: float = 0.0
    extracted_knowledge: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "is_teaching": self.is_teaching,
            "teaching_confidence": self.teaching_confidence,
            "teaching_type": self.teaching_type,
            "teaching_knowledge": self.teaching_knowledge,
            "is_correction": self.is_correction,
            "correction_confidence": self.correction_confidence,
            "correction_type": self.correction_type,
            "correction_insight": self.correction_insight,
            "has_response_knowledge": self.has_response_knowledge,
            "response_confidence": self.response_confidence,
            "response_knowledge_type": self.response_knowledge_type,
            "response_knowledge": self.response_knowledge,
            "total_confidence": self.total_confidence,
            "extracted_knowledge": self.extracted_knowledge,
        }


# Teaching patterns in user messages
# Format: (regex pattern, confidence, teaching_type)
TEACHING_PATTERNS: List[Tuple[str, float, TeachingType]] = [
    # Explicit instruction patterns (highest confidence)
    (r"remember\s+that\s+(.+?)(?:\.|$)", 0.95, TeachingType.EXPLICIT_INSTRUCTION),
    (r"keep\s+in\s+mind\s+that\s+(.+?)(?:\.|$)", 0.90, TeachingType.EXPLICIT_INSTRUCTION),
    (r"note\s+that\s+(.+?)(?:\.|$)", 0.80, TeachingType.EXPLICIT_INSTRUCTION),

    # Standing rules
    (r"always\s+(?:do\s+|use\s+|run\s+)?(.+?)(?:\.|$)", 0.90, TeachingType.STANDING_RULE),
    (r"make\s+sure\s+(?:to\s+)?always\s+(.+?)(?:\.|$)", 0.85, TeachingType.STANDING_RULE),
    (r"(?:you\s+)?should\s+always\s+(.+?)(?:\.|$)", 0.85, TeachingType.STANDING_RULE),

    # Prohibitions
    (r"never\s+(?:do\s+|use\s+)?(.+?)(?:\.|$)", 0.90, TeachingType.PROHIBITION),
    (r"don'?t\s+ever\s+(.+?)(?:\.|$)", 0.90, TeachingType.PROHIBITION),
    (r"avoid\s+(.+?)(?:\.|$)", 0.75, TeachingType.PROHIBITION),

    # Pattern teaching
    (r"the\s+pattern\s+(?:here\s+)?is\s+(?:to\s+)?(.+?)(?:\.|$)", 0.85, TeachingType.PATTERN_TEACHING),
    (r"the\s+(?:rule|convention)\s+is\s+(?:to\s+)?(.+?)(?:\.|$)", 0.85, TeachingType.PATTERN_TEACHING),
    (r"(?:our|the)\s+approach\s+is\s+(?:to\s+)?(.+?)(?:\.|$)", 0.80, TeachingType.PATTERN_TEACHING),

    # Preferences
    (r"i\s+prefer\s+(.+?)\s+(?:over|to|instead)", 0.85, TeachingType.PREFERENCE),
    (r"i\s+(?:like|want)\s+(?:it\s+)?when\s+(?:you\s+)?(.+?)(?:\.|$)", 0.80, TeachingType.PREFERENCE),
    (r"(?:my|i)\s+prefer(?:ence|red)?\s+(?:is\s+)?(.+?)(?:\.|$)", 0.80, TeachingType.PREFERENCE),

    # Memory requests
    (r"for\s+future\s+reference[,:\s]+(.+?)(?:\.|$)", 0.90, TeachingType.MEMORY_REQUEST),
    (r"save\s+(?:this|that)\s+for\s+later", 0.85, TeachingType.MEMORY_REQUEST),
    (r"keep\s+this\s+in\s+mind\s+for\s+(?:the\s+)?future", 0.85, TeachingType.MEMORY_REQUEST),
]


# Response knowledge patterns (in Claude responses)
# Format: (regex pattern, confidence, knowledge_type)
RESPONSE_KNOWLEDGE_PATTERNS: List[Tuple[str, float, ResponseKnowledgeType]] = [
    # Key insight markers
    (r"key\s+insight[:\s]+(.+?)(?:\n|$)", 0.85, ResponseKnowledgeType.KEY_INSIGHT),
    (r"important\s+insight[:\s]+(.+?)(?:\n|$)", 0.85, ResponseKnowledgeType.KEY_INSIGHT),
    (r"main\s+insight[:\s]+(.+?)(?:\n|$)", 0.80, ResponseKnowledgeType.KEY_INSIGHT),

    # Insight blocks (★ format) - handle indentation with \s*
    (r"★\s*[Ii]nsight[^\n]*\n(.+?)(?:\n\s*`─|$)", 0.90, ResponseKnowledgeType.INSIGHT_BLOCK),
    (r"`★\s*[Ii]nsight[^`]*`\s*\n(.+?)(?:\n\s*`─|$)", 0.90, ResponseKnowledgeType.INSIGHT_BLOCK),

    # Important/Note markers
    (r"IMPORTANT[:\s]+(.+?)(?:\n|$)", 0.80, ResponseKnowledgeType.IMPORTANT_NOTE),
    (r"NOTE[:\s]+(.+?)(?:\n|$)", 0.75, ResponseKnowledgeType.IMPORTANT_NOTE),
    (r"⚠️?\s*(?:Warning|Important)[:\s]+(.+?)(?:\n|$)", 0.80, ResponseKnowledgeType.IMPORTANT_NOTE),

    # Synthesis patterns
    (r"the\s+(?:key|main|core)\s+(?:point|takeaway)\s+is[:\s]+(.+?)(?:\n|$)", 0.80, ResponseKnowledgeType.SYNTHESIS),
    (r"in\s+summary[:\s]+(.+?)(?:\n|$)", 0.75, ResponseKnowledgeType.SYNTHESIS),
]


def normalize_text(text: str) -> str:
    """Normalize text for pattern matching."""
    text = text.lower()
    text = " ".join(text.split())
    return text


def detect_teaching(user_message: str) -> TeachingResult:
    """
    Detect teaching patterns in a user message.

    Analyzes the message for patterns indicating the user is teaching
    Claude something to remember (rules, preferences, patterns, etc.)

    Args:
        user_message: The user's message to analyze

    Returns:
        TeachingResult with detection details
    """
    if not user_message or not user_message.strip():
        return TeachingResult(
            is_teaching=False,
            confidence=0.0,
            teaching_type=TeachingType.UNKNOWN.value,
            extracted_knowledge="",
            matched_patterns=[],
        )

    normalized = normalize_text(user_message)
    matched_patterns: List[str] = []
    max_confidence = 0.0
    detected_type = TeachingType.UNKNOWN
    extracted_knowledge = ""

    for pattern, confidence, teaching_type in TEACHING_PATTERNS:
        match = re.search(pattern, normalized, re.IGNORECASE | re.DOTALL)
        if match:
            pattern_name = f"{teaching_type.value}: {pattern[:30]}..."
            matched_patterns.append(pattern_name)

            if confidence > max_confidence:
                max_confidence = confidence
                detected_type = teaching_type

                # Extract the captured group if present
                if match.groups():
                    extracted_knowledge = match.group(1).strip()
                else:
                    # No capture group, use a portion of the original message
                    extracted_knowledge = user_message.strip()[:200]

    # Threshold for detection
    is_teaching = max_confidence >= 0.5

    return TeachingResult(
        is_teaching=is_teaching,
        confidence=round(max_confidence, 3),
        teaching_type=detected_type.value,
        extracted_knowledge=extracted_knowledge,
        matched_patterns=matched_patterns,
    )


def detect_response_knowledge(assistant_response: str) -> ResponseKnowledgeResult:
    """
    Detect knowledge synthesis patterns in Claude's response.

    Analyzes the response for patterns indicating Claude has synthesized
    useful knowledge (insights, important notes, summaries).

    Args:
        assistant_response: Claude's response to analyze

    Returns:
        ResponseKnowledgeResult with detection details
    """
    if not assistant_response or not assistant_response.strip():
        return ResponseKnowledgeResult(
            has_knowledge=False,
            confidence=0.0,
            knowledge_type=ResponseKnowledgeType.UNKNOWN.value,
            extracted_knowledge="",
            matched_patterns=[],
        )

    # Don't normalize case for response - preserve original for extraction
    text = assistant_response
    normalized = normalize_text(assistant_response)

    matched_patterns: List[str] = []
    max_confidence = 0.0
    detected_type = ResponseKnowledgeType.UNKNOWN
    extracted_knowledge = ""

    for pattern, confidence, knowledge_type in RESPONSE_KNOWLEDGE_PATTERNS:
        # Try both original (for case-sensitive patterns like IMPORTANT) and normalized
        for variant in [text, normalized]:
            flags = re.IGNORECASE | re.DOTALL if variant == normalized else re.DOTALL
            match = re.search(pattern, variant, flags)
            if match:
                pattern_name = f"{knowledge_type.value}: {pattern[:30]}..."
                if pattern_name not in matched_patterns:
                    matched_patterns.append(pattern_name)

                if confidence > max_confidence:
                    max_confidence = confidence
                    detected_type = knowledge_type

                    if match.groups():
                        extracted_knowledge = match.group(1).strip()
                    else:
                        extracted_knowledge = assistant_response.strip()[:200]

    has_knowledge = max_confidence >= 0.5

    return ResponseKnowledgeResult(
        has_knowledge=has_knowledge,
        confidence=round(max_confidence, 3),
        knowledge_type=detected_type.value,
        extracted_knowledge=extracted_knowledge,
        matched_patterns=matched_patterns,
    )


def detect_knowledge(
    user_message: str,
    assistant_response: str = ""
) -> KnowledgeResult:
    """
    Unified knowledge detection combining all signals.

    Detects:
    1. Teaching patterns in user message
    2. Corrections in user message (from existing module)
    3. Knowledge synthesis in assistant response

    Args:
        user_message: The user's message to analyze
        assistant_response: Optional Claude response to analyze

    Returns:
        KnowledgeResult with all detection signals
    """
    result = KnowledgeResult()

    # Detect teaching patterns
    teaching = detect_teaching(user_message)
    result.is_teaching = teaching.is_teaching
    result.teaching_confidence = teaching.confidence
    result.teaching_type = teaching.teaching_type
    result.teaching_knowledge = teaching.extracted_knowledge

    # Detect corrections (using existing module)
    correction = detect_correction(user_message, assistant_response)
    result.is_correction = correction["is_correction"]
    result.correction_confidence = correction["confidence"]
    result.correction_type = correction["correction_type"]
    result.correction_insight = correction["extracted_insight"]

    # Detect response knowledge
    if assistant_response:
        response_knowledge = detect_response_knowledge(assistant_response)
        result.has_response_knowledge = response_knowledge.has_knowledge
        result.response_confidence = response_knowledge.confidence
        result.response_knowledge_type = response_knowledge.knowledge_type
        result.response_knowledge = response_knowledge.extracted_knowledge

    # Calculate total confidence (max of all signals)
    confidences = [
        result.teaching_confidence,
        result.correction_confidence,
        result.response_confidence,
    ]
    result.total_confidence = max(confidences)

    # Combine extracted knowledge
    knowledge_parts = []
    if result.teaching_knowledge:
        knowledge_parts.append(f"Teaching: {result.teaching_knowledge}")
    if result.correction_insight:
        knowledge_parts.append(f"Correction: {result.correction_insight}")
    if result.response_knowledge:
        knowledge_parts.append(f"Insight: {result.response_knowledge}")

    result.extracted_knowledge = " | ".join(knowledge_parts) if knowledge_parts else ""

    return result


def generate_classification_prompt(knowledge_result: KnowledgeResult) -> Dict[str, Any]:
    """
    Generate a classification prompt for user/project level classification.

    Creates an AskUserQuestion-compatible format for asking the user
    how to classify the extracted knowledge.

    Args:
        knowledge_result: The KnowledgeResult to generate prompt for

    Returns:
        Dictionary in AskUserQuestion format
    """
    # Get a preview of the knowledge (first 100 chars)
    preview = knowledge_result.extracted_knowledge[:100]
    if len(knowledge_result.extracted_knowledge) > 100:
        preview += "..."

    return {
        "questions": [{
            "question": f"How should this knowledge be classified?\n\"{preview}\"",
            "header": "Scope",
            "options": [
                {
                    "label": "User-level",
                    "description": "Applies across all projects (personal preferences, tool knowledge)"
                },
                {
                    "label": "Project-level",
                    "description": "Specific to this project only (local patterns, file paths)"
                },
                {
                    "label": "Skip",
                    "description": "Don't extract this as a skill"
                }
            ],
            "multiSelect": False
        }]
    }


def suggest_classification(knowledge_result: KnowledgeResult) -> str:
    """
    Provide a heuristic suggestion for classification.

    Uses simple heuristics to suggest whether knowledge should be
    user-level, project-level, or skipped.

    Args:
        knowledge_result: The KnowledgeResult to classify

    Returns:
        Suggested classification: "user", "project", or "skip"
    """
    knowledge = knowledge_result.extracted_knowledge.lower()

    # Project-level indicators (paths, specific services, accounts)
    project_indicators = [
        r"/src/", r"/lib/", r"/config/", r"/app/",  # Common paths
        r"\b\d{12}\b",  # AWS account IDs
        r"\.json\b", r"\.yaml\b", r"\.yml\b",  # Config file types
        r"\bthis\s+project\b", r"\bthis\s+repo\b",
        r"\bour\s+api\b", r"\bour\s+service\b",
    ]

    # User-level indicators (tools, general patterns)
    user_indicators = [
        r"\bdocker\b", r"\bgit\b", r"\bnpm\b", r"\bpython\b",
        r"\btypescript\b", r"\brust\b", r"\bgo\b",
        r"\balways\b", r"\bnever\b", r"\bprefer\b",
        r"\brestart\b", r"\bconfig\b", r"\bchanges\b",
    ]

    project_score = sum(1 for p in project_indicators if re.search(p, knowledge))
    user_score = sum(1 for p in user_indicators if re.search(p, knowledge))

    # Low confidence knowledge should be skipped
    if knowledge_result.total_confidence < 0.5:
        return "skip"

    if project_score > user_score:
        return "project"
    elif user_score > project_score:
        return "user"
    else:
        # Default to project if unclear (safer)
        return "project"


# Module exports
__all__ = [
    "detect_teaching",
    "detect_response_knowledge",
    "detect_knowledge",
    "generate_classification_prompt",
    "suggest_classification",
    "TeachingType",
    "ResponseKnowledgeType",
    "TeachingResult",
    "ResponseKnowledgeResult",
    "KnowledgeResult",
]


if __name__ == "__main__":
    # Demo when run directly
    import json

    print("Knowledge Detection Demo")
    print("=" * 70)

    # Test teaching detection
    teaching_tests = [
        "Remember that API calls should always include auth headers",
        "Always use TypeScript for new modules",
        "Never commit secrets to the repository",
        "I prefer functional components over class components",
        "For future reference, the deploy key is in 1Password",
        "Can you help me fix this bug?",  # Not teaching
    ]

    print("\n--- Teaching Detection ---")
    for msg in teaching_tests:
        result = detect_teaching(msg)
        print(f"\nMessage: '{msg}'")
        print(f"  Is Teaching: {result.is_teaching}")
        print(f"  Confidence: {result.confidence}")
        print(f"  Type: {result.teaching_type}")
        if result.extracted_knowledge:
            print(f"  Knowledge: {result.extracted_knowledge[:50]}...")

    # Test response knowledge detection
    print("\n--- Response Knowledge Detection ---")
    response_tests = [
        """After investigating, here's what I found:

        Key insight: The connection pool exhaustion happens because
        Lambda doesn't reuse connections across cold starts.""",

        """Done! I've updated the file as requested.""",  # No knowledge
    ]

    for resp in response_tests:
        result = detect_response_knowledge(resp)
        print(f"\nResponse: '{resp[:50]}...'")
        print(f"  Has Knowledge: {result.has_knowledge}")
        print(f"  Confidence: {result.confidence}")
        if result.extracted_knowledge:
            print(f"  Knowledge: {result.extracted_knowledge[:50]}...")

    # Test unified detection
    print("\n--- Unified Detection ---")
    unified_result = detect_knowledge(
        "Remember that we always use snake_case for database columns",
        "Key insight: The naming convention ensures consistency."
    )
    print(json.dumps(unified_result.to_dict(), indent=2))
