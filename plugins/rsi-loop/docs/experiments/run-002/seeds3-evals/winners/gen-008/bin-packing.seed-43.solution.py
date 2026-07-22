def pack(items: list[int], capacity: int) -> list[list[int]]:
    """Return a list of bins; each bin is a list of item INDICES (0-based).

    Every index 0..len(items)-1 must appear in exactly one bin.
    The sum of item sizes in each bin must not exceed `capacity`.
    """
    # Create list of (size, original_index) pairs and sort by size descending
    indexed_items = [(items[i], i) for i in range(len(items))]
    indexed_items.sort(reverse=True, key=lambda x: x[0])

    # List of bins, each bin stores list of indices
    bins = []
    # Track remaining capacity for each bin
    bin_capacities = []

    # First Fit Decreasing: for each item (largest first),
    # place it in the first bin with enough space
    for size, idx in indexed_items:
        placed = False
        for bin_idx in range(len(bins)):
            if bin_capacities[bin_idx] >= size:
                bins[bin_idx].append(idx)
                bin_capacities[bin_idx] -= size
                placed = True
                break

        # If item didn't fit in any existing bin, create new bin
        if not placed:
            bins.append([idx])
            bin_capacities.append(capacity - size)

    return bins
