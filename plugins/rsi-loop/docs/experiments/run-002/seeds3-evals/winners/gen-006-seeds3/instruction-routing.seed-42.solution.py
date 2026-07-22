import re


def solve(instruction: str) -> str:
    """
    Robust instruction router with principled, ultra-tolerant parsing.

    Strategy: Aggressively normalize and preprocess input, then detect operations
    using specificity-ordered patterns with rich synonym/variant fallbacks.
    Each operation tries multiple pattern variants to maximize generalization
    to adversarially rephrased, restructured, and edge-case inputs.
    """

    # Normalize: lowercase, strip, compress whitespace, remove extra punctuation
    text = instruction.strip().lower()
    text = re.sub(r'\s+', ' ', text)

    # ========== OPERATION 1: LARGEST NUMBER (most specific: list + comparison) ==========
    # Patterns: "the largest number in [...]", "largest in [...]", "max of [...]",
    # "find the largest", "what is the largest", "biggest number", etc.
    max_patterns = [
        r'(?:the\s+)?(?:largest|biggest|greatest|maximum|max)\s+(?:number\s+)?in\s+\[(.*?)\]',
        r'(?:the\s+)?(?:largest|biggest|greatest|maximum|max)\s+(?:value\s+)?(?:from|in|of)\s+\[(.*?)\]',
        r'\[(.*?)\]\s*,?\s*(?:largest|biggest|maximum)',
        r'(?:find\s+)?(?:the\s+)?(?:largest|biggest|maximum|max)\s+(?:from|of|in)\s+\[(.*?)\]',
        r'(?:what\s+is\s+the\s+)?(?:largest|biggest|maximum)\s+(?:number\s+)?in\s+\[(.*?)\]',
        r'(?:calculate|compute|get)\s+(?:the\s+)?(?:largest|biggest|maximum)\s+(?:from|in)\s+\[(.*?)\]',
    ]
    for pattern in max_patterns:
        match = re.search(pattern, text)
        if match:
            nums_str = match.group(1)
            try:
                numbers = [int(n.strip()) for n in nums_str.split(',')]
                if numbers:
                    return str(max(numbers))
            except ValueError:
                pass

    # ========== OPERATION 2: NTH LIST ITEM (specific: list + ordinal) ==========
    # Patterns: "the Nth item in [...]", "Nth element in [...]", "Nth from [...]", etc.
    # Handle ordinals with and without suffixes, and flexible ordering
    nth_patterns = [
        r'(?:the\s+)?(\d+)(?:\s*(?:st|nd|rd|th))?\s+(?:item|element|position|entry|one)\s+in\s+\[(.*?)\]',
        r'\[(.*?)\]\s*,?\s*(?:the\s+)?(\d+)(?:\s*(?:st|nd|rd|th))?\s+(?:item|element)',
        r'(?:the\s+)?(\d+)(?:\s*(?:st|nd|rd|th))?\s+(?:from|in|of|within)\s+\[(.*?)\]',
        r'(?:pick|select|get|find|retrieve)\s+(?:the\s+)?(\d+)(?:\s*(?:st|nd|rd|th))?\s+(?:item|element)?\s+(?:from|in|of)\s+\[(.*?)\]',
        r'(?:what\s+is\s+the\s+)?(\d+)(?:\s*(?:st|nd|rd|th))?\s+(?:item|element|entry)\s+(?:in|from)\s+\[(.*?)\]',
        r'(?:the\s+)?item\s+(?:at\s+)?(?:position\s+)?(\d+)(?:\s*(?:st|nd|rd|th))?\s+in\s+\[(.*?)\]',
    ]
    for pattern in nth_patterns:
        match = re.search(pattern, text)
        if match:
            # Handle group order for second pattern (reversed)
            groups = match.groups()
            if len(groups) == 2:
                # Try to detect if groups are reversed by looking at pattern structure
                if 'item|element' in pattern and '\[' in pattern:
                    pos_str = groups[-1] if groups[-1] and not groups[-1].startswith('[') else groups[0]
                    items_str = groups[0] if groups[0] and '[' in str(groups[0]) or groups[0] and ',' in groups[0] else groups[1]
                    # Safer: look for actual list content
                    has_brackets = '[' in text[match.start():match.end()]
                    if text[match.start():match.end()].index('[') if '[' in text[match.start():match.end()] else -1 < text[match.start():match.end()].index(str(match.group(1))) if str(match.group(1)) in text[match.start():match.end()] else -1:
                        position = int(match.group(1))
                        items_str = match.group(2)
                    else:
                        items_str = match.group(1)
                        position = int(match.group(2))
                else:
                    position = int(match.group(1))
                    items_str = match.group(2)

                items = [item.strip() for item in items_str.split(',')]
                if 1 <= position <= len(items):
                    return items[position - 1]

    # ========== OPERATION 3: COUNT LETTERS (medium: word extraction + measurement) ==========
    # Patterns: "how many letters in X", "count letters in X", "length of X",
    # "letters in X", "letter count", "how many letters", etc.
    count_patterns = [
        r'(?:how\s+many|how\s+much|what\s+is\s+the|count\s+the)\s+(?:number\s+)?(?:of\s+)?letters\s+(?:in|of|inside|within)\s+(\w+)',
        r'(?:count|number|total|sum)\s+(?:of\s+)?(?:letters|characters)?\s+(?:in|of)\s+(\w+)',
        r'(?:the\s+)?(?:length|size|count|total)\s+(?:of\s+)?(?:the\s+)?(?:word\s+)?(\w+)',
        r'(\w+)\s+has\s+(?:how\s+many|what\s+number\s+of|how\s+many)\s+letters',
        r'(?:letter\s+)?count\s+(?:in|for|of)\s+(\w+)',
        r'(?:letters\s+in|characters\s+in|letters\s+within)\s+(\w+)',
        r'(?:how\s+many)\s+(?:letters|chars|characters)\s+(?:are\s+there\s+)?in\s+(\w+)',
    ]
    for pattern in count_patterns:
        match = re.search(pattern, text)
        if match:
            word = match.group(1)
            return str(len(word))

    # ========== OPERATION 4: REVERSE WORD (medium: word transformation) ==========
    # Patterns: "reverse the word X", "spell X backwards", "reverse X", etc.
    reverse_patterns = [
        r'reverse\s+(?:the\s+)?(?:word\s+)?(\w+)',
        r'spell\s+(\w+)\s+(?:backwards|in\s+reverse|backward)',
        r'(?:backwards|reversed|in\s+reverse|backward)\s+(?:spelling|spelling\s+of|spell\s+of|of|for)?\s+(\w+)',
        r'(\w+)\s+(?:reversed|spelled\s+backwards|in\s+reverse|backward)',
        r'(?:what\s+is\s+)?(\w+)\s+(?:reversed|backwards|backward)',
        r'(?:reverse|flip|invert)\s+(?:the\s+word\s+)?(\w+)',
        r'write\s+(\w+)\s+(?:backwards|in\s+reverse)',
        r'(\w+)\s+backwards',
    ]
    for pattern in reverse_patterns:
        match = re.search(pattern, text)
        if match:
            word = match.group(1)
            return word[::-1]

    # ========== OPERATION 5: UPPERCASE WORD (medium: word transformation) ==========
    # Patterns: "uppercase the word X", "make X uppercase", "X in uppercase", etc.
    uppercase_patterns = [
        r'uppercase\s+(?:the\s+)?(?:word\s+)?(\w+)',
        r'(?:make|convert|turn|change)\s+(\w+)\s+(?:to\s+)?(?:uppercase|capital|capitals|all\s+caps)',
        r'(?:shout|yell|capitalize)\s+(?:the\s+)?(?:word\s+)?(\w+)',
        r'(\w+)\s+in\s+(?:uppercase|capital|all\s+caps)',
        r'(?:what\s+is\s+)?(\w+)\s+(?:in\s+uppercase|uppercase)',
        r'(?:uppercase|capitalize|upcase|all\s+caps)\s+(?:the\s+)?(\w+)',
        r'(?:write|spell|say)\s+(\w+)\s+in\s+(?:uppercase|capitals|all\s+caps)',
    ]
    for pattern in uppercase_patterns:
        match = re.search(pattern, text)
        if match:
            word = match.group(1)
            return word.upper()

    # ========== OPERATION 6: MULTIPLY (easy arithmetic) ==========
    # Patterns: "multiply X by Y", "X times Y", "X multiplied by Y", etc.
    multiply_patterns = [
        r'multiply\s+(-?\d+)\s+by\s+(-?\d+)',
        r'(-?\d+)\s+times?\s+(-?\d+)',
        r'(-?\d+)\s+multiplied\s+by\s+(-?\d+)',
        r'product\s+(?:of\s+)?(-?\d+)\s+(?:and\s+)?(-?\d+)',
        r'(?:what\s+is\s+)?(-?\d+)\s+times?\s+(-?\d+)',
        r'(-?\d+)\s+(?:\*|x)\s+(-?\d+)',
        r'(?:calculate|compute|get)\s+(-?\d+)\s+times?\s+(-?\d+)',
        r'multiply\s+by\s+(-?\d+).*?(-?\d+)',
    ]
    for pattern in multiply_patterns:
        match = re.search(pattern, text)
        if match:
            a, b = int(match.group(1)), int(match.group(2))
            return str(a * b)

    # ========== OPERATION 7: ADD (easy arithmetic) ==========
    # Patterns: "add X and Y", "X plus Y", "sum of X and Y", etc.
    add_patterns = [
        r'add\s+(-?\d+)\s+and\s+(-?\d+)',
        r'(-?\d+)\s+(?:plus|\+)\s+(-?\d+)',
        r'sum\s+(?:of\s+)?(-?\d+)\s+(?:and\s+)?(-?\d+)',
        r'(-?\d+)\s+added\s+to\s+(-?\d+)',
        r'(?:what\s+is\s+)?(-?\d+)\s+(?:plus|\+)\s+(-?\d+)',
        r'(-?\d+)\s+and\s+(-?\d+)',
        r'(?:calculate|compute|get)\s+(?:the\s+)?sum\s+(?:of\s+)?(-?\d+)\s+and\s+(-?\d+)',
        r'add\s+(-?\d+).*?(?:to|and)\s+(-?\d+)',
    ]
    for pattern in add_patterns:
        match = re.search(pattern, text)
        if match:
            a, b = int(match.group(1)), int(match.group(2))
            return str(a + b)

    # ========== OPERATION 8: SUBTRACT (easy arithmetic) ==========
    # Patterns: "subtract X from Y", "Y minus X", "difference", etc.
    # Order is critical: "subtract X from Y" means Y - X
    subtract_patterns = [
        r'subtract\s+(-?\d+)\s+from\s+(-?\d+)',
        r'take\s+(?:away\s+)?(-?\d+)\s+from\s+(-?\d+)',
        r'(-?\d+)\s+minus\s+(-?\d+)',
        r'difference\s+(?:between|of)\s+(-?\d+)\s+and\s+(-?\d+)',
        r'(?:what\s+is\s+)?(-?\d+)\s+minus\s+(-?\d+)',
        r'(-?\d+)\s+(?:-)\s+(-?\d+)',
        r'(?:calculate|compute|get)\s+(?:the\s+)?difference\s+(?:between|of)\s+(-?\d+)\s+and\s+(-?\d+)',
        r'subtract\s+(-?\d+).*?from\s+(-?\d+)',
        r'(?:remove|deduct)\s+(-?\d+)\s+from\s+(-?\d+)',
    ]
    for pattern in subtract_patterns:
        match = re.search(pattern, text)
        if match:
            # For "subtract X from Y" patterns: order is (Y - X)
            if 'subtract' in pattern or 'take' in pattern or 'remove' in pattern or 'deduct' in pattern:
                x, y = int(match.group(1)), int(match.group(2))
                return str(y - x)
            else:
                # For "X minus Y" patterns: order is (X - Y)
                x, y = int(match.group(1)), int(match.group(2))
                return str(x - y)

    # Fallback: no operation recognized
    return ""
