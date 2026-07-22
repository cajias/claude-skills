import re


def solve(instruction: str) -> str:
    """Return the exact answer to one instruction, as a string."""

    # Normalize: strip, lowercase, collapse whitespace, remove punctuation
    text = instruction.strip().lower()
    text = re.sub(r'\s+', ' ', text)
    # Remove trailing punctuation but preserve brackets and commas for lists
    text = re.sub(r'[.!?;:]+$', '', text)
    text = re.sub(r'[.!?;:]+\s', ' ', text)

    # Aggressive synonym normalization
    text = normalize_input(text)

    # Try each operation with multiple strategies
    # List operations first (most specific patterns)

    result = try_nth_item(text)
    if result is not None:
        return result

    result = try_largest_number(text)
    if result is not None:
        return result

    # Arithmetic operations
    result = try_add(text)
    if result is not None:
        return result

    result = try_subtract(text)
    if result is not None:
        return result

    result = try_multiply(text)
    if result is not None:
        return result

    # String operations
    result = try_reverse_word(text)
    if result is not None:
        return result

    result = try_uppercase_word(text)
    if result is not None:
        return result

    result = try_count_letters(text)
    if result is not None:
        return result

    return ""


def normalize_input(text: str) -> str:
    """Normalize synonyms, passive voice, and common phrasings."""

    # === Arithmetic operation synonyms ===
    # Add variations
    text = re.sub(r'\badd\s+(\w+\s+)?to\b', 'add', text)
    text = re.sub(r'\bplus\b', 'and', text)
    text = re.sub(r'\badd\s+together\b', 'add', text)
    text = re.sub(r'\bsummarize\b', 'add', text)

    # Subtract variations
    text = re.sub(r'\bminus\b', 'from', text)
    text = re.sub(r'\bsubtract\s+away\b', 'subtract', text)
    text = re.sub(r'\btake\s+away\b', 'subtract', text)
    text = re.sub(r'\btake\s+off\b', 'subtract', text)
    text = re.sub(r'\bfrom\s+(\d+)\s+take\b', 'subtract', text)
    text = re.sub(r'\bremove\s+(\d+)\s+from\b', 'subtract', text)

    # Multiply variations
    text = re.sub(r'\btimes\b', 'by', text)
    text = re.sub(r'\bmultiplied\s+by\b', 'multiply by', text)
    text = re.sub(r'\bproduct\s+of\b', 'multiply', text)

    # === String operation synonyms ===
    # Reverse
    text = re.sub(r'\b(flip|backwards|invert|mirror|backward)\b', 'reverse', text)
    text = re.sub(r'\breverse\s+the\s+order\s+of\b', 'reverse', text)

    # Uppercase
    text = re.sub(r'\b(upper|capitalize|make upper|make uppercase|upper case)\b', 'uppercase', text)
    text = re.sub(r'\bconvert\s+to\s+uppercase\b', 'uppercase', text)

    # Lowercase
    text = re.sub(r'\b(lower|lowercase|make lower|make lowercase|lower case)\b', 'lowercase', text)

    # === Comparison/aggregation synonyms ===
    # Largest
    text = re.sub(r'\b(maximum|biggest|greatest|max|highest|topmost|greatest value)\b', 'largest', text)
    text = re.sub(r'\bgreatest\s+number\b', 'largest number', text)

    # Smallest
    text = re.sub(r'\b(minimum|smallest|least|min|lowest)\b', 'smallest', text)

    # === Count/length synonyms ===
    text = re.sub(r'\bcount\s+(?:the\s+)?(?:letters|chars|characters)\s+(?:of|in)\b', 'how many letters in', text)
    text = re.sub(r'\bcount\s+(?:the\s+)?letters\s+in\b', 'how many letters in', text)
    text = re.sub(r'\blength\s+(?:of\s+)?(?:the\s+)?word\b', 'how many letters in', text)
    text = re.sub(r'\bhow\s+(?:many\s+)?long\b', 'how many letters in', text)
    text = re.sub(r'\bhow\s+many\s+(?:chars|characters)\b', 'how many letters in', text)
    text = re.sub(r'\bword\s+length\b', 'how many letters in', text)

    # === List/item synonyms ===
    text = re.sub(r'\b(element|index|position|member|entry|value|place)\b', 'item', text)

    # === Ordinal word conversion ===
    ordinal_map = {
        'first': '1st', 'second': '2nd', 'third': '3rd', 'fourth': '4th',
        'fifth': '5th', 'sixth': '6th', 'seventh': '7th', 'eighth': '8th',
        'ninth': '9th', 'tenth': '10th', 'eleventh': '11th', 'twelfth': '12th',
        'thirteenth': '13th', 'fourteenth': '14th', 'fifteenth': '15th',
        'sixteenth': '16th', 'seventeenth': '17th', 'eighteenth': '18th',
        'nineteenth': '19th', 'twentieth': '20th',
    }
    for word, ordinal in ordinal_map.items():
        text = re.sub(r'\b' + word + r'\b', ordinal, text)

    # === Passive voice conversion ===
    # "be reversed" -> "reverse"
    text = re.sub(r'\bbe\s+reversed\b', 'reverse', text)
    text = re.sub(r'\bbe\s+uppercased?\b', 'uppercase', text)
    text = re.sub(r'\bbe\s+uppercased?\b', 'uppercase', text)
    text = re.sub(r'\bbe\s+added\b', 'add', text)
    text = re.sub(r'\bbe\s+subtracted\b', 'subtract', text)
    text = re.sub(r'\bbe\s+multiplied\b', 'multiply', text)

    # === Filler removal ===
    text = re.sub(r'\bplease\b', '', text)
    text = re.sub(r'\bkindly\b', '', text)
    text = re.sub(r'\bnow\b', '', text)
    text = re.sub(r'\bcould\s+you\b', '', text)
    text = re.sub(r'\bwill\s+you\b', '', text)

    # Re-collapse whitespace after replacements
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def extract_numbers(text: str) -> list:
    """Extract all integers from text, including negative."""
    return [int(x) for x in re.findall(r'-?\d+', text)]


