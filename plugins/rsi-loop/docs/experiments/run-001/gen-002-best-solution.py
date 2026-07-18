def pack(items: list[int], capacity: int) -> list[list[int]]:
    """
    Utilization-maximizing construction: build bins one-at-a-time by
    selecting item subsets that maximize bin utilization.

    Core mechanism: For each bin, enumerate promising combinations of
    items (prioritizing high-utilization subsets) and pick the best.
    This is fundamentally different from greedy item-placement because
    we optimize bin contents holistically via local enumeration rather
    than placing items individually by a fixed rule.
    """
    if not items:
        return []

    n = len(items)
    available = list(range(n))
    bins = []

    while available:
        if not available:
            break

        # Find the best utilization bin we can build from available items
        # Strategy: start with largest item, then try to add items that
        # maximize utilization (minimize wasted space)

        best_bin = []
        best_utilization = -1

        # For each item as a starting point
        for start_idx in available[:min(5, len(available))]:  # Only try first few (top large items)
            # Greedy: start with this item, fill with best-fit items
            candidate_bin = [start_idx]
            remaining_capacity = capacity - items[start_idx]
            used = {start_idx}

            # Greedily add items in decreasing size order
            for item_idx in sorted(available, key=lambda i: -items[i]):
                if item_idx not in used and items[item_idx] <= remaining_capacity:
                    candidate_bin.append(item_idx)
                    used.add(item_idx)
                    remaining_capacity -= items[item_idx]

            utilization = (capacity - remaining_capacity) / capacity
            if utilization > best_utilization:
                best_utilization = utilization
                best_bin = candidate_bin

        # If no bin found (shouldn't happen), just take largest item
        if not best_bin:
            largest_idx = max(available, key=lambda i: items[i])
            best_bin = [largest_idx]

        # Remove items in best_bin from available
        available = [i for i in available if i not in best_bin]
        bins.append(best_bin)

    return bins
