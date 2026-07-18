def pack(items: list[int], capacity: int) -> list[list[int]]:
    """
    Multi-start exploration with diverse heuristics.

    Combines:
    - First-Fit Decreasing (FFD): sort items, place in first bin that fits
    - Next-Fit Decreasing (NFD): sort items, maintain current bin, move to next when full

    These are structurally different placement strategies, forming a portfolio.
    """
    n = len(items)
    if n == 0:
        return []

    solutions = []

    # Construction 1: First-Fit Decreasing
    solutions.append(_first_fit_decreasing(items, capacity))

    # Construction 2: Next-Fit Decreasing
    solutions.append(_next_fit_decreasing(items, capacity))

    # Return the best solution (fewest bins)
    return min(solutions, key=len)


def _first_fit_decreasing(items: list[int], capacity: int) -> list[list[int]]:
    """
    First-Fit Decreasing (FFD): sort items by size (descending), then place
    each item into the first bin where it fits.
    """
    n = len(items)
    indices = sorted(range(n), key=lambda i: items[i], reverse=True)
    bins = []
    bin_usage = []

    for i in indices:
        placed = False
        # Try each bin in order until one fits
        for bid in range(len(bins)):
            if bin_usage[bid] + items[i] <= capacity:
                bins[bid].append(i)
                bin_usage[bid] += items[i]
                placed = True
                break

        if not placed:
            # Open a new bin
            bins.append([i])
            bin_usage.append(items[i])

    return bins


def _next_fit_decreasing(items: list[int], capacity: int) -> list[list[int]]:
    """
    Next-Fit Decreasing (NFD): sort items by size (descending), then place
    each item into the current bin if it fits, otherwise open a new bin and
    never return to previous bins.

    This is structurally different from FFD and may find different solutions
    on some instances.
    """
    n = len(items)
    indices = sorted(range(n), key=lambda i: items[i], reverse=True)
    bins = []
    bin_usage = []
    current_bin = -1

    for i in indices:
        # Try to place in current bin
        if current_bin >= 0 and bin_usage[current_bin] + items[i] <= capacity:
            bins[current_bin].append(i)
            bin_usage[current_bin] += items[i]
        else:
            # Move to next bin (or create one)
            current_bin += 1
            if current_bin >= len(bins):
                bins.append([i])
                bin_usage.append(items[i])
            else:
                bins[current_bin].append(i)
                bin_usage[current_bin] += items[i]

    return bins
