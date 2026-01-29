#!/usr/bin/env python3
"""Claudeception v4.0 - Correction Detection Module.

Detects when a user is correcting Claude's behavior and extracts insights
about what the correct behavior should be. This enables learning from
mistakes and user feedback.

Detection categories:
- Direct negation: "no, ", "no that's", "no I meant"
- Wrong assessment: "wrong", "that's wrong", "incorrect"
- Clarification: "actually", "actually I want"
- Contrast patterns: "not X, Y", "not X but Y", "I said X not Y"
- Commands: "don't", "stop", "instead"
- Misunderstanding: "you misunderstood", "that's not what I"
- Negation with reference: mentions previous response + negative sentiment

The module is robust to typos (fuzzy matching for common corrections).
"""

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from enum import Enum
from typing import Any, Optional


class CorrectionType(Enum):
    """Types of corrections users make."""

    DIRECT_NEGATION = "direct_negation"
    WRONG_ASSESSMENT = "wrong_assessment"
    CLARIFICATION = "clarification"
    CONTRAST = "contrast"
    COMMAND = "command"
    MISUNDERSTANDING = "misunderstanding"
    NEGATION_REFERENCE = "negation_reference"
    UNKNOWN = "unknown"


@dataclass
class CorrectionResult:
    """Result of correction detection."""

    is_correction: bool
    confidence: float
    correction_type: str
    extracted_insight: str
    matched_patterns: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "is_correction": self.is_correction,
            "confidence": self.confidence,
            "correction_type": self.correction_type,
            "extracted_insight": self.extracted_insight,
            "matched_patterns": self.matched_patterns,
        }


# Pattern definitions with weights for confidence scoring
# Format: (pattern, weight, correction_type)
CORRECTION_PATTERNS: list[tuple[str, float, CorrectionType]] = [
    # Direct negation patterns (high confidence when at start)
    (r"^no[,\.\s]", 0.7, CorrectionType.DIRECT_NEGATION),
    (r"^no\s+that'?s", 0.85, CorrectionType.DIRECT_NEGATION),
    (r"^no\s+i\s+(meant|want|need|said)", 0.9, CorrectionType.DIRECT_NEGATION),
    (r"^no\s+no\s+no", 0.95, CorrectionType.DIRECT_NEGATION),
    (r"^nope[,\.\s]", 0.7, CorrectionType.DIRECT_NEGATION),
    # Wrong assessment patterns
    (r"\b(that'?s\s+)?wrong\b", 0.8, CorrectionType.WRONG_ASSESSMENT),
    (r"\b(that'?s\s+)?incorrect\b", 0.85, CorrectionType.WRONG_ASSESSMENT),
    (r"\b(that'?s\s+)?not\s+right\b", 0.75, CorrectionType.WRONG_ASSESSMENT),
    (r"\b(that'?s\s+)?not\s+correct\b", 0.8, CorrectionType.WRONG_ASSESSMENT),
    (r"\bthat'?s\s+not\s+it\b", 0.75, CorrectionType.WRONG_ASSESSMENT),
    (r"\byou('re|\s+are)\s+wrong\b", 0.85, CorrectionType.WRONG_ASSESSMENT),
    # Clarification patterns
    (r"^actually[,\s]", 0.7, CorrectionType.CLARIFICATION),
    (r"^actually\s+i\s+(want|meant|need)", 0.85, CorrectionType.CLARIFICATION),
    (r"\bwhat\s+i\s+(actually\s+)?(meant|want|need)\b", 0.8, CorrectionType.CLARIFICATION),
    (r"\bi\s+meant\s+to\s+say\b", 0.85, CorrectionType.CLARIFICATION),
    (r"\blet\s+me\s+(clarify|rephrase|explain)\b", 0.6, CorrectionType.CLARIFICATION),
    # Contrast patterns ("not X, Y" / "not X but Y")
    (r"\bnot\s+\w+[,\s]+but\s+", 0.85, CorrectionType.CONTRAST),
    (r"\bnot\s+\w+[,\s]+\w+\b", 0.5, CorrectionType.CONTRAST),
    (r"\bi\s+said\s+\w+\s+not\s+\w+", 0.9, CorrectionType.CONTRAST),
    (r"\bi\s+asked\s+for\s+\w+\s+not\s+\w+", 0.9, CorrectionType.CONTRAST),
    (r"\bi\s+asked\s+for\s+\w+,?\s+not\s+\w+", 0.9, CorrectionType.CONTRAST),
    (r"\b\w+,\s+not\s+\w+", 0.75, CorrectionType.CONTRAST),  # "X, not Y" format
    (r"\binstead\s+of\s+\w+[,\s]+", 0.7, CorrectionType.CONTRAST),
    (r"\brather\s+than\s+", 0.6, CorrectionType.CONTRAST),
    # Command patterns
    (r"^don'?t\b", 0.75, CorrectionType.COMMAND),
    (r"^stop\b", 0.8, CorrectionType.COMMAND),
    (r"^instead[,\s]", 0.7, CorrectionType.COMMAND),
    (r"\bplease\s+don'?t\b", 0.7, CorrectionType.COMMAND),
    (r"\bstop\s+(doing|using|making)\b", 0.85, CorrectionType.COMMAND),
    (r"\bdon'?t\s+(do|use|make)\s+that\b", 0.8, CorrectionType.COMMAND),
    (r"\bnever\s+(do|use|make)\b", 0.7, CorrectionType.COMMAND),
    # Misunderstanding patterns
    (r"\byou\s+misunderstood\b", 0.95, CorrectionType.MISUNDERSTANDING),
    (r"\bthat'?s\s+not\s+what\s+i\b", 0.9, CorrectionType.MISUNDERSTANDING),
    (r"\bi\s+didn'?t\s+(mean|ask|want|say)\s+that\b", 0.85, CorrectionType.MISUNDERSTANDING),
    (r"\bthat'?s\s+a\s+misunderstanding\b", 0.95, CorrectionType.MISUNDERSTANDING),
    (r"\byou\s+got\s+it\s+wrong\b", 0.9, CorrectionType.MISUNDERSTANDING),
    (r"\byou'?re\s+misunderstanding\b", 0.9, CorrectionType.MISUNDERSTANDING),
    (r"\bnot\s+what\s+i\s+(meant|asked|wanted)\b", 0.85, CorrectionType.MISUNDERSTANDING),
    (r"\ba\s+misunderstanding\b", 0.7, CorrectionType.MISUNDERSTANDING),  # "a misunderstanding" anywhere
    (r"\bmisunderstanding\b", 0.6, CorrectionType.MISUNDERSTANDING),  # Standalone "misunderstanding"
]