def extract_list_items(text: str) -> list:
    """Extract list items from brackets."""
    match = re.search(r'\[(.*?)\]', text)
    if not match:
        return []
    content = match.group(1)
    items = [item.strip() for item in content.split(',')]
    return items


def extract_word_after(text: str, keyword: str) -> str:
    """Extract the first word after a keyword."""
    # Pattern: keyword followed by optional "the", then a word
    pattern = keyword + r'\s+(?:the\s+)?(?:word\s+)?(\w+)'
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    return None


def try_add(text: str) -> str:
    """Try to parse and compute addition with multiple patterns."""
    # Primary: "add X and Y"
    match = re.search(r'add\s+(-?\d+)\s+and\s+(-?\d+)', text)
    if match:
        a, b = int(match.group(1)), int(match.group(2))
        return str(a + b)

    # Alternative: "X and Y add"
    match = re.search(r'(-?\d+)\s+and\s+(-?\d+)\s+add', text)
    if match:
        a, b = int(match.group(1)), int(match.group(2))
        return str(a + b)

    # Fallback: "add" present with two numbers
    if 'add' in text:
        numbers = extract_numbers(text)
        if len(numbers) >= 2:
            return str(numbers[0] + numbers[1])

    return None


def try_subtract(text: str) -> str:
    """Try to parse and compute subtraction with multiple patterns."""
    # Primary: "subtract X from Y" means Y - X
    match = re.search(r'subtract\s+(-?\d+)\s+from\s+(-?\d+)', text)
    if match:
        x, y = int(match.group(1)), int(match.group(2))
        return str(y - x)

    # Alternative: "from Y subtract X"
    match = re.search(r'from\s+(-?\d+)\s+subtract\s+(-?\d+)', text)
    if match:
        y, x = int(match.group(1)), int(match.group(2))
        return str(y - x)

    # Alternative: "X minus Y"
    match = re.search(r'(-?\d+)\s+minus\s+(-?\d+)', text)
    if match:
        x, y = int(match.group(1)), int(match.group(2))
        return str(x - y)

    # Alternative: "take X from Y"
    match = re.search(r'take\s+(-?\d+)\s+from\s+(-?\d+)', text)
    if match:
        x, y = int(match.group(1)), int(match.group(2))
        return str(y - x)

    # Alternative: "remove X from Y"
    match = re.search(r'remove\s+(-?\d+)\s+from\s+(-?\d+)', text)
    if match:
        x, y = int(match.group(1)), int(match.group(2))
        return str(y - x)

    # Fallback: "subtract" present with two numbers, first is X, second is Y
    if 'subtract' in text:
        numbers = extract_numbers(text)
        if len(numbers) >= 2:
            return str(numbers[1] - numbers[0])

    return None


