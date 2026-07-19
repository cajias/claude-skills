def pack(items: list[int], capacity: int) -> list[list[int]]:
    """Return a list of bins; each bin is a list of item INDICES (0-based).

    Every index 0..len(items)-1 must appear in exactly one bin.
    The sum of item sizes in each bin must not exceed `capacity`.
    """
    # Create list of (size, original_index) pairs and sort by size (decreasing)
    indexed_items = [(items[i], i) for i in range(len(items))]
    indexed_items.sort(reverse=True, key=lambda x: x[0])

    # Initialize bins: each bin tracks (current_total_size, [list of indices])
    bins = []

    # Place each item in the first bin that fits (First-Fit Decreasing)
    for size, original_idx in indexed_items:
        placed = False
        for i in range(len(bins)):
            if bins[i][0] + size <= capacity:
                bins[i][0] += size
                bins[i][1].append(original_idx)
                placed = True
                break

        # If item doesn't fit in any existing bin, create a new one
        if not placed:
            bins.append([size, [original_idx]])

    # Return just the bin contents (drop the size tracking)
    return [bin_contents[1] for bin_contents in bins]
