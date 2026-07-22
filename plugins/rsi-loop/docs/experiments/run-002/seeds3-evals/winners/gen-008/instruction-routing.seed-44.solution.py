import re


def solve(instruction: str) -> str:
    """Return the exact answer to one instruction, as a string."""

    # Normalize: strip, lowercase, collapse multiple spaces
    text = ' '.join(instruction.strip().split()).lower()
    # Remove trailing punctuation that might interfere
    text = re.sub(r'[.,!?;:]+$', '', text)

    # === ADD ===
    # Patterns: "add X and Y", "add X to Y", "add X plus Y", "add X with Y"
    # Also handle "X plus Y" or "X and Y" as standalone (optional "add" keyword)
    # Extended synonyms: "adding X to Y"
    add_match = re.search(
        r'(?:add|adding)(?:ing)?\s+(-?\d+(?:\.\d+)?)\s+(?:and|to|plus|with)\s+(-?\d+(?:\.\d+)?)',
        text
    )
    if add_match:
        try:
            a = int(float(add_match.group(1)))
            b = int(float(add_match.group(2)))
            return str(a + b)
        except (ValueError, TypeError):
            pass

    # Fallback: "X and Y" or "X plus Y" without verb
    add_fallback = re.search(
        r'(-?\d+(?:\.\d+)?)\s+(?:and|plus|with)\s+(-?\d+(?:\.\d+)?)',
        text
    )
    if add_fallback:
        try:
            a = int(float(add_fallback.group(1)))
            b = int(float(add_fallback.group(2)))
            return str(a + b)
        except (ValueError, TypeError):
            pass

    # === SUBTRACT ===
    # Primary pattern: "subtract X from Y" = Y - X
    subtract_match = re.search(
        r'\bsubtract(?:ing)?\s+(-?\d+(?:\.\d+)?)\s+from\s+(-?\d+(?:\.\d+)?)',
        text
    )
    if subtract_match:
        try:
            a = int(float(subtract_match.group(1)))
            b = int(float(subtract_match.group(2)))
            return str(b - a)
        except (ValueError, TypeError):
            pass

    # Alternative: "X minus Y" pattern
    minus_match = re.search(
        r'(-?\d+(?:\.\d+)?)\s+(?:minus|take away)\s+(-?\d+(?:\.\d+)?)',
        text
    )
    if minus_match:
        try:
            a = int(float(minus_match.group(1)))
            b = int(float(minus_match.group(2)))
            return str(a - b)
        except (ValueError, TypeError):
            pass

    # === MULTIPLY ===
    # Patterns: "multiply X by Y", "multiply X times Y"
    multiply_match = re.search(
        r'\bmultiply(?:ing)?\s+(-?\d+(?:\.\d+)?)\s+(?:by|times)\s+(-?\d+(?:\.\d+)?)',
        text
    )
    if multiply_match:
        try:
            a = int(float(multiply_match.group(1)))
            b = int(float(multiply_match.group(2)))
            return str(a * b)
        except (ValueError, TypeError):
            pass

    # === REVERSE WORD ===
    # Patterns: "reverse the word X", "reverse word X", "reverse X"
    # More tolerant: optional articles, handle punctuation gracefully
    reverse_match = re.search(
        r'\breverse\s+(?:(?:the\s+)?(?:word\s+)?)?(\w+)',
        text
    )
    if reverse_match:
        word = reverse_match.group(1)
        return word[::-1]

    # === UPPERCASE WORD ===
    # Patterns: "uppercase the word X", "uppercase word X", "uppercase X"
    # Also: "make X uppercase"
    uppercase_match = re.search(
        r'\buppercase\s+(?:(?:the\s+)?(?:word\s+)?)?(\w+)',
        text
    )
    if uppercase_match:
        word = uppercase_match.group(1)
        return word.upper()

    # Alternative pattern: "make X uppercase"
    uppercase_alt = re.search(
        r'\bmake\s+(?:the\s+(?:word\s+)?)?(\w+)\s+(?:uppercase|upper\s+case)',
        text
    )
    if uppercase_alt:
        word = uppercase_alt.group(1)
        return word.upper()

    # === COUNT LETTERS ===
    # Patterns: "how many letters in X", "count letters in X", "letters in X"
    # More flexible: handles various phrasings, optional "many" and "how"
    count_match = re.search(
        r'(?:how\s+)?(?:many\s+)?(?:count\s+)?letters\s+in\s+(\w+)',
        text
    )
    if count_match:
        word = count_match.group(1)
        return str(len(word))

    # Alternative: "count of letters in X"
    count_alt = re.search(
        r'(?:count|number)\s+(?:of\s+)?letters\s+in\s+(\w+)',
        text
    )
    if count_alt:
        word = count_alt.group(1)
        return str(len(word))

    # === NTH LIST ITEM ===
    # Patterns: "the Nth item in [...]", "Nth item in [...]"
    # Support ordinals: 1st, 2nd, 3rd, 4th, etc.
    # Also support word-form: first, second, third, etc.

    # Try numeric ordinals first (1st, 2nd, etc.)
    # Allow optional "the" and make pattern more flexible
    nth_match = re.search(
        r'(?:the\s+)?(\d+)(?:st|nd|rd|th)?\s+(?:item|element|entry)\s+in\s+\[(.*?)\]',
        text
    )

    if nth_match:
        try:
            index = int(nth_match.group(1))
            items_str = nth_match.group(2)
            # Parse list items - split by comma and strip whitespace/punctuation
            items = []
            for item in items_str.split(','):
                item = item.strip()
                # Remove leading/trailing quotes or punctuation from items
                item = re.sub(r'^["\']|["\']$', '', item)
                if item:
                    items.append(item)
            # Convert to 1-indexed
            if 1 <= index <= len(items):
                return items[index - 1]
        except (ValueError, IndexError):
            pass

    # Try word-form ordinals (first, second, third, etc.)
    ordinal_words = {
        'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5,
        'sixth': 6, 'seventh': 7, 'eighth': 8, 'ninth': 9, 'tenth': 10,
        'eleventh': 11, 'twelfth': 12, 'zeroth': 0
    }

    nth_word_match = re.search(
        r'(?:the\s+)?(' + '|'.join(ordinal_words.keys()) + r')\s+(?:item|element|entry)\s+in\s+\[(.*?)\]',
        text
    )

    if nth_word_match:
        try:
            ordinal_word = nth_word_match.group(1).lower()
            index = ordinal_words[ordinal_word]
            items_str = nth_word_match.group(2)
            # Parse list items - split by comma and strip whitespace/punctuation
            items = []
            for item in items_str.split(','):
                item = item.strip()
                # Remove leading/trailing quotes or punctuation from items
                item = re.sub(r'^["\']|["\']$', '', item)
                if item:
                    items.append(item)
            # Convert to 1-indexed (unless it's zeroth)
            if index == 0:
                return items[0] if items else ""
            elif 1 <= index <= len(items):
                return items[index - 1]
        except (ValueError, IndexError, KeyError):
            pass

    # === LARGEST NUMBER ===
    # Patterns: "the largest number in [...]", "largest number in [...]"
    # Also support: "maximum", "max", "greatest", "biggest", "highest"
    max_match = re.search(
        r'(?:the\s+)?(?:largest|maximum|max|greatest|biggest|highest)\s+(?:number\s+)?in\s+\[(.*?)\]',
        text
    )
    if max_match:
        try:
            numbers_str = max_match.group(1)
            # Extract all numbers (including negative, floats)
            number_strs = re.findall(r'-?\d+(?:\.\d+)?', numbers_str)
            if number_strs:
                numbers = [int(float(n)) for n in number_strs]
                return str(max(numbers))
        except (ValueError, AttributeError):
            pass

    # Fallback for largest: try "the X in [...]" without "number" keyword
    # This handles rephrasings like "the largest in [...]"
    max_fallback = re.search(
        r'(?:the\s+)?(?:largest|maximum|max|greatest|biggest|highest)\s+in\s+\[(.*?)\]',
        text
    )
    if max_fallback:
        try:
            numbers_str = max_fallback.group(1)
            # Extract all numbers (including negative, floats)
            number_strs = re.findall(r'-?\d+(?:\.\d+)?', numbers_str)
            if number_strs:
                numbers = [int(float(n)) for n in number_strs]
                return str(max(numbers))
        except (ValueError, AttributeError):
            pass

    # Fallback (should not reach here if input is valid)
    return ""
