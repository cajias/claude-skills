def pack(items: list[int], capacity: int) -> list[list[int]]:
    """Return a list of bins; each bin is a list of item INDICES (0-based).

    Every index 0..len(items)-1 must appear in exactly one bin.
    The sum of item sizes in each bin must not exceed `capacity`.
    """
    # Create list of (size, index) and sort by size descending (First Fit Decreasing)
    indexed_items = [(items[i], i) for i in range(len(items))]
    indexed_items.sort(reverse=True, key=lambda x: x[0])

    # Initialize bins with their remaining capacity
    bins = []  # Each bin is [remaining_capacity, [list of indices]]

    # Place each item in the first bin that has room
    for size, index in indexed_items:
        # Try to fit in existing bins
        placed = False
        for i in range(len(bins)):
            if bins[i][0] >= size:
                bins[i][0] -= size
                bins[i][1].append(index)
                placed = True
                break

        # If not placed, create a new bin
        if not placed:
            bins.append([capacity - size, [index]])

    # Return just the list of indices for each bin
    return [bin[1] for bin in bins]
