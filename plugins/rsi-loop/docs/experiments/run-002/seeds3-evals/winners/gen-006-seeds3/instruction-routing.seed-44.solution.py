import re
from typing import Optional, List


def solve(instruction: str) -> str:
    """Parse natural-language instruction and return the exact answer as a string."""

    instruction = instruction.strip()
    lower = instruction.lower()

    # Detect operation using robust keyword-based patterns
    # Ordered by specificity to minimize false matches

    # 1. LARGEST NUMBER: detect with multiple synonyms
    if _matches_largest(lower):
        return _handle_largest(instruction, lower)

    # 2. NTH ITEM: detect ordinals and list structure
    if _matches_nth_item(lower):
        return _handle_nth_item(instruction, lower)

    # 3. COUNT LETTERS: detect counting operations
    if _matches_count_letters(lower):
        return _handle_count_letters(instruction, lower)

    # 4. REVERSE WORD: detect reverse + word
    if _matches_reverse(lower):
        return _handle_reverse(instruction, lower)

    # 5. UPPERCASE WORD: detect uppercase + word
    if _matches_uppercase(lower):
        return _handle_uppercase(instruction, lower)

    # 6. MULTIPLY: detect multiply + by
    if _matches_multiply(lower):
        return _handle_multiply(instruction, lower)

    # 7. SUBTRACT: detect subtract + from
    if _matches_subtract(lower):
        return _handle_subtract(instruction, lower)

    # 8. ADD: detect add + and
    if _matches_add(lower):
        return _handle_add(instruction, lower)

    return ""


# ============================================================================
# DETECTION HELPERS (keyword-based with synonyms)
# ============================================================================


def _matches_largest(lower: str) -> bool:
    """Detect largest number operation."""
    has_keyword = re.search(
        r'\b(?:largest|greatest|max|maximum|biggest|highest)\b', lower
    )
    has_number = re.search(r'\bnumber\b|\bvalue\b', lower)
    has_list = '[' in lower and ']' in lower
    return bool(has_keyword and (has_number or has_list))


def _matches_nth_item(lower: str) -> bool:
    """Detect nth item from list operation."""
    # Detect ordinal (1st, 2nd, 3rd, etc.) or just numeric index
    has_ordinal = re.search(r'\d+(?:st|nd|rd|th)?\b', lower)
    # Check for item/element keyword or list presence
    has_item_keyword = re.search(r'\b(?:item|element)\b', lower)
    has_list = '[' in lower and ']' in lower
    # Must have ordinal and either item keyword or list
    return bool(has_ordinal and (has_item_keyword or has_list) and has_list)


def _matches_count_letters(lower: str) -> bool:
    """Detect count letters operation."""
    has_count = (
        re.search(r'\bhow\s+many\s+letters\b', lower)
        or re.search(r'\bcount.*\bletters?\b', lower)
        or re.search(r'\bletters\b.*\bhow\b', lower)
    )
    has_in = re.search(r'\bin\b', lower)
    return bool(has_count and has_in)


def _matches_reverse(lower: str) -> bool:
    """Detect word reversal operation."""
    return re.search(r'\breverse\b', lower) is not None and re.search(
        r'\bword\b', lower
    ) is not None


def _matches_uppercase(lower: str) -> bool:
    """Detect word uppercase operation."""
    return re.search(r'\buppercase\b', lower) is not None and re.search(
        r'\bword\b', lower
    ) is not None


def _matches_multiply(lower: str) -> bool:
    """Detect multiplication operation."""
    has_multiply = re.search(r'\bmultiply\b', lower)
    has_by = re.search(r'\bby\b', lower) or '×' in lower or '*' in lower
    return bool(has_multiply and has_by)


def _matches_subtract(lower: str) -> bool:
    """Detect subtraction operation."""
    has_subtract = re.search(r'\bsubtract\b', lower)
    has_from = re.search(r'\bfrom\b', lower)
    return bool(has_subtract and has_from)


def _matches_add(lower: str) -> bool:
    """Detect addition operation."""
    has_add = re.search(r'\badd\b', lower)
    has_and = re.search(r'\band\b', lower)
    return bool(has_add and has_and)


