import re
from typing import Optional, List


def solve(instruction: str) -> str:
    """Parse and execute a natural language instruction, returning the result as a string."""

    # Normalize: strip, lowercase, collapse whitespace
    normalized = re.sub(r'\s+', ' ', instruction.strip().lower())

    # Try operations in order of specificity/distinctiveness

    # 1. Reverse word - distinctive "reverse" keyword
    result = try_reverse_word(normalized)
    if result is not None:
        return result

    # 2. Uppercase word - distinctive "uppercase" keyword
    result = try_uppercase_word(normalized)
    if result is not None:
        return result

    # 3. Count letters - distinctive "how many letters" pattern or similar
    result = try_count_letters(normalized)
    if result is not None:
        return result

    # 4. Nth list item - distinctive "item in [...]" pattern
    result = try_nth_list_item(normalized)
    if result is not None:
        return result

    # 5. Largest number - distinctive "largest number in [...]" pattern
    result = try_largest_number(normalized)
    if result is not None:
        return result

    # 6. Arithmetic operations (harder to distinguish)
    # Add - "add X and Y" or alternatives
    result = try_add(normalized)
    if result is not None:
        return result

    # 7. Subtract - "subtract X from Y"
    result = try_subtract(normalized)
    if result is not None:
        return result

    # 8. Multiply - "multiply X by Y" or alternatives
    result = try_multiply(normalized)
    if result is not None:
        return result

    return ""


def extract_numbers(text: str) -> List[int]:
    """Extract all integers from text, handling negatives."""
    matches = re.findall(r'-?\d+', text)
    return [int(m) for m in matches]


def extract_list_content(text: str) -> Optional[List[str]]:
    """Extract list content from [item1, item2, ...] pattern."""
    match = re.search(r'\[(.*?)\]', text)
    if not match:
        return None

    content = match.group(1)
    # Split by comma and strip whitespace
    items = [item.strip() for item in content.split(',')]
    return items


def try_reverse_word(text: str) -> Optional[str]:
    """Try to match and execute reverse word operation."""
    if 'reverse' not in text:
        return None

    # Pattern: "reverse the word WORD" or "reverse WORD"
    match = re.search(r'reverse\s+(?:the\s+)?word\s+(\w+)', text)
    if match:
        word = match.group(1)
        return word[::-1]

    # Also try: "reverse word WORD" or just "reverse WORD"
    match = re.search(r'reverse\s+(\w+)', text)
    if match:
        word = match.group(1)
        return word[::-1]

    return None


def try_uppercase_word(text: str) -> Optional[str]:
    """Try to match and execute uppercase word operation."""
    if 'uppercase' not in text and 'upper' not in text:
        return None

    # Pattern: "uppercase the word WORD" or "uppercase WORD" or "upper word WORD"
    match = re.search(r'(?:uppercase|upper)\s+(?:the\s+)?word\s+(\w+)', text)
    if match:
        word = match.group(1)
        return word.upper()

    # Also try: "uppercase WORD" or "upper WORD"
    match = re.search(r'(?:uppercase|upper)\s+(\w+)', text)
    if match:
        word = match.group(1)
        return word.upper()

    return None


def try_count_letters(text: str) -> Optional[str]:
    """Try to match and execute count letters operation."""
    if 'letter' not in text and 'count' not in text:
        return None

    if 'in' not in text:
        return None

    # Pattern: "how many letters in WORD" or "count letters in WORD" or "letters in WORD"
    # or "count characters in WORD" etc.
    match = re.search(r'(?:how\s+many\s+)?(?:letters?|characters?)\s+in\s+(\w+)', text)
    if match:
        word = match.group(1)
        # Count only letters
        letter_count = sum(1 for c in word if c.isalpha())
        return str(letter_count)

    return None


