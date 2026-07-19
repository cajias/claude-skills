def pack(items: list[int], capacity: int) -> list[list[int]]:
    """Pack items using adaptive multi-strategy approach with instance analysis.

    Core mechanism: Analyze instance structure (coefficient of variation,
    item distribution), then adaptively select and run multiple strategies.
    This is fundamentally different from sorted-greedy (uses problem-aware
    selection, not just sort + fixed rule).

    Unlike multi-ordering-ensemble (which re-sorts with different orders),
    this uses structurally different construction methods guided by
    instance properties.

    Time: O(n log n) analysis + O(k*n^2) strategies = O(n^2).
    """
    n = len(items)
    if n == 0:
        return []

    if n == 1:
        return [[0]]

    # Analyze instance structure
    mean_size = sum(items) / n
    max_size = max(items)
    min_size = min(items)
    variance = sum((x - mean_size) ** 2 for x in items) / n
    std_dev = variance ** 0.5
    cv = std_dev / mean_size if mean_size > 0 else 0

    # Try strategies appropriate for instance type
    candidates = []

    # Always try best-fit (universal good heuristic)
    candidates.append(pack_best_fit_desc(items, capacity))

    # Try lookahead best-fit (considers future items)
    candidates.append(pack_lookahead_best_fit(items, capacity))

    # High-variance instances (bimodal-like): try large-item-first
    if cv > 0.5:
        candidates.append(pack_large_item_first(items, capacity))

    # Low-variance instances (uniform-like): try rotations
    if cv <= 0.8:
        candidates.append(pack_rotating_aggressive(items, capacity))
        candidates.append(pack_rotating_conservative(items, capacity))

    # Always try first-fit as fallback
    candidates.append(pack_first_fit_desc(items, capacity))

    # Also try worst-fit (sometimes surprisingly good)
    candidates.append(pack_worst_fit_desc(items, capacity))

    # Return the packing with best combined score
    def score_packing(packing):
        n_bins = len(packing)
        if n_bins == 0:
            return (0, 0, 0)

        bin_sums = [sum(items[idx] for idx in bin_list) for bin_list in packing]
        mean_util = sum(bin_sums) / n_bins

        # Variance in utilization (lower is more balanced)
        variance_util = sum((u - mean_util) ** 2 for u in bin_sums) / n_bins if n_bins > 0 else 0

        # Max utilization (prefer not to have overfull bins)
        max_util_ratio = max(bin_sums) / capacity if bin_sums else 0

        # Composite score:
        # Primary: minimize bins
        # Secondary: minimize variance (prefer balanced bins)
        # Tertiary: minimize max utilization (avoid extreme cases)
        return (n_bins, variance_util, max_util_ratio)

    best = min(candidates, key=score_packing)
    return best


def pack_best_fit_desc(items, capacity):
    """Pure best-fit decreasing: always place in bin with tightest fit."""
    n = len(items)
    indexed = [(items[i], i) for i in range(n)]
    indexed.sort(reverse=True, key=lambda x: x[0])

    bins = []
    bin_sums = []

    for size, idx in indexed:
        best_bin = -1
        best_residual = capacity + 1

        for j in range(len(bins)):
            if bin_sums[j] + size <= capacity:
                residual = capacity - bin_sums[j] - size
                if residual < best_residual:
                    best_residual = residual
                    best_bin = j

        if best_bin == -1:
            bins.append([idx])
            bin_sums.append(size)
        else:
            bins[best_bin].append(idx)
            bin_sums[best_bin] += size

    return bins


def pack_rotating_aggressive(items, capacity):
    """Rotate through first-fit, best-fit, worst-fit on every item."""
    n = len(items)
    indexed = [(items[i], i) for i in range(n)]
    indexed.sort(reverse=True, key=lambda x: x[0])

    bins = []
    bin_sums = []
    strategy = 0  # 0=first-fit, 1=best-fit, 2=worst-fit

    for size, idx in indexed:
        best_bin = -1

        if strategy == 0:  # First-fit
            for j in range(len(bins)):
                if bin_sums[j] + size <= capacity:
                    best_bin = j
                    break

        elif strategy == 1:  # Best-fit
            best_residual = capacity + 1
            for j in range(len(bins)):
                if bin_sums[j] + size <= capacity:
                    residual = capacity - bin_sums[j] - size
                    if residual < best_residual:
                        best_residual = residual
                        best_bin = j

        else:  # Worst-fit
            best_residual = -1
            for j in range(len(bins)):
                if bin_sums[j] + size <= capacity:
                    residual = capacity - bin_sums[j] - size
                    if residual > best_residual:
                        best_residual = residual
                        best_bin = j

        if best_bin == -1:
            bins.append([idx])
            bin_sums.append(size)
        else:
            bins[best_bin].append(idx)
            bin_sums[best_bin] += size

        strategy = (strategy + 1) % 3

    return bins