# Common typos for correction words (fuzzy matching)
TYPO_CORRECTIONS: dict[str, list[str]] = {
    "no": ["bo", "ni", "np", "mo"],
    "wrong": ["worng", "wrogn", "wrongg", "wronf", "wrnog"],
    "incorrect": ["incorect", "incorret", "incorrct", "inccorect"],
    "actually": ["actualy", "acutally", "acctualy", "actully", "acutlly"],
    "instead": ["insted", "insead", "intead", "insteda"],
    "dont": ["dnt", "donr", "dotn"],
    "stop": ["stpo", "sotp", "stopp"],
    "misunderstood": ["misundertood", "misundertsood", "misunderstod"],
    "thats": ["taht's", "tht's", "tahts"],
    "meant": ["ment", "menat", "maent"],
}

# Words that indicate reference to previous response
REFERENCE_WORDS = [
    "that",
    "this",
    "it",
    "your",
    "you",
    "the response",
    "what you said",
    "what you did",
    "above",
    "previous",
]

# Negative sentiment words
NEGATIVE_WORDS = [
    "wrong",
    "incorrect",
    "bad",
    "no",
    "not",
    "dont",
    "shouldnt",
    "cant",
    "wont",
    "never",
    "stop",
    "mistake",
    "error",
    "problem",
    "issue",
    "fix",
    "change",
    "different",
    "other",
    "else",
]


def normalize_text(text: str) -> str:
    """Normalize text for pattern matching."""
    # Convert to lowercase
    text = text.lower()
    # Normalize whitespace
    return " ".join(text.split())


def fix_common_typos(text: str) -> str:
    """Apply common typo corrections for better matching."""
    fixed = text.lower()
    for correct, typos in TYPO_CORRECTIONS.items():
        for typo in typos:
            # Use word boundaries to avoid partial matches
            pattern = r"\b" + re.escape(typo) + r"\b"
            fixed = re.sub(pattern, correct, fixed)
    return fixed


def fuzzy_match(word: str, target: str, threshold: float = 0.8) -> bool:
    """Check if word fuzzy-matches target (for typo tolerance)."""
    if len(word) < 2 or len(target) < 2:
        return word == target
    ratio = SequenceMatcher(None, word.lower(), target.lower()).ratio()
    return ratio >= threshold


