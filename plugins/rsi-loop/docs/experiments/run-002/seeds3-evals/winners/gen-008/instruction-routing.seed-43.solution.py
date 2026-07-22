import re
from typing import Optional, List


def solve(instruction: str) -> str:
    """Parse instruction and return the exact answer as a string.

    Adversarial-resilient parser with comprehensive pattern coverage,
    tolerance to formatting variations, and robust edge-case handling.
    Handles rephrasing, synonym variation, and formatting differences.
    """
    inst = normalize_input(instruction)

    # Try operations in order of specificity (hardest patterns first)
    result = try_nth_item(inst)
    if result is not None:
        return result

    result = try_largest_number(inst)
    if result is not None:
        return result

    result = try_reverse_word(inst)
    if result is not None:
        return result

    result = try_uppercase_word(inst)
    if result is not None:
        return result

    result = try_count_letters(inst)
    if result is not None:
        return result

    result = try_add(inst)
    if result is not None:
        return result

    result = try_subtract(inst)
    if result is not None:
        return result

    result = try_multiply(inst)
    if result is not None:
        return result

    return ""


def normalize_input(instruction: str) -> str:
    """Normalize input for adversarial-resilient parsing.

    - Lowercase everything
    - Normalize whitespace uniformly
    - Expand written-out ordinals to numeric forms
    - Normalize common synonyms
    """
    s = instruction.strip()
    s = s.lower()
    s = re.sub(r'\s+', ' ', s)  # Collapse multiple spaces

    # Normalize written-out ordinals (1st through 20th)
    ordinal_words = [
        (r'\bfirst\s+(?=item)', '1st '),
        (r'\bsecond\s+(?=item)', '2nd '),
        (r'\bthird\s+(?=item)', '3rd '),
        (r'\bfourth\s+(?=item)', '4th '),
        (r'\bfifth\s+(?=item)', '5th '),
        (r'\bsixth\s+(?=item)', '6th '),
        (r'\bseventh\s+(?=item)', '7th '),
        (r'\beighth\s+(?=item)', '8th '),
        (r'\bninth\s+(?=item)', '9th '),
        (r'\btenth\s+(?=item)', '10th '),
        (r'\beleven(?:th)?\s+(?=item)', '11th '),
        (r'\btwelfth\s+(?=item)', '12th '),
        (r'\bthirteen(?:th)?\s+(?=item)', '13th '),
        (r'\bfourteen(?:th)?\s+(?=item)', '14th '),
        (r'\bfifteen(?:th)?\s+(?=item)', '15th '),
        (r'\bsixteen(?:th)?\s+(?=item)', '16th '),
        (r'\bseventeen(?:th)?\s+(?=item)', '17th '),
        (r'\beighteen(?:th)?\s+(?=item)', '18th '),
        (r'\bnineteen(?:th)?\s+(?=item)', '19th '),
        (r'\btwentieth?\s+(?=item)', '20th '),
    ]
    for pattern, replacement in ordinal_words:
        s = re.sub(pattern, replacement, s)

    # Normalize operation synonyms
    s = re.sub(r'\b(?:max|maximum|biggest|greatest)\b', 'largest', s)
    s = re.sub(r'\b(?:sum|add\s+up)\b', 'add', s)
    s = re.sub(r'\b(?:difference|minus)\b', 'subtract', s)
    s = re.sub(r'\b(?:product|multiply|multiplied)\b', 'multiply', s)

    return s


def try_nth_item(inst: str) -> Optional[str]:
    """Parse nth list item with comprehensive pattern variants."""
    if 'item' not in inst or '[' not in inst or ']' not in inst:
        return None

    list_match = re.search(r'\[(.*?)\]', inst)
    if not list_match:
        return None

    list_str = list_match.group(1)

    # Pattern 1: "the Nth item" with optional ordinal suffix
    pos_match = re.search(r'the\s+(\d+)(?:st|nd|rd|th)?\s+item\b', inst)
    if pos_match:
        pos = int(pos_match.group(1))
        items = parse_list_items(list_str)
        idx = pos - 1
        if 0 <= idx < len(items):
            return items[idx]

    # Pattern 2: "Nth item" (without "the")
    pos_match = re.search(r'(?<!the\s)(?<!\bfirst\s)(?<!\bsecond\s)(\d+)(?:st|nd|rd|th)?\s+item\b', inst)
    if pos_match:
        pos = int(pos_match.group(1))
        items = parse_list_items(list_str)
        idx = pos - 1
        if 0 <= idx < len(items):
            return items[idx]

    # Pattern 3: "item number N" or "item N"
    pos_match = re.search(r'\bitem\s+(?:number\s+)?(\d+)\b', inst)
    if pos_match:
        pos = int(pos_match.group(1))
        items = parse_list_items(list_str)
        idx = pos - 1
        if 0 <= idx < len(items):
            return items[idx]

    return None


