def pack(items: list[int], capacity: int) -> list[list[int]]:
    """
    Constraint-driven greedy packing: items placed in order of flexibility.

    Mechanism: Iteratively pack unpacked items, always selecting the item with
    the fewest placement options (most constrained) and packing it into the
    first available bin. This differs fundamentally from sorted-greedy because
    item order is not determined upfront—it's computed dynamically during
    packing based on constraint analysis of each item's compatibility with
    current bins.

    The algorithm works as follows:
    1. While unpacked items remain:
       a. For each unpacked item, count how many existing bins it can fit into
       b. Select the item with the fewest options (most constrained)
       c. Use ties to prefer larger items (likely to leave more space)
       d. Place selected item in first available bin (or create new bin)
       e. Mark item as packed

    Family: constraint-driven-placement
    """
    n = len(items)
    if n == 0:
        return []

    packed = [False] * n
    bins = []
    bin_fills = []

    while not all(packed):
        # Analyze flexibility: for each unpacked item, count how many existing
        # bins can accommodate it
        item_flexibility = []

        for i in range(n):
            if not packed[i]:
                # Count bins this item fits into
                fit_count = sum(1 for j in range(len(bins))
                                if bin_fills[j] + items[i] <= capacity)

                # If no existing bin has space, item can only go in a new bin
                if fit_count == 0:
                    fit_count = 1  # Can always open a new bin

                # Store: (index, fit_count, size)
                # Sort by flexibility (ascending), then size (descending) for tiebreak
                item_flexibility.append((i, fit_count, items[i]))

        # Sort items by:
        # 1. Ascending fit_count (least flexible first—constrained items first)
        # 2. Descending size (larger items first as tiebreak)
        item_flexibility.sort(key=lambda x: (x[1], -x[2]))

        # Pack the most constrained item
        idx, _, _ = item_flexibility[0]
        size = items[idx]

        # Place in the first bin that fits
        placed = False
        for j in range(len(bins)):
            if bin_fills[j] + size <= capacity:
                bins[j].append(idx)
                bin_fills[j] += size
                placed = True
                break

        if not placed:
            # No existing bin has space; open a new bin
            bins.append([idx])
            bin_fills.append(size)

        packed[idx] = True

    return bins