def detect_typo_correction(text: str, correction_word: str) -> Optional[tuple[str, float]]:
    """Detect if a typo version of a correction word is present.

    Returns (matched_word, confidence_penalty) or None.
    """
    words = text.lower().split()
    for word in words:
        if fuzzy_match(word, correction_word, threshold=0.75):
            if word != correction_word.lower():
                # It is a typo - return with slight confidence penalty
                return (word, 0.9)  # 10% confidence penalty for typo
            return (word, 1.0)  # Exact match
    return None


def detect_negation_with_reference(text: str, previous_response: str = "") -> tuple[bool, float]:
    """Detect negation combined with reference to previous response.

    This catches cases like "thats not what I wanted" or "your answer is wrong".
    """
    text_lower = text.lower()

    # Check for reference words
    has_reference = any(ref in text_lower for ref in REFERENCE_WORDS)

    # Check for negative sentiment
    negative_count = sum(1 for neg in NEGATIVE_WORDS if neg in text_lower)

    # If both reference and negative words present, likely a correction
    if has_reference and negative_count >= 1:
        confidence = min(0.4 + (negative_count * 0.15), 0.85)
        return (True, confidence)

    return (False, 0.0)


def extract_correction_insight(user_message: str, previous_response: str = "") -> str:
    """Extract what the correct behavior should be from a correction message.

    Analyzes the user's correction to understand what they actually wanted
    instead of what Claude provided.

    Args:
        user_message: The user's correction message
        previous_response: Optional previous Claude response for context

    Returns:
        A string describing the extracted insight about correct behavior
    """
    text = normalize_text(user_message)
    insights = []

    # Pattern 1: "not X, Y" or "not X but Y" - extract Y as the desired behavior
    contrast_match = re.search(r"not\s+(\w+(?:\s+\w+)?)[,\s]+(?:but\s+)?(\w+(?:\s+\w+)?)", text)
    if contrast_match:
        unwanted = contrast_match.group(1)
        wanted = contrast_match.group(2)
        insights.append(f"User wants '{wanted}' instead of '{unwanted}'")

    # Pattern 2: "I want/need/meant X" - extract X
    want_match = re.search(r"i\s+(want|need|meant|asked\s+for)\s+(.+?)(?:\.|,|$)", text)
    if want_match:
        action = want_match.group(1)
        target = want_match.group(2).strip()
        insights.append(f"User {action}: '{target}'")

    # Pattern 3: "instead X" or "instead of X, Y" - extract the desired action
    instead_match = re.search(r"instead(?:\s+of\s+\w+)?[,\s]+(\w+.+?)(?:\.|,|$)", text)
    if instead_match:
        desired = instead_match.group(1).strip()
        insights.append(f"User wants instead: '{desired}'")

    # Pattern 4: "dont X" - extract what NOT to do
    dont_match = re.search(r"(?:don'?t|do\s+not|never)\s+(\w+.+?)(?:\.|,|$)", text)
    if dont_match:
        avoid = dont_match.group(1).strip()
        insights.append(f"Avoid: '{avoid}'")

    # Pattern 5: "should/shouldve X" - extract expected behavior
    should_match = re.search(r"(?:should|should'?ve|should\s+have)\s+(\w+.+?)(?:\.|,|$)", text)
    if should_match:
        expected = should_match.group(1).strip()
        insights.append(f"Expected behavior: '{expected}'")

    # Pattern 6: Check for specific task correction
    # "I asked for X" or "I said X"
    asked_match = re.search(r"i\s+(?:asked|said|told|requested)\s+(?:for\s+)?(.+?)(?:\.|,|!|$)", text)
    if asked_match:
        original_request = asked_match.group(1).strip()
        insights.append(f"Original request: '{original_request}'")

    # If no specific patterns matched, try to extract the key complaint
    if not insights:
        # Look for sentences after negation words
        sentences = re.split(r"[.!?]", text)
        for sentence in sentences:
            stripped_sentence = sentence.strip()
            if any(neg in stripped_sentence for neg in ["wrong", "incorrect", "not what"]):
                # This sentence contains the complaint
                insights.append(f"Issue: '{stripped_sentence}'")
                break

    if insights:
        return " | ".join(insights)

    return "Unable to extract specific insight - manual review recommended"


