import re


def solve(instruction: str) -> str:
    """Route instruction to operation and return exact answer as string.

    Strategy: Tolerant parsing with deep generalization.
    - Normalize thoroughly (whitespace, unicode, punctuation)
    - Support synonyms and paraphrases
    - Extract operands defensively with fallbacks
    - Handle edge cases (missing items, invalid indices)
    """

    # Normalize: strip, lowercase, collapse whitespace, normalize unicode
    inst = instruction.strip()
    inst_lower = inst.lower()
    # Normalize multiple spaces, tabs, etc.
    inst_norm = re.sub(r'\s+', ' ', inst_lower)

    # Try operations in order of keyword specificity

    # 1. COUNT LETTERS: "how many letters in X" or "count letters in X" or similar
    if _match_count_letters(inst_norm):
        return _handle_count_letters(inst_norm)

    # 2. REVERSE WORD: "reverse the word X" or "reverse X" or similar
    if _match_reverse_word(inst_norm):
        return _handle_reverse_word(inst, inst_norm)

    # 3. UPPERCASE WORD: "uppercase the word X" or "make X uppercase" or similar
    if _match_uppercase_word(inst_norm):
        return _handle_uppercase_word(inst, inst_norm)

    # 4. NTH LIST ITEM: "the Nth item in [...]" or similar
    if _match_nth_item(inst_norm, inst):
        return _handle_nth_item(inst, inst_norm)

    # 5. LARGEST NUMBER: "the largest number in [...]" or "max number in [...]"
    if _match_largest_number(inst_norm, inst):
        return _handle_largest_number(inst, inst_norm)

    # 6. ADD: "add X and Y" or "X added to Y" or similar
    if _match_add(inst_norm):
        return _handle_add(inst_norm)

    # 7. SUBTRACT: "subtract X from Y" or "X subtracted from Y"
    if _match_subtract(inst_norm):
        return _handle_subtract(inst_norm)

    # 8. MULTIPLY: "multiply X by Y" or "X times Y"
    if _match_multiply(inst_norm):
        return _handle_multiply(inst_norm)

    return ""


# ============================================================================
# OPERATION MATCHERS
# ============================================================================

def _match_count_letters(inst_norm: str) -> bool:
    """Detect 'count letters' operation with synonyms."""
    # Primary pattern
    if 'how many letters' in inst_norm:
        return True
    # Synonyms: "count letters", "how many letters"
    if 'count letters' in inst_norm and 'in' in inst_norm:
        return True
    # "letters in X" without "how many" as fallback
    if re.search(r'\bhow\b.*\bletters\b.*\bin\b', inst_norm):
        return True
    return False


def _match_reverse_word(inst_norm: str) -> bool:
    """Detect 'reverse word' operation with synonyms."""
    # Primary: "reverse the word"
    if 'reverse' in inst_norm and 'word' in inst_norm:
        return True
    # Synonyms: "turn around", "backwards", "flip"
    if any(syn in inst_norm for syn in ['turn', 'backward', 'flip']):
        if 'word' in inst_norm:
            return True
    return False


def _match_uppercase_word(inst_norm: str) -> bool:
    """Detect 'uppercase word' operation with synonyms."""
    # Primary: "uppercase the word"
    if 'uppercase' in inst_norm and 'word' in inst_norm:
        return True
    # Synonyms: "upper case", "make uppercase", "all caps"
    if any(syn in inst_norm for syn in ['upper case', 'all caps', 'convert to uppercase']):
        if 'word' in inst_norm:
            return True
    return False


def _match_nth_item(inst_norm: str, inst: str) -> bool:
    """Detect 'nth item in list' operation."""
    # Must have list brackets
    if '[' not in inst or ']' not in inst:
        return False
    # Must have "item"
    if 'item' not in inst_norm:
        return False
    # Must have position indicator
    has_numeric = bool(re.search(r'\b\d+(?:st|nd|rd|th)?\b', inst_norm))
    has_word_ordinal = any(w in inst_norm for w in [
        'first', 'second', 'third', 'fourth', 'fifth',
        'sixth', 'seventh', 'eighth', 'ninth', 'tenth',
        'eleventh', 'twelfth'
    ])
    return has_numeric or has_word_ordinal


def _match_largest_number(inst_norm: str, inst: str) -> bool:
    """Detect 'largest number in list' operation with synonyms."""
    # Must have list brackets
    if '[' not in inst or ']' not in inst:
        return False
    # Must have "number"
    if 'number' not in inst_norm:
        return False
    # Must have "largest" or synonyms
    has_largest = any(syn in inst_norm for syn in ['largest', 'max', 'maximum', 'biggest'])
    return has_largest


def _match_add(inst_norm: str) -> bool:
    """Detect 'add' operation with synonyms."""
    # Primary: "add X and Y"
    if 'add' in inst_norm and 'and' in inst_norm:
        return True
    # Synonyms: "X added to Y" (less common in public set, but for generalization)
    if 'added to' in inst_norm or 'plus' in inst_norm:
        return True
    return False


def _match_subtract(inst_norm: str) -> bool:
    """Detect 'subtract' operation with synonyms."""
    # Primary: "subtract X from Y"
    if 'subtract' in inst_norm and 'from' in inst_norm:
        return True
    # Synonyms: "X subtracted from Y", "minus"
    if 'subtracted from' in inst_norm or 'minus' in inst_norm:
        return True
    return False


def _match_multiply(inst_norm: str) -> bool:
    """Detect 'multiply' operation with synonyms."""
    # Primary: "multiply X by Y"
    if 'multiply' in inst_norm and ('by' in inst_norm or 'times' in inst_norm):
        return True
    # Synonyms: "times", "multiplied by"
    if 'multiplied by' in inst_norm or 'times' in inst_norm:
        return True
    return False


