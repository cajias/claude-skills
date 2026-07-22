import re


def solve(instruction: str) -> str:
    """Return the exact answer to one instruction, as a string."""

    # Normalize: lowercase, strip, collapse multiple spaces
    text = instruction.strip().lower()
    text = re.sub(r'\s+', ' ', text)

    # Strategy: Check operations in order of specificity and complexity.
    # List operations (nth item, largest number) are most specific.
    # Numeric operations (add, subtract, multiply) are next.
    # String operations (reverse, uppercase, count) are simplest.
    #
    # Key robustness improvements:
    # 1. Use word boundaries (\b) in regex to avoid partial keyword matches
    # 2. Flexible clause ordering for list operations
    # 3. Explicit bounds checking and better fallback patterns
    # 4. Synonym coverage with alternation

    # =========================================================================
    # OPERATION 1: NTH LIST ITEM
    # =========================================================================
    # Patterns: "the Nth item in [...]", "[...] find the Nth item",
    # "get the Nth element from [...]", etc.
    if ('[' in text and ']' in text) and (re.search(r'\bitem\b', text) or re.search(r'\belement\b', text)):
        # First, extract the list
        list_match = re.search(r'\[(.*?)\]', text)
        if list_match:
            list_str = list_match.group(1)
            items = [item.strip() for item in list_str.split(',')]

            # Extract ordinal position: "the 2nd item", "3rd element", "1st", etc.
            # Allow flexible clause ordering: position may come before or after list
            ordinal_match = re.search(
                r'\b(\d+)(?:st|nd|rd|th)?\s+(?:item|element)\b',
                text
            )
            if ordinal_match:
                ordinal = int(ordinal_match.group(1))
                # Convert 1-indexed to 0-indexed and validate bounds
                if 1 <= ordinal <= len(items):
                    return items[ordinal - 1]

    # =========================================================================
    # OPERATION 2: LARGEST NUMBER
    # =========================================================================
    # Patterns: "the largest/maximum number in [...]", "find max in [...]",
    # "what's the biggest number in [...]", etc.
    if ('[' in text and ']' in text):
        # Check for any synonym for "largest"
        if re.search(r'\b(?:largest|maximum|max|biggest|greatest)\b', text):
            list_match = re.search(r'\[(.*?)\]', text)
            if list_match:
                list_str = list_match.group(1)
                numbers = []
                # Extract all integers (including negatives) from list items
                for item in list_str.split(','):
                    item = item.strip()
                    num_match = re.search(r'-?\d+', item)
                    if num_match:
                        numbers.append(int(num_match.group(0)))
                # Return max if we found any numbers
                if numbers:
                    return str(max(numbers))

    # =========================================================================
    # OPERATION 3: ADD
    # =========================================================================
    # Patterns: "add X and Y", "add X to Y", "X plus Y", etc.
    if re.search(r'\badd\b', text):
        # Try "add X and Y"
        match = re.search(r'\badd\s+(-?\d+)\s+and\s+(-?\d+)', text)
        if match:
            a, b = int(match.group(1)), int(match.group(2))
            return str(a + b)
        # Try "add X to Y"
        match = re.search(r'\badd\s+(-?\d+)\s+to\s+(-?\d+)', text)
        if match:
            a, b = int(match.group(1)), int(match.group(2))
            return str(a + b)

    # Also try "X plus Y" even if "add" not present
    if re.search(r'\bplus\b', text):
        match = re.search(r'(-?\d+)\s+\bplus\b\s+(-?\d+)', text)
        if match:
            a, b = int(match.group(1)), int(match.group(2))
            return str(a + b)

    # =========================================================================
    # OPERATION 4: SUBTRACT
    # =========================================================================
    # Patterns: "subtract X from Y" -> Y - X, "take X from Y", "Y minus X", etc.
    if re.search(r'\bsubtract\b', text) or re.search(r'\btake\b', text):
        # Try "subtract X from Y" or "take X from Y"
        match = re.search(r'\b(?:subtract|take)\s+(-?\d+)\s+from\s+(-?\d+)', text)
        if match:
            x, y = int(match.group(1)), int(match.group(2))
            return str(y - x)
        # Try "from Y subtract X" (reordered clause)
        match = re.search(r'\bfrom\s+(-?\d+)\s+(?:subtract|take)\s+(-?\d+)', text)
        if match:
            y, x = int(match.group(1)), int(match.group(2))
            return str(y - x)

    # Also try "X minus Y" even if subtract not present
    if re.search(r'\bminus\b', text):
        match = re.search(r'(-?\d+)\s+\bminus\b\s+(-?\d+)', text)
        if match:
            y, x = int(match.group(1)), int(match.group(2))
            return str(y - x)

    # =========================================================================
    # OPERATION 5: MULTIPLY
    # =========================================================================
    # Patterns: "multiply X by Y", "X times Y", "X multiplied by Y", etc.
    if re.search(r'\bmultiply\b', text):
        # Try "multiply X by Y"
        match = re.search(r'\bmultiply\s+(-?\d+)\s+by\s+(-?\d+)', text)
        if match:
            a, b = int(match.group(1)), int(match.group(2))
            return str(a * b)

    # Also try "X times Y" even if multiply not present
    if re.search(r'\btimes\b', text):
        match = re.search(r'(-?\d+)\s+\btimes\b\s+(-?\d+)', text)
        if match:
            a, b = int(match.group(1)), int(match.group(2))
            return str(a * b)

    # =========================================================================
    # OPERATION 6: REVERSE WORD
    # =========================================================================
    # Patterns: "reverse [the] word X", "reverse X", "flip X", etc.
    if re.search(r'\breverse\b', text) or re.search(r'\bflip\b', text) or re.search(r'\bbackwards\b', text):
        # Try "reverse [the] word X"
        match = re.search(r'\b(?:reverse|flip)\s+(?:the\s+)?\bword\b\s+(\w+)', text)
        if match:
            word = match.group(1)
            return word[::-1]
        # Try standalone "reverse X" / "flip X"
        match = re.search(r'\b(?:reverse|flip)\s+(\w+)', text)
        if match:
            word = match.group(1)
            return word[::-1]
        # Try "X backwards" or "backwards X"
        match = re.search(r'\b(\w+)\s+\bbackwards\b', text)
        if not match:
            match = re.search(r'\bbackwards\s+(\w+)', text)
        if match:
            word = match.group(1)
            return word[::-1]

    # =========================================================================
    # OPERATION 7: UPPERCASE WORD
    # =========================================================================
    # Patterns: "uppercase [the] word X", "make X uppercase", "capitalize X", etc.
    if re.search(r'\buppercase\b', text) or re.search(r'\bcapitalize\b', text) or re.search(r'\buppers\b', text) or re.search(r'\ball\s+caps\b', text):
        # Try "uppercase [the] word X"
        match = re.search(r'\buppercase\s+(?:the\s+)?\bword\b\s+(\w+)', text)
        if match:
            word = match.group(1)
            return word.upper()
        # Try "capitalize [the] word X"
        match = re.search(r'\bcapitalize\s+(?:the\s+)?\bword\b\s+(\w+)', text)
        if match:
            word = match.group(1)
            return word.upper()
        # Try "make X uppercase" or standalone "uppercase X"
        match = re.search(r'\buppercase\s+(\w+)', text)
        if match:
            word = match.group(1)
            return word.upper()
        # Try "X all caps" or "all caps X"
        match = re.search(r'\b(\w+)\s+\ball\s+caps\b', text)
        if not match:
            match = re.search(r'\ball\s+caps\s+(\w+)', text)
        if match:
            word = match.group(1)
            return word.upper()

    # =========================================================================
    # OPERATION 8: COUNT LETTERS
    # =========================================================================
    # Patterns: "how many letters in X", "count letters in X", "letter count of X", etc.
    if re.search(r'\bhow\s+many\s+letters\b', text) or re.search(r'\bcount\s+letters\b', text) or re.search(r'\bletter\s+count\b', text) or re.search(r'\bletters\s+in\b', text):
        # Try "how many letters in X"
        match = re.search(r'(?:\bhow\s+many\s+)?\bletters\s+in\s+(\w+)', text)
        if match:
            word = match.group(1)
            return str(len(word))
        # Try "count letters in X" or "count X"
        match = re.search(r'\bcount\s+(?:\bletters\s+)?(?:in\s+)?(\w+)', text)
        if match:
            word = match.group(1)
            return str(len(word))
        # Try "letter count [of|for] X"
        match = re.search(r'\bletter\s+count\s+(?:of|for)\s+(\w+)', text)
        if match:
            word = match.group(1)
            return str(len(word))

    # Fallback: no pattern matched
    return ""