def try_largest_number(inst: str) -> Optional[str]:
    """Parse largest number with comprehensive pattern variants."""
    if '[' not in inst or ']' not in inst:
        return None

    if not re.search(r'\b(?:largest|max|biggest|greatest)\b', inst) or 'number' not in inst:
        return None

    list_match = re.search(r'\[(.*?)\]', inst)
    if not list_match:
        return None

    list_str = list_match.group(1)

    try:
        numbers = [int(n) for n in re.findall(r'-?\d+', list_str)]
        if numbers:
            return str(max(numbers))
    except (ValueError, IndexError):
        pass

    return None


def try_reverse_word(inst: str) -> Optional[str]:
    """Parse reverse word with comprehensive pattern variants."""
    if 'reverse' not in inst:
        return None

    # Pattern 1: "reverse the word <word>"
    word_match = re.search(r'reverse\s+(?:the\s+)?word\s+([a-zA-Z0-9_-]+)', inst)
    if word_match:
        word = word_match.group(1)
        return word[::-1]

    # Pattern 2: "reverse <word>" (standalone)
    word_match = re.search(r'reverse\s+([a-zA-Z0-9_-]+)(?:\s|$)', inst)
    if word_match:
        word = word_match.group(1)
        # Avoid matching common non-word tokens
        if word not in ('word', 'the', 'string'):
            return word[::-1]

    return None


def try_uppercase_word(inst: str) -> Optional[str]:
    """Parse uppercase word with comprehensive pattern variants."""
    if 'word' not in inst and not re.search(r'\b(?:uppercase|upper|capital)\b', inst):
        return None

    # Pattern 1: "uppercase the word <word>"
    word_match = re.search(r'(?:uppercase|upper|make|capitalize)\s+(?:the\s+)?word\s+([a-zA-Z0-9_-]+)', inst)
    if word_match:
        word = word_match.group(1)
        return word.upper()

    # Pattern 2: "make <word> uppercase"
    word_match = re.search(r'make\s+([a-zA-Z0-9_-]+)\s+(?:uppercase|upper|capital)', inst)
    if word_match:
        word = word_match.group(1)
        return word.upper()

    # Pattern 3: "convert <word> to uppercase"
    word_match = re.search(r'convert\s+([a-zA-Z0-9_-]+)\s+(?:to\s+)?(?:uppercase|upper|capital)', inst)
    if word_match:
        word = word_match.group(1)
        return word.upper()

    # Pattern 4: "<word> in uppercase" or "<word> to uppercase"
    word_match = re.search(r'([a-zA-Z0-9_-]+)\s+(?:to|in)\s+(?:uppercase|upper|capital)', inst)
    if word_match:
        word = word_match.group(1)
        return word.upper()

    return None


def try_count_letters(inst: str) -> Optional[str]:
    """Parse count letters with comprehensive pattern variants."""
    if 'letter' not in inst or 'in' not in inst:
        return None

    # Pattern 1: "how many letters in <word>"
    count_match = re.search(r'how\s+many\s+letters?\s+(?:are\s+)?in\s+([a-zA-Z0-9_-]+)', inst)
    if count_match:
        word = count_match.group(1)
        return str(len(word))

    # Pattern 2: "count [the] letters in <word>"
    count_match = re.search(r'count\s+(?:the\s+)?letters?\s+(?:in|of)\s+([a-zA-Z0-9_-]+)', inst)
    if count_match:
        word = count_match.group(1)
        return str(len(word))

    # Pattern 3: "number of letters in <word>" or "letter count in <word>"
    count_match = re.search(r'(?:number\s+of|count\s+of)\s+letters?\s+in\s+([a-zA-Z0-9_-]+)', inst)
    if count_match:
        word = count_match.group(1)
        return str(len(word))

    # Pattern 4: generic "letters in <word>"
    count_match = re.search(r'letters?\s+in\s+([a-zA-Z0-9_-]+)', inst)
    if count_match:
        word = count_match.group(1)
        if word != 'letters':
            return str(len(word))

    return None