def try_multiply(text: str) -> str:
    """Try to parse and compute multiplication with multiple patterns."""
    # Primary: "multiply X by Y"
    match = re.search(r'multiply\s+(-?\d+)\s+by\s+(-?\d+)', text)
    if match:
        a, b = int(match.group(1)), int(match.group(2))
        return str(a * b)

    # Alternative: "by Y multiply X"
    match = re.search(r'by\s+(-?\d+)\s+multiply\s+(-?\d+)', text)
    if match:
        b, a = int(match.group(1)), int(match.group(2))
        return str(a * b)

    # Alternative: "X times Y"
    match = re.search(r'(-?\d+)\s+times\s+(-?\d+)', text)
    if match:
        a, b = int(match.group(1)), int(match.group(2))
        return str(a * b)

    # Alternative: "X multiplied by Y"
    match = re.search(r'(-?\d+)\s+multiplied\s+by\s+(-?\d+)', text)
    if match:
        a, b = int(match.group(1)), int(match.group(2))
        return str(a * b)

    # Fallback: "multiply" present with two numbers
    if 'multiply' in text:
        numbers = extract_numbers(text)
        if len(numbers) >= 2:
            return str(numbers[0] * numbers[1])

    return None


def try_reverse_word(text: str) -> str:
    """Try to parse and reverse a word with multiple patterns."""
    # Primary: "reverse [the] word X"
    match = re.search(r'reverse\s+(?:the\s+)?word\s+(\w+)', text)
    if match:
        word = match.group(1)
        return word[::-1]

    # Alternative: "flip [the] word X"
    match = re.search(r'flip\s+(?:the\s+)?word\s+(\w+)', text)
    if match:
        word = match.group(1)
        return word[::-1]

    # Alternative: "reverse [the] X" (without explicit "word")
    match = re.search(r'reverse\s+(?:the\s+)?(\w+)(?:\s|$)', text)
    if match and 'item' not in text and '[' not in text:
        word = match.group(1)
        if len(word) > 1:
            return word[::-1]

    # Alternative: "X be reversed"
    match = re.search(r'(\w+)\s+(?:be\s+)?reversed', text)
    if match and 'item' not in text and '[' not in text:
        word = match.group(1)
        if len(word) > 1:
            return word[::-1]

    return None


def try_uppercase_word(text: str) -> str:
    """Try to parse and uppercase a word with multiple patterns."""
    # Primary: "uppercase [the] word X"
    match = re.search(r'uppercase\s+(?:the\s+)?word\s+(\w+)', text)
    if match:
        word = match.group(1)
        return word.upper()

    # Alternative: "capitalize [the] word X"
    match = re.search(r'capitalize\s+(?:the\s+)?word\s+(\w+)', text)
    if match:
        word = match.group(1)
        return word.upper()

    # Alternative: "make uppercase [the] word X"
    match = re.search(r'make\s+uppercase\s+(?:the\s+)?word\s+(\w+)', text)
    if match:
        word = match.group(1)
        return word.upper()

    # Alternative: "X be uppercased"
    match = re.search(r'(\w+)\s+(?:be\s+)?uppercased?', text)
    if match and 'item' not in text and '[' not in text:
        word = match.group(1)
        if len(word) > 1:
            return word.upper()

    return None


def try_count_letters(text: str) -> str:
    """Try to parse and count letters with multiple patterns."""
    # Primary: "how many letters in X"
    match = re.search(r'how\s+many\s+letters\s+in\s+(\w+)', text)
    if match:
        word = match.group(1)
        return str(len(word))

    # Alternative: "count letters in X"
    match = re.search(r'count\s+letters\s+in\s+(\w+)', text)
    if match:
        word = match.group(1)
        return str(len(word))

    # Alternative: "length of X" or "size of X"
    match = re.search(r'(?:length|size)\s+(?:of\s+)?(?:the\s+)?(?:word\s+)?(\w+)', text)
    if match:
        word = match.group(1)
        return str(len(word))

    # Alternative: "word X has how many letters"
    match = re.search(r'word\s+(\w+)\s+has\s+how\s+many\s+letters', text)
    if match:
        word = match.group(1)
        return str(len(word))

    # Alternative: "how long is X"
    match = re.search(r'how\s+long\s+is\s+(?:the\s+)?(?:word\s+)?(\w+)', text)
    if match:
        word = match.group(1)
        return str(len(word))

    # Alternative: "letters in X" with context clue "how many"
    if 'letters' in text and 'in' in text:
        match = re.search(r'letters\s+in\s+(\w+)', text)
        if match:
            word = match.group(1)
            return str(len(word))

    return None


