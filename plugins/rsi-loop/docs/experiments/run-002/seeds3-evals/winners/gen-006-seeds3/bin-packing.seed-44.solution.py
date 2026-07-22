def pack(items: list[int], capacity: int) -> list[list[int]]:
    """Pack items into as few bins as possible using First Fit Decreasing.

    Args:
        items: list of item sizes
        capacity: capacity of each bin

    Returns:
        list of bins, where each bin is a list of item indices
    """
    # Create list of (size, original_index) and sort by size descending
    indexed_items = [(items[i], i) for i in range(len(items))]
    indexed_items.sort(reverse=True)

    # Bins: list of (current_weight, [indices])
    bins = []

    # First Fit Decreasing: for each item, place in first bin with space
    for size, idx in indexed_items:
        placed = False
        for i, (current_weight, bin_items) in enumerate(bins):
            if current_weight + size <= capacity:
                bins[i] = (current_weight + size, bin_items + [idx])
                placed = True
                break

        if not placed:
            # Create new bin
            bins.append((size, [idx]))

    # Return just the indices, not the weights
    return [bin_items for _, bin_items in bins]
