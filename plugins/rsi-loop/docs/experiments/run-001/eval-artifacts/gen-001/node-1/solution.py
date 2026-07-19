def pack(items: list[int], capacity: int) -> list[list[int]]:
    """Pack items into bins using First Fit Decreasing heuristic.

    Sort items in decreasing order, then use first-fit to place each item
    into the first bin with sufficient remaining capacity.
    """
    # Create a list of (size, original_index) tuples
    indexed_items = [(items[i], i) for i in range(len(items))]

    # Sort by size in decreasing order
    indexed_items.sort(key=lambda x: x[0], reverse=True)

    # Initialize bins with remaining capacity tracking
    bins = []
    bin_remaining = []

    # Place each item using first fit
    for size, original_index in indexed_items:
        # Try to fit in an existing bin
        placed = False
        for bin_idx in range(len(bins)):
            if bin_remaining[bin_idx] >= size:
                bins[bin_idx].append(original_index)
                bin_remaining[bin_idx] -= size
                placed = True
                break

        # If not placed, create a new bin
        if not placed:
            bins.append([original_index])
            bin_remaining.append(capacity - size)

    return bins
