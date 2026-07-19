def pack(items: list[int], capacity: int) -> list[list[int]]:
    """Return a list of bins; each bin is a list of item INDICES (0-based).

    Every index 0..len(items)-1 must appear in exactly one bin.
    The sum of item sizes in each bin must not exceed `capacity`.

    Strategy: Adaptive partitioning with specialized handling.
    Classifies items into large/medium/small and packs them strategically:
    1. Large items first (more constrained)
    2. Medium items with best fit
    3. Small items to fill gaps
    4. Consolidation pass
    """
    if not items:
        return []

    if len(items) == 1:
        return [[0]]

    # Partition items by size
    large_threshold = capacity // 2
    medium_threshold = capacity // 4

    large_items = []    # > capacity/2
    medium_items = []   # capacity/4 to capacity/2
    small_items = []    # <= capacity/4

    for i, size in enumerate(items):
        if size > large_threshold:
            large_items.append((size, i))
        elif size > medium_threshold:
            medium_items.append((size, i))
        else:
            small_items.append((size, i))

    # Sort each category by size (descending)
    large_items.sort(reverse=True)
    medium_items.sort(reverse=True)
    small_items.sort(reverse=True)

    bins = []
    bin_loads = []

    # Phase 1: Pack large items (each might go in its own bin)
    for size, idx in large_items:
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

    # Phase 2: Pack medium items using best fit
    for size, idx in medium_items:
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

    # Phase 3: Pack small items using first fit (fast and efficient)
    for size, idx in small_items:
        placed = False
        for i in range(len(bins)):
            if bin_loads[i] + size <= capacity:
                bins[i].append(idx)
                bin_loads[i] += size
                placed = True
                break

        if not placed:
            bins.append([idx])
            bin_loads.append(size)

    # Phase 4: Consolidation - aggressive movement of items
    improved = True
    iterations = 0
    max_iterations = len(items)

    while improved and iterations < max_iterations:
        improved = False
        iterations += 1

        # Try to move items from later bins to earlier bins
        for src in range(len(bins) - 1, 0, -1):
            if not bins[src]:
                continue

            # Move smallest items first (easier to place)
            items_in_bin = sorted([(items[idx], idx) for idx in bins[src]])

            for size, idx in items_in_bin:
                # Try earlier bins with best fit
                best_dest = -1
                best_remaining = capacity + 1

                for dest in range(src):
                    remaining = capacity - bin_loads[dest]
                    if remaining >= size and remaining < best_remaining:
                        best_dest = dest
                        best_remaining = remaining

                if best_dest >= 0:
                    bins[src].remove(idx)
                    bins[best_dest].append(idx)
                    bin_loads[src] -= size
                    bin_loads[best_dest] += size
                    improved = True
                    break

            if improved:
                break

    # Remove empty bins
    result = [b for b in bins if b]
    return result
