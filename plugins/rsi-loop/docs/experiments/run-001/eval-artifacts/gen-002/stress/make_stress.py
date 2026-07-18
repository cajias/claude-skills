#!/usr/bin/env python3
"""Generate synthetic stress-test instances for bin packing.

This creates a deterministic suite of diverse instances that test various
packing challenges: extreme sizes, various distributions, edge cases, and
pathological inputs that generic heuristics may struggle with.
"""
import json
import random
import os

SEED = 1729
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "instances")

def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def gen_stress_instances():
    """Generate diverse stress instances."""
    rng = random.Random(SEED)
    instances = []

    # 1. Tiny items (all small, test many items in few bins)
    instances.append({
        "name": "stress-tiny-items-100",
        "capacity": 1000,
        "items": [rng.randint(1, 5) for _ in range(100)]
    })

    # 2. Large items (items nearly fill bin, force efficient packing)
    instances.append({
        "name": "stress-large-items-50",
        "capacity": 100,
        "items": [rng.randint(45, 99) for _ in range(50)]
    })

    # 3. Uniform items (capacity 50, items 25 - easy to pack 2 per bin)
    instances.append({
        "name": "stress-uniform-medium-100",
        "capacity": 100,
        "items": [rng.randint(20, 40) for _ in range(100)]
    })

    # 4. Half-capacity items (each item is ~half capacity - limits bin utilization)
    instances.append({
        "name": "stress-half-capacity-80",
        "capacity": 100,
        "items": [rng.randint(48, 52) for _ in range(80)]
    })

    # 5. Triplet distribution (3 clusters)
    triplet_items = []
    for _ in range(40):
        choice = rng.randint(0, 2)
        if choice == 0:
            triplet_items.append(rng.randint(15, 25))
        elif choice == 1:
            triplet_items.append(rng.randint(35, 45))
        else:
            triplet_items.append(rng.randint(55, 65))
    instances.append({
        "name": "stress-triplet-clusters-120",
        "capacity": 100,
        "items": triplet_items
    })

    # 6. Bimodal (small and large)
    bimodal_items = []
    for _ in range(80):
        if rng.random() < 0.6:
            bimodal_items.append(rng.randint(5, 15))
        else:
            bimodal_items.append(rng.randint(75, 95))
    instances.append({
        "name": "stress-bimodal-wide-150",
        "capacity": 100,
        "items": bimodal_items
    })

    # 7. Exponential-ish (1-2 large, rest small)
    exp_items = [rng.randint(85, 99)]
    exp_items.extend([rng.randint(85, 99) for _ in range(2)])
    exp_items.extend([rng.randint(1, 10) for _ in range(97)])
    instances.append({
        "name": "stress-exponential-100",
        "capacity": 100,
        "items": exp_items
    })

    # 8. Items exactly filling capacity (perfect squares)
    instances.append({
        "name": "stress-exact-fit-50",
        "capacity": 100,
        "items": [50] * 50
    })

    # 9. Two-size packing challenge (51 + 49 = 100, or 60 + 40, etc)
    two_size_items = []
    for _ in range(60):
        if rng.random() < 0.5:
            two_size_items.append(51)
        else:
            two_size_items.append(49)
    instances.append({
        "name": "stress-two-size-60",
        "capacity": 100,
        "items": two_size_items
    })

    # 10. Many small with few large (stress FFD)
    mixed_items = [rng.randint(60, 90) for _ in range(30)]
    mixed_items.extend([rng.randint(1, 10) for _ in range(100)])
    instances.append({
        "name": "stress-mixed-many-small-130",
        "capacity": 100,
        "items": mixed_items
    })

    # 11. All same size (200 items of size 25)
    instances.append({
        "name": "stress-all-same-200",
        "capacity": 100,
        "items": [25] * 200
    })

    # 12. Three-segment with tricky ratios
    seg_items = []
    for _ in range(50):
        choice = rng.randint(0, 2)
        if choice == 0:
            seg_items.append(rng.randint(10, 20))
        elif choice == 1:
            seg_items.append(rng.randint(30, 45))
        else:
            seg_items.append(rng.randint(50, 70))
    instances.append({
        "name": "stress-three-segment-150",
        "capacity": 100,
        "items": seg_items
    })

    # 13. Strongly skewed (1-50 with tail to 100)
    skewed_items = [rng.randint(1, 30) for _ in range(120)]
    skewed_items.extend([rng.randint(70, 100) for _ in range(20)])
    instances.append({
        "name": "stress-skewed-140",
        "capacity": 100,
        "items": skewed_items
    })

    # 14. Powers of 2 (1,2,4,8,16,32,64)
    power_items = []
    for _ in range(10):
        power_items.extend([1] * 50)
        power_items.extend([2] * 25)
        power_items.extend([4] * 12)
        power_items.extend([8] * 6)
        power_items.extend([16] * 3)
        power_items.extend([32] * 1)
    instances.append({
        "name": "stress-powers-of-2-97",
        "capacity": 100,
        "items": power_items[:97]
    })

    # 15. Nearly all fit (items ~99, rare smaller items)
    nearly_all_items = [99] * 60
    nearly_all_items.extend([rng.randint(1, 20) for _ in range(20)])
    instances.append({
        "name": "stress-nearly-full-80",
        "capacity": 100,
        "items": nearly_all_items
    })

    # 16. Alternating small/large
    alternating_items = []
    for _ in range(50):
        alternating_items.append(rng.randint(5, 15))
        alternating_items.append(rng.randint(75, 95))
    instances.append({
        "name": "stress-alternating-100",
        "capacity": 100,
        "items": alternating_items
    })

    # 17. Moderate uniform (mid-range)
    instances.append({
        "name": "stress-uniform-moderate-120",
        "capacity": 200,
        "items": [rng.randint(60, 140) for _ in range(120)]
    })

    # 18. Small items with large capacity
    instances.append({
        "name": "stress-small-large-cap-200",
        "capacity": 500,
        "items": [rng.randint(1, 50) for _ in range(200)]
    })

    # 19. Very large capacity, diverse items
    large_cap_items = []
    for _ in range(100):
        choice = rng.randint(0, 3)
        if choice == 0:
            large_cap_items.append(rng.randint(10, 50))
        elif choice == 1:
            large_cap_items.append(rng.randint(100, 200))
        elif choice == 2:
            large_cap_items.append(rng.randint(300, 400))
        else:
            large_cap_items.append(rng.randint(500, 700))
    instances.append({
        "name": "stress-huge-capacity-100",
        "capacity": 1000,
        "items": large_cap_items
    })

    # 20. Boundary case: items just under capacity
    instances.append({
        "name": "stress-just-under-capacity-60",
        "capacity": 100,
        "items": [99] * 60
    })

    # 21. Gap test (items that force specific pairing)
    gap_items = []
    for _ in range(80):
        if rng.random() < 0.5:
            gap_items.append(35)
        else:
            gap_items.append(66)  # 35 + 66 = 101, won't fit; need separate bins
    instances.append({
        "name": "stress-gap-pairing-80",
        "capacity": 100,
        "items": gap_items
    })

    # 22. Geometric sequence (ratios matter)
    geo_items = []
    for _ in range(15):
        geo_items.extend([1, 2, 4, 8, 16, 32])
    instances.append({
        "name": "stress-geometric-90",
        "capacity": 100,
        "items": geo_items
    })

    # 23. Few very large items
    instances.append({
        "name": "stress-few-large-15",
        "capacity": 500,
        "items": [rng.randint(400, 499) for _ in range(15)]
    })

    # 24. Pathological for FFD (sorted decreasing order)
    ffd_bad = []
    ffd_bad.extend([7] * 20)
    ffd_bad.extend([6] * 20)
    ffd_bad.extend([5] * 20)
    ffd_bad.extend([1] * 20)  # Can fit 10-11 size-1 items but hard with larger
    instances.append({
        "name": "stress-ffd-pathological-80",
        "capacity": 20,
        "items": ffd_bad
    })

    # 25. Dense packing challenge (many sizes, high utilization target)
    dense_items = []
    for _ in range(100):
        dense_items.append(rng.randint(10, 45))
    instances.append({
        "name": "stress-dense-challenge-100",
        "capacity": 100,
        "items": dense_items
    })

    return instances

def main():
    ensure_output_dir()
    instances = gen_stress_instances()

    # Write instances.json
    output_path = os.path.join(OUTPUT_DIR, "instances.json")
    with open(output_path, "w") as f:
        json.dump(instances, f, indent=1)

    print(f"Generated {len(instances)} stress instances at {output_path}")
    print(f"Instance names:")
    for inst in instances:
        print(f"  {inst['name']}: {len(inst['items'])} items, capacity {inst['capacity']}")

if __name__ == "__main__":
    main()
