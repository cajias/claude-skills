def pack(items: list[int], capacity: int) -> list[list[int]]:
    """Return a list of bins; each bin is a list of item INDICES (0-based).

    Every index 0..len(items)-1 must appear in exactly one bin.
    The sum of item sizes in each bin must not exceed `capacity`.
    """
    # First Fit Decreasing: sort by size (descending), then pack greedily

    # Create list of (size, original_index) tuples and sort by size descending
    indexed_items = [(items[i], i) for i in range(len(items))]
    indexed_items.sort(reverse=True, key=lambda x: x[0])

    # Track remaining capacity in each bin
    bins: list[list[int]] = []
    bin_capacity: list[int] = []

    # Pack each item
    for size, original_index in indexed_items:
        # Try to fit in existing bins
        placed = False
        for bin_idx in range(len(bins)):
            if bin_capacity[bin_idx] >= size:
                bins[bin_idx].append(original_index)
                bin_capacity[bin_idx] -= size
                placed = True
                break

        # If not placed, open a new bin
        if not placed:
            bins.append([original_index])
            bin_capacity.append(capacity - size)

    return bins
