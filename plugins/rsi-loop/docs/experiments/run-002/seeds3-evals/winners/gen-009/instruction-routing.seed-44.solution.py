import re
from typing import Optional, List


def solve(instruction: str) -> str:
    """Return the exact answer to one instruction, as a string."""

    # Normalize: lowercase, strip, collapse multiple spaces
    text = instruction.strip().lower()
    text = re.sub(r'\s+', ' ', text)

    # Dispatch based on operation type
    # Critical: check list operations first (distinctive patterns)
    # Then word operations, then arithmetic

    # 1. NTH ITEM - must come before LARGEST_NUMBER to avoid false matches
    if ("item in" in text or "element in" in text or "position in" in text or
        "place in" in text or "pick" in text or any(ord_word in text for ord_word in
        ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th", "10th",
         "11th", "12th", "13th", "14th", "15th", "16th", "17th", "18th", "19th", "20th",
         "21st", "22nd", "23rd", "24th", "25th", "26th", "27th", "28th", "29th", "30th",
         "31st", "32nd", "33rd", "34th", "35th"])):
        result = _nth_item(text)
        if result is not None:
            return result

    # 2. LARGEST NUMBER - must check list brackets
    if ("largest number" in text or "maximum number" in text or "biggest number" in text or
        "greatest number" in text or "highest number" in text or "max number" in text or
        "find the largest" in text or "find the biggest" in text or "find the maximum" in text):
        result = _largest_number(text)
        if result is not None:
            return result

    # 3. REVERSE WORD
    if ("reverse" in text or "flip" in text or "backwards" in text or "invert" in text) and "word" in text:
        result = _reverse_word(text)
        if result is not None:
            return result

    # 4. UPPERCASE WORD
    if ("uppercase" in text or "upper" in text or "capitalize" in text or "make uppercase" in text) and "word" in text:
        result = _uppercase_word(text)
        if result is not None:
            return result

    # 5. COUNT LETTERS
    if ("how many letters" in text or "count the letters" in text or "count letters" in text or
        "letters in" in text or "how many characters" in text or "letter count" in text or
        "character count" in text):
        result = _count_letters(text)
        if result is not None:
            return result

    # 6. MULTIPLY
    if ("multiply" in text or "product" in text or "times" in text or "multiplied by" in text):
        result = _multiply(text)
        if result is not None:
            return result

    # 7. ADD
    if ("add" in text or "plus" in text or "sum" in text or "combined" in text or "together" in text):
        result = _add(text)
        if result is not None:
            return result

    # 8. SUBTRACT
    if ("subtract" in text or "minus" in text or "difference" in text or "take away" in text or "remove" in text):
        result = _subtract(text)
        if result is not None:
            return result

    return ""


def _nth_item(text: str) -> Optional[str]:
    """Extract the nth item from a list. Robust against whitespace variation."""
    # Comprehensive ordinal map
    ordinals = {
        "1st": 0, "2nd": 1, "3rd": 2, "4th": 3, "5th": 4, "6th": 5,
        "7th": 6, "8th": 7, "9th": 8, "10th": 9, "11th": 10, "12th": 11,
        "13th": 12, "14th": 13, "15th": 14, "16th": 15, "17th": 16, "18th": 17,
        "19th": 18, "20th": 19, "21st": 20, "22nd": 21, "23rd": 22, "24th": 23,
        "25th": 24, "26th": 25, "27th": 26, "28th": 27, "29th": 28, "30th": 29,
        "31st": 30, "32nd": 31, "33rd": 32, "34th": 33, "35th": 34,
    }

    # Find ordinal pattern (explicit strings first)
    idx = None
    for ordinal_str, zero_idx in ordinals.items():
        if ordinal_str in text:
            idx = zero_idx
            break

    if idx is None:
        # Try numeric pattern "the N item" or "N-th item" or just "N item"
        # Match flexible patterns with or without "the", with flexible ordinal suffixes
        ordinal_match = re.search(
            r'(?:the\s+)?(\d+)(?:st|nd|rd|th)?\s+(?:item|element|thing|position|place)',
            text
        )
        if ordinal_match:
            try:
                idx = int(ordinal_match.group(1)) - 1
            except (ValueError, IndexError):
                return None

    if idx is None:
        return None

    # Extract list from brackets [...], handling flexible whitespace
    list_match = re.search(r'\[\s*([^\]]+)\s*\]', text)
    if not list_match:
        return None

    list_str = list_match.group(1)

    # Parse items: split by comma, strip whitespace and quotes
    items = []
    for item in list_str.split(","):
        item = item.strip()
        # Remove surrounding quotes if present (both single and double)
        if (item.startswith('"') and item.endswith('"')) or \
           (item.startswith("'") and item.endswith("'")):
            item = item[1:-1]
        items.append(item)

    # Bounds check - critical for robustness
    if 0 <= idx < len(items):
        return items[idx]

    return None


