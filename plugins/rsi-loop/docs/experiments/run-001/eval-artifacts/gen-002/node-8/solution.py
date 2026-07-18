def pack(items: list[int], capacity: int) -> list[list[int]]:
    """Pack items into bins using Largest-First Bin-Centric Construction (LFBCC).

    Core mechanism: Build bins dynamically, one at a time, using:
    1. Start each bin with the largest unpacked item
    2. Greedily fill by selecting items with minimum waste

    This is fundamentally different from sorted-greedy heuristics:
    - No global sort of all items
    - Bin-centric construction (build bins, not place items)
    - Items selected dynamically during bin filling based on current state
    - Best-fit selection minimizes waste per item placement

    The mechanism is: "iteratively form bins by greedily selecting items",
    NOT "order items once, then place each by fixed rule" (sorted-greedy).

    Args:
        items: List of item sizes
        capacity: Maximum capacity of each bin

    Returns:
        List of bins, where each bin is a list of item indices
    """
    n = len(items)
    if n == 0:
        return []

    bins = []
    unpacked = set(range(n))

    while unpacked:
        # Start bin with largest unpacked item
        start_idx = max(unpacked, key=lambda i: items[i])
        current_bin = [start_idx]
        space_left = capacity - items[start_idx]
        unpacked.remove(start_idx)

        # Greedily fill bin with best-fit items (minimize waste)
        while space_left > 0 and unpacked:
            # Find all items that fit in remaining space
            candidates = [i for i in unpacked if items[i] <= space_left]

            if not candidates:
                # No item fits, close this bin
                break

            # Select item that minimizes waste (best-fit)
            best_item = min(candidates, key=lambda i: space_left - items[i])
            current_bin.append(best_item)
            space_left -= items[best_item]
            unpacked.remove(best_item)

        bins.append(current_bin)

    return bins
