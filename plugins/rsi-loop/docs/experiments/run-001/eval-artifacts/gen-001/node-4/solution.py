def pack(items: list[int], capacity: int) -> list[list[int]]:
    """Return a list of bins; each bin is a list of item INDICES (0-based).

    Uses a hybrid approach: runs two different heuristics (FFD and BFD)
    and returns the packing with fewer bins.
    """
    if not items:
        return []

    # Create list of (size, original_index) tuples for sorting
    indexed_items = [(size, idx) for idx, size in enumerate(items)]

    # Heuristic 1: First Fit Decreasing (FFD)
    ffd_result = _first_fit_decreasing(indexed_items, capacity)

    # Heuristic 2: Best Fit Decreasing (BFD)
    bfd_result = _best_fit_decreasing(indexed_items, capacity)

    # Return the packing with fewer bins
    if len(ffd_result) <= len(bfd_result):
        return ffd_result
    else:
        return bfd_result


def _first_fit_decreasing(indexed_items: list[tuple[int, int]], capacity: int) -> list[list[int]]:
    """First Fit Decreasing heuristic.

    Sort items by size descending, then place each item in the first bin
    that has enough remaining space.
    """
    # Sort by size descending (then by index for determinism)
    sorted_items = sorted(indexed_items, key=lambda x: (-x[0], x[1]))

    bins = []
    bin_remaining = []

    for size, idx in sorted_items:
        # Try to fit in first bin with enough space
        placed = False
        for i, remaining in enumerate(bin_remaining):
            if remaining >= size:
                bins[i].append(idx)
                bin_remaining[i] -= size
                placed = True
                break

        # If not placed, create a new bin
        if not placed:
            bins.append([idx])
            bin_remaining.append(capacity - size)

    return bins


def _best_fit_decreasing(indexed_items: list[tuple[int, int]], capacity: int) -> list[list[int]]:
    """Best Fit Decreasing heuristic.

    Sort items by size descending, then place each item in the bin with
    the least remaining capacity that still fits the item.
    """
    # Sort by size descending (then by index for determinism)
    sorted_items = sorted(indexed_items, key=lambda x: (-x[0], x[1]))

    bins = []
    bin_remaining = []

    for size, idx in sorted_items:
        # Find bin with least remaining space that fits this item
        best_bin = -1
        best_remaining = capacity + 1

        for i, remaining in enumerate(bin_remaining):
            if remaining >= size and remaining < best_remaining:
                best_bin = i
                best_remaining = remaining

        if best_bin >= 0:
            bins[best_bin].append(idx)
            bin_remaining[best_bin] -= size
        else:
            # Create a new bin
            bins.append([idx])
            bin_remaining.append(capacity - size)

    return bins
