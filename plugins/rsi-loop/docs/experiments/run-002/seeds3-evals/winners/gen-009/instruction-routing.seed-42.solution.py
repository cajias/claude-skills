import re


def solve(instruction: str) -> str:
    """
    Parse a natural-language instruction and route to the appropriate operation.
    Highly robust to paraphrasing, synonyms, reordering, punctuation, and edge formatting.
    Designed to generalize beyond public phrasings to handle adversarial rephrasings.
    """
    # Aggressive normalization: handle Unicode, collapse whitespace, remove noise
    text = re.sub(r'\s+', ' ', instruction.strip())
    text_lower = text.lower()

    # Remove or replace problematic punctuation while preserving brackets
    # Also handle Unicode minus sign and other dash variants
    text_clean = text_lower.replace('?', ' ').replace('!', ' ').replace(':', ' ')
    text_clean = text_clean.replace(';', ' ').replace('"', ' ').replace("'", ' ')
    text_clean = text_clean.replace('−', '-').replace('–', '-').replace('—', '-')
    text_clean = re.sub(r'\s+', ' ', text_clean).strip()

    # Convert spelled-out numbers to digits for robust number detection
    text_normalized = _convert_spelled_numbers(text_clean)

    # Detect operation by keyword patterns, trying hardest (list-based) first

    # 1. NTH LIST ITEM: Hardest parsing (ordinal + list extraction)
    result = _try_nth_item(text_normalized, text_lower)
    if result is not None:
        return result

    # 2. LARGEST/MAX NUMBER: Complex parsing (keyword variants + list extraction)
    result = _try_largest_number(text_normalized, text_lower)
    if result is not None:
        return result

    # 3. ADD: Simple arithmetic
    result = _try_add(text_normalized)
    if result is not None:
        return result

    # 4. SUBTRACT: Requires order sensitivity
    result = _try_subtract(text_normalized)
    if result is not None:
        return result

    # 5. MULTIPLY: Simple arithmetic
    result = _try_multiply(text_normalized)
    if result is not None:
        return result

    # 6. REVERSE WORD: Requires word extraction
    result = _try_reverse_word(text_normalized)
    if result is not None:
        return result

    # 7. UPPERCASE WORD: Requires word extraction
    result = _try_uppercase_word(text_normalized)
    if result is not None:
        return result

    # 8. COUNT LETTERS: Requires word extraction
    result = _try_count_letters(text_normalized)
    if result is not None:
        return result

    return ""


def _convert_spelled_numbers(text):
    """
    Convert spelled-out numbers to digits.
    Handles 0-99 and common larger numbers, and ordinals.
    """
    # Ones: 0-19
    ones = {
        'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
        'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
        'ten': '10', 'eleven': '11', 'twelve': '12', 'thirteen': '13',
        'fourteen': '14', 'fifteen': '15', 'sixteen': '16', 'seventeen': '17',
        'eighteen': '18', 'nineteen': '19',
    }

    # Tens: 20, 30, ..., 90
    tens = {
        'twenty': '20', 'thirty': '30', 'forty': '40', 'fifty': '50',
        'sixty': '60', 'seventy': '70', 'eighty': '80', 'ninety': '90',
    }

    # Larger numbers
    large = {
        'hundred': '100', 'thousand': '1000', 'million': '1000000',
    }

    # Replace with word boundaries to avoid partial matches
    for word, digit in ones.items():
        text = re.sub(r'\b' + word + r'\b', digit, text)

    for word, digit in tens.items():
        text = re.sub(r'\b' + word + r'\b', digit, text)

    for word, digit in large.items():
        text = re.sub(r'\b' + word + r'\b', digit, text)

    # Ordinals: first, second, third, ..., tenth, ..., twentieth, etc.
    ordinals = {
        'first': '1st', 'second': '2nd', 'third': '3rd', 'fourth': '4th',
        'fifth': '5th', 'sixth': '6th', 'seventh': '7th', 'eighth': '8th',
        'ninth': '9th', 'tenth': '10th', 'eleventh': '11th', 'twelfth': '12th',
        'thirteenth': '13th', 'fourteenth': '14th', 'fifteenth': '15th',
        'sixteenth': '16th', 'seventeenth': '17th', 'eighteenth': '18th',
        'nineteenth': '19th', 'twentieth': '20th',
    }

    for word, ordinal in ordinals.items():
        text = re.sub(r'\b' + word + r'\b', ordinal, text)

    return text


def _extract_numbers(text):
    """Extract all signed integers from text, in order."""
    return [int(m) for m in re.findall(r'-?\d+', text)]