def try_nth_list_item(text: str) -> Optional[str]:
    """Try to match and execute nth list item operation."""
    if 'item' not in text or 'in' not in text or '[' not in text:
        return None

    # Extract list first
    items = extract_list_content(text)
    if not items:
        return None

    # Try to find ordinal pattern: "the Nth item in [...]"
    # First try numeric ordinals with optional suffix
    ordinal_match = re.search(r'the\s+(\d+)(?:st|nd|rd|th)?\s+item', text)

    index = None
    if ordinal_match:
        try:
            index = int(ordinal_match.group(1)) - 1  # Convert to 0-indexed
        except ValueError:
            pass

    # If no numeric match, try word-based ordinals
    if index is None:
        word_ordinals = {
            'first': 0, 'second': 1, 'third': 2, 'fourth': 3, 'fifth': 4,
            'sixth': 5, 'seventh': 6, 'eighth': 7, 'ninth': 8, 'tenth': 9,
            'eleventh': 10, 'twelfth': 11, 'thirteenth': 12, 'fourteenth': 13,
            'fifteenth': 14, 'sixteenth': 15, 'seventeenth': 16, 'eighteenth': 17,
            'nineteenth': 18, 'twentieth': 19
        }
        for word, idx in word_ordinals.items():
            if f'the {word} item' in text:
                index = idx
                break

    if index is None:
        return None

    # Return item if in bounds (0-indexed)
    if 0 <= index < len(items):
        return items[index]

    return None


def try_largest_number(text: str) -> Optional[str]:
    """Try to match and execute largest number operation."""
    # Support multiple synonyms for "largest"
    if not any(word in text for word in ['largest', 'maximum', 'max', 'greatest', 'biggest', 'highest']):
        return None

    if 'number' not in text or '[' not in text:
        return None

    # Extract list
    items = extract_list_content(text)
    if not items:
        return None

    # Parse items as integers
    try:
        numbers = [int(item.strip()) for item in items]
    except ValueError:
        return None

    if not numbers:
        return None

    return str(max(numbers))


def try_add(text: str) -> Optional[str]:
    """Try to match and execute add operation."""
    # Support multiple synonyms for addition
    add_keywords = ['add', 'sum', 'total', 'plus']
    if not any(keyword in text for keyword in add_keywords):
        return None

    # Try multiple patterns for addition
    patterns = [
        r'add\s+(-?\d+)\s+and\s+(-?\d+)',
        r'add\s+(-?\d+)\s+plus\s+(-?\d+)',
        r'sum\s+(?:of\s+)?(-?\d+)\s+and\s+(-?\d+)',
        r'total\s+(?:of\s+)?(-?\d+)\s+and\s+(-?\d+)',
        r'(-?\d+)\s+plus\s+(-?\d+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            x = int(match.group(1))
            y = int(match.group(2))
            return str(x + y)

    return None


def try_subtract(text: str) -> Optional[str]:
    """Try to match and execute subtract operation."""
    if 'subtract' not in text:
        return None

    # Pattern: "subtract X from Y" → Y - X
    if 'from' not in text:
        return None

    match = re.search(r'subtract\s+(-?\d+)\s+from\s+(-?\d+)', text)
    if match:
        x = int(match.group(1))  # value to subtract
        y = int(match.group(2))  # value to subtract from
        return str(y - x)

    return None


def try_multiply(text: str) -> Optional[str]:
    """Try to match and execute multiply operation."""
    # Support multiple synonyms for multiplication
    multiply_keywords = ['multiply', 'product', 'times']
    if not any(keyword in text for keyword in multiply_keywords):
        return None

    # Try multiple patterns for multiplication
    patterns = [
        r'multiply\s+(-?\d+)\s+by\s+(-?\d+)',
        r'multiply\s+(-?\d+)\s+times\s+(-?\d+)',
        r'product\s+(?:of\s+)?(-?\d+)\s+(?:and\s+)?(-?\d+)',
        r'(-?\d+)\s+times\s+(-?\d+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            x = int(match.group(1))
            y = int(match.group(2))
            return str(x * y)

    return None