def _largest_number(text: str) -> Optional[str]:
    """Find the largest number in a list. Handles negatives and flexible formatting."""
    # Extract list from brackets [...], handling flexible whitespace
    list_match = re.search(r'\[\s*([^\]]+)\s*\]', text)
    if not list_match:
        return None

    list_str = list_match.group(1)

    # Extract all numbers (including negatives), parsing robustly
    numbers = []
    for item in list_str.split(","):
        item = item.strip()
        # Remove quotes if present
        if (item.startswith('"') and item.endswith('"')) or \
           (item.startswith("'") and item.endswith("'")):
            item = item[1:-1].strip()

        try:
            # Try integer first (most common)
            numbers.append(int(item))
        except ValueError:
            try:
                # Try float and convert to int (handles "3.0" -> 3)
                numbers.append(int(float(item)))
            except ValueError:
                # Skip non-numeric items
                pass

    if numbers:
        return str(max(numbers))

    return None


def _reverse_word(text: str) -> Optional[str]:
    """Reverse a word. Handles synonyms: reverse, flip, invert, backwards."""
    # Pattern: "(reverse|flip|invert|backwards) [the] word WORD"
    # Use looser regex to handle variations
    match = re.search(
        r'(?:reverse|flip|backwards|invert)\s+(?:the\s+)?word\s+([a-zA-Z]+)',
        text
    )
    if match:
        word = match.group(1)
        return word[::-1]

    return None


def _uppercase_word(text: str) -> Optional[str]:
    """Uppercase a word. Handles synonyms: uppercase, upper, capitalize."""
    # Pattern: "(uppercase|upper|capitalize|make uppercase) [the] word WORD"
    match = re.search(
        r'(?:uppercase|upper|capitalize|make uppercase)\s+(?:the\s+)?word\s+([a-zA-Z]+)',
        text
    )
    if match:
        word = match.group(1)
        return word.upper()

    return None


def _count_letters(text: str) -> Optional[str]:
    """Count letters in a word. Handles multiple phrasings."""
    # Multiple patterns for counting letters/characters
    patterns = [
        r'(?:how\s+many|count)\s+(?:letters|characters)\s+in\s+([a-zA-Z]+)',
        r'letters\s+in\s+([a-zA-Z]+)',
        r'characters\s+in\s+([a-zA-Z]+)',
        r'(?:letter|character)\s+count\s+(?:of|in)\s+([a-zA-Z]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            word = match.group(1)
            # Sanity check: word should be alphabetic and reasonable length
            if word.isalpha() and 1 <= len(word) <= 10000:
                return str(len(word))

    return None


def _multiply(text: str) -> Optional[str]:
    """Multiply two numbers. Handles variations like 'X times Y'."""
    # Try standard patterns: "multiply X by Y", "X times Y", etc.
    patterns = [
        r'(?:multiply|multiplied by)\s+(-?\d+)\s+(?:by|times|x)\s+(-?\d+)',
        r'(-?\d+)\s+(?:times|multiplied by)\s+(-?\d+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                a = int(match.group(1))
                b = int(match.group(2))
                return str(a * b)
            except (ValueError, IndexError):
                pass

    return None


def _add(text: str) -> Optional[str]:
    """Add two numbers. Handles 'add X and Y', 'X plus Y', etc."""
    # Patterns: "add X and Y", "X plus Y", "sum of X and Y"
    patterns = [
        r'add\s+(-?\d+)\s+and\s+(-?\d+)',
        r'(-?\d+)\s+(?:plus|and)\s+(-?\d+)',
        r'(?:sum|combined|total)\s+(?:of\s+)?(-?\d+)\s+(?:and|\+)\s+(-?\d+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                a = int(match.group(1))
                b = int(match.group(2))
                return str(a + b)
            except (ValueError, IndexError):
                pass

    return None


def _subtract(text: str) -> Optional[str]:
    """Subtract: extract Y from X (X - Y). Handles 'subtract Y from X', 'X minus Y'."""
    # Patterns: "subtract Y from X" (X - Y), "X minus Y" (X - Y)
    patterns = [
        r'subtract\s+(-?\d+)\s+from\s+(-?\d+)',
        r'(-?\d+)\s+(?:minus|take away|subtract|remove)\s+(-?\d+)',
        r'(?:difference|result)\s+(?:of|between|from)\s+(-?\d+)\s+(?:and|-)\s+(-?\d+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                # For "subtract Y from X" pattern: group 2 is X, group 1 is Y → X - Y
                if "subtract" in pattern and "from" in pattern:
                    y = int(match.group(1))
                    x = int(match.group(2))
                    return str(x - y)
                else:
                    # For "X minus Y" pattern: group 1 is X, group 2 is Y → X - Y
                    x = int(match.group(1))
                    y = int(match.group(2))
                    return str(x - y)
            except (ValueError, IndexError):
                pass

    return None