# ============================================================================
# HANDLER FUNCTIONS (extract and compute)
# ============================================================================


def _handle_add(instruction: str, lower: str) -> str:
    """Handle 'add X and Y' -> X + Y"""
    nums = _extract_numbers_in_order(instruction)
    if len(nums) >= 2:
        return str(nums[0] + nums[1])
    return ""


def _handle_subtract(instruction: str, lower: str) -> str:
    """Handle 'subtract X from Y' -> Y - X"""
    # Find position of "from" to split the instruction
    from_pos = lower.find("from")
    if from_pos == -1:
        return ""

    before_from = instruction[:from_pos]
    after_from = instruction[from_pos:]

    nums_before = _extract_numbers_in_order(before_from)
    nums_after = _extract_numbers_in_order(after_from)

    if nums_before and nums_after:
        # "subtract X from Y" means Y - X
        x = nums_before[-1]  # Last number before "from" is X
        y = nums_after[0]    # First number after "from" is Y
        return str(y - x)

    return ""


def _handle_multiply(instruction: str, lower: str) -> str:
    """Handle 'multiply X by Y' -> X * Y"""
    nums = _extract_numbers_in_order(instruction)
    if len(nums) >= 2:
        return str(nums[0] * nums[1])
    return ""


def _handle_reverse(instruction: str, lower: str) -> str:
    """Handle 'reverse the word X'"""
    word = _extract_word_after(instruction, lower, "word")
    if word:
        return word[::-1]
    return ""


def _handle_uppercase(instruction: str, lower: str) -> str:
    """Handle 'uppercase the word X'"""
    word = _extract_word_after(instruction, lower, "word")
    if word:
        return word.upper()
    return ""


def _handle_count_letters(instruction: str, lower: str) -> str:
    """Handle 'how many letters in X'"""
    word = _extract_word_after(instruction, lower, "in")
    if word:
        return str(len(word))
    return ""


def _handle_nth_item(instruction: str, lower: str) -> str:
    """Handle 'the Nth item in [...]'"""
    # Extract ordinal number (1st, 2nd, 3rd, etc.)
    ordinal_match = re.search(r'\b(\d+)(?:st|nd|rd|th)?\b', lower)
    if not ordinal_match:
        return ""

    try:
        index = int(ordinal_match.group(1)) - 1  # Convert to 0-based
    except (ValueError, IndexError):
        return ""

    # Extract list content from brackets
    list_match = re.search(r'\[(.*?)\]', instruction)
    if not list_match:
        return ""

    items_str = list_match.group(1)
    # Split by comma and clean items (strip whitespace and quotes)
    items = [_clean_item(item) for item in items_str.split(",")]

    if 0 <= index < len(items):
        return items[index]

    return ""


def _handle_largest(instruction: str, lower: str) -> str:
    """Handle 'the largest number in [...]'"""
    # Extract list content from brackets
    list_match = re.search(r'\[(.*?)\]', instruction)
    if not list_match:
        return ""

    items_str = list_match.group(1)
    # Extract all numbers from list
    numbers = _extract_numbers_in_order(items_str)

    if numbers:
        return str(max(numbers))

    return ""


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def _extract_numbers_in_order(text: str) -> List[int]:
    """Extract all integers (including negative) from text, preserving order."""
    # Match integers and floats, then convert to int
    matches = re.findall(r'-?\d+(?:\.\d+)?', text)
    result = []
    for m in matches:
        try:
            result.append(int(float(m)))
        except ValueError:
            pass
    return result


def _extract_word_after(instruction: str, lower: str, keyword: str) -> Optional[str]:
    """Extract the first word after a given keyword."""
    keyword_pos = lower.find(keyword)
    if keyword_pos == -1:
        return None

    # Get text after the keyword
    after_keyword = instruction[keyword_pos + len(keyword):].strip()

    # Extract the first word (alphanumeric and underscore sequence)
    word_match = re.search(r'[a-zA-Z0-9_]+', after_keyword)
    if word_match:
        return word_match.group()

    return None


def _clean_item(item: str) -> str:
    """Clean a list item: strip whitespace and quotes."""
    item = item.strip()
    # Strip common quote characters from both ends
    if item:
        item = item.strip('\'""`')
    return item