def try_add(inst: str) -> Optional[str]:
    """Parse add operation with comprehensive pattern variants."""
    if not any(x in inst for x in ['add', 'plus', 'sum']):
        return None

    # Pattern 1: "add <num> and <num>"
    add_match = re.search(r'add\s+(-?\d+)\s+and\s+(-?\d+)', inst)
    if add_match:
        a = int(add_match.group(1))
        b = int(add_match.group(2))
        return str(a + b)

    # Pattern 2: "add <num> to <num>"
    add_match = re.search(r'add\s+(-?\d+)\s+to\s+(-?\d+)', inst)
    if add_match:
        a = int(add_match.group(1))
        b = int(add_match.group(2))
        return str(a + b)

    # Pattern 3: "<num> plus <num>"
    plus_match = re.search(r'(-?\d+)\s+plus\s+(-?\d+)', inst)
    if plus_match:
        a = int(plus_match.group(1))
        b = int(plus_match.group(2))
        return str(a + b)

    # Pattern 4: "sum of <num> and <num>"
    sum_match = re.search(r'sum\s+(?:of\s+)?(-?\d+)\s+and\s+(-?\d+)', inst)
    if sum_match:
        a = int(sum_match.group(1))
        b = int(sum_match.group(2))
        return str(a + b)

    # Pattern 5: weak fallback for "add" + two numbers anywhere
    if 'add' in inst:
        nums = re.findall(r'-?\d+', inst)
        if len(nums) >= 2:
            return str(int(nums[0]) + int(nums[1]))

    return None


def try_subtract(inst: str) -> Optional[str]:
    """Parse subtract operation with comprehensive pattern variants."""
    if not any(x in inst for x in ['subtract', 'minus', 'difference', 'take', 'remove']):
        return None

    # Pattern 1: "subtract <num> from <num>" -> second - first
    sub_match = re.search(r'subtract\s+(-?\d+)\s+from\s+(-?\d+)', inst)
    if sub_match:
        a = int(sub_match.group(1))
        b = int(sub_match.group(2))
        return str(b - a)

    # Pattern 2: "<num> minus <num>" -> first - second
    minus_match = re.search(r'(-?\d+)\s+minus\s+(-?\d+)', inst)
    if minus_match:
        a = int(minus_match.group(1))
        b = int(minus_match.group(2))
        return str(a - b)

    # Pattern 3: "take <num> from <num>" or "remove <num> from <num>" -> second - first
    take_match = re.search(r'(?:take|remove)\s+(-?\d+)\s+from\s+(-?\d+)', inst)
    if take_match:
        a = int(take_match.group(1))
        b = int(take_match.group(2))
        return str(b - a)

    # Pattern 4: "difference between <num> and <num>" or "difference of <num> and <num>"
    diff_match = re.search(r'difference\s+(?:between|of)\s+(-?\d+)\s+and\s+(-?\d+)', inst)
    if diff_match:
        a = int(diff_match.group(1))
        b = int(diff_match.group(2))
        return str(a - b)

    # Pattern 5: "subtract <num> and <num>" (ambiguous, left - right)
    sub_match = re.search(r'subtract\s+(-?\d+)\s+and\s+(-?\d+)', inst)
    if sub_match:
        a = int(sub_match.group(1))
        b = int(sub_match.group(2))
        return str(a - b)

    return None


def try_multiply(inst: str) -> Optional[str]:
    """Parse multiply operation with comprehensive pattern variants."""
    if not any(x in inst for x in ['multiply', 'times', 'product']):
        return None

    # Pattern 1: "multiply <num> by <num>"
    mul_match = re.search(r'multiply\s+(-?\d+)\s+by\s+(-?\d+)', inst)
    if mul_match:
        a = int(mul_match.group(1))
        b = int(mul_match.group(2))
        return str(a * b)

    # Pattern 2: "<num> times <num>"
    times_match = re.search(r'(-?\d+)\s+times\s+(-?\d+)', inst)
    if times_match:
        a = int(times_match.group(1))
        b = int(times_match.group(2))
        return str(a * b)

    # Pattern 3: "product of <num> and <num>"
    prod_match = re.search(r'product\s+(?:of\s+)?(-?\d+)\s+and\s+(-?\d+)', inst)
    if prod_match:
        a = int(prod_match.group(1))
        b = int(prod_match.group(2))
        return str(a * b)

    # Pattern 4: "<num> multiplied by <num>" (handled by normalization as "multiply")
    mul_match = re.search(r'(-?\d+)\s+multiply\s+(-?\d+)', inst)
    if mul_match:
        a = int(mul_match.group(1))
        b = int(mul_match.group(2))
        return str(a * b)

    return None


def parse_list_items(list_str: str) -> List[str]:
    """Parse comma-separated list items robustly.

    Handles:
    - Whitespace normalization
    - Quoted strings (single or double)
    - Numbers and alphanumeric items
    """
    items = []
    for item in list_str.split(','):
        item = item.strip()

        # Remove surrounding quotes if present
        if (item.startswith('"') and item.endswith('"')) or \
           (item.startswith("'") and item.endswith("'")):
            item = item[1:-1].strip()

        items.append(item)

    return items
