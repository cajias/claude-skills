def pack(items: list[int], capacity: int) -> list[list[int]]:
    """Return a list of bins; each bin is a list of item INDICES (0-based).

    Every index 0..len(items)-1 must appear in exactly one bin.
    The sum of item sizes in each bin must not exceed `capacity`.
    """
    if not items:
        return []

    # Create list of (size, original_index) and sort by size descending
    indexed_items = [(items[i], i) for i in range(len(items))]
    indexed_items.sort(reverse=True, key=lambda x: x[0])

    # First Fit Decreasing: place each item in first bin with room
    bins = []  # Each bin is [item_size_sum, [list of indices]]

    for size, idx in indexed_items:
        # Try to fit in existing bin
        placed = False
        for bin_data in bins:
            if bin_data[0] + size <= capacity:
                bin_data[0] += size
                bin_data[1].append(idx)
                placed = True
                break

        # If no bin has room, create new bin
        if not placed:
            bins.append([size, [idx]])

    # Extract just the index lists
    return [bin_data[1] for bin_data in bins]