def pack_rotating_conservative(items, capacity):
    """Conservative rotation: favor best-fit (every 3 items), with occasional diversity."""
    n = len(items)
    indexed = [(items[i], i) for i in range(n)]
    indexed.sort(reverse=True, key=lambda x: x[0])

    bins = []
    bin_sums = []

    for item_idx, (size, idx) in enumerate(indexed):
        # Favor best-fit with occasional first-fit
        use_best_fit = (item_idx % 3) != 2
        best_bin = -1

        if use_best_fit:  # Best-fit
            best_residual = capacity + 1
            for j in range(len(bins)):
                if bin_sums[j] + size <= capacity:
                    residual = capacity - bin_sums[j] - size
                    if residual < best_residual:
                        best_residual = residual
                        best_bin = j

        else:  # First-fit
            for j in range(len(bins)):
                if bin_sums[j] + size <= capacity:
                    best_bin = j
                    break

        if best_bin == -1:
            bins.append([idx])
            bin_sums.append(size)
        else:
            bins[best_bin].append(idx)
            bin_sums[best_bin] += size

    return bins


def pack_first_fit_desc(items, capacity):
    """First-fit decreasing: place in first bin with space."""
    n = len(items)
    indexed = [(items[i], i) for i in range(n)]
    indexed.sort(reverse=True, key=lambda x: x[0])

    bins = []
    bin_sums = []

    for size, idx in indexed:
        best_bin = -1

        for j in range(len(bins)):
            if bin_sums[j] + size <= capacity:
                best_bin = j
                break

        if best_bin == -1:
            bins.append([idx])
            bin_sums.append(size)
        else:
            bins[best_bin].append(idx)
            bin_sums[best_bin] += size

    return bins


def pack_worst_fit_desc(items, capacity):
    """Worst-fit decreasing: place in bin with most remaining space."""
    n = len(items)
    indexed = [(items[i], i) for i in range(n)]
    indexed.sort(reverse=True, key=lambda x: x[0])

    bins = []
    bin_sums = []

    for size, idx in indexed:
        best_bin = -1
        best_residual = -1

        for j in range(len(bins)):
            if bin_sums[j] + size <= capacity:
                residual = capacity - bin_sums[j] - size
                if residual > best_residual:
                    best_residual = residual
                    best_bin = j

        if best_bin == -1:
            bins.append([idx])
            bin_sums.append(size)
        else:
            bins[best_bin].append(idx)
            bin_sums[best_bin] += size

    return bins


def pack_large_item_first(items, capacity):
    """Separate large items, pack each independently, then fill gaps."""
    n = len(items)
    indexed = [(items[i], i) for i in range(n)]

    threshold = 0.4 * capacity
    large_items = [(s, i) for s, i in indexed if s > threshold]
    small_items = [(s, i) for s, i in indexed if s <= threshold]

    # Sort both
    large_items.sort(reverse=True, key=lambda x: x[0])
    small_items.sort(reverse=True, key=lambda x: x[0])

    bins = []
    bin_sums = []

    # Place large items (each in its own bin initially)
    for size, idx in large_items:
        bins.append([idx])
        bin_sums.append(size)

    # Place small items using best-fit into existing bins
    for size, idx in small_items:
        best_bin = -1
        best_residual = capacity + 1

        for j in range(len(bins)):
            if bin_sums[j] + size <= capacity:
                residual = capacity - bin_sums[j] - size
                if residual < best_residual:
                    best_residual = residual
                    best_bin = j

        if best_bin == -1:
            bins.append([idx])
            bin_sums.append(size)
        else:
            bins[best_bin].append(idx)
            bin_sums[best_bin] += size

    return bins


def pack_lookahead_best_fit(items, capacity):
    """Best-fit with lookahead: consider how many future items could fit."""
    n = len(items)
    indexed = [(items[i], i) for i in range(n)]
    indexed.sort(reverse=True, key=lambda x: x[0])

    bins = []
    bin_sums = []

    for step, (size, idx) in enumerate(indexed):
        best_bin = -1
        best_score = (float('inf'), float('inf'))  # (future_capacity, residual)

        for j in range(len(bins)):
            if bin_sums[j] + size <= capacity:
                residual = capacity - bin_sums[j] - size

                # Lookahead: count how many of the next items could fit
                future_count = 0
                for k in range(step + 1, min(step + 5, len(indexed))):
                    if indexed[k][0] <= residual:
                        future_count += 1

                # Prefer bins that preserve future options
                # Score: (-future_count, residual)
                # Lower is better: more future items is better
                score = (-future_count, residual)
                if score < best_score:
                    best_score = score
                    best_bin = j

        if best_bin == -1:
            bins.append([idx])
            bin_sums.append(size)
        else:
            bins[best_bin].append(idx)
            bin_sums[best_bin] += size

    return bins
