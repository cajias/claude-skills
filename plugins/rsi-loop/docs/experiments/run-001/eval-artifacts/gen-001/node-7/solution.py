def pack(items: list[int], capacity: int) -> list[list[int]]:
    """Return a list of bins; each bin is a list of item INDICES (0-based).

    Every index 0..len(items)-1 must appear in exactly one bin.
    The sum of item sizes in each bin must not exceed `capacity`.

    Strategy: Intelligent item pairing with multi-phase packing.
    """
    if not items:
        return []

    if len(items) == 1:
        return [[0]]

    # Try multiple strategic approaches
    solutions = []

    # Approach 1: Standard FFD
    sol = _pack_ffd(items, capacity)
    sol = _refine(sol, items, capacity)
    solutions.append(sol)

    # Approach 2: Pair-aware packing for compatibility
    sol = _pack_pair_aware(items, capacity)
    sol = _refine(sol, items, capacity)
    solutions.append(sol)

    # Approach 3: Three-phase (large, medium, small) with careful ordering
    sol = _pack_three_phase(items, capacity)
    sol = _refine(sol, items, capacity)
    solutions.append(sol)

    # Approach 4: BFD with heavy refinement
    sol = _pack_bfd(items, capacity)
    sol = _refine_heavy(sol, items, capacity)
    solutions.append(sol)

    # Approach 5: WFD variant
    sol = _pack_wfd(items, capacity)
    sol = _refine_heavy(sol, items, capacity)
    solutions.append(sol)

    # Return best solution
    best = min(solutions, key=len)
    return [b for b in best if b]


def _pack_ffd(items, capacity):
    """First-Fit Decreasing."""
    indexed = [(items[i], i) for i in range(len(items))]
    indexed.sort(reverse=True)

    bins = []
    bin_loads = []

    for size, idx in indexed:
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

    return bins


def _pack_bfd(items, capacity):
    """Best-Fit Decreasing."""
    indexed = [(items[i], i) for i in range(len(items))]
    indexed.sort(reverse=True)

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


def _pack_wfd(items, capacity):
    """Worst-Fit Decreasing."""
    indexed = [(items[i], i) for i in range(len(items))]
    indexed.sort(reverse=True)

    bins = []
    bin_loads = []

    for size, idx in indexed:
        best_bin = -1
        best_remaining = -1
        for i in range(len(bins)):
            remaining = capacity - bin_loads[i]
            if remaining >= size and remaining > best_remaining:
                best_bin = i
                best_remaining = remaining
        if best_bin >= 0:
            bins[best_bin].append(idx)
            bin_loads[best_bin] += size
        else:
            bins.append([idx])
            bin_loads.append(size)

    return bins


def _pack_pair_aware(items, capacity):
    """Pack with awareness of item pairs that fit well together."""
    # Sort items
    indexed = sorted(enumerate(items), key=lambda x: -x[1])

    # Identify items that could pair well
    bins = []
    bin_loads = []
    used = set()

    # Phase 1: Try to pair large items
    for i in range(len(indexed)):
        if i in used:
            continue

        size_i, idx_i = indexed[i][1], indexed[i][0]

        if size_i > capacity // 2:  # Large item
            # Try to find a pairing partner
            best_partner = -1
            best_fit = capacity + 1

            for j in range(i + 1, len(indexed)):
                if j in used:
                    continue

                size_j, idx_j = indexed[j][1], indexed[j][0]
                combined = size_i + size_j

                if combined <= capacity:
                    fit_quality = capacity - combined
                    if fit_quality < best_fit:
                        best_partner = j
                        best_fit = fit_quality

            if best_partner >= 0:
                # Create bin with pair
                size_j, idx_j = indexed[best_partner][1], indexed[best_partner][0]
                bins.append([idx_i, idx_j])
                bin_loads.append(size_i + size_j)
                used.add(i)
                used.add(best_partner)
            else:
                # Place alone
                bins.append([idx_i])
                bin_loads.append(size_i)
                used.add(i)

    # Phase 2: Pack remaining items with FFD
    remaining = [(indexed[i][1], indexed[i][0]) for i in range(len(indexed)) if i not in used]
    remaining.sort(reverse=True)

    for size, idx in remaining:
        placed = False
        for b in range(len(bins)):
            if bin_loads[b] + size <= capacity:
                bins[b].append(idx)
                bin_loads[b] += size
                placed = True
                break
        if not placed:
            bins.append([idx])
            bin_loads.append(size)

    return bins


