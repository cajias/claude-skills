def pack(items: list[int], capacity: int) -> list[list[int]]:
    """Return a list of bins; each bin is a list of item INDICES (0-based).

    Every index 0..len(items)-1 must appear in exactly one bin.
    The sum of item sizes in each bin must not exceed `capacity`.
    """
    if not items:
        return []

    # Create list of (size, original_index) and sort by size descending
    indexed_items = [(size, idx) for idx, size in enumerate(items)]
    indexed_items.sort(reverse=True, key=lambda x: x[0])

    # Initialize bins with their current usage
    bins = []
    bin_usage = []

    # First Fit Decreasing: for each item, place in first bin with space
    for size, idx in indexed_items:
        placed = False
        for bin_idx, usage in enumerate(bin_usage):
            if usage + size <= capacity:
                bins[bin_idx].append(idx)
                bin_usage[bin_idx] += size
                placed = True
                break

        if not placed:
            # Create new bin
            bins.append([idx])
            bin_usage.append(size)

    return bins
