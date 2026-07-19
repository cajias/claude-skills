def pack(items: list[int], capacity: int) -> list[list[int]]:
    """Return a list of bins; each bin is a list of item INDICES (0-based).

    Every index 0..len(items)-1 must appear in exactly one bin.
    The sum of item sizes in each bin must not exceed `capacity`.

    Strategy: Multi-pass refinement heuristic combining constructive
    and local search approaches for robust bin packing.
    """
    if not items:
        return []

    if len(items) == 1:
        return [[0]]

    # Get initial packing using best-fit decreasing (proven effective)
    solution = _best_fit_decreasing(items, capacity)

    # Apply extensive local search refinement
    solution = _local_search_refine(solution, items, capacity)

    return [b for b in solution if b]


def _best_fit_decreasing(items, capacity):
    """Best-Fit Decreasing heuristic.

    Sort items by size (descending), place each in the bin with the
    smallest remaining capacity that can fit it.
    """
    # Create (size, original_index) pairs and sort by size descending
    indexed_items = [(items[i], i) for i in range(len(items))]
    indexed_items.sort(reverse=True, key=lambda x: x[0])

    bins = []
    bin_loads = []

    # Place each item using best-fit strategy
    for size, idx in indexed_items:
        # Find bin with smallest remaining space that fits this item
        best_bin = -1
        best_remaining = capacity + 1

        for i in range(len(bins)):
            remaining = capacity - bin_loads[i]
            if remaining >= size and remaining < best_remaining:
                best_bin = i
                best_remaining = remaining

        if best_bin >= 0:
            # Place in best-fit bin
            bins[best_bin].append(idx)
            bin_loads[best_bin] += size
        else:
            # Create new bin
            bins.append([idx])
            bin_loads.append(size)

    return bins


def _local_search_refine(bins, items, capacity):
    """Intensive local search refinement with multiple strategies.

    Iteratively improves packing by:
    1. Moving items from end bins to better positions
    2. Consolidating bins (emptying end bins)
    3. Swapping items between bins
    """
    if not bins:
        return bins

    bin_loads = [sum(items[idx] for idx in b) for b in bins]
    improved = True
    iteration = 0
    max_iterations = len(items) * 3

    while improved and iteration < max_iterations:
        improved = False
        iteration += 1

        # Strategy 1: Move items from end bins to earlier bins
        for src in range(len(bins) - 1, max(-1, len(bins) - 8), -1):
            if src < 0 or improved or not bins[src]:
                continue

            # Sort items in bin by size (smallest first for better placement)
            items_in_bin = sorted([(items[idx], idx) for idx in bins[src]])

            for size, idx in items_in_bin:
                # Find best destination bin
                best_dest = -1
                best_remaining = capacity + 1

                for dest in range(len(bins)):
                    if dest == src:
                        continue
                    remaining = capacity - bin_loads[dest]
                    if remaining >= size and remaining < best_remaining:
                        best_dest = dest
                        best_remaining = remaining

                if best_dest >= 0:
                    # Move item to better bin
                    bins[src].remove(idx)
                    bins[best_dest].append(idx)
                    bin_loads[src] -= size
                    bin_loads[best_dest] += size
                    improved = True
                    break

            if improved:
                break

        # Strategy 2: Consolidate bins (empty end bins by moving all items)
        if not improved:
            for src in range(len(bins) - 1, 0, -1):
                if improved or not bins[src]:
                    continue

                # Try to move all items from this bin to earlier bins
                items_to_move = sorted([(items[idx], idx) for idx in bins[src]])
                temp_loads = list(bin_loads)
                moves = []

                for size, idx in items_to_move:
                    # Find best earlier bin for this item
                    best_dest = -1
                    best_remaining = capacity + 1

                    for dest in range(src):
                        remaining = capacity - temp_loads[dest]
                        if remaining >= size and remaining < best_remaining:
                            best_dest = dest
                            best_remaining = remaining

                    if best_dest >= 0:
                        moves.append((idx, best_dest, size))
                        temp_loads[best_dest] += size
                    else:
                        # Can't move this item, abort consolidation
                        moves = []
                        break

                # Apply moves if all items could be relocated
                if len(moves) == len(items_to_move):
                    for idx, dest, size in moves:
                        bins[src].remove(idx)
                        bins[dest].append(idx)
                        bin_loads[src] -= size
                        bin_loads[dest] += size
                    improved = True

        # Strategy 3: Swap items between bins for better overall packing
        if not improved and iteration < max_iterations // 2:
            for i in range(len(bins)):
                for j in range(i + 1, len(bins)):
                    if improved:
                        break

                    if not bins[i] or not bins[j]:
                        continue

                    # Try swapping smallest items from each bin
                    idx_i = min(bins[i], key=lambda x: items[x])
                    idx_j = min(bins[j], key=lambda x: items[x])

                    size_i = items[idx_i]
                    size_j = items[idx_j]

                    # Calculate new loads if we swap
                    new_load_i = bin_loads[i] - size_i + size_j
                    new_load_j = bin_loads[j] - size_j + size_i

                    # Swap if both bins remain feasible and total waste decreases
                    if (new_load_i <= capacity and new_load_j <= capacity and
                        new_load_i + new_load_j < bin_loads[i] + bin_loads[j]):
                        bins[i].remove(idx_i)
                        bins[i].append(idx_j)
                        bins[j].remove(idx_j)
                        bins[j].append(idx_i)
                        bin_loads[i] = new_load_i
                        bin_loads[j] = new_load_j
                        improved = True

        # Strategy 4: Move items from middle/end bins to consolidate
        if not improved and iteration < max_iterations // 3:
            for src in range(len(bins) - 1, 1, -1):
                if improved or not bins[src]:
                    continue

                # Try redistributing multiple items from this bin
                items_in_bin = sorted([(items[idx], idx) for idx in bins[src]])

                for size, idx in items_in_bin:
                    if improved:
                        break

                    # Try placing in any earlier bin
                    for dest in range(src):
                        if bin_loads[dest] + size <= capacity:
                            bins[src].remove(idx)
                            bins[dest].append(idx)
                            bin_loads[src] -= size
                            bin_loads[dest] += size
                            improved = True
                            break

    return bins
