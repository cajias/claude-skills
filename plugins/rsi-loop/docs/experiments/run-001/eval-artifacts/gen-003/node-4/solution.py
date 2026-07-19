def pack(items: list[int], capacity: int) -> list[list[int]]:
    """Pack items into bins using exact-hybrid approach.

    For small instances (n <= 20): use branch-and-bound exact algorithm.
    For larger instances: use Best Fit Decreasing (fast greedy).
    """
    n = len(items)

    if n == 0:
        return []

    # For small instances, use exact branch-and-bound
    if n <= 20:
        return _pack_exact(items, capacity)
    else:
        return _pack_bfd(items, capacity)


def _pack_exact(items: list[int], capacity: int) -> list[list[int]]:
    """Exact algorithm using branch-and-bound backtracking.

    Sorts items in decreasing order and recursively tries to pack them,
    pruning branches when current bin count exceeds best found.
    """
    n = len(items)

    # Create indexed items and sort by size (decreasing)
    indexed_items = [(items[i], i) for i in range(n)]
    indexed_items.sort(reverse=True)

    # Container for best solution found
    best = {'bins': None, 'count': n + 1}

    def backtrack(idx, bins):
        """Recursively pack items using branch-and-bound."""
        # If all items packed
        if idx == n:
            if len(bins) < best['count']:
                best['bins'] = [bin_list[:] for bin_list in bins]
                best['count'] = len(bins)
            return

        # Pruning: if current bins >= best, no point continuing
        if len(bins) >= best['count']:
            return

        item_size, orig_idx = indexed_items[idx]

        # Try placing in existing bins first
        for bin_list in bins:
            bin_used = sum(items[i] for i in bin_list)
            if bin_used + item_size <= capacity:
                bin_list.append(orig_idx)
                backtrack(idx + 1, bins)
                bin_list.pop()

        # Try placing in a new bin (only if it might improve solution)
        if len(bins) + 1 < best['count']:
            bins.append([orig_idx])
            backtrack(idx + 1, bins)
            bins.pop()

    backtrack(0, [])

    # Fallback to BFD if exact algorithm fails (shouldn't happen)
    if best['bins'] is None:
        return _pack_bfd(items, capacity)

    return best['bins']


def _pack_bfd(items: list[int], capacity: int) -> list[list[int]]:
    """Best Fit Decreasing greedy algorithm.

    Sort items in decreasing order, then place each item in the bin
    with the least remaining space that fits it.
    """
    n = len(items)

    # Create indexed items and sort by size (decreasing)
    indexed_items = [(items[i], i) for i in range(n)]
    indexed_items.sort(reverse=True)

    bins = []

    for item_size, orig_idx in indexed_items:
        # Find bin with best fit (least remaining space that fits)
        best_bin_idx = -1
        best_remaining = capacity + 1

        for bin_idx, bin_list in enumerate(bins):
            bin_used = sum(items[i] for i in bin_list)
            remaining = capacity - bin_used

            if remaining >= item_size and remaining < best_remaining:
                best_bin_idx = bin_idx
                best_remaining = remaining

        if best_bin_idx == -1:
            # Need a new bin
            bins.append([orig_idx])
        else:
            bins[best_bin_idx].append(orig_idx)

    return bins
