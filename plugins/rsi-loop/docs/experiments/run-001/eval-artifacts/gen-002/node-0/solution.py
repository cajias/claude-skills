def pack(items: list[int], capacity: int) -> list[list[int]]:
    """Pack items into bins using First Fit Decreasing (FFD) algorithm.

    Sorts items in decreasing order of size, then places each item into
    the first bin with sufficient remaining capacity. If no bin has room,
    a new bin is created.

    Args:
        items: List of item sizes
        capacity: Maximum capacity of each bin

    Returns:
        List of bins, where each bin is a list of item indices
    """
    # Create list of (size, index) pairs
    indexed_items = [(items[i], i) for i in range(len(items))]

    # Sort by size in decreasing order
    indexed_items.sort(reverse=True, key=lambda x: x[0])

    # List of bins, each bin contains item indices
    bins = []
    # Track remaining capacity in each bin
    bin_capacity = []

    # Place each item in decreasing order of size
    for size, index in indexed_items:
        # Try to fit in existing bin
        placed = False
        for i in range(len(bins)):
            if bin_capacity[i] >= size:
                bins[i].append(index)
                bin_capacity[i] -= size
                placed = True
                break

        # If not placed in any existing bin, create new bin
        if not placed:
            bins.append([index])
            bin_capacity.append(capacity - size)

    return bins
