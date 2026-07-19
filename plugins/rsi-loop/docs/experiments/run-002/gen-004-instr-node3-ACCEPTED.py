import re


def _parse_number(s):
    """Parse a number from a string, handling various formats."""
    s = s.strip()
    try:
        return int(s)
    except ValueError:
        try:
            return int(float(s))
        except ValueError:
            return None


def _parse_ordinal(s):
    """Parse ordinal text like 'first', 'second', '2nd', '3rd', etc."""
    s = s.strip().lower()
    ordinal_map = {
        'first': 1, '1st': 1,
        'second': 2, '2nd': 2,
        'third': 3, '3rd': 3,
        'fourth': 4, '4th': 4,
        'fifth': 5, '5th': 5,
        'sixth': 6, '6th': 6,
        'seventh': 7, '7th': 7,
        'eighth': 8, '8th': 8,
        'ninth': 9, '9th': 9,
        'tenth': 10, '10th': 10,
    }
    if s in ordinal_map:
        return ordinal_map[s]
    # Try parsing as numeric ordinal
    match = re.match(r'(\d+)(?:st|nd|rd|th)?', s)
    if match:
        return int(match.group(1))
    return None


def solve(instruction: str) -> str:
    """
    Route a natural-language instruction to the correct operation and return the answer.

    Operations:
    - add: "add X and Y" -> X + Y
    - subtract: "subtract X from Y" -> Y - X
    - multiply: "multiply X by Y" -> X * Y
    - reverse word: "reverse the word X" -> reverse(X)
    - uppercase word: "uppercase the word X" -> upper(X)
    - count letters: "how many letters in X" -> len(X)
    - nth list item: "the Nth item in [list]" -> list[N-1]
    - largest number: "the largest number in [list]" -> max(list)
    """
    s = instruction.strip().lower()

    # Try to detect operation type and extract operands

    # 1. ADD pattern - "add X and Y", "X plus Y", "X added to Y"
    if 'add' in s or 'plus' in s or ('and' in s and re.search(r'\d+\s+and\s+\d+', s)):
        # Look for "add X and Y" pattern
        match = re.search(r'add\s+([-\d.]+)\s+and\s+([-\d.]+)', s)
        if match:
            a = _parse_number(match.group(1))
            b = _parse_number(match.group(2))
            if a is not None and b is not None:
                return str(a + b)
        # Look for "X and Y" or "X plus Y"
        match = re.search(r'([-\d.]+)\s+(?:and|plus)\s+([-\d.]+)', s)
        if match:
            a = _parse_number(match.group(1))
            b = _parse_number(match.group(2))
            if a is not None and b is not None:
                return str(a + b)

    # 2. SUBTRACT pattern - "subtract X from Y", "Y minus X"
    if 'subtract' in s or 'minus' in s:
        # Look for "subtract X from Y"
        match = re.search(r'subtract\s+([-\d.]+)\s+from\s+([-\d.]+)', s)
        if match:
            a = _parse_number(match.group(1))
            b = _parse_number(match.group(2))
            if a is not None and b is not None:
                return str(b - a)
        # Look for "Y minus X"
        match = re.search(r'([-\d.]+)\s+minus\s+([-\d.]+)', s)
        if match:
            a = _parse_number(match.group(1))
            b = _parse_number(match.group(2))
            if a is not None and b is not None:
                return str(a - b)

    # 3. MULTIPLY pattern - "multiply X by Y", "X times Y", "X multiplied by Y"
    if 'multiply' in s or 'times' in s:
        # Look for "multiply X by Y"
        match = re.search(r'multiply\s+([-\d.]+)\s+by\s+([-\d.]+)', s)
        if match:
            a = _parse_number(match.group(1))
            b = _parse_number(match.group(2))
            if a is not None and b is not None:
                return str(a * b)
        # Look for "X times Y"
        match = re.search(r'([-\d.]+)\s+times\s+([-\d.]+)', s)
        if match:
            a = _parse_number(match.group(1))
            b = _parse_number(match.group(2))
            if a is not None and b is not None:
                return str(a * b)

    # 4. REVERSE WORD pattern - "reverse the word X", "reverse word X", "reverse X"
    if 'reverse' in s and 'word' in s:
        # Try with "word" keyword first
        match = re.search(r'reverse\s+(?:the\s+)?word\s+([a-z]+)', s)
        if match:
            word = match.group(1)
            return word[::-1]
        # Try without "word" keyword but still with "reverse"
        match = re.search(r'reverse\s+([a-z]+)', s)
        if match:
            word = match.group(1)
            return word[::-1]

    # 5. UPPERCASE WORD pattern - "uppercase the word X", "uppercase word X", "convert X to uppercase", "make X uppercase"
    if ('uppercase' in s or 'upper' in s or 'convert' in s) and 'word' in s:
        # Try with "word" keyword
        match = re.search(r'(?:uppercase|upper|make)\s+(?:the\s+)?word\s+([a-z]+)', s)
        if not match:
            match = re.search(r'(?:convert|make)\s+([a-z]+)\s+(?:to\s+)?(?:uppercase|upper)', s)
        if match:
            word = match.group(1)
            return word.upper()

    # 6. COUNT LETTERS pattern - "how many letters in X", "count letters in X", "length of X", "number of letters in X"
    if ('how many' in s or 'count' in s or 'length' in s or 'number of' in s) and ('letters' in s or 'characters' in s):
        if 'in' in s:
            # Try various patterns
            match = re.search(r'(?:how many letters in|count letters in|letters in)\s+([a-z]+)', s)
            if not match:
                match = re.search(r'(?:how many|number of)\s+letters\s+in\s+([a-z]+)', s)
            if not match:
                match = re.search(r'(?:how many|number of)\s+characters\s+in\s+([a-z]+)', s)
            if not match:
                match = re.search(r'length\s+of\s+([a-z]+)', s)
            if match:
                word = match.group(1)
                return str(len(word))

    # 7. NTH LIST ITEM pattern - "the Nth item in [list]", "Nth element of [list]", "item at position N"
    # Need to handle ordinals: "the 2nd item in [kiwi, pear, apple]"
    if ('item' in s or 'element' in s) and 'in' in s:
        # Look for bracketed list
        list_match = re.search(r'\[(.*?)\]', s)
        if list_match:
            list_str = list_match.group(1)
            # Look for ordinal before the list
            match = re.search(r'(?:the\s+)?(\d+|first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)(?:st|nd|rd|th)?\s+(?:item|element)(?:\s+in|\s+of)?', s)
            if match:
                position_str = match.group(1)
                position = _parse_ordinal(position_str)
                if position is not None:
                    # Parse comma-separated list
                    items = [item.strip() for item in list_str.split(',')]
                    if 0 < position <= len(items):
                        return items[position - 1]  # Convert 1-indexed to 0-indexed

    # 8. LARGEST NUMBER pattern - "the largest number in [list]", "max of [list]", "largest in [list]", "what is the largest number in [list]"
    if ('largest' in s or 'max' in s or 'greatest' in s or 'highest' in s) and ('number' in s or 'value' in s) and 'in' in s:
        # Look for bracketed list with numbers
        list_match = re.search(r'\[(.*?)\]', s)
        if list_match:
            list_str = list_match.group(1)
            try:
                # Parse comma-separated numbers
                numbers = [int(item.strip()) for item in list_str.split(',')]
                if numbers:
                    return str(max(numbers))
            except ValueError:
                pass

    # Fallback
    return ""
