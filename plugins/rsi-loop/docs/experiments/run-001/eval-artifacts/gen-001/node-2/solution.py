def pack(items: list[int], capacity: int) -> list[list[int]]:
    """Pack items into bins using incremental best-choice heuristic (Best Fit Decreasing).

    At each step, choose the locally optimal placement: the bin with the smallest
    remaining capacity that can still fit the current item.
    """
    # Create list of (item_size, original_index)
    indexed_items = [(items[i], i) for i in range(len(items))]

    # Sort by size in descending order (decreasing heuristic improves packing)
    indexed_items.sort(key=lambda x: x[0], reverse=True)

    # List of bins and their remaining capacities
    bins = []  # Each element is a list of item indices
    bin_loads = []  # Track remaining capacity in each bin

    # Place each item using best-fit strategy
    for size, idx in indexed_items:
        # Find the bin with the smallest remaining capacity that fits this item
        best_bin = -1
        best_remaining = capacity + 1

        for bin_idx, remaining in enumerate(bin_loads):
            if remaining >= size:  # Item fits in this bin
                if remaining < best_remaining:  # Best fit: tightest fit
                    best_bin = bin_idx
                    best_remaining = remaining

        if best_bin == -1:
            # No existing bin has space; create a new one
            bins.append([idx])
            bin_loads.append(capacity - size)
        else:
            # Place item in the best-fit bin
            bins[best_bin].append(idx)
            bin_loads[best_bin] -= size

    return bins
