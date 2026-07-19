def pack(items: list[int], capacity: int) -> list[list[int]]:
    """Pack items into as few bins as possible using local search with improvement moves.

    Strategy:
    1. Start with First Fit Decreasing (FFD) initial solution
    2. Apply local improvement moves (relocate, merge) until fixpoint:
       - Relocate: move items between bins if beneficial
       - Merge: combine bins when possible
    3. Return the improved packing
    """
    n = len(items)
    if n == 0:
        return []

    # Create list of (item_size, original_index) and sort by size descending
    indexed_items = [(items[i], i) for i in range(n)]
    indexed_items.sort(reverse=True, key=lambda x: x[0])

    # Phase 1: Initial FFD packing
    bins = []
    bin_loads = []

    for size, idx in indexed_items:
        # Find first bin with enough space
        placed = False
        for b in range(len(bins)):
            if bin_loads[b] + size <= capacity:
                bins[b].append(idx)
                bin_loads[b] += size
                placed = True
                break

        # If no bin has space, create new bin
        if not placed:
            bins.append([idx])
            bin_loads.append(size)

    # Phase 2: Local search improvements
    improved = True
    max_iterations = 1000
    iteration = 0

    while improved and iteration < max_iterations:
        improved = False
        iteration += 1

        # Try merge moves: for each pair of bins, try merging
        for b1 in range(len(bins) - 1):
            if improved:
                break
            for b2 in range(b1 + 1, len(bins)):
                if improved:
                    break
                # Check if smaller bin fits into larger bin
                if bin_loads[b1] + bin_loads[b2] <= capacity:
                    # Merge b1 into b2
                    bins[b2].extend(bins[b1])
                    bin_loads[b2] += bin_loads[b1]
                    bins.pop(b1)
                    bin_loads.pop(b1)
                    improved = True
                    break

        if improved:
            continue

        # Try relocate moves: move each item to a better bin
        for b in range(len(bins)):
            if improved:
                break
            # Try to move items from this bin to other bins
            items_in_bin = list(bins[b])
            for item_idx in items_in_bin:
                if improved:
                    break
                item_size = items[item_idx]
                current_bin_load = bin_loads[b]

                # Try moving to each other bin
                for target_b in range(len(bins)):
                    if target_b == b:
                        continue

                    # Can we fit this item in target bin?
                    if bin_loads[target_b] + item_size <= capacity:
                        # Move it
                        bins[b].remove(item_idx)
                        bin_loads[b] -= item_size
                        bins[target_b].append(item_idx)
                        bin_loads[target_b] += item_size

                        # Check if moving this item allows us to merge b with another bin
                        # or improve the overall packing. For now, accept it and continue.
                        improved = True
                        break

        # Try another merge pass after relocations
        if not improved:
            for b1 in range(len(bins) - 1):
                if improved:
                    break
                for b2 in range(b1 + 1, len(bins)):
                    if improved:
                        break
                    if bin_loads[b1] + bin_loads[b2] <= capacity:
                        bins[b2].extend(bins[b1])
                        bin_loads[b2] += bin_loads[b1]
                        bins.pop(b1)
                        bin_loads.pop(b1)
                        improved = True
                        break

    return bins
