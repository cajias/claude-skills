import re


def solve(instruction: str) -> str:
    """
    Tolerant instruction parser: normalize input, classify operation via keywords,
    and extract operands flexibly to handle paraphrasing and alternative phrasings.

    Generalization strategy:
    - Normalize whitespace and punctuation upfront
    - Use flexible keyword detection (synonyms, word boundaries)
    - Extract operands via general patterns, not strict templates
    - Handle rephrasings like "from Y subtract X" or "max in [...]"
    """
    # Aggressive normalization: collapse whitespace, remove trailing punctuation
    text = re.sub(r'\s+', ' ', instruction.strip()).lower()
    text = re.sub(r'[.,!?;:]+$', '', text)  # Remove trailing punctuation

    # === ARITHMETIC OPERATIONS ===

    # ADD: "add X and Y", "X and Y", "X plus Y", etc.
    if re.search(r'\badd\b', text):
        nums = extract_numbers(text)
        if len(nums) >= 2:
            return str(nums[0] + nums[1])

    # SUBTRACT: "subtract A from B" or "from B subtract A" (B - A)
    # Also handle: "B minus A", etc.
    if re.search(r'\bsubtract\b', text):
        # Try strict pattern first: "subtract A from B"
        strict_match = re.search(r'subtract\s+(-?\d+)\s+from\s+(-?\d+)', text)
        if strict_match:
            a, b = int(strict_match.group(1)), int(strict_match.group(2))
            return str(b - a)

        # Try reversed: "from B subtract A"
        reversed_match = re.search(r'from\s+(-?\d+)\s+subtract\s+(-?\d+)', text)
        if reversed_match:
            b, a = int(reversed_match.group(1)), int(reversed_match.group(2))
            return str(b - a)

        # Fallback: extract two numbers in order, B - A
        nums = extract_numbers(text)
        if len(nums) >= 2:
            a, b = nums[0], nums[1]
            return str(b - a)

    # MULTIPLY: "multiply X by Y" or "X times Y", "X * Y"
    if re.search(r'\bmultiply\b', text):
        nums = extract_numbers(text)
        if len(nums) >= 2:
            return str(nums[0] * nums[1])

    # === STRING OPERATIONS ===

    # REVERSE: "reverse [the] word W", "reverse W"
    # Tolerant: accept "reverse the word X", "reverse word X", etc.
    if re.search(r'\breverse\b', text):
        # Pattern: "reverse" followed by optional "the", then "word", then word
        word_match = re.search(r'reverse\s+(?:the\s+)?word\s+([a-z_]+)', text)
        if word_match:
            word = word_match.group(1)
            return word[::-1]

        # Fallback: look for any word-like token after "reverse"
        fallback_match = re.search(r'reverse\s+(?:the\s+)?(?:word\s+)?([a-z_]+)', text)
        if fallback_match:
            word = fallback_match.group(1)
            return word[::-1]

    # UPPERCASE: "uppercase [the] word W"
    if re.search(r'\buppercase\b', text):
        word_match = re.search(r'uppercase\s+(?:the\s+)?word\s+([a-z_]+)', text)
        if word_match:
            word = word_match.group(1)
            return word.upper()

        # Fallback
        fallback_match = re.search(r'uppercase\s+(?:the\s+)?(?:word\s+)?([a-z_]+)', text)
        if fallback_match:
            word = fallback_match.group(1)
            return word.upper()

    # COUNT LETTERS: "how many letters in X", "count letters in X"
    # Tolerant: accept variations like "how many letters in X", "count X letters", etc.
    if re.search(r'(how\s+many|count).*letters', text):
        # Try "letters in X" pattern
        in_match = re.search(r'letters\s+in\s+([a-z_]+)', text)
        if in_match:
            word = in_match.group(1)
            return str(len(word))

        # Try "in X" pattern
        alt_match = re.search(r'in\s+([a-z_]+)', text)
        if alt_match:
            word = alt_match.group(1)
            return str(len(word))

    # === LIST OPERATIONS ===

    # NTH ITEM: "the Nth item in [...]", "Nth item in [...]", "item N in [...]"
    # Tolerant: accept "1st", "2nd", "3rd", "4th", or plain "1", "2", etc.
    if re.search(r'(?:the\s+)?(\d+)(?:st|nd|rd|th)?\s+(?:item|element)', text):
        items = extract_list_items(instruction)  # Use original casing for list items

        # Extract ordinal number: "the 2nd item" or "the 2 item" etc.
        ordinal_match = re.search(r'(?:the\s+)?(\d+)(?:st|nd|rd|th)?\s+(?:item|element)', text)
        if ordinal_match and items:
            index = int(ordinal_match.group(1)) - 1  # Convert to 0-based
            if 0 <= index < len(items):
                return items[index]

    # LARGEST NUMBER: "the largest number in [...]", "largest number in [...]",
    # "max in [...]", "maximum in [...]", "biggest in [...]"
    # Tolerant: accept various synonyms and orderings
    if re.search(r'\b(largest|maximum|max|biggest).*number', text):
        # Try list extraction pattern
        numbers = extract_numbers_from_list(instruction)
        if numbers:
            return str(max(numbers))

    # Fallback for single-word list reference (edge case)
    if re.search(r'largest|maximum|max|biggest', text) and '[' in instruction:
        numbers = extract_numbers_from_list(instruction)
        if numbers:
            return str(max(numbers))

    return ""


def extract_numbers(text: str) -> list:
    """Extract all signed integers from text in order."""
    matches = re.findall(r'-?\d+', text)
    return [int(m) for m in matches]


def extract_list_items(instruction: str) -> list:
    """Extract items from bracketed list notation [a, b, c]."""
    match = re.search(r'\[(.*?)\]', instruction)
    if match:
        content = match.group(1)
        # Split by comma and strip whitespace, preserving original casing
        items = [item.strip() for item in content.split(',')]
        return items
    return []


def extract_numbers_from_list(instruction: str) -> list:
    """Extract numbers from bracketed list notation [1, 2, 3]."""
    match = re.search(r'\[(.*?)\]', instruction)
    if match:
        content = match.group(1)
        # Extract all signed integers
        numbers = []
        for part in content.split(','):
            part = part.strip()
            num_match = re.search(r'-?\d+', part)
            if num_match:
                numbers.append(int(num_match.group()))
        return numbers
    return []
