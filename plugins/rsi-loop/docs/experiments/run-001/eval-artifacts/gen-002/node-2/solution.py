def pack(items: list[int], capacity: int) -> list[list[int]]:
    """Pack items into bins using complement-matching strategy.

    This approach explicitly pairs complementary items (small with large)
    before packing, rather than using a single-pass greedy algorithm.
    """
    n = len(items)

    # Create (size, original_index) pairs and sort by size
    indexed_items = [(items[i], i) for i in range(n)]
    indexed_items.sort()

    bins = []
    # Track which items (by their original indices) have been packed
    used = set()

    # Phase 1: Two-pointer matching of complementary items
    # Match smallest with largest to fill bins efficiently
    left = 0
    right = n - 1

    while left < right:
        small_size, small_idx = indexed_items[left]
        large_size, large_idx = indexed_items[right]

        if small_idx not in used and large_idx not in used:
            # Both items are available
            if small_size + large_size <= capacity:
                # Complementary pair fits together
                bins.append([small_idx, large_idx])
                used.add(small_idx)
                used.add(large_idx)
                left += 1
                right -= 1
            else:
                # Large item too big to pair with this small item
                # Try large with a slightly larger small item
                right -= 1
        elif small_idx in used:
            # Small item already packed, move to next small
            left += 1
        else:
            # Large item already packed, move to next large
            right -= 1

    # Phase 2: Pack remaining unpacked items
    remaining = []
    for size, idx in indexed_items:
        if idx not in used:
            remaining.append((size, idx))

    # Sort remaining by size in descending order (First Fit Decreasing)
    remaining.sort(reverse=True)

    # Use First Fit strategy for remaining items
    for size, idx in remaining:
        placed = False
        # Try to fit into an existing bin
        for bin_list in bins:
            bin_sum = sum(items[i] for i in bin_list)
            if bin_sum + size <= capacity:
                bin_list.append(idx)
                placed = True
                break

        # Create a new bin if item doesn't fit in any existing bin
        if not placed:
            bins.append([idx])

    return bins
