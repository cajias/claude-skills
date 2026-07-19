def pack(items: list[int], capacity: int) -> list[list[int]]:
    """
    Pack items using deterministic local search with aggressive refinement.

    Strategy:
    1. Use Best Fit Decreasing for initial solution
    2. Apply aggressive local search with item redistribution
    """

    if not items:
        return []

    indexed_items = [(items[i], i) for i in range(len(items))]
    indexed_items.sort(reverse=True)

    # Initial packing using Best Fit Decreasing
    bins = []
    bin_loads = []

    for size, idx in indexed_items:
        best_bin = -1
        best_remaining = capacity + 1

        for bin_idx in range(len(bins)):
            remaining = capacity - bin_loads[bin_idx]
            if remaining >= size and remaining < best_remaining:
                best_bin = bin_idx
                best_remaining = remaining

        if best_bin != -1:
            bins[best_bin].append(idx)
            bin_loads[best_bin] += size
        else:
            bins.append([idx])
            bin_loads.append(size)

    # Aggressive local search: repeatedly try to improve by moving and redistributing items
    improved = True
    iterations = 0
    max_iterations = len(items) * 3

    while improved and iterations < max_iterations:
        improved = False
        iterations += 1

        # Strategy 1: Move single items to better bins
        for i in range(len(bins)):
            if not bins[i]:
                continue

            items_in_bin = list(bins[i])
            items_in_bin.sort(key=lambda idx: items[idx])

            for item_idx in items_in_bin:
                item_size = items[item_idx]

                # Try to move to any earlier bin
                for j in range(i):
                    if bin_loads[j] + item_size <= capacity:
                        bins[i].remove(item_idx)
                        bins[j].append(item_idx)
                        bin_loads[i] -= item_size
                        bin_loads[j] += item_size
                        improved = True
                        break

                if improved:
                    break

            if improved:
                break

        # Strategy 2: Aggressive consolidation - remove items from last bins and repack
        if not improved:
            # Find the bin with the most items or lowest load
            for i in range(len(bins) - 1, max(0, len(bins) - 3), -1):
                if not bins[i]:
                    continue

                # Extract all items from this bin
                items_to_repack = [(items[idx], idx) for idx in bins[i]]
                items_to_repack.sort(reverse=True)
                bin_total = bin_loads[i]
                bin_loads[i] = 0
                bins[i] = []

                # Try to repack these items into earlier bins
                all_moved = True
                for size, idx in items_to_repack:
                    placed = False
                    # Try earlier bins first (Best Fit)
                    best_bin = -1
                    best_remaining = capacity + 1
                    for j in range(i):
                        remaining = capacity - bin_loads[j]
                        if remaining >= size and remaining < best_remaining:
                            best_bin = j
                            best_remaining = remaining

                    if best_bin != -1:
                        bins[best_bin].append(idx)
                        bin_loads[best_bin] += size
                    else:
                        # If can't fit in earlier bins, put back
                        bins[i].append(idx)
                        bin_loads[i] += size
                        all_moved = False

                if all_moved and not bins[i]:
                    improved = True
                    break

        # Strategy 3: Try to merge pairs of bins
        if not improved:
            for i in range(len(bins) - 1, 0, -1):
                if not bins[i] or sum(bin_loads[max(0, i-2):i]) == 0:
                    continue

                # Try to move all items from bin i and i-1 to earlier bins
                items_to_move = []
                if i > 0 and bins[i-1]:
                    items_to_move.extend([(items[idx], idx, i-1) for idx in bins[i-1]])
                items_to_move.extend([(items[idx], idx, i) for idx in bins[i]])
                items_to_move.sort(reverse=True)

                temp_loads = list(bin_loads)
                temp_bins = [list(b) for b in bins]
                moves = []

                for size, idx, source_bin in items_to_move:
                    placed = False
                    for j in range(source_bin):
                        if temp_loads[j] + size <= capacity:
                            moves.append((idx, source_bin, j, size))
                            temp_loads[j] += size
                            placed = True
                            break

                    if not placed:
                        moves = []
                        break

                if moves and len(moves) > 0:
                    for idx, source_bin, target_bin, size in moves:
                        if idx in bins[source_bin]:
                            bins[source_bin].remove(idx)
                            bins[target_bin].append(idx)
                            bin_loads[source_bin] -= size
                            bin_loads[target_bin] += size
                    improved = True
                    break

    result = [b for b in bins if b]
    return result
