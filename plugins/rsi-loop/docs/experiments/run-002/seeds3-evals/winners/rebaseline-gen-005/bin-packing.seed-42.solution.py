def pack(items: list[int], capacity: int) -> list[list[int]]:
    """Return a list of bins; each bin is a list of item INDICES (0-based).

    Every index 0..len(items)-1 must appear in exactly one bin.
    The sum of item sizes in each bin must not exceed `capacity`.
    """
    # First Fit Decreasing: sort by size descending, then place each item
    # in the first bin that has room.

    # Create list of (size, original_index) and sort by size descending
    indexed_items = [(items[i], i) for i in range(len(items))]
    indexed_items.sort(reverse=True, key=lambda x: x[0])

    bins = []
    bin_loads = []

    for size, idx in indexed_items:
        # Find first bin with enough space
        placed = False
        for bin_idx in range(len(bins)):
            if bin_loads[bin_idx] + size <= capacity:
                bins[bin_idx].append(idx)
                bin_loads[bin_idx] += size
                placed = True
                break

        # If no bin has space, create a new one
        if not placed:
            bins.append([idx])
            bin_loads.append(size)

    return bins
