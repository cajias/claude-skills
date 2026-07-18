def pack(items: list[int], capacity: int) -> list[list[int]]:
    """
    Deterministic multi-ordering ensemble with adaptive placement.

    Core mechanism: Generates multiple deterministic orderings of items
    (not just sort-by-size) based on hash-derived seeds. For each ordering,
    applies placement heuristics, then returns the best result. Different
    orderings can reveal different packing opportunities that single-sort
    approaches miss.

    Algorithm family: multi-ordering-ensemble.
    """

    if not items:
        return []

    n = len(items)
    indices = list(range(n))

    def ffd_with_order(order):
        """FFD with specified ordering."""
        bins = []
        bin_fills = []

        for idx in order:
            placed = False
            for i in range(len(bins)):
                if bin_fills[i] + items[idx] <= capacity:
                    bins[i].append(idx)
                    bin_fills[i] += items[idx]
                    placed = True
                    break

            if not placed:
                bins.append([idx])
                bin_fills.append(items[idx])

        return bins

    def bfd_with_order(order):
        """BFD with specified ordering."""
        bins = []
        bin_fills = []

        for idx in order:
            best_bin = -1
            best_space = capacity + 1

            for i in range(len(bins)):
                space_left = capacity - bin_fills[i]
                if space_left >= items[idx] and space_left < best_space:
                    best_bin = i
                    best_space = space_left

            if best_bin >= 0:
                bins[best_bin].append(idx)
                bin_fills[best_bin] += items[idx]
            else:
                bins.append([idx])
                bin_fills.append(items[idx])

        return bins

    # Generate multiple orderings using deterministic hash-based perturbation
    results = []

    # Order 1: Decreasing size (standard FFD)
    order_dec = sorted(indices, key=lambda i: -items[i])
    results.append(ffd_with_order(order_dec))
    results.append(bfd_with_order(order_dec))

    # Order 2: Increasing size
    order_inc = sorted(indices, key=lambda i: items[i])
    results.append(ffd_with_order(order_inc))
    results.append(bfd_with_order(order_inc))

    # Order 3: Hash-based order (deterministic but different from pure sort)
    # Use item size + index hash to create a different order
    order_hash = sorted(indices, key=lambda i: (items[i] * 31 + i) % (n + 1))
    results.append(ffd_with_order(order_hash))
    results.append(bfd_with_order(order_hash))

    # Order 4: Distance from median
    sorted_by_size = sorted(indices, key=lambda i: items[i])
    median_idx = sorted_by_size[n // 2]
    median_val = items[median_idx]
    order_median = sorted(indices, key=lambda i: abs(items[i] - median_val))
    results.append(ffd_with_order(order_median))
    results.append(bfd_with_order(order_median))

    # Order 5: Ratio to capacity
    order_ratio = sorted(indices, key=lambda i: items[i] / capacity)
    results.append(ffd_with_order(order_ratio))

    # Order 6: Reverse ratio
    order_rev_ratio = sorted(indices, key=lambda i: -items[i] / capacity)
    results.append(bfd_with_order(order_rev_ratio))

    # Return the best result (minimum bins used)
    return min(results, key=lambda bins: len(bins))