def parse_ordinal_number(text: str) -> int:
    """Extract ordinal number from text like '1st', '2nd', '3rd', etc."""
    # Match digit with optional suffix
    match = re.search(r'(\d+)(?:st|nd|rd|th)?', text)
    if match:
        return int(match.group(1))
    return None


def try_nth_item(text: str) -> str:
    """Try to parse and extract nth item from list with multiple patterns."""
    # Primary: "the Xth item in [...]"
    match = re.search(r'the\s+(\d+(?:st|nd|rd|th)?)\s+item\s+in\s+\[(.*?)\]', text)
    if match:
        position = parse_ordinal_number(match.group(1))
        if position is None:
            return None
        list_str = match.group(2)
        items = [item.strip() for item in list_str.split(',')]
        index = position - 1
        if 0 <= index < len(items):
            return items[index]

    # Alternative: "Xth item in [...]" (without "the")
    match = re.search(r'(\d+(?:st|nd|rd|th)?)\s+item\s+in\s+\[(.*?)\]', text)
    if match:
        position = parse_ordinal_number(match.group(1))
        if position is None:
            return None
        list_str = match.group(2)
        items = [item.strip() for item in list_str.split(',')]
        index = position - 1
        if 0 <= index < len(items):
            return items[index]

    # Alternative: "Xth/Xnd/Xrd item from [...]"
    match = re.search(r'(\d+(?:st|nd|rd|th)?)\s+item\s+from\s+\[(.*?)\]', text)
    if match:
        position = parse_ordinal_number(match.group(1))
        if position is None:
            return None
        list_str = match.group(2)
        items = [item.strip() for item in list_str.split(',')]
        index = position - 1
        if 0 <= index < len(items):
            return items[index]

    # Alternative: "the Xth element/index/position in [...]"
    match = re.search(r'the\s+(\d+(?:st|nd|rd|th)?)\s+(?:element|index|position|member)\s+in\s+\[(.*?)\]', text)
    if match:
        position = parse_ordinal_number(match.group(1))
        if position is None:
            return None
        list_str = match.group(2)
        items = [item.strip() for item in list_str.split(',')]
        index = position - 1
        if 0 <= index < len(items):
            return items[index]

    return None


def try_largest_number(text: str) -> str:
    """Try to parse and find largest number in list with multiple patterns."""
    # Primary: "the largest number in [...]"
    match = re.search(r'the\s+largest\s+number\s+in\s+\[(.*?)\]', text)
    if match:
        list_str = match.group(1)
        try:
            numbers = [int(num.strip()) for num in list_str.split(',')]
            if numbers:
                return str(max(numbers))
        except ValueError:
            pass

    # Alternative: "largest number in [...]" (without "the")
    match = re.search(r'largest\s+number\s+in\s+\[(.*?)\]', text)
    if match:
        list_str = match.group(1)
        try:
            numbers = [int(num.strip()) for num in list_str.split(',')]
            if numbers:
                return str(max(numbers))
        except ValueError:
            pass

    # Alternative: "maximum/max/greatest number in [...]"
    match = re.search(r'(?:maximum|max|greatest)\s+number\s+in\s+\[(.*?)\]', text)
    if match:
        list_str = match.group(1)
        try:
            numbers = [int(num.strip()) for num in list_str.split(',')]
            if numbers:
                return str(max(numbers))
        except ValueError:
            pass

    # Alternative: "find the largest number in [...]"
    match = re.search(r'(?:find|get)\s+(?:the\s+)?largest\s+(?:number\s+)?in\s+\[(.*?)\]', text)
    if match:
        list_str = match.group(1)
        try:
            numbers = [int(num.strip()) for num in list_str.split(',')]
            if numbers:
                return str(max(numbers))
        except ValueError:
            pass

    # Alternative: "the highest/topmost number in [...]"
    match = re.search(r'(?:highest|topmost)\s+(?:number\s+)?in\s+\[(.*?)\]', text)
    if match:
        list_str = match.group(1)
        try:
            numbers = [int(num.strip()) for num in list_str.split(',')]
            if numbers:
                return str(max(numbers))
        except ValueError:
            pass

    return None