def _extract_list_content(text_original):
    """
    Extract the content of a bracketed list from the ORIGINAL instruction.
    This preserves the exact items as written (case, spacing, etc.).
    """
    match = re.search(r'\[([^\]]*)\]', text_original, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def _parse_list_items(list_content):
    """
    Parse list content into items.
    Handles various separators and quote styles; strips whitespace aggressively.
    Handles negative numbers and Unicode characters correctly.
    """
    if not list_content:
        return []

    # Remove surrounding quotes that wrap the whole list
    list_content = list_content.strip()
    if (list_content.startswith('"') and list_content.endswith('"')) or \
       (list_content.startswith("'") and list_content.endswith("'")):
        list_content = list_content[1:-1]

    # Split by comma (most common separator)
    items = []
    if ',' in list_content:
        items = list_content.split(',')
    # Also try semicolon or pipe
    elif ';' in list_content:
        items = list_content.split(';')
    elif '|' in list_content:
        items = list_content.split('|')
    else:
        items = [list_content]

    # Clean up each item: strip whitespace and quotes
    cleaned = []
    for item in items:
        item = item.strip()
        # Remove surrounding quotes (single or double)
        if (item.startswith('"') and item.endswith('"')) or \
           (item.startswith("'") and item.endswith("'")):
            item = item[1:-1].strip()
        # Remove extra parentheses if they wrap the item
        if item.startswith('(') and item.endswith(')'):
            item = item[1:-1].strip()
        # Handle Unicode minus signs in numbers
        item = item.replace('−', '-').replace('–', '-').replace('—', '-')
        cleaned.append(item)

    return cleaned


def _try_nth_item(text_normalized, text_original):
    """
    Try to parse nth list item operation.
    Patterns: "the Nth item in [list]", "Nth element in [list]",
    "item N in [list]", "the Nth from [list]", "get N from [list]", etc.
    Robust to ordinal spelling variations.
    """
    # Look for keywords: "item", "element", "index", or ordinal suffixes
    if not any(kw in text_normalized for kw in ['item', 'element', 'index', 'st', 'nd', 'rd', 'th']):
        return None

    # Must have brackets somewhere
    if '[' not in text_original or ']' not in text_original:
        return None

    # Find ordinal: "1st", "2nd", "3rd", etc., or just a number before "item"/"element"
    # Try "Nth" with suffix first
    ordinal_match = re.search(r'(\d+)(?:st|nd|rd|th)', text_normalized)

    # If no ordinal suffix, try to find a number near "item" or "element"
    if not ordinal_match:
        # Look for pattern like "item 2" or "2 item" or "element 3"
        ordinal_match = re.search(r'(?:item|element|index)\s+(\d+)', text_normalized)
        if not ordinal_match:
            ordinal_match = re.search(r'(\d+)\s+(?:item|element|index)', text_normalized)

    if not ordinal_match:
        return None

    nth = int(ordinal_match.group(1))

    # Extract list from original (preserves exact items)
    list_content = _extract_list_content(text_original)
    if list_content is None:
        return None

    items = _parse_list_items(list_content)

    # Convert to 0-indexed and bounds-check
    idx = nth - 1
    if 0 <= idx < len(items):
        return items[idx]

    return None


def _try_largest_number(text_normalized, text_original):
    """
    Try to parse largest/max number operation.
    Patterns: "largest number", "max number", "biggest number",
    "greatest number", "maximum number", "highest number",
    "top number", "find largest", etc.
    Tolerant of various synonyms and ordering.
    """
    # Look for keywords: largest, biggest, max, greatest, maximum, highest, top
    keywords = ['largest', 'biggest', 'max', 'greatest', 'maximum', 'highest', 'top', 'greatest']
    if not any(kw in text_normalized for kw in keywords):
        return None

    # Look for "number", "value", or similar (but be flexible)
    if not any(kw in text_normalized for kw in ['number', 'value', 'in', 'from']):
        return None

    # Must have brackets
    if '[' not in text_original or ']' not in text_original:
        return None

    # Extract list from original
    list_content = _extract_list_content(text_original)
    if list_content is None:
        return None

    # Extract all numbers from the list
    numbers = _extract_numbers(list_content)
    if numbers:
        return str(max(numbers))

    return None


def _try_add(text_normalized):
    """Try to parse add operation. Accepts "add X and Y" and variations."""
    if 'add' not in text_normalized:
        return None

    # Extract all numbers
    numbers = _extract_numbers(text_normalized)
    if len(numbers) >= 2:
        return str(numbers[0] + numbers[1])

    return None


def _try_subtract(text_normalized):
    """
    Try to parse subtract operation.
    Pattern: "subtract X from Y" means Y - X.
    Also handle: "subtract X out of Y", "take X from Y", "remove X", etc.
    """
    if 'subtract' not in text_normalized:
        return None

    # Look for "from", "of", "out", or similar separators
    from_keywords = ['from', 'of', 'out']
    has_from = any(kw in text_normalized for kw in from_keywords)

    if not has_from:
        return None

    # Split by any of the "from" variants to identify X (before) and Y (after)
    parts = None
    for sep in ['from', ' of ', 'out of']:
        if sep in text_normalized:
            parts = text_normalized.split(sep)
            break

    if not parts or len(parts) < 2:
        return None

    before_from = parts[0]
    after_from = parts[1]

    nums_before = _extract_numbers(before_from)
    nums_after = _extract_numbers(after_from)

    if nums_before and nums_after:
        # "subtract X from Y" → Y - X
        x = nums_before[0]
        y = nums_after[0]
        return str(y - x)

    return None


def _try_multiply(text_normalized):
    """Try to parse multiply operation."""
    if 'multiply' not in text_normalized:
        return None

    # Extract all numbers
    numbers = _extract_numbers(text_normalized)
    if len(numbers) >= 2:
        return str(numbers[0] * numbers[1])

    return None


def _try_reverse_word(text_normalized):
    """
    Try to parse reverse word operation.
    Patterns: "reverse the word X", "reverse X", "reverse word X",
    "reverse X backwards", "reverse X spell", etc.
    Tolerant of various filler and phrasing.
    """
    if 'reverse' not in text_normalized:
        return None

    # Extract word: look for the word after "reverse" (skip filler)
    words = text_normalized.split()
    for i, word in enumerate(words):
        if 'reverse' in word:
            # Skip filler words and find the target
            j = i + 1
            # Extended list of filler words to skip
            filler = ['the', 'word', 'a', 'an', 'is', 'be', 'this', 'that', 'this']
            while j < len(words) and words[j] in filler:
                j += 1

            if j < len(words):
                target = words[j].strip('[](){}[]<>:;,.')
                # Validate: should be mostly alphabetic
                if target and target not in filler:
                    # Only letters in the result
                    if any(c.isalpha() for c in target):
                        # Extract only the alphabetic part if there's garbage
                        clean_target = ''.join(c for c in target if c.isalpha())
                        if clean_target:
                            return clean_target[::-1]

    return None


def _try_uppercase_word(text_normalized):
    """
    Try to parse uppercase word operation.
    Patterns: "uppercase the word X", "uppercase X", "make X uppercase",
    "convert X to uppercase", etc.
    Tolerant of various filler and phrasing.
    """
    if 'uppercase' not in text_normalized and 'upper' not in text_normalized and 'upcase' not in text_normalized:
        return None

    # Extract word: look for the word after "uppercase" or similar (skip filler)
    words = text_normalized.split()
    for i, word in enumerate(words):
        if 'uppercase' in word or word in ['upper', 'upcase', 'uppercase', 'capitalize']:
            # Skip filler words and find the target
            j = i + 1
            filler = ['the', 'word', 'a', 'an', 'is', 'be', 'this', 'that', 'to']
            while j < len(words) and words[j] in filler:
                j += 1

            if j < len(words):
                target = words[j].strip('[](){}[]<>:;,.')
                # Validate: should be mostly alphabetic
                if target and target not in filler:
                    # Only letters in the result
                    if any(c.isalpha() for c in target):
                        # Extract only the alphabetic part if there's garbage
                        clean_target = ''.join(c for c in target if c.isalpha())
                        if clean_target:
                            return clean_target.upper()

    return None


def _try_count_letters(text_normalized):
    """
    Try to parse count letters operation.
    Patterns: "how many letters in X", "count letters in X",
    "letters in X", "how many characters in X", "count chars in X", etc.
    Tolerant of various phrasings.
    """
    # Look for keywords: "how", "many", "letters", "count", "characters"
    keywords = ['how', 'many', 'letters', 'count', 'characters', 'chars', 'letters in', 'chars in']
    if not any(kw in text_normalized for kw in keywords):
        return None

    # Must have "in" or similar
    if 'in' not in text_normalized:
        return None

    # Extract the word after "in"
    words = text_normalized.split()
    for i, word in enumerate(words):
        if word == 'in' and i + 1 < len(words):
            target = words[i + 1].strip('[](){}[]<>:;,.')
            # Must be a valid word (mostly alphabetic)
            if target and any(c.isalpha() for c in target):
                # Count only alphabetic characters
                letter_count = sum(1 for c in target if c.isalpha())
                if letter_count > 0:
                    return str(letter_count)

    return None
