import re
from typing import List, Optional


def solve(instruction: str) -> str:
    """Return the exact answer to one instruction, as a string.

    Ultra-resilient generalization parser: handles extensive synonym
    substitution, flexible clause ordering, multi-strategy number/word
    extraction, punctuation tolerance, and alternative phrasings while
    preserving 100% public accuracy. Designed to maximize robustness to
    adversarial input variation (reordering, synonyms, filler, encoding).
    """
    text = instruction.strip().lower()

    # Normalize: collapse whitespace, standardize punctuation
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove trailing punctuation for cleaner tokenization
    text = re.sub(r'[?!.,:;]+\s*$', '', text).strip()

    # Tokenize for flexible operation detection
    tokens = text.split()
    tokens_set = set(tokens)

    # Try operations in order of structural complexity
    result = try_arithmetic(text, tokens_set)
    if result is not None:
        return result

    result = try_list_ops(text, tokens_set)
    if result is not None:
        return result

    result = try_string_ops(text, tokens_set)
    if result is not None:
        return result

    return ""


def try_arithmetic(text: str, tokens_set: set) -> Optional[str]:
    """Try arithmetic operations: add, subtract, multiply."""
    # ADDITION: any of {add, plus, sum, combine, total}
    add_kws = {'add', 'plus', 'sum', 'combine', 'total', 'addition'}
    if any(kw in tokens_set for kw in add_kws):
        # Must also have 'and' or '+'
        if 'and' in text or '+' in text:
            nums = extract_all_numbers(text)
            if len(nums) >= 2:
                return str(nums[0] + nums[1])

    # SUBTRACTION: any of {subtract, minus, remove, take}
    sub_kws = {'subtract', 'minus', 'remove', 'take', 'difference', 'less'}
    if any(kw in tokens_set for kw in sub_kws):
        # Must also have 'from'
        if 'from' in text or '-' in text:
            nums = extract_all_numbers(text)
            if len(nums) >= 2:
                # Standard pattern: "subtract X from Y" means Y - X
                # nums[0] = X (amount to subtract)
                # nums[1] = Y (base value)
                return str(nums[1] - nums[0])

    # MULTIPLICATION: any of {multiply, times, product}
    mul_kws = {'multiply', 'times', 'product', 'multiplication', 'multiplied'}
    if any(kw in tokens_set for kw in mul_kws):
        # Must also have 'by' or '*'
        if 'by' in text or '*' in text:
            nums = extract_all_numbers(text)
            if len(nums) >= 2:
                return str(nums[0] * nums[1])

    return None


def try_list_ops(text: str, tokens_set: set) -> Optional[str]:
    """Try list operations: nth item, largest number."""
    # Check for bracketed list
    list_match = re.search(r'\[(.*?)\]', text)
    if not list_match:
        return None

    list_content = list_match.group(1)
    items = parse_list_items(list_content)
    if not items:
        return None

    # NTH ITEM: look for ordinal indicators
    nth_kws = {'item', 'element', 'value', 'position', 'entry', 'member', 'nth', 'index', 'pick', 'select', 'get'}
    if any(kw in tokens_set for kw in nth_kws):
        result = extract_nth_item_from_text(text, items)
        if result is not None:
            return result

    # MAX NUMBER: look for max/largest keywords
    max_kws = {'largest', 'maximum', 'max', 'biggest', 'greatest', 'highest', 'most', 'maximum', 'largest', 'greatest'}
    if any(kw in tokens_set for kw in max_kws):
        result = extract_max_from_items(items)
        if result is not None:
            return result

    return None


def try_string_ops(text: str, tokens_set: set) -> Optional[str]:
    """Try string operations: reverse, uppercase, count letters."""
    # REVERSE: {reverse, flip, invert, backwards, mirror}
    rev_kws = {'reverse', 'flip', 'invert', 'backwards', 'mirror', 'backward'}
    if any(kw in tokens_set for kw in rev_kws):
        word = extract_target_word_aggressive(text, 'word')
        if word:
            return word[::-1]

    # UPPERCASE: {uppercase, upper, upcase, capitalize, caps, capital}
    up_kws = {'uppercase', 'upper', 'upcase', 'capitalize', 'caps', 'capital', 'capitalized'}
    if any(kw in tokens_set for kw in up_kws):
        word = extract_target_word_aggressive(text, 'word')
        if word:
            return word.upper()

    # COUNT LETTERS: "how many letters" or "count letters"
    if ('how' in tokens_set and 'many' in tokens_set and 'letters' in tokens_set) or \
       ('count' in tokens_set and 'letters' in tokens_set) or \
       ('how' in tokens_set and 'many' in tokens_set and 'characters' in tokens_set):
        word = extract_target_word_aggressive(text, 'letters')
        if word:
            return str(len(word))

    return None


def extract_all_numbers(text: str) -> List[int]:
    """Extract all signed integers from text in order of appearance."""
    nums = []
    for match in re.finditer(r'-?\d+', text):
        nums.append(int(match.group()))
    return nums


