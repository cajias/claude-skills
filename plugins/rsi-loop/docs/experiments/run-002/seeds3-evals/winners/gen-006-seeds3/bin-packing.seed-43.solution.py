def pack(items: list[int], capacity: int) -> list[list[int]]:
    """Return a list of bins; each bin is a list of item INDICES (0-based).

    Every index 0..len(items)-1 must appear in exactly one bin.
    The sum of item sizes in each bin must not exceed `capacity`.
    """
    if not items:
        return []

    # Create list of (size, original_index) and sort by size descending
    indexed_items = [(items[i], i) for i in range(len(items))]
    indexed_items.sort(reverse=True)

    bins = []
    bin_loads = []

    # First Fit Decreasing: for each item, place in first bin with room
    for size, idx in indexed_items:
        placed = False
        for bin_idx, load in enumerate(bin_loads):
            if load + size <= capacity:
                bins[bin_idx].append(idx)
                bin_loads[bin_idx] += size
                placed = True
                break

        if not placed:
            # Create new bin
            bins.append([idx])
            bin_loads.append(size)

    return bins
