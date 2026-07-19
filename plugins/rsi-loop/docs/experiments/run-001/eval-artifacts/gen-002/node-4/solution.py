def pack(items: list[int], capacity: int) -> list[list[int]]:
    """Return a list of bins; each bin is a list of item INDICES (0-based).

    This solution uses an exact-hybrid approach:
    - For small instances (<=20 items), use branch-and-bound for exact solving
    - For larger instances, fall back to First-Fit Decreasing (FFD) heuristic
    """

    if not items:
        return []

    n = len(items)

    # For small instances, try exact solving with branch-and-bound
    if n <= 20:
        result = solve_branch_and_bound(items, capacity)
        if result is not None:
            return result

    # For larger instances or if exact solving returns None, use FFD heuristic
    return solve_ffd(items, capacity)


def solve_branch_and_bound(items: list[int], capacity: int) -> list[list[int]]:
    """Branch-and-bound algorithm to find optimal or near-optimal packing.

    Strategy:
    1. Compute a greedy upper bound (FFD) for pruning
    2. Process items in decreasing size order
    3. For each item, try placing in each existing bin or create new bin
    4. Prune branches that can't improve the best solution found
    """

    n = len(items)
    best_solution = {'bins': None, 'count': float('inf')}

    # Get greedy upper bound first for better pruning
    greedy = solve_ffd(items, capacity)
    best_solution['bins'] = greedy
    best_solution['count'] = len(greedy)

    # Sort item indices by decreasing size for better branch-and-bound performance
    order = sorted(range(n), key=lambda i: -items[i])

    def branch(idx, bins, spaces):
        """Recursively branch on item placements."""

        if idx == n:
            # All items placed
            if len(bins) < best_solution['count']:
                best_solution['count'] = len(bins)
                best_solution['bins'] = [list(b) for b in bins]
            return

        # Pruning: if current number of bins >= best found, no point continuing
        if len(bins) >= best_solution['count']:
            return

        item_idx = order[idx]
        item_size = items[item_idx]

        # Try placing in each existing bin (in order)
        for j in range(len(bins)):
            if spaces[j] >= item_size:
                bins[j].append(item_idx)
                spaces[j] -= item_size
                branch(idx + 1, bins, spaces)
                bins[j].pop()
                spaces[j] += item_size

        # Try creating a new bin (only if it could potentially be better)
        if len(bins) < best_solution['count']:
            bins.append([item_idx])
            spaces.append(capacity - item_size)
            branch(idx + 1, bins, spaces)
            bins.pop()
            spaces.pop()

    branch(0, [], [])
    return best_solution['bins']


def solve_ffd(items: list[int], capacity: int) -> list[list[int]]:
    """First-Fit Decreasing (FFD) heuristic for bin packing.

    Algorithm:
    1. Sort items in decreasing order of size
    2. For each item, place it in the first bin that has room
    3. If no bin has room, create a new bin

    FFD is a fast greedy heuristic with good approximation properties.
    """

    # Create pairs of (index, size) and sort by size descending
    indexed_items = sorted(enumerate(items), key=lambda x: -x[1])

    bins = []
    spaces = []

    for item_idx, item_size in indexed_items:
        # Try to place in first bin with enough space (First-Fit)
        placed = False
        for i in range(len(bins)):
            if spaces[i] >= item_size:
                bins[i].append(item_idx)
                spaces[i] -= item_size
                placed = True
                break

        # If no bin has space, create new bin
        if not placed:
            bins.append([item_idx])
            spaces.append(capacity - item_size)

    return bins
