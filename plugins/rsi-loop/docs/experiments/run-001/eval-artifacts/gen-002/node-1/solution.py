def pack(items: list[int], capacity: int) -> list[list[int]]:
    """
    Pack items into bins using First Fit Decreasing (FFD) algorithm.

    This is a sorted-greedy approach:
    1. Sort items in decreasing order (while tracking original indices)
    2. For each item, place it in the first bin with enough remaining space
    3. If no bin has room, create a new bin
    """
    if not items:
        return []

    # Create list of (size, original_index) pairs
    indexed_items = [(items[i], i) for i in range(len(items))]

    # Sort in decreasing order by size
    indexed_items.sort(reverse=True, key=lambda x: x[0])

    # Bins: each bin is a tuple of (current_load, list_of_indices)
    bins = []

    # Place each item
    for size, original_index in indexed_items:
        # Try to fit in existing bins (First Fit)
        placed = False
        for i in range(len(bins)):
            current_load, bin_items = bins[i]
            if current_load + size <= capacity:
                # Item fits in this bin
                bins[i] = (current_load + size, bin_items + [original_index])
                placed = True
                break

        # If not placed in any existing bin, create a new one
        if not placed:
            bins.append((size, [original_index]))

    # Extract just the item indices from each bin
    return [bin_items for _, bin_items in bins]