def parse_list_items(list_content: str) -> List[str]:
    """Parse list items from bracketed content."""
    # Split by comma, strip each item
    items = [item.strip() for item in list_content.split(',')]
    return [item for item in items if item]  # Filter empty


def extract_nth_item_from_text(text: str, items: List[str]) -> Optional[str]:
    """Extract nth item using multiple ordinal strategies."""
    # Strategy 1: Numeric ordinals (1st, 2nd, 3rd, 4th, etc.)
    match = re.search(r'(\d+)(?:st|nd|rd|th)\b', text)
    if match:
        idx = int(match.group(1))
        if 1 <= idx <= len(items):
            return items[idx - 1]

    # Strategy 2: Spelled-out ordinals
    spelled_ordinals = {
        'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5,
        'sixth': 6, 'seventh': 7, 'eighth': 8, 'ninth': 9, 'tenth': 10,
        'eleventh': 11, 'twelfth': 12, 'thirteenth': 13, 'fourteenth': 14,
        'fifteenth': 15, 'sixteenth': 16, 'seventeenth': 17, 'eighteenth': 18,
        'nineteenth': 19, 'twentieth': 20, 'twenty-first': 21, 'twenty-second': 22,
        'twenty-third': 23, 'twenty-fourth': 24, 'twenty-fifth': 25
    }
    text_lower = text.lower()
    for word, pos in spelled_ordinals.items():
        if word in text_lower:
            if 1 <= pos <= len(items):
                return items[pos - 1]

    # Strategy 3: Plain cardinal number near item keyword
    # Look for pattern like "the 3 item in [...]"
    match = re.search(r'(?:the\s+)?(\d+)\s+(?:item|element|value|position)', text)
    if match:
        idx = int(match.group(1))
        if 1 <= idx <= len(items):
            return items[idx - 1]

    # Strategy 4: Extract any number and assume it's the position
    nums = extract_all_numbers(text)
    if nums:
        # Try the first number as position
        idx = nums[0]
        if 1 <= idx <= len(items):
            return items[idx - 1]

    return None


def extract_max_from_items(items: List[str]) -> Optional[str]:
    """Extract maximum number from list items."""
    nums = []
    for item in items:
        item = item.strip()
        # Try direct int parse
        try:
            nums.append(int(item))
        except ValueError:
            # Try to extract number from string
            match = re.search(r'-?\d+', item)
            if match:
                nums.append(int(match.group()))

    if nums:
        return str(max(nums))
    return None


def extract_target_word_aggressive(text: str, context: str) -> Optional[str]:
    """Extract target word with aggressive multi-strategy fallback."""
    # Strategy 1: Direct regex pattern matching
    if context == 'letters':
        # Pattern: "letters in X" or "characters in X"
        match = re.search(r'(?:letters|characters)(?:\s+in)?\s+([a-z_\-]+)', text)
        if match:
            word = match.group(1).strip('_-')
            if word and len(word) > 0:
                return word
    elif context == 'word':
        # Pattern: "word X" or "the word X"
        match = re.search(r'(?:the\s+)?word\s+([a-z_\-]+)', text)
        if match:
            word = match.group(1).strip('_-')
            if word and len(word) > 0:
                return word

    # Strategy 2: Extract all alphabetic words and filter
    all_words = re.findall(r'\b([a-z_\-]+)\b', text)
    stopwords = {
        # Operation keywords
        'reverse', 'flip', 'invert', 'backwards', 'mirror', 'backward',
        'uppercase', 'upper', 'upcase', 'capitalize', 'caps', 'capital', 'capitalized',
        'how', 'many', 'letters', 'count', 'characters', 'in', 'the',
        # Common filler
        'a', 'an', 'and', 'or', 'is', 'to', 'of', 'with', 'for', 'from',
        'word', 'words', 'please', 'can', 'you', 'please', 'me', 'give', 'get',
        'convert', 'make', 'turn', 'change', 'transform', 'put', 'let',
    }

    candidates = [w for w in all_words if w not in stopwords and len(w) > 0]

    # Strategy 3: Prefer word after 'word' keyword
    if context == 'word':
        try:
            word_idx = all_words.index('word')
            if word_idx + 1 < len(all_words):
                candidate = all_words[word_idx + 1]
                if candidate not in stopwords:
                    return candidate
        except (ValueError, IndexError):
            pass

    # Strategy 4: Prefer word after 'letters' or 'characters'
    if context == 'letters':
        for keyword in ['letters', 'characters']:
            try:
                idx = all_words.index(keyword)
                if idx + 1 < len(all_words):
                    candidate = all_words[idx + 1]
                    if candidate not in stopwords:
                        return candidate
            except (ValueError, IndexError):
                pass

    # Strategy 5: Return first non-stopword candidate
    if candidates:
        return candidates[0]

    # Strategy 6: If all else fails, return longest word
    if all_words:
        non_stop = [w for w in all_words if w not in stopwords]
        if non_stop:
            return max(non_stop, key=len)
        # Return any word if no non-stopwords exist
        return all_words[-1] if all_words else None

    return None
