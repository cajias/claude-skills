def pack(items: list[int], capacity: int) -> list[list[int]]:
    """Return a list of bins; each bin is a list of item INDICES (0-based).

    Every index 0..len(items)-1 must appear in exactly one bin.
    The sum of item sizes in each bin must not exceed `capacity`.

    Uses First Fit Decreasing (FFD) with robust input normalization:
    - Handles edge cases gracefully (empty items, zero/negative sizes)
    - Normalizes items before packing (validates types)
    - Deterministic and fast
    """
    # Edge case: empty items list
    if not items:
        return []

    # Validate capacity
    if capacity <= 0:
        # Invalid capacity; return each item in its own bin
        return [[i] for i in range(len(items))]

    # Create list of (size, original_index) pairs with validation
    # Normalize: treat negative or zero as 0 (safe fallback)
    indexed_items = []
    for i, size in enumerate(items):
        # Ensure size is numeric
        try:
            size_val = int(size)
        except (TypeError, ValueError):
            # Invalid item size; treat as 0
            size_val = 0

        # Clamp negative sizes to 0 (cannot have negative space)
        size_val = max(0, size_val)

        indexed_items.append((size_val, i))

    # Sort by size descending (First Fit Decreasing heuristic)
    indexed_items.sort(reverse=True, key=lambda x: x[0])

    # Track bins: each bin is a list of indices
    bins = []
    bin_loads = []  # Current load of each bin

    # Place each item
    for size, original_idx in indexed_items:
        # Find first bin with enough space
        placed = False
        for bin_idx in range(len(bins)):
            if bin_loads[bin_idx] + size <= capacity:
                bins[bin_idx].append(original_idx)
                bin_loads[bin_idx] += size
                placed = True
                break

        # If no bin had space, create new bin
        if not placed:
            bins.append([original_idx])
            bin_loads.append(size)

    return bins
