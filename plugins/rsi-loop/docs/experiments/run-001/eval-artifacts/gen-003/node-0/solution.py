def pack(items: list[int], capacity: int) -> list[list[int]]:
    """Pack items into bins using First Fit Decreasing (FFD).

    Returns a list of bins, where each bin is a list of item indices.
    Every index 0..len(items)-1 appears exactly once.
    """
    if not items:
        return []

    # Create list of (size, original_index) and sort by size descending
    indexed_items = [(items[i], i) for i in range(len(items))]
    indexed_items.sort(reverse=True)

    # Bins will store: [(remaining_capacity, [list of indices])]
    bins = []

    # Place each item using First Fit
    for size, idx in indexed_items:
        # Try to fit in an existing bin
        placed = False
        for i in range(len(bins)):
            if bins[i][0] >= size:  # If bin has enough capacity
                bins[i][0] -= size  # Reduce remaining capacity
                bins[i][1].append(idx)  # Add index to bin
                placed = True
                break

        # If item doesn't fit in any existing bin, create a new one
        if not placed:
            bins.append([capacity - size, [idx]])

    # Return just the lists of indices
    return [bin[1] for bin in bins]
