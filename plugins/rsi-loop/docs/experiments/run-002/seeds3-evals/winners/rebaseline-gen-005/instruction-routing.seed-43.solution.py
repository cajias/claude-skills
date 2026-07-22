import re


def solve(instruction: str) -> str:
    """
    Parse and execute a natural-language instruction.

    Maximally tolerant parsing with principled input normalization to handle:
    - Whitespace variations (multiple spaces, tabs, newlines)
    - Punctuation (trailing periods, commas, question marks)
    - Synonyms and rephrasings (largest/biggest/maximum, item/element/entry, etc.)
    - Case insensitivity for keywords (while preserving original case for content)
    - Flexible number and word extraction with defensive semantics
    - Robust list parsing with extra punctuation and spacing
    - Alternative verb forms and phrasings
    """
    # Normalize: strip, collapse whitespace, remove trailing punctuation
    normalized = re.sub(r'\s+', ' ', instruction.strip()).lower()
    # Remove only trailing sentence punctuation, not internal commas or brackets
    normalized = re.sub(r'([.!?])\s*$', '', normalized)

    # Extract list content first: [...] with flexible spacing and punctuation
    list_items = []
    list_match = re.search(r'\[\s*(.*?)\s*\]', normalized)
    if list_match:
        content = list_match.group(1)
        # Split by comma, strip whitespace from each item, filter empty
        list_items = [item.strip() for item in content.split(',') if item.strip()]

    # Extract all signed integers (for arithmetic and list operations)
    all_numbers = [int(m) for m in re.findall(r'-?\d+', normalized)]

    # --- ARITHMETIC OPERATIONS ---

    # ADD: "add X and Y" or synonyms
    if any(kw in normalized for kw in ['add', 'plus', 'sum']):
        if 'and' in normalized and len(all_numbers) >= 2:
            return str(all_numbers[0] + all_numbers[1])

    # SUBTRACT: "subtract Y from X" means X - Y
    # More defensive: extract numbers in order of keyword appearance
    if 'subtract' in normalized and 'from' in normalized:
        subtract_match = re.search(r'subtract\s+(-?\d+)', normalized)
        from_match = re.search(r'from\s+(-?\d+)', normalized)
        if subtract_match and from_match:
            y = int(subtract_match.group(1))
            x = int(from_match.group(1))
            return str(x - y)

    # MULTIPLY: "multiply X by Y" or synonyms
    if any(kw in normalized for kw in ['multiply', 'times']) and 'by' in normalized:
        if len(all_numbers) >= 2:
            return str(all_numbers[0] * all_numbers[1])

    # --- WORD OPERATIONS ---

    # REVERSE: "reverse [the] word|term X" or similar
    if 'reverse' in normalized and any(kw in normalized for kw in ['word', 'term', 'string']):
        # Extract word after "word" or "term" or "string"
        # Preserve case from original instruction for extraction
        word_match = re.search(
            r'(?:word|term|string)\s+([a-z_][a-z0-9_\-]*)',
            normalized
        )
        if word_match:
            word = word_match.group(1)
            # Get original casing if possible
            orig_word_match = re.search(
                r'(?:word|term|string)\s+(\w+)',
                instruction,
                re.IGNORECASE
            )
            if orig_word_match:
                word = orig_word_match.group(1)
            return word[::-1]

    # UPPERCASE: "uppercase [the] word|term X" or similar
    if 'uppercase' in normalized and any(kw in normalized for kw in ['word', 'term', 'string']):
        word_match = re.search(
            r'(?:word|term|string)\s+(\w+)',
            instruction,
            re.IGNORECASE
        )
        if word_match:
            word = word_match.group(1)
            return word.upper()

    # COUNT LETTERS: "how many letters|characters in X" or "count letters|characters in X"
    if any(kw in normalized for kw in ['letter', 'character', 'count']):
        if 'in' in normalized:
            # Extract word after "in"
            in_match = re.search(
                r'in\s+([a-z_][a-z0-9_\-]*)',
                normalized
            )
            if in_match:
                word = in_match.group(1)
                # Get original casing
                orig_match = re.search(r'in\s+(\w+)', instruction, re.IGNORECASE)
                if orig_match:
                    word = orig_match.group(1)
                return str(len(word))

    # --- LIST OPERATIONS ---

    # NTH ITEM: "the Nth item|element|entry in [...]"
    # Match ordinals (1st, 2nd, 3rd, etc.) or cardinals
    if any(kw in normalized for kw in ['item', 'element', 'entry']) and 'in' in normalized and list_items:
        # Match ordinal patterns: digit(s) followed optionally by st/nd/rd/th
        ordinal_match = re.search(r'(?:the\s+)?(\d+)(?:st|nd|rd|th)?\s+(?:item|element|entry)', normalized)
        if ordinal_match:
            index = int(ordinal_match.group(1)) - 1  # Convert to 0-based
            if 0 <= index < len(list_items):
                return list_items[index]

    # LARGEST NUMBER: "the largest|biggest|maximum|greatest number in [...]"
    if any(kw in normalized for kw in ['largest', 'biggest', 'maximum', 'greatest']) and 'in' in normalized and list_items:
        # Try to parse all items as numbers
        try:
            parsed_numbers = [int(item.strip()) for item in list_items]
            if parsed_numbers:
                return str(max(parsed_numbers))
        except (ValueError, IndexError):
            pass

    # Fallback: should not reach here for valid inputs
    return ""
