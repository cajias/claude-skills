def pack(items: list[int], capacity: int) -> list[list[int]]:
    """Return a list of bins; each bin is a list of item INDICES (0-based).

    Every index 0..len(items)-1 must appear in exactly one bin.
    The sum of item sizes in each bin must not exceed `capacity`.

    Strategy: Balanced packing with adaptive bin targeting.
    Tries to keep bins balanced while respecting best-fit principles.
    """
    if not items:
        return []

    if len(items) == 1:
        return [[0]]

    # Create indexed items sorted by size
    indexed = [(items[i], i) for i in range(len(items))]

    # Try multiple passes with different orderings to find best packing
    solutions = []

    # Pass 1: Standard BFD
    sol1 = _pack_best_fit_dec(indexed[:], capacity)
    solutions.append(sol1)

    # Pass 2: FFD
    sol2 = _pack_first_fit_dec(indexed[:], capacity)
    solutions.append(sol2)

    # Pass 3: Balanced fit (target bins at mid-capacity)
    sol3 = _pack_balanced(indexed[:], capacity)
    solutions.append(sol3)

    # Choose best
    best = min(solutions, key=len)

    # Apply refinement
    best = _refine(best, items, capacity)

    return best


def _pack_best_fit_dec(indexed, capacity):
    """Best-Fit Decreasing."""
    indexed.sort(reverse=True, key=lambda x: x[0])

    bins = []
    bin_loads = []

    for size, idx in indexed:
        best_bin = -1
        best_remaining = capacity + 1

        for i in range(len(bins)):
            remaining = capacity - bin_loads[i]
            if remaining >= size and remaining < best_remaining:
                best_bin = i
                best_remaining = remaining

        if best_bin >= 0:
            bins[best_bin].append(idx)
            bin_loads[best_bin] += size
        else:
            bins.append([idx])
            bin_loads.append(size)

    return bins


def _pack_first_fit_dec(indexed, capacity):
    """First-Fit Decreasing."""
    indexed.sort(reverse=True, key=lambda x: x[0])

    bins = []
    bin_remaining = []

    for size, idx in indexed:
        placed = False
        for i in range(len(bins)):
            if bin_remaining[i] >= size:
                bins[i].append(idx)
                bin_remaining[i] -= size
                placed = True
                break

        if not placed:
            bins.append([idx])
            bin_remaining.append(capacity - size)

    return bins


def _pack_balanced(indexed, capacity):
    """Balanced packing - tries to keep bins at target utilization."""
    indexed.sort(reverse=True, key=lambda x: x[0])

    target_util = 0.75 * capacity  # Try to get bins to 75% full

    bins = []
    bin_loads = []

    for size, idx in indexed:
        # Find bin closest to target that can fit this item
        best_bin = -1
        best_distance = float('inf')

        for i in range(len(bins)):
            remaining = capacity - bin_loads[i]
            if remaining >= size:
                new_load = bin_loads[i] + size
                distance = abs(new_load - target_util)
                if distance < best_distance:
                    best_bin = i
                    best_distance = distance

        if best_bin >= 0:
            bins[best_bin].append(idx)
            bin_loads[best_bin] += size
        else:
            bins.append([idx])
            bin_loads.append(size)

    return bins


def _refine(bins, items, capacity):
    """Aggressive refinement of packing."""
    if not bins:
        return bins

    bin_loads = [sum(items[idx] for idx in b) for b in bins]

    improved = True
    iteration = 0
    max_iters = len(items) * 2

    while improved and iteration < max_iters:
        improved = False
        iteration += 1

        # Try consolidating sparse bins
        for src in range(len(bins) - 1, 0, -1):
            if improved or not bins[src]:
                continue

            items_to_move = sorted([(items[idx], idx) for idx in bins[src]])
            temp_loads = list(bin_loads)
            moves = []

            for size, idx in items_to_move:
                placed = False
                for dest in range(src):
                    if temp_loads[dest] + size <= capacity:
                        moves.append((idx, dest, size))
                        temp_loads[dest] += size
                        placed = True
                        break

                if not placed:
                    break

            if len(moves) == len(items_to_move):
                for idx, dest, size in moves:
                    bins[src].remove(idx)
                    bins[dest].append(idx)
                    bin_loads[src] -= size
                    bin_loads[dest] += size
                improved = True
                break

        # Try moving items to better bins
        if not improved:
            for src in range(len(bins)):
                if improved or not bins[src]:
                    continue

                items_in_src = sorted([(items[idx], idx) for idx in bins[src]])

                for size, idx in items_in_src:
                    if improved:
                        break

                    for dest in range(src + 1, len(bins)):
                        if bin_loads[dest] + size <= capacity:
                            bins[src].remove(idx)
                            bins[dest].append(idx)
                            bin_loads[src] -= size
                            bin_loads[dest] += size
                            improved = True
                            break

    return [b for b in bins if b]
