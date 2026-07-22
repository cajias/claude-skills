def pack(items: list[int], capacity: int) -> list[list[int]]:
    """Return a list of bins; each bin is a list of item INDICES (0-based).

    Every index 0..len(items)-1 must appear in exactly one bin.
    The sum of item sizes in each bin must not exceed `capacity`.
    """
    if not items:
        return []

    # Create list of (size, original_index) tuples
    indexed_items = [(items[i], i) for i in range(len(items))]

    # Sort by size in decreasing order (First Fit Decreasing heuristic)
    indexed_items.sort(key=lambda x: x[0], reverse=True)

    # List of bins, each bin tracks [current_used_space, [list of indices]]
    bins = []

    # Place each item using First Fit
    for size, idx in indexed_items:
        # Try to fit in existing bin
        placed = False
        for bin_info in bins:
            if bin_info[0] + size <= capacity:
                bin_info[0] += size
                bin_info[1].append(idx)
                placed = True
                break

        # If not placed, create new bin
        if not placed:
            bins.append([size, [idx]])

    # Return just the lists of indices
    return [bin_info[1] for bin_info in bins]
