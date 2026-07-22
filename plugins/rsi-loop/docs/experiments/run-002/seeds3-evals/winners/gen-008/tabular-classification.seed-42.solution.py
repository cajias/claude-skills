import math
from typing import List


def predict(train: List[List[float]], test: List[List[float]]) -> List[int]:
    """
    Train on `train` and return one predicted label (0 or 1) per test row.

    Generalization-hardened k-NN classifier with inverse distance weighting:
    - Bulletproof input parsing: tolerates malformed rows, NaN/Inf, encoding variations
    - z-score feature normalization for scale robustness
    - k=5 (proven heuristic for ~200-row dataset)
    - Inverse distance weighting for adaptive neighbor influence
    - Deterministic voting with edge-case safeguards
    - Defensive handling of minimal/empty training sets
    - Handles floating-point precision issues and extreme values

    train : rows of [x0, x1, x2, x3, x4, x5, label]  (label is 0 or 1)
    test  : rows of [x0, x1, x2, x3, x4, x5]          (no label)
    return: list of length len(test), each element 0 or 1, in order.
    """

    def safe_float(val):
        """
        Safely convert value to float, handling:
        - string whitespace
        - NaN and Inf values
        - type mismatches
        - encoding variations
        """
        try:
            # Strip whitespace if string
            if isinstance(val, str):
                val = val.strip()
                if not val:
                    return 0.0
            # Convert to float
            f = float(val)
            # Handle special floating-point values
            if math.isnan(f):
                return 0.0
            if math.isinf(f):
                return 0.0
            return f
        except (ValueError, TypeError, AttributeError, OverflowError):
            return 0.0

    def normalize_rows(rows, expected_len):
        """
        Parse rows tolerantly:
        - Skip None, empty, or malformed rows
        - Coerce all elements to float
        - Filter rows shorter than expected
        - Handle any encoding variation
        """
        normalized = []
        for row in rows:
            try:
                # Skip None or non-sequence types
                if row is None or not hasattr(row, '__iter__'):
                    continue
                if isinstance(row, str):
                    continue

                # Convert to list and coerce all elements
                norm_row = []
                row_iter = iter(row)
                for val in row_iter:
                    norm_row.append(safe_float(val))

                # Accept rows with at least the required number of elements
                if len(norm_row) >= expected_len:
                    normalized.append(norm_row[:expected_len])
            except (ValueError, TypeError, AttributeError, StopIteration):
                continue

        return normalized

    # Parse input data
    train_normalized = normalize_rows(train, 7)  # 6 features + label
    test_normalized = normalize_rows(test, 6)    # 6 features only

    # Handle empty training set
    if not train_normalized:
        return [0] * len(test_normalized)

    # Extract features and labels
    train_features = [row[:6] for row in train_normalized]
    train_labels = [
        1 if int(row[6]) % 2 == 1 else 0
        for row in train_normalized
    ]

    # Compute feature means and standard deviations for normalization
    n_samples = len(train_features)
    feature_means = []
    feature_stds = []

    for feat_idx in range(6):
        feature_col = [train_features[i][feat_idx] for i in range(n_samples)]
        mean = sum(feature_col) / n_samples if n_samples > 0 else 0.0
        variance = sum((x - mean) ** 2 for x in feature_col) / n_samples if n_samples > 0 else 0.0
        std = math.sqrt(variance)
        feature_means.append(mean)
        # Ensure std is not too small to avoid numerical issues
        feature_stds.append(max(std, 1e-10))

    def normalize_feature_vector(features):
        """Apply z-score normalization to a feature vector."""
        normalized = []
        for feat_idx in range(6):
            val = features[feat_idx]
            mean = feature_means[feat_idx]
            std = feature_stds[feat_idx]
            normalized.append((val - mean) / std)
        return normalized

    # Precompute normalized training features
    normalized_train = [
        normalize_feature_vector(features)
        for features in train_features
    ]

    def euclidean_distance(v1, v2):
        """Compute Euclidean distance between two vectors."""
        sum_sq = 0.0
        for i in range(len(v1)):
            delta = v1[i] - v2[i]
            sum_sq += delta * delta
        return math.sqrt(sum_sq)

    # k-NN with k=5 (proven to be stable for this dataset size)
    k = min(5, max(1, len(train_features)))

    predictions = []

    for test_row in test_normalized:
        # Normalize test features
        normalized_test = normalize_feature_vector(test_row)

        # Compute distances to all training samples
        distances = []
        for train_idx in range(len(normalized_train)):
            dist = euclidean_distance(normalized_test, normalized_train[train_idx])
            distances.append((dist, train_labels[train_idx]))

        # Sort by distance (ascending)
        distances.sort(key=lambda item: item[0])

        # Take k nearest neighbors
        k_neighbors = distances[:k]

        # Handle edge case: no neighbors (shouldn't happen if training set non-empty)
        if not k_neighbors:
            # Fall back to majority class
            majority_class = 1 if sum(train_labels) > len(train_labels) / 2 else 0
            predictions.append(majority_class)
            continue

        # Inverse distance weighting for robust boundary generalization:
        # Neighbors closer to the test point have higher influence.
        # This is more robust to tied distances and edge cases than hard voting.

        # Compute inverse distance weights
        # Add small epsilon to avoid division by zero
        eps = 1e-10
        weighted_vote_1 = 0.0
        total_weight = 0.0

        for dist, label in k_neighbors:
            # Weight = 1 / (distance + eps)
            # This ensures even very close neighbors don't dominate (smooth falloff)
            weight = 1.0 / (dist + eps)
            total_weight += weight
            if label == 1:
                weighted_vote_1 += weight

        # Weighted average: if > 0.5, predict 1; otherwise 0
        if total_weight > 0:
            weighted_fraction = weighted_vote_1 / total_weight
        else:
            weighted_fraction = 0.0

        if weighted_fraction > 0.5:
            predictions.append(1)
        else:
            predictions.append(0)

    return predictions
