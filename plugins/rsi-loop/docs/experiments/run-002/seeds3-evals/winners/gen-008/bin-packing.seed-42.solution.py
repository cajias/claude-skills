def pack(items: list[int], capacity: int) -> list[list[int]]:
    """Pack items into as few bins as possible using First Fit Decreasing.

    Args:
        items: List of item sizes
        capacity: Maximum capacity per bin

    Returns:
        List of bins, where each bin is a list of item indices
    """
    # Create list of (size, original_index) and sort by size descending
    indexed_items = [(items[i], i) for i in range(len(items))]
    indexed_items.sort(reverse=True, key=lambda x: x[0])

    # List to track current remaining capacity in each bin
    bins = []
    # List to track which indices are in each bin
    bin_contents = []

    # Place each item (in decreasing size order) into first bin with room
    for size, idx in indexed_items:
        # Find first bin with enough space
        placed = False
        for i, remaining in enumerate(bins):
            if remaining >= size:
                bins[i] -= size
                bin_contents[i].append(idx)
                placed = True
                break

        # If no bin has room, create a new bin
        if not placed:
            bins.append(capacity - size)
            bin_contents.append([idx])

    return bin_contents