def _pack_three_phase(items, capacity):
    """Three-phase packing: large, medium, small with specific strategies."""
    # Categorize items
    large_threshold = capacity // 2
    medium_threshold = capacity // 4

    large = []
    medium = []
    small = []

    for i, size in enumerate(items):
        if size > large_threshold:
            large.append((size, i))
        elif size > medium_threshold:
            medium.append((size, i))
        else:
            small.append((size, i))

    large.sort(reverse=True)
    medium.sort(reverse=True)
    small.sort(reverse=True)

    bins = []
    bin_loads = []

    # Phase 1: Pack large items with attempt to pair
    for i, (size_i, idx_i) in enumerate(large):
        best_partner = -1
        best_fit = capacity + 1

        for j in range(i + 1, len(large)):
            size_j, idx_j = large[j]
            combined = size_i + size_j
            if combined <= capacity:
                fit_quality = capacity - combined
                if fit_quality < best_fit:
                    best_partner = j
                    best_fit = fit_quality

        if best_partner >= 0:
            size_j, idx_j = large[best_partner]
            bins.append([idx_i, idx_j])
            bin_loads.append(size_i + size_j)
            large.pop(best_partner)
        else:
            # Try to fit with first compatible bin
            placed = False
            best_bin = -1
            best_remaining = capacity + 1
            for b in range(len(bins)):
                remaining = capacity - bin_loads[b]
                if remaining >= size_i and remaining < best_remaining:
                    best_bin = b
                    best_remaining = remaining
            if best_bin >= 0:
                bins[best_bin].append(idx_i)
                bin_loads[best_bin] += size_i
                placed = True

            if not placed:
                bins.append([idx_i])
                bin_loads.append(size_i)

    # Phase 2: Pack medium items with BFD
    for size, idx in medium:
        best_bin = -1
        best_remaining = capacity + 1
        for b in range(len(bins)):
            remaining = capacity - bin_loads[b]
            if remaining >= size and remaining < best_remaining:
                best_bin = b
                best_remaining = remaining
        if best_bin >= 0:
            bins[best_bin].append(idx)
            bin_loads[best_bin] += size
        else:
            bins.append([idx])
            bin_loads.append(size)

    # Phase 3: Pack small items with FFD
    for size, idx in small:
        placed = False
        for b in range(len(bins)):
            if bin_loads[b] + size <= capacity:
                bins[b].append(idx)
                bin_loads[b] += size
                placed = True
                break
        if not placed:
            bins.append([idx])
            bin_loads.append(size)

    return bins


def _refine(bins, items, capacity):
    """Basic refinement."""
    if not bins:
        return bins

    bin_loads = [sum(items[idx] for idx in b) for b in bins]

    for _ in range(min(10, len(items))):
        improved = False

        for src in range(len(bins) - 1, 0, -1):
            if improved or not bins[src]:
                continue

            for item_idx in sorted([(items[idx], idx) for idx in bins[src]]):
                size, idx = item_idx
                for dest in range(src):
                    if bin_loads[dest] + size <= capacity:
                        bins[src].remove(idx)
                        bins[dest].append(idx)
                        bin_loads[src] -= size
                        bin_loads[dest] += size
                        improved = True
                        break
                if improved:
                    break

    return bins


def _refine_heavy(bins, items, capacity):
    """Aggressive refinement with consolidation."""
    if not bins:
        return bins

    bin_loads = [sum(items[idx] for idx in b) for b in bins]

    for iteration in range(len(items)):
        improved = False

        # Move items
        for src in range(len(bins) - 1, 0, -1):
            if improved or not bins[src]:
                continue

            for item_idx in sorted([(items[idx], idx) for idx in bins[src]]):
                size, idx = item_idx
                for dest in range(src):
                    if bin_loads[dest] + size <= capacity:
                        bins[src].remove(idx)
                        bins[dest].append(idx)
                        bin_loads[src] -= size
                        bin_loads[dest] += size
                        improved = True
                        break
                if improved:
                    break

        # Consolidate bins
        if not improved:
            for src in range(len(bins) - 1, max(-1, len(bins) - 4), -1):
                if improved or not bins[src]:
                    continue

                to_move = [(items[idx], idx) for idx in bins[src]]
                to_move.sort(reverse=True)

                temp_loads = list(bin_loads)
                moves = []

                for size, idx in to_move:
                    placed = False
                    for dest in range(src):
                        if temp_loads[dest] + size <= capacity:
                            moves.append((idx, size, dest))
                            temp_loads[dest] += size
                            placed = True
                            break

                    if not placed:
                        break

                if len(moves) == len(to_move):
                    for idx, size, dest in moves:
                        bins[src].remove(idx)
                        bins[dest].append(idx)
                        bin_loads[src] -= size
                        bin_loads[dest] += size
                    improved = True

    return bins