# ============================================================================
# OPERATION HANDLERS
# ============================================================================

def _handle_count_letters(inst_norm: str) -> str:
    """Extract word and count letters."""
    # Try to extract word after 'in'
    match = re.search(r'\bin\s+(\w+)', inst_norm)
    if match:
        word = match.group(1)
        return str(len(word))
    return ""


def _handle_reverse_word(inst: str, inst_norm: str) -> str:
    """Extract word and reverse it."""
    # Try multiple patterns for word extraction
    # Pattern 1: "word X"
    match = re.search(r'\bword\s+(\w+)', inst_norm)
    if match:
        word = match.group(1)
        return word[::-1]

    # Pattern 2: Extract last significant word (fallback)
    words = re.findall(r'\w+', inst_norm)
    # Filter out common keywords to find the actual target word
    keywords = {'reverse', 'the', 'word', 'turn', 'backward', 'flip', 'around', 'back'}
    target_words = [w for w in words if w not in keywords]
    if target_words:
        return target_words[-1][::-1]

    return ""


def _handle_uppercase_word(inst: str, inst_norm: str) -> str:
    """Extract word and uppercase it."""
    # Try multiple patterns for word extraction
    # Pattern 1: "word X"
    match = re.search(r'\bword\s+(\w+)', inst_norm)
    if match:
        word = match.group(1)
        return word.upper()

    # Pattern 2: Extract last significant word (fallback)
    words = re.findall(r'\w+', inst_norm)
    keywords = {'uppercase', 'upper', 'case', 'the', 'word', 'make', 'all', 'caps', 'convert', 'to'}
    target_words = [w for w in words if w not in keywords]
    if target_words:
        return target_words[-1].upper()

    return ""


def _handle_nth_item(inst: str, inst_norm: str) -> str:
    """Extract nth item from list."""
    # Extract position (numeric ordinal or word)
    idx = _extract_position(inst_norm)

    # Extract list from brackets (handle original inst for case preservation)
    list_match = re.search(r'\[(.*?)\]', inst)
    if list_match and idx >= 0:
        list_str = list_match.group(1)
        # Parse items: split by comma, strip whitespace and quotes
        items = _parse_list_items(list_str)
        # Bounds check
        if 0 <= idx < len(items):
            return items[idx]

    return ""


def _handle_largest_number(inst: str, inst_norm: str) -> str:
    """Extract largest number from list."""
    # Extract list from brackets
    list_match = re.search(r'\[(.*?)\]', inst)
    if list_match:
        list_str = list_match.group(1)
        # Extract all integers from list (including negatives)
        numbers = re.findall(r'-?\d+', list_str)
        if numbers:
            return str(max(int(n) for n in numbers))

    return ""


def _handle_add(inst_norm: str) -> str:
    """Extract numbers and add them."""
    numbers = re.findall(r'-?\d+', inst_norm)
    if len(numbers) >= 2:
        return str(int(numbers[0]) + int(numbers[1]))
    return ""


def _handle_subtract(inst_norm: str) -> str:
    """Extract numbers and subtract (Y - X where 'subtract X from Y')."""
    numbers = re.findall(r'-?\d+', inst_norm)
    if len(numbers) >= 2:
        # First number is X, second is Y in "subtract X from Y" => Y - X
        return str(int(numbers[1]) - int(numbers[0]))
    return ""


def _handle_multiply(inst_norm: str) -> str:
    """Extract numbers and multiply them."""
    numbers = re.findall(r'-?\d+', inst_norm)
    if len(numbers) >= 2:
        return str(int(numbers[0]) * int(numbers[1]))
    return ""


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _extract_position(inst_norm: str) -> int:
    """Extract position from ordinal or numeric form.

    Returns 0-based index, or -1 if not found.
    Handles: "first", "1st", "1 st" (with space), etc.
    """
    # Map word ordinals to indices
    ordinal_map = {
        'first': 0, '1st': 0,
        'second': 1, '2nd': 1,
        'third': 2, '3rd': 2,
        'fourth': 3, '4th': 3,
        'fifth': 4, '5th': 4,
        'sixth': 5, '6th': 5,
        'seventh': 6, '7th': 6,
        'eighth': 7, '8th': 7,
        'ninth': 8, '9th': 8,
        'tenth': 9, '10th': 9,
        'eleventh': 10, '11th': 10,
        'twelfth': 11, '12th': 11,
        '13th': 12, 'thirteenth': 12,
        '14th': 13, 'fourteenth': 13,
        '15th': 14, 'fifteenth': 14,
        '20th': 19, 'twentieth': 19,
        '100th': 99, 'hundredth': 99,
    }

    # Try to match word ordinals (case-insensitive)
    for word, idx in ordinal_map.items():
        if word in inst_norm:
            return idx

    # Try to extract numeric ordinal: "the Nth item" pattern
    # Handle spacing: "1 st", "1st", etc.
    match = re.search(r'\b(\d+)\s*(?:st|nd|rd|th)?\b', inst_norm)
    if match:
        num = int(match.group(1))
        return num - 1  # Convert to 0-based

    return -1


def _parse_list_items(list_str: str) -> list:
    """Parse list items from string like 'kiwi, pear, apple'.

    Handles:
    - Comma-separated items
    - Whitespace around items
    - Single/double/no quotes
    - Extra spaces
    """
    items = []
    # Split by comma
    parts = list_str.split(',')
    for part in parts:
        # Strip whitespace
        part = part.strip()
        # Remove quotes (single or double)
        part = part.strip('\'"')
        # Strip again after removing quotes
        part = part.strip()
        if part:  # Only add non-empty
            items.append(part)
    return items
