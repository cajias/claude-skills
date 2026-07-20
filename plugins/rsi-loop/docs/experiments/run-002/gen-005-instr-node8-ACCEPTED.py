import re


def solve(instruction: str) -> str:
    """Return the exact answer to one instruction, as a string."""
    instruction = instruction.strip()

    # Normalize: remove common punctuation but preserve list brackets
    # This makes the solution robust to question marks, exclamation marks, etc.
    instr_clean = instruction.rstrip('?!.,;:')
    instr_lower = instr_clean.lower()

    # Normalize whitespace for pattern matching
    instr_normalized = re.sub(r'\s+', ' ', instr_lower)

    # Remove common filler phrases and question words
    # This handles: "Can you add 3 and 5?", "What is 3 plus 5?", "Please add 3 and 5", etc.
    instr_normalized = re.sub(
        r'\b(?:can\s+you|could\s+you|would\s+you|please|what\s+is|what|tell\s+me|calculate|compute)\s+',
        '',
        instr_normalized
    )

    # Order operations by specificity: list operations first (most distinctive),
    # then word operations, then arithmetic (most ambiguous)

    # ========== NTH LIST ITEM (Most specific, requires list extraction) ==========
    ordinal_map = {
        'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5,
        'sixth': 6, 'seventh': 7, 'eighth': 8, 'ninth': 9, 'tenth': 10,
        'eleventh': 11, 'twelfth': 12, 'thirteenth': 13, 'fourteenth': 14,
        'fifteenth': 15, 'sixteenth': 16, 'seventeenth': 17, 'eighteenth': 18,
        'nineteenth': 19, 'twentieth': 20
    }

    # Try numeric ordinals with various formats (1st, 2nd, 3rd, 4th, etc.)
    nth_patterns = [
        r'(?:the\s+)?(\d+)(?:\s*(?:st|nd|rd|th))?\s+(?:item|element|entry)\s+(?:in|from|of)\s+\[(.*?)\]',
        r'(?:find|get|retrieve|select)\s+(?:the\s+)?(\d+)(?:\s*(?:st|nd|rd|th))?\s+(?:item|element|entry)\s+(?:in|from|of)\s+\[(.*?)\]',
        r'(?:item|element|entry)\s+(?:\#)?\s*(\d+)\s+(?:in|from|of)\s+\[(.*?)\]',
        r'(\d+)(?:\s*(?:st|nd|rd|th))\s+(?:item|element|entry)(?:\s+in|\s+from|\s+of)?\s+\[(.*?)\]',
    ]

    for pattern in nth_patterns:
        match = re.search(pattern, instr_normalized)
        if match:
            position = int(match.group(1))
            items_str = match.group(2)
            # Parse list items, stripping whitespace and trailing punctuation
            items = [item.strip().rstrip(',.;:') for item in items_str.split(',')]
            if 1 <= position <= len(items):
                return items[position - 1]

    # Try word-based ordinals (first, second, third, etc.)
    for word_ordinal, num_pos in ordinal_map.items():
        word_patterns = [
            rf'(?:the\s+)?{word_ordinal}\s+(?:item|element|entry)\s+(?:in|from|of)\s+\[(.*?)\]',
            rf'(?:find|get|retrieve|select)\s+(?:the\s+)?{word_ordinal}\s+(?:item|element|entry)\s+(?:in|from|of)\s+\[(.*?)\]',
        ]
        for pattern in word_patterns:
            match = re.search(pattern, instr_normalized)
            if match:
                items_str = match.group(1)
                items = [item.strip().rstrip(',.;:') for item in items_str.split(',')]
                if 1 <= num_pos <= len(items):
                    return items[num_pos - 1]

    # ========== LARGEST NUMBER (List operation) ==========
    # Synonyms: largest, biggest, maximum, max, greatest, highest, biggest
    max_synonyms = ['largest', 'biggest', 'maximum', 'max', 'greatest', 'highest', 'minimum', 'smallest']

    for synonym in max_synonyms:
        if synonym in ['minimum', 'smallest']:
            # Skip minimum/smallest for now, focus on largest
            continue
        max_patterns = [
            rf'(?:the\s+)?{synonym}(?:\s+number)?\s+(?:in|from|of)\s+\[(.*?)\]',
            rf'(?:find|get|retrieve|select)\s+(?:the\s+)?{synonym}(?:\s+number)?\s+(?:in|from|of)\s+\[(.*?)\]',
            rf'{synonym}(?:\s+number)?\s+(?:in|from|of)\s+\[(.*?)\]',
        ]
        for pattern in max_patterns:
            match = re.search(pattern, instr_normalized)
            if match:
                numbers_str = match.group(1)
                try:
                    # Parse numbers, handling spaces and other variations
                    numbers = [int(num.strip().rstrip(',.;:')) for num in numbers_str.split(',')]
                    if numbers:
                        return str(max(numbers))
                except ValueError:
                    pass

    # ========== REVERSE WORD ==========
    # Patterns: "reverse [the] word WORD", "reverse WORD", "flip/invert word"
    # Synonyms: reverse, flip, invert, invert
    reverse_patterns = [
        r'reverse\s+(?:the\s+)?word\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        r'reverse\s+(?:the\s+)?(?:word\s+)?([a-zA-Z_][a-zA-Z0-9_]*)',
        r'(?:flip|invert|spell\s+backwards)\s+(?:the\s+)?word\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        r'(?:flip|invert)\s+(?:the\s+)?(?:word\s+)?([a-zA-Z_][a-zA-Z0-9_]*)',
        r'spell\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+backwards',
        r'(?:backwards|backwards)\s+spelling\s+of\s+([a-zA-Z_][a-zA-Z0-9_]*)',
    ]
    for pattern in reverse_patterns:
        match = re.search(pattern, instr_normalized)
        if match:
            word = match.group(1)
            return word[::-1]

    # ========== UPPERCASE WORD ==========
    # Patterns: "uppercase [the] word WORD", "make WORD uppercase", "capitalize WORD"
    # Synonyms: uppercase, upper, capitalize, convert to uppercase
    upper_patterns = [
        r'uppercase\s+(?:the\s+)?word\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        r'uppercase\s+(?:the\s+)?(?:word\s+)?([a-zA-Z_][a-zA-Z0-9_]*)',
        r'(?:make|turn|convert|change)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+(?:to\s+)?uppercase',
        r'(?:make|turn|convert|change)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+(?:to\s+)?upper',
        r'(?:make|turn|convert|change)\s+(?:the\s+)?(?:word\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s+(?:to\s+)?(?:upper|uppercase)',
        r'capitalize\s+(?:the\s+)?(?:word\s+)?([a-zA-Z_][a-zA-Z0-9_]*)',
        r'(?:upper|UPPER)\s+(?:the\s+)?word\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        r'(?:to\s+)?uppercase\s+(?:the\s+)?(?:word\s+)?([a-zA-Z_][a-zA-Z0-9_]*)',
    ]
    for pattern in upper_patterns:
        match = re.search(pattern, instr_normalized)
        if match:
            word = match.group(1)
            return word.upper()

    # ========== COUNT LETTERS ==========
    # Patterns: "how many letters in WORD", "count letters in WORD", "letter count"
    # Synonyms: letters, characters; variations: count, how many, length
    count_patterns = [
        r'(?:how\s+many|count)\s+(?:letters?|characters?)\s+(?:in|of|are\s+there\s+in)\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        r'(?:letters?|characters?)\s+(?:count|length)(?:\s+(?:of|in))?\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        r'(?:letter|character)\s+(?:count|length)\s+(?:of|in)?\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        r'count\s+(?:the\s+)?(?:letters?|characters?)\s+(?:in|of)\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        r'length\s+(?:of|in)?\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        r'how\s+long\s+(?:is|are)\s+(?:the\s+)?(?:word\s+)?([a-zA-Z_][a-zA-Z0-9_]*)',
    ]
    for pattern in count_patterns:
        match = re.search(pattern, instr_normalized)
        if match:
            word = match.group(1)
            return str(len(word))

    # ========== MULTIPLY ==========
    # Patterns: "multiply X by Y", "X times Y", "X * Y"
    # Synonyms: multiply, times, *, multiplied by
    multiply_patterns = [
        r'multiply\s+([-+]?\d+)\s+by\s+([-+]?\d+)',
        r'([-+]?\d+)\s+times\s+([-+]?\d+)',
        r'([-+]?\d+)\s+\*\s+([-+]?\d+)',
        r'([-+]?\d+)\s+multiplied\s+by\s+([-+]?\d+)',
        r'product\s+of\s+([-+]?\d+)\s+and\s+([-+]?\d+)',
    ]
    for pattern in multiply_patterns:
        match = re.search(pattern, instr_normalized)
        if match:
            a = int(match.group(1))
            b = int(match.group(2))
            return str(a * b)

    # ========== ADD ==========
    # Patterns: "add X and Y", "X plus Y", "X + Y"
    # Synonyms: add, plus, sum, combined with, total
    # Try explicit "add" patterns first to avoid false positives
    add_patterns = [
        r'add\s+([-+]?\d+)\s+and\s+([-+]?\d+)',
        r'add\s+together\s+([-+]?\d+)\s+and\s+([-+]?\d+)',
        r'add\s+([-+]?\d+)\s+plus\s+([-+]?\d+)',
        r'([-+]?\d+)\s+plus\s+([-+]?\d+)',
        r'([-+]?\d+)\s+\+\s+([-+]?\d+)',
        r'sum\s+(?:of\s+)?([-+]?\d+)\s+and\s+([-+]?\d+)',
        r'total\s+(?:of\s+)?([-+]?\d+)\s+and\s+([-+]?\d+)',
        r'combined\s+(?:total\s+)?(?:of\s+)?([-+]?\d+)\s+and\s+([-+]?\d+)',
    ]
    for pattern in add_patterns:
        match = re.search(pattern, instr_normalized)
        if match:
            a = int(match.group(1))
            b = int(match.group(2))
            return str(a + b)

    # ========== SUBTRACT ==========
    # Patterns: "subtract X from Y" -> Y - X, "Y minus X" -> Y - X
    # Synonyms: subtract, minus, take away, remove, difference
    subtract_patterns = [
        (r'subtract\s+([-+]?\d+)\s+from\s+([-+]?\d+)', 'from'),
        (r'(?:take|remove)\s+([-+]?\d+)\s+from\s+([-+]?\d+)', 'from'),
        (r'([-+]?\d+)\s+minus\s+([-+]?\d+)', 'minus'),
        (r'([-+]?\d+)\s+-\s+([-+]?\d+)', 'minus'),
        (r'([-+]?\d+)\s+(?:take\s+)?away\s+([-+]?\d+)', 'minus'),
        (r'difference\s+(?:between\s+)?([-+]?\d+)\s+and\s+([-+]?\d+)', 'minus'),
    ]
    for pattern, ptype in subtract_patterns:
        match = re.search(pattern, instr_normalized)
        if match:
            if ptype == 'from':
                # "subtract X from Y" or "take X from Y" -> Y - X
                x = int(match.group(1))
                y = int(match.group(2))
                return str(y - x)
            else:
                # "X minus Y" -> X - Y
                a = int(match.group(1))
                b = int(match.group(2))
                return str(a - b)

    # Fallback: no pattern matched
    return ""
