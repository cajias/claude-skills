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

    # bins[i] = (current_total_size, [list of indices])
    bins = []

    # First Fit Decreasing: for each item, place it in first bin with room
    for size, idx in indexed_items:
        placed = False
        for i in range(len(bins)):
            if bins[i][0] + size <= capacity:
                bins[i][0] += size
                bins[i][1].append(idx)
                placed = True
                break

        # If no bin has room, create new bin
        if not placed:
            bins.append([size, [idx]])

    # Return just the index lists
    return [bin_indices for _, bin_indices in bins]