def detect_correction(user_message: str, previous_response: str = "") -> dict[str, Any]:
    """Detect if a user message is correcting Claude's behavior.

    Analyzes the message for correction patterns and returns a detailed
    result including confidence score and extracted insights.

    Args:
        user_message: The user's message to analyze
        previous_response: Optional previous Claude response for context

    Returns:
        Dictionary with:
        - is_correction: bool - Whether this is a correction
        - confidence: float - Confidence score (0.0 to 1.0)
        - correction_type: str - Type of correction detected
        - extracted_insight: str - What the correct behavior should be
        - matched_patterns: list - Patterns that matched
    """
    if not user_message or not user_message.strip():
        return CorrectionResult(
            is_correction=False,
            confidence=0.0,
            correction_type=CorrectionType.UNKNOWN.value,
            extracted_insight="",
            matched_patterns=[],
        ).to_dict()

    # Normalize and fix typos
    original_text = user_message
    normalized = normalize_text(user_message)
    typo_fixed = fix_common_typos(normalized)

    matched_patterns: list[str] = []
    max_confidence = 0.0
    detected_type = CorrectionType.UNKNOWN

    # Test against all patterns
    for pattern, weight, correction_type in CORRECTION_PATTERNS:
        # Try both normalized and typo-fixed versions
        for text_variant in [normalized, typo_fixed]:
            match = re.search(pattern, text_variant, re.IGNORECASE)
            if match:
                matched_patterns.append(f"{pattern} -> '{match.group()}'")

                # Apply position bonus for start-of-message patterns
                position_bonus = 0.0
                if pattern.startswith("^") and match.start() == 0:
                    position_bonus = 0.1

                # Apply typo penalty if using typo-fixed text
                typo_penalty = 0.0
                if text_variant == typo_fixed and text_variant != normalized:
                    typo_penalty = 0.05

                confidence = min(weight + position_bonus - typo_penalty, 1.0)

                if confidence > max_confidence:
                    max_confidence = confidence
                    detected_type = correction_type

    # Check for negation with reference (catches implicit corrections)
    neg_ref_detected, neg_ref_confidence = detect_negation_with_reference(normalized, previous_response)
    if neg_ref_detected and neg_ref_confidence > max_confidence:
        max_confidence = neg_ref_confidence
        detected_type = CorrectionType.NEGATION_REFERENCE
        matched_patterns.append("negation_with_reference")

    # Determine if this is a correction
    is_correction = max_confidence >= 0.5

    # Extract insight if it is a correction
    extracted_insight = ""
    if is_correction:
        extracted_insight = extract_correction_insight(original_text, previous_response)

    return CorrectionResult(
        is_correction=is_correction,
        confidence=round(max_confidence, 3),
        correction_type=detected_type.value,
        extracted_insight=extracted_insight,
        matched_patterns=matched_patterns,
    ).to_dict()


def analyze_correction_batch(messages: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Analyze a batch of messages for corrections.

    Useful for analyzing conversation history to find all corrections.

    Args:
        messages: List of dicts with 'user' and optionally 'assistant' keys

    Returns:
        List of detection results for each message
    """
    results = []
    previous_response = ""

    for msg in messages:
        user_message = msg.get("user", "")
        if user_message:
            result = detect_correction(user_message, previous_response)
            result["original_message"] = user_message
            results.append(result)

        # Update previous response for context
        assistant_response = msg.get("assistant", "")
        if assistant_response:
            previous_response = assistant_response

    return results


# Module-level convenience exports
__all__ = [
    "CorrectionResult",
    "CorrectionType",
    "analyze_correction_batch",
    "detect_correction",
    "extract_correction_insight",
]


if __name__ == "__main__":
    # Demo/test when run directly
    import json
    import sys

    test_messages = [
        "No, I meant the other file",
        "That's wrong, it should be blue not red",
        "Actually I want a Python script not JavaScript",
        "Stop using that approach",
        "You misunderstood - I asked for the tests",
        "don't use emojis please",
        "worng answer",  # Typo test
        "I said function not class",
        "Thanks, that's perfect!",  # Not a correction
        "Can you help me?",  # Not a correction
    ]

    print("Correction Detection Demo")
    print("=" * 70)

    for msg in test_messages:
        result = detect_correction(msg)
        print(f"\nMessage: '{msg}'")
        print(f"  Is Correction: {result['is_correction']}")
        print(f"  Confidence: {result['confidence']}")
        print(f"  Type: {result['correction_type']}")
        if result["extracted_insight"]:
            print(f"  Insight: {result['extracted_insight']}")

    # If stdin has input, process it
    if not sys.stdin.isatty():
        print("\n" + "=" * 70)
        print("Processing stdin input...")
        try:
            input_data = sys.stdin.read().strip()
            if input_data:
                result = detect_correction(input_data)
                print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Error processing input: {e}", file=sys.stderr)
            sys.exit(1)
