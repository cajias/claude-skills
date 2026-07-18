#!/usr/bin/env python3
"""Generate a diverse synthetic stress suite for bin packing.

The suite is deterministic (fixed seed) and covers diverse instance families
to test generalization: edge cases, scaling behavior, and various item
distributions (uniform, clustered, bimodal, skewed, near-boundary).
"""

import json
import os
import random

# Fixed seed for deterministic generation
SEED = 1729

# Output directory
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "instances")


def generate_suite():
    """Generate a diverse suite of synthetic instances."""
    rng = random.Random(SEED)
    instances = []

    # 1. Edge cases: very small instances
    instances.append({
        "name": "stress-edge-tiny-1",
        "capacity": 10,
        "items": [5],
    })
    instances.append({
        "name": "stress-edge-tiny-2",
        "capacity": 10,
        "items": [3, 5],
    })
    instances.append({
        "name": "stress-edge-tiny-3",
        "capacity": 10,
        "items": [3, 3, 4],
    })

    # 2. Edge case: items equal to capacity
    instances.append({
        "name": "stress-edge-equal-capacity",
        "capacity": 100,
        "items": [100] * 5 + [50, 50],
    })

    # 3. Small items tightly packed
    instances.append({
        "name": "stress-small-items-20",
        "capacity": 50,
        "items": [rng.randint(1, 10) for _ in range(20)],
    })
    instances.append({
        "name": "stress-small-items-40",
        "capacity": 100,
        "items": [rng.randint(1, 15) for _ in range(40)],
    })

    # 4. Uniform distribution, similar to public instances
    instances.append({
        "name": "stress-uniform-60",
        "capacity": 180,
        "items": [rng.randint(50, 150) for _ in range(60)],
    })
    instances.append({
        "name": "stress-uniform-80",
        "capacity": 200,
        "items": [rng.randint(40, 160) for _ in range(80)],
    })

    # 5. Large instances (2-3x public size)
    instances.append({
        "name": "stress-large-uniform-100",
        "capacity": 250,
        "items": [rng.randint(60, 200) for _ in range(100)],
    })
    instances.append({
        "name": "stress-large-uniform-120",
        "capacity": 300,
        "items": [rng.randint(70, 220) for _ in range(120)],
    })

    # 6. Bimodal: mix of large and small items
    instances.append({
        "name": "stress-bimodal-60",
        "capacity": 150,
        "items": (
            [rng.randint(10, 30) for _ in range(30)]  # Small items
            + [rng.randint(80, 140) for _ in range(30)]  # Large items
        ),
    })
    instances.append({
        "name": "stress-bimodal-100",
        "capacity": 200,
        "items": (
            [rng.randint(10, 40) for _ in range(50)]  # Small items
            + [rng.randint(100, 180) for _ in range(50)]  # Large items
        ),
    })

    # 7. Clustered: items clustered around a few values
    instances.append({
        "name": "stress-clustered-50",
        "capacity": 150,
        "items": (
            [rng.randint(40, 60) for _ in range(25)]  # Cluster 1
            + [rng.randint(80, 120) for _ in range(25)]  # Cluster 2
        ),
    })
    instances.append({
        "name": "stress-clustered-70",
        "capacity": 200,
        "items": (
            [rng.randint(30, 50) for _ in range(25)]  # Cluster 1
            + [rng.randint(70, 90) for _ in range(25)]  # Cluster 2
            + [rng.randint(140, 180) for _ in range(20)]  # Cluster 3
        ),
    })

    # 8. Skewed distribution: many small, few large
    instances.append({
        "name": "stress-skewed-60",
        "capacity": 150,
        "items": (
            [rng.randint(1, 30) for _ in range(50)]  # Many small
            + [rng.randint(80, 140) for _ in range(10)]  # Few large
        ),
    })
    instances.append({
        "name": "stress-skewed-100",
        "capacity": 250,
        "items": (
            [rng.randint(1, 40) for _ in range(80)]  # Many small
            + [rng.randint(100, 200) for _ in range(20)]  # Few large
        ),
    })

    # 9. Near-boundary: items close to capacity
    instances.append({
        "name": "stress-near-boundary-30",
        "capacity": 100,
        "items": [rng.randint(90, 100) for _ in range(30)],
    })
    instances.append({
        "name": "stress-near-boundary-50",
        "capacity": 200,
        "items": [rng.randint(180, 200) for _ in range(50)],
    })

    # 10. Mixed scales: some items large relative to capacity
    instances.append({
        "name": "stress-mixed-scale-70",
        "capacity": 100,
        "items": (
            [rng.randint(1, 20) for _ in range(35)]  # Small
            + [rng.randint(50, 100) for _ in range(35)]  # Large
        ),
    })
    instances.append({
        "name": "stress-mixed-scale-90",
        "capacity": 150,
        "items": (
            [rng.randint(1, 30) for _ in range(45)]  # Small
            + [rng.randint(70, 150) for _ in range(45)]  # Large
        ),
    })

    # 11. Ultra-small items
    instances.append({
        "name": "stress-ultra-small-80",
        "capacity": 1000,
        "items": [rng.randint(1, 5) for _ in range(80)],
    })

    # 12. Extremely large instance (stress scalability)
    instances.append({
        "name": "stress-xlarge-150",
        "capacity": 400,
        "items": [rng.randint(50, 300) for _ in range(150)],
    })

    # 13. Precision test: near-optimal instances
    # Items that pack efficiently with careful placement
    instances.append({
        "name": "stress-precise-60",
        "capacity": 200,
        "items": (
            [100] * 30  # 30 items of size 100
            + [67] * 20  # 20 items of size 67
            + [33] * 10  # 10 items of size 33
        ),
    })

    # 14. Three-way partition: many small, some medium, few large
    instances.append({
        "name": "stress-trimodal-80",
        "capacity": 200,
        "items": (
            [rng.randint(1, 20) for _ in range(40)]  # Many tiny
            + [rng.randint(50, 100) for _ in range(30)]  # Medium
            + [rng.randint(150, 200) for _ in range(10)]  # Few large
        ),
    })

    # 15. Challenging: items just over half capacity
    instances.append({
        "name": "stress-over-half-50",
        "capacity": 100,
        "items": [rng.randint(51, 99) for _ in range(50)],
    })

    # 16. Very skewed: most items tiny, few large
    instances.append({
        "name": "stress-very-skewed-100",
        "capacity": 300,
        "items": (
            [rng.randint(1, 10) for _ in range(80)]
            + [rng.randint(150, 280) for _ in range(20)]
        ),
    })

    # 17. Repeating pattern: same item sizes
    instances.append({
        "name": "stress-uniform-size-40",
        "capacity": 150,
        "items": [30] * 40,
    })

    # 18. Two sizes only
    instances.append({
        "name": "stress-two-sizes-60",
        "capacity": 200,
        "items": [70] * 30 + [50] * 30,
    })

    # 19. Gradually increasing
    instances.append({
        "name": "stress-increasing-50",
        "capacity": 200,
        "items": [(i % 100) + 1 for i in range(50)],
    })

    # 20. Random larger instance
    instances.append({
        "name": "stress-random-130",
        "capacity": 350,
        "items": [rng.randint(30, 280) for _ in range(130)],
    })

    # 21. Tight packing challenge
    instances.append({
        "name": "stress-tight-75",
        "capacity": 150,
        "items": [rng.randint(60, 150) for _ in range(75)],
    })

    # 22. Highly variable sizes
    instances.append({
        "name": "stress-variable-100",
        "capacity": 500,
        "items": [rng.randint(1, 400) for _ in range(100)],
    })

    return instances


def main():
    """Generate and write the stress suite."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    instances = generate_suite()

    # Write as JSON in the same format as public/instances.json
    output_path = os.path.join(OUTPUT_DIR, "instances.json")
    with open(output_path, "w") as f:
        json.dump(instances, f, indent=1)

    print(f"Generated {len(instances)} stress instances at {output_path}")


if __name__ == "__main__":
    main()
