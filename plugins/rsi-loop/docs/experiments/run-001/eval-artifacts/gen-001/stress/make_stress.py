#!/usr/bin/env python3
"""
Synthetic stress suite generator for bin-packing.
Creates diverse parametric families of instances to stress-test solutions.
"""
import json
import os
import random

SEED = 1729
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "instances")

def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_uniform(rng, n_items, capacity, item_range):
    """Uniform distribution of items."""
    items = [rng.randint(1, item_range) for _ in range(n_items)]
    return items

def generate_clustered(rng, n_items, capacity, n_clusters):
    """Clustered distribution: multiple clusters of similar sizes."""
    items = []
    cluster_size = n_items // n_clusters
    for c in range(n_clusters):
        center = rng.randint(1, capacity - 1)
        radius = min(center // 2, capacity // 4)
        for _ in range(cluster_size):
            item = rng.randint(max(1, center - radius), min(capacity - 1, center + radius))
            items.append(item)
    # Add remaining items
    for _ in range(n_items - len(items)):
        center = rng.randint(1, capacity - 1)
        radius = min(center // 2, capacity // 4)
        item = rng.randint(max(1, center - radius), min(capacity - 1, center + radius))
        items.append(item)
    return items[:n_items]

def generate_bimodal(rng, n_items, capacity):
    """Bimodal: two dominant sizes."""
    items = []
    small = capacity // 3
    large = 2 * capacity // 3
    for i in range(n_items):
        if rng.random() < 0.5:
            items.append(rng.randint(small // 2, small + small // 2))
        else:
            items.append(rng.randint(large // 2, min(capacity - 1, large + large // 2)))
    return items

def generate_skewed(rng, n_items, capacity):
    """Skewed: many small items, few large items."""
    items = []
    small_count = int(0.8 * n_items)
    for _ in range(small_count):
        items.append(rng.randint(1, capacity // 4))
    for _ in range(n_items - small_count):
        items.append(rng.randint(capacity // 2, capacity - 1))
    return items

def generate_near_boundary(rng, n_items, capacity):
    """Near-boundary: items clustered near capacity/2 and capacity-1."""
    items = []
    for i in range(n_items):
        if rng.random() < 0.5:
            items.append(rng.randint(max(1, capacity - capacity // 5), capacity - 1))
        else:
            items.append(rng.randint(max(1, capacity // 2 - capacity // 10), capacity // 2 + capacity // 10))
    return items

def generate_all_same(rng, n_items, capacity):
    """All items the same size."""
    size = capacity // 2
    return [size] * n_items

def generate_power_law(rng, n_items, capacity):
    """Power law distribution: most items small, few very large."""
    items = []
    for _ in range(n_items):
        # Exponential-like distribution
        u = rng.random()
        item = max(1, int(capacity * (u ** 2)))
        items.append(min(item, capacity - 1))
    return items

def generate_mixed(rng, n_items, capacity):
    """Mix of small, medium, and large items."""
    items = []
    third = n_items // 3
    # Small items
    for _ in range(third):
        items.append(rng.randint(1, capacity // 4))
    # Medium items
    for _ in range(third):
        items.append(rng.randint(capacity // 3, 2 * capacity // 3))
    # Large items
    for _ in range(n_items - 2 * third):
        items.append(rng.randint(2 * capacity // 3, capacity - 1))
    return items

def generate_worst_case_first_fit(rng, n_items, capacity):
    """Generate instance that causes First-Fit to perform poorly."""
    # Create items that force suboptimal packing
    items = []
    # Create pattern where greedy approaches fail
    third = capacity // 3
    for _ in range(n_items // 3):
        items.append(third + rng.randint(1, 5))
    for _ in range(n_items // 3):
        items.append(third + rng.randint(1, 5))
    for _ in range(n_items - len(items)):
        items.append(rng.randint(1, third // 2))
    return items

def main():
    ensure_output_dir()
    rng = random.Random(SEED)
    instances = []

    # Very small instances (5-10 items)
    instances.append({
        "name": "stress-tiny-uniform-5",
        "capacity": 50,
        "items": generate_uniform(rng, 5, 50, 40),
    })
    instances.append({
        "name": "stress-tiny-bimodal-8",
        "capacity": 100,
        "items": generate_bimodal(rng, 8, 100),
    })

    # Small instances (15-20 items)
    instances.append({
        "name": "stress-small-uniform-15",
        "capacity": 80,
        "items": generate_uniform(rng, 15, 80, 70),
    })
    instances.append({
        "name": "stress-small-clustered-18",
        "capacity": 120,
        "items": generate_clustered(rng, 18, 120, 3),
    })
    instances.append({
        "name": "stress-small-skewed-20",
        "capacity": 100,
        "items": generate_skewed(rng, 20, 100),
    })
    instances.append({
        "name": "stress-small-same-16",
        "capacity": 100,
        "items": generate_all_same(rng, 16, 100),
    })

    # Medium instances (30-40 items)
    instances.append({
        "name": "stress-medium-uniform-35",
        "capacity": 150,
        "items": generate_uniform(rng, 35, 150, 130),
    })
    instances.append({
        "name": "stress-medium-bimodal-32",
        "capacity": 100,
        "items": generate_bimodal(rng, 32, 100),
    })
    instances.append({
        "name": "stress-medium-clustered-38",
        "capacity": 200,
        "items": generate_clustered(rng, 38, 200, 5),
    })
    instances.append({
        "name": "stress-medium-power-law-40",
        "capacity": 100,
        "items": generate_power_law(rng, 40, 100),
    })
    instances.append({
        "name": "stress-medium-mixed-36",
        "capacity": 180,
        "items": generate_mixed(rng, 36, 180),
    })
    instances.append({
        "name": "stress-medium-boundary-34",
        "capacity": 100,
        "items": generate_near_boundary(rng, 34, 100),
    })

    # Large instances (50-80 items)
    instances.append({
        "name": "stress-large-uniform-60",
        "capacity": 250,
        "items": generate_uniform(rng, 60, 250, 220),
    })
    instances.append({
        "name": "stress-large-bimodal-55",
        "capacity": 150,
        "items": generate_bimodal(rng, 55, 150),
    })
    instances.append({
        "name": "stress-large-clustered-70",
        "capacity": 300,
        "items": generate_clustered(rng, 70, 300, 7),
    })
    instances.append({
        "name": "stress-large-skewed-65",
        "capacity": 200,
        "items": generate_skewed(rng, 65, 200),
    })
    instances.append({
        "name": "stress-large-power-law-75",
        "capacity": 180,
        "items": generate_power_law(rng, 75, 180),
    })
    instances.append({
        "name": "stress-large-mixed-58",
        "capacity": 280,
        "items": generate_mixed(rng, 58, 280),
    })
    instances.append({
        "name": "stress-large-first-fit-hard-62",
        "capacity": 120,
        "items": generate_worst_case_first_fit(rng, 62, 120),
    })

    # Very large instances (100+ items)
    instances.append({
        "name": "stress-xlarge-uniform-100",
        "capacity": 400,
        "items": generate_uniform(rng, 100, 400, 350),
    })
    instances.append({
        "name": "stress-xlarge-bimodal-95",
        "capacity": 250,
        "items": generate_bimodal(rng, 95, 250),
    })
    instances.append({
        "name": "stress-xlarge-clustered-110",
        "capacity": 500,
        "items": generate_clustered(rng, 110, 500, 10),
    })
    instances.append({
        "name": "stress-xlarge-power-law-120",
        "capacity": 300,
        "items": generate_power_law(rng, 120, 300),
    })
    instances.append({
        "name": "stress-xlarge-mixed-105",
        "capacity": 450,
        "items": generate_mixed(rng, 105, 450),
    })

    # Extreme/pathological cases
    instances.append({
        "name": "stress-pathological-identical-40",
        "capacity": 100,
        "items": [60] * 40,
    })
    instances.append({
        "name": "stress-pathological-prime-factors-50",
        "capacity": 97,
        "items": [i % 97 + 1 for i in range(50)],
    })
    instances.append({
        "name": "stress-boundary-single-large-120",
        "capacity": 1000,
        "items": [999] + [1] * 119,
    })

    # Write to file
    output_path = os.path.join(OUTPUT_DIR, "instances.json")
    with open(output_path, "w") as f:
        json.dump(instances, f, indent=1)

    print(f"Generated {len(instances)} stress instances at {output_path}")

if __name__ == "__main__":
    main()
