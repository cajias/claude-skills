def pack(items: list[int], capacity: int) -> list[list[int]]:
    """Return a list of bins; each bin is a list of item INDICES (0-based).

    Uses First Fit Decreasing (sorted-greedy) heuristic:
    1. Sort items in descending order by size (largest first)
    2. For each item, place it in the first bin with enough remaining space
    3. If no bin has space, create a new bin
    """
    # Create list of (size, original_index) pairs
    indexed_items = [(items[i], i) for i in range(len(items))]

    # Sort by size in descending order (largest first)
    indexed_items.sort(key=lambda x: x[0], reverse=True)

    # Initialize bins and their remaining capacities
    bins = []  # list of lists of indices
    bin_remaining = []  # remaining capacity in each bin

    # Place each item using first-fit strategy
    for size, index in indexed_items:
        # Try to fit in first bin with enough space
        placed = False
        for i in range(len(bins)):
            if bin_remaining[i] >= size:
                bins[i].append(index)
                bin_remaining[i] -= size
                placed = True
                break

        # If no bin had space, create a new bin
        if not placed:
            bins.append([index])
            bin_remaining.append(capacity - size)

    return bins
