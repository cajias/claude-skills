def pack(items: list[int], capacity: int) -> list[list[int]]:
    """
    Pack items into bins using local search with improvement moves.

    Algorithm: Start with a greedy initial packing (First Fit Decreasing),
    then iteratively apply improvement moves (relocate, swap, merge) until
    reaching a local optimum (fixpoint).
    """
    n = len(items)
    if n == 0:
        return []

    # ===== Phase 1: Initial greedy packing (First Fit Decreasing) =====
    indexed_items = [(items[i], i) for i in range(n)]
    indexed_items.sort(reverse=True)  # Sort by size, descending

    bins = []
    for size, idx in indexed_items:
        # Try to fit in existing bin
        placed = False
        for bin_idx in range(len(bins)):
            current_sum = sum(items[i] for i in bins[bin_idx])
            if current_sum + size <= capacity:
                bins[bin_idx].append(idx)
                placed = True
                break

        if not placed:
            # Create new bin
            bins.append([idx])

    # ===== Phase 2: Local search improvements =====
    improved = True
    max_iterations = 1000  # Safety limit
    iteration = 0

    while improved and iteration < max_iterations:
        improved = False
        iteration += 1

        # ===== Move 1: Merge bins =====
        # If two bins fit together, merge them
        i = 0
        while i < len(bins) and not improved:
            j = i + 1
            while j < len(bins):
                bin_i_sum = sum(items[idx] for idx in bins[i])
                bin_j_sum = sum(items[idx] for idx in bins[j])
                if bin_i_sum + bin_j_sum <= capacity:
                    # Merge bin j into bin i
                    bins[i].extend(bins[j])
                    bins.pop(j)
                    improved = True
                    break
                j += 1
            if not improved:
                i += 1

        if improved:
            continue

        # ===== Move 2: Relocate items =====
        # Try to move an item from one bin to another to enable merging or reduce bins
        for source_bin_idx in range(len(bins)):
            if improved:
                break

            for item_idx_in_list in range(len(bins[source_bin_idx])):
                if improved:
                    break

                item_idx = bins[source_bin_idx][item_idx_in_list]
                item_size = items[item_idx]

                # Try moving to each other bin
                for target_bin_idx in range(len(bins)):
                    if target_bin_idx == source_bin_idx:
                        continue

                    target_sum = sum(items[i] for i in bins[target_bin_idx])
                    if target_sum + item_size <= capacity:
                        # Can fit in target bin
                        bins[source_bin_idx].pop(item_idx_in_list)
                        bins[target_bin_idx].append(item_idx)

                        # Remove empty source bin
                        if not bins[source_bin_idx]:
                            bins.pop(source_bin_idx)

                        improved = True
                        break

        if improved:
            continue

        # ===== Move 3: Swap items between bins =====
        # Try swapping an item from bin A to bin B and vice versa
        for i in range(len(bins)):
            if improved:
                break

            for j in range(i + 1, len(bins)):
                if improved:
                    break

                for idx_in_i in range(len(bins[i])):
                    if improved:
                        break

                    for idx_in_j in range(len(bins[j])):
                        item_i = bins[i][idx_in_i]
                        item_j = bins[j][idx_in_j]
                        size_i = items[item_i]
                        size_j = items[item_j]

                        # Check if swap is valid
                        bin_i_sum = sum(items[k] for k in bins[i]) - size_i + size_j
                        bin_j_sum = sum(items[k] for k in bins[j]) - size_j + size_i

                        if bin_i_sum <= capacity and bin_j_sum <= capacity:
                            # Swap items
                            bins[i][idx_in_i] = item_j
                            bins[j][idx_in_j] = item_i
                            improved = True
                            break

    return bins
