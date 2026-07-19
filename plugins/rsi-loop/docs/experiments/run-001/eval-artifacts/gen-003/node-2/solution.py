def pack(items: list[int], capacity: int) -> list[list[int]]:
    """Pack items into bins using complement-matching strategy.

    Uses a two-pointer approach to explicitly pair complementary items:
    - Smallest items from the left
    - Largest items from the right
    When paired items fit together, they go in the same bin.
    When a large item doesn't fit with any small item, it gets its own bin.
    """
    n = len(items)
    if n == 0:
        return []

    # Create list of (size, original_index) tuples and sort by size
    indexed_items = [(items[i], i) for i in range(n)]
    indexed_items.sort()

    bins = []
    left = 0
    right = n - 1

    # Two-pointer complementary matching phase
    # Match smallest items with largest items
    while left < right:
        left_size, left_idx = indexed_items[left]
        right_size, right_idx = indexed_items[right]

        if left_size + right_size <= capacity:
            # Pair small and large items together in one bin
            bins.append([left_idx, right_idx])
            left += 1
            right -= 1
        else:
            # Large item is too large to pair with this small item
            # (and all smaller items won't fit either)
            # Place it alone and continue with the next largest
            bins.append([right_idx])
            right -= 1

    # If odd number of items, the middle item hasn't been placed yet
    if left == right:
        _, middle_idx = indexed_items[left]
        bins.append([middle_idx])

    return bins
