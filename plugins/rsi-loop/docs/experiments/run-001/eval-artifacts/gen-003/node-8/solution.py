def pack(items: list[int], capacity: int) -> list[list[int]]:
    """
    Placement-strategy-adaptive FFD with instance-aware selection.

    Core mechanism: Analyze instance properties upfront (size distribution,
    variance, etc.) and select the best placement strategy (First-Fit,
    Best-Fit, or Worst-Fit) for that specific instance characteristic.
    Then run FFD with the selected strategy and refine.

    Family: placement-strategy-adaptive

    This is distinct from sorted-greedy (fixed rule) and multi-ordering-ensemble
    (tries all orderings): it uses instance properties to make a single
    strategic decision upfront about which placement rule to use.
    """
    if not items:
        return []

    n = len(items)

    # Analyze instance properties
    item_sizes = items[:]
    item_sizes.sort()

    min_size = min(items)
    max_size = max(items)
    avg_size = sum(items) / n
    total_size = sum(items)

    # Compute size variance (coefficient of variation)
    variance = sum((x - avg_size) ** 2 for x in items) / n
    std_dev = variance ** 0.5
    cv = std_dev / avg_size if avg_size > 0 else 0

    # Compute bimodality indicator (gap in middle)
    sorted_items = sorted(items)
    mid_point = len(sorted_items) // 2
    lower_median = sorted_items[mid_point - 1] if mid_point > 0 else sorted_items[0]
    upper_median = sorted_items[mid_point]

    # Count items above and below capacity/2
    large_count = sum(1 for x in items if x > capacity // 2)
    small_count = sum(1 for x in items if x <= capacity // 2)

    # Select placement strategy based on instance properties
    if large_count > 0 and small_count > 0 and large_count < n and small_count < n:
        # Bimodal distribution (both large and small items)
        strategy = "best_fit"  # Best Fit works well for bimodal
    elif cv > 0.4:
        # High variance (diverse sizes)
        strategy = "first_fit"  # First Fit is simple and effective
    else:
        # Low variance or uniform
        strategy = "worst_fit"  # Worst Fit helps spread items for consolidation

    # Sort items in decreasing order
    indexed_items = [(items[i], i) for i in range(n)]
    indexed_items.sort(reverse=True)

    # Phase 1: Construct with selected strategy
    bins = []

    if strategy == "best_fit":
        # Best Fit: place in bin with least remaining space that fits
        for size, idx in indexed_items:
            best_bin = -1
            best_space = capacity + 1

            for bin_idx, bin_items in enumerate(bins):
                bin_sum = sum(items[i] for i in bin_items)
                remaining = capacity - bin_sum
                if remaining >= size and remaining < best_space:
                    best_space = remaining
                    best_bin = bin_idx

            if best_bin >= 0:
                bins[best_bin].append(idx)
            else:
                bins.append([idx])

    elif strategy == "worst_fit":
        # Worst Fit: place in bin with most remaining space that fits
        for size, idx in indexed_items:
            worst_bin = -1
            worst_space = -1

            for bin_idx, bin_items in enumerate(bins):
                bin_sum = sum(items[i] for i in bin_items)
                remaining = capacity - bin_sum
                if remaining >= size and remaining > worst_space:
                    worst_space = remaining
                    worst_bin = bin_idx

            if worst_bin >= 0:
                bins[worst_bin].append(idx)
            else:
                bins.append([idx])

    else:  # first_fit
        # First Fit: place in first bin that fits
        for size, idx in indexed_items:
            placed = False
            for bin_idx, bin_items in enumerate(bins):
                bin_sum = sum(items[i] for i in bin_items)
                if bin_sum + size <= capacity:
                    bin_items.append(idx)
                    placed = True
                    break

            if not placed:
                bins.append([idx])

    best_solution = [b[:] for b in bins]
    best_count = len(bins)

    # Phase 2: Consolidation pass
    for iteration in range(min(40, n)):
        if len(bins) <= 1:
            break

        improved = False

        for i in range(len(bins)):
            if len(bins[i]) == 0:
                continue

            sum_i = sum(items[j] for j in bins[i])

            for j in range(i + 1, len(bins)):
                if len(bins[j]) == 0:
                    continue

                sum_j = sum(items[k] for k in bins[j])

                if sum_i + sum_j <= capacity:
                    bins[i].extend(bins[j])
                    bins[j] = []
                    improved = True
                    break

            if improved:
                break

        bins = [b for b in bins if len(b) > 0]

        if len(bins) < best_count:
            best_count = len(bins)
            best_solution = [b[:] for b in bins]

        if not improved:
            break

    # Phase 3: Item redistribution
    for _ in range(min(20, n)):
        if len(bins) <= 1:
            break

        moved = False

        for from_idx in range(len(bins)):
            if len(bins[from_idx]) == 0:
                continue

            for item in bins[from_idx][:]:
                item_size = items[item]

                for to_idx in range(len(bins)):
                    if to_idx == from_idx:
                        continue

                    to_sum = sum(items[i] for i in bins[to_idx])

                    if to_sum + item_size <= capacity:
                        bins[from_idx].remove(item)
                        bins[to_idx].append(item)
                        moved = True
                        break

                if moved:
                    break

            if moved:
                break

        bins = [b for b in bins if len(b) > 0]

        if len(bins) < len(best_solution):
            best_solution = [b[:] for b in bins]
        elif not moved:
            break

    return best_solution
