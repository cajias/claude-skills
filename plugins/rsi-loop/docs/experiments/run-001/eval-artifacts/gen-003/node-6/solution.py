def pack(items: list[int], capacity: int) -> list[list[int]]:
    """
    Dual-strategy bin packing with adaptive phase routing.

    Core mechanism: Partition items into two groups using problem structure
    (items matching common bin fractions vs. the remainder), apply different
    strategies to each group, then unify. Different from sorted-greedy because
    it makes strategic decisions about which items to process first based on
    structure, not a single sort order.
    """
    n = len(items)
    if n == 0:
        return []

    indexed_items = [(items[i], i) for i in range(n)]

    # Identify "structured" items: those close to useful capacity fractions
    # These are items that naturally fit well together
    structured = []
    unstructured = []

    # Key fractions that enable good packings
    key_fractions = [
        (1, 1),    # Items that are exactly capacity (singletons)
        (1, 2),    # Items near half-capacity
        (2, 3),    # Items near 2/3 capacity
        (1, 3),    # Items near 1/3 capacity
        (1, 4),    # Items near 1/4 capacity
    ]

    for size, idx in indexed_items:
        is_structured = False
        tolerance = capacity * 0.15

        for num, denom in key_fractions:
            target = (capacity * num) / denom
            if abs(size - target) < tolerance:
                is_structured = True
                break

        if is_structured:
            structured.append((size, idx))
        else:
            unstructured.append((size, idx))

    # Sort both groups by size descending
    structured.sort(reverse=True, key=lambda x: x[0])
    unstructured.sort(reverse=True, key=lambda x: x[0])

    bins = []
    bin_weights = []

    # Phase 1: Pack structured items first (they pair well)
    for size, idx in structured:
        # For structured items, use best-fit
        best_bin = -1
        best_waste = float('inf')

        for i, w in enumerate(bin_weights):
            if w + size <= capacity:
                waste = capacity - (w + size)
                if waste < best_waste:
                    best_waste = waste
                    best_bin = i

        if best_bin >= 0:
            bins[best_bin].append(idx)
            bin_weights[best_bin] += size
        else:
            bins.append([idx])
            bin_weights.append(size)

    # Phase 2: Pack unstructured items (fill remaining space)
    for size, idx in unstructured:
        # Adaptive placement based on current state
        num_bins = len(bins)
        candidates = [
            (i, bin_weights[i])
            for i in range(num_bins)
            if bin_weights[i] + size <= capacity
        ]

        if not candidates:
            bins.append([idx])
            bin_weights.append(size)
            continue

        # Adaptive decision
        if size > capacity * 0.4:
            # Large unstructured items: best-fit
            chosen = min(candidates, key=lambda x: capacity - (x[1] + size))[0]
        elif len(candidates) > 1:
            # Multiple options: prefer worst-fit (balance)
            chosen = max(candidates, key=lambda x: x[1])[0]
        else:
            # Only one option
            chosen = candidates[0][0]

        bins[chosen].append(idx)
        bin_weights[chosen] += size

    return bins
