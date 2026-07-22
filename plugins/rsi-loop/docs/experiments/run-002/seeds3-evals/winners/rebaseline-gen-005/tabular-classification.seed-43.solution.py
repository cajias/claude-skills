import math
from statistics import mean, median


def predict(train: list[list[float]], test: list[list[float]]) -> list[int]:
    """Train on `train` and return one predicted label (0 or 1) per test row.

    train : rows of [x0, x1, x2, x3, x4, x5, label]  (label is 0 or 1)
    test  : rows of [x0, x1, x2, x3, x4, x5]          (no label)
    return: list of length len(test), each element 0 or 1, in order.

    Weighted k-NN with adaptive local confidence weighting and robust preprocessing.
    Key generalization improvements:
    - Tolerant input parsing with defensive type coercion
    - Robust feature normalization resilient to outliers (quantile-based)
    - Adaptive neighborhood sizing based on local density
    - Confidence-weighted predictions that favor aligned neighbors
    - Deterministic tie-breaking for reproducibility
    """

    if not train:
        return [0] * len(test)

    # Defensive extraction with type coercion and validation
    train_features = []
    train_labels = []
    for row in train:
        if not row or len(row) < 7:
            continue
        try:
            features = []
            for i in range(6):
                if i >= len(row):
                    features.append(0.0)
                else:
                    val = float(row[i])
                    if math.isfinite(val):
                        features.append(val)
                    else:
                        features.append(0.0)
            label = int(row[6])
            if label in (0, 1):
                train_features.append(features)
                train_labels.append(label)
        except (ValueError, TypeError, IndexError):
            continue

    if not train_features or not train_labels:
        return [0] * len(test)

    # Robust normalization using quantile-based scaling (resistant to outliers)
    normalized_train, norm_params = normalize_features_quantile(train_features)
    normalized_test = [normalize_row_quantile(row, norm_params) for row in test]

    # Compute feature importance weights based on discriminative power
    feature_weights = compute_discriminative_weights(normalized_train, train_labels)

    # Sort training data by ambiguity (decision boundary proximity)
    sorted_indices = sort_by_local_confidence(
        normalized_train, train_labels, feature_weights
    )
    sorted_train = [normalized_train[i] for i in sorted_indices]
    sorted_labels = [train_labels[i] for i in sorted_indices]

    # Predict using adaptive confidence-weighted k-NN
    predictions = []
    for test_row in normalized_test:
        # Compute weighted distances to all training points
        distances = []
        for train_idx, train_row in enumerate(sorted_train):
            # Weighted Euclidean distance using feature importance
            dist_sq = sum(
                (feature_weights[j] * (test_row[j] - train_row[j])) ** 2
                for j in range(len(test_row))
            )
            dist = math.sqrt(dist_sq) if dist_sq > 0 else 0.0
            distances.append((dist, train_idx, sorted_labels[train_idx]))

        # Sort by distance (deterministic with index as tie-breaker)
        distances.sort(key=lambda x: (x[0], x[1]))

        # Adaptive k: use locality to determine neighborhood size
        k = compute_adaptive_k(len(sorted_train), distances)

        nearest_k = distances[:k]

        # Confidence-weighted prediction using exponential distance decay
        # Heavily favor very close neighbors
        weighted_sum = 0.0
        weight_sum = 0.0
        epsilon = 1e-10

        for dist, train_idx, label in nearest_k:
            # Exponential weighting: exp(-alpha * dist^2) for smooth falloff
            # Tuned to heavily favor close neighbors while using context from farther ones
            weight = math.exp(-2.0 * dist * dist)
            weighted_sum += weight * label
            weight_sum += weight

        # Predict 1 if weighted average > 0.5, else 0
        # Deterministic: on exact tie, round down
        if weight_sum > epsilon:
            prediction = 1 if (weighted_sum / weight_sum) > 0.5 else 0
        else:
            # Fallback to majority vote if weights are degenerate
            votes = sum(1 for _, _, label in nearest_k if label == 1)
            prediction = 1 if votes > len(nearest_k) / 2 else 0

        predictions.append(prediction)

    return predictions


def normalize_features_quantile(
    features: list[list[float]],
) -> tuple:
    """
    Normalize features using quantile-based scaling (25th and 75th percentiles).
    More robust to outliers than min-max or mean/std normalization.
    Returns: (normalized_features, norm_params)
    """
    if not features:
        return [], []

    n_features = len(features[0]) if features else 0
    if n_features == 0:
        return [], []

    norm_params = []

    # Compute 25th and 75th percentiles for each feature
    for j in range(n_features):
        col = []
        for row in features:
            if j < len(row):
                val = float(row[j])
                if math.isfinite(val):
                    col.append(val)

        if not col or len(col) < 2:
            # No valid values: use safe defaults
            norm_params.append((0.0, 1.0, 0.5))
            continue

        col_sorted = sorted(col)
        n = len(col_sorted)

        # Compute quartiles
        q1_idx = max(0, n // 4)
        q2_idx = max(0, (n + 1) // 2)
        q3_idx = min(n - 1, (3 * n) // 4)

        q1 = col_sorted[q1_idx]
        q2 = col_sorted[q2_idx]  # median
        q3 = col_sorted[q3_idx]

        iqr = q3 - q1
        if iqr < 1e-10:
            iqr = 1.0

        norm_params.append((q1, q3, q2))

    # Normalize: (x - median) / (IQR), clipped to [-1, 1]
    normalized = []
    for row in features:
        norm_row = []
        for j in range(n_features):
            if j >= len(row):
                norm_row.append(0.0)
                continue

            val = float(row[j])
            if not math.isfinite(val):
                norm_row.append(0.0)
                continue

            q1, q3, q2 = norm_params[j]
            iqr = q3 - q1
            if iqr < 1e-10:
                iqr = 1.0

            # Normalize using IQR
            norm_val = (val - q2) / iqr
            # Clip to [-1, 1] for stability
            norm_val = max(-1.0, min(1.0, norm_val))
            norm_row.append(norm_val)

        normalized.append(norm_row)

    return normalized, norm_params


def normalize_row_quantile(row: list[float], norm_params: list) -> list[float]:
    """Normalize a single row using precomputed quantile parameters."""
    if not norm_params:
        return [0.0] * 6

    norm_row = []
    for j in range(len(norm_params)):
        if j >= len(row):
            norm_row.append(0.0)
            continue

        try:
            val = float(row[j])
            if not math.isfinite(val):
                norm_row.append(0.0)
                continue
        except (ValueError, TypeError):
            norm_row.append(0.0)
            continue

        q1, q3, q2 = norm_params[j]
        iqr = q3 - q1
        if iqr < 1e-10:
            iqr = 1.0

        norm_val = (val - q2) / iqr
        norm_val = max(-1.0, min(1.0, norm_val))
        norm_row.append(norm_val)

    return norm_row


def compute_discriminative_weights(
    features: list[list[float]], labels: list[int]
) -> list[float]:
    """
    Compute feature importance weights based on discriminative power.
    Uses Fisher's Linear Discriminant ratio: class separation / within-class variance.
    Features that better separate classes get higher weight.
    """
    if not features or not labels:
        return [1.0] * 6

    n_features = len(features[0]) if features else 6

    # Separate indices by class
    pos_idx = [i for i, l in enumerate(labels) if l == 1]
    neg_idx = [i for i, l in enumerate(labels) if l == 0]

    if not pos_idx or not neg_idx:
        return [1.0] * n_features

    weights = []
    for j in range(n_features):
        # Extract values for each class
        pos_vals = [features[i][j] for i in pos_idx if j < len(features[i])]
        neg_vals = [features[i][j] for i in neg_idx if j < len(features[i])]

        if not pos_vals or not neg_vals:
            weights.append(1.0)
            continue

        # Compute class statistics
        pos_mean = mean(pos_vals)
        neg_mean = mean(neg_vals)
        class_sep = abs(pos_mean - neg_mean)

        # Compute within-class variance
        pos_var = mean((x - pos_mean) ** 2 for x in pos_vals)
        neg_var = mean((x - neg_mean) ** 2 for x in neg_vals)
        within_var = (pos_var + neg_var) / 2.0

        # Fisher ratio: high separation / high within-variance = good feature
        if within_var > 1e-10:
            fisher_ratio = class_sep / math.sqrt(within_var)
        else:
            fisher_ratio = max(0.0, class_sep)

        # Stabilize weights: map Fisher ratio to [0.5, 2.0] range
        # This keeps weights interpretable and prevents extreme values
        weight = 1.0 + (fisher_ratio / 4.0)
        weight = max(0.5, min(2.0, weight))
        weights.append(weight)

    # Normalize to sum to n_features (preserve mean weight of 1.0)
    weight_sum = sum(weights)
    if weight_sum > 0:
        scale = n_features / weight_sum
        weights = [w * scale for w in weights]
    else:
        weights = [1.0] * n_features

    return weights


def sort_by_local_confidence(
    features: list[list[float]],
    labels: list[int],
    feature_weights: list[float],
) -> list[int]:
    """
    Sort training data by local confidence score.
    Points that are well-aligned with their local neighborhood (high confidence)
    are sorted first. This prioritizes examples that are easier to classify correctly,
    which can improve generalization by building on solid decision boundaries first.
    """
    if not features or not labels:
        return list(range(len(features))) if features else []

    n_points = len(features)
    if n_points <= 1:
        return list(range(n_points))

    # Local neighborhood size for confidence calculation
    local_k = min(max(3, n_points // 10), 15)
    confidence_scores = []

    for i in range(n_points):
        # Compute weighted distances to all other points
        distances = []
        for j in range(n_points):
            if i == j:
                dist = 0.0
            else:
                # Weighted Euclidean distance
                dist_sq = sum(
                    (feature_weights[d] * (features[i][d] - features[j][d])) ** 2
                    for d in range(len(features[i]))
                )
                dist = math.sqrt(dist_sq)
            distances.append((dist, j))

        # Sort by distance and take k nearest
        distances.sort(key=lambda x: (x[0], x[1]))
        nearest_indices = [idx for _, idx in distances[:local_k]]

        # Compute local label agreement: what fraction of neighbors agree with this point?
        neighbor_labels = [labels[idx] for idx in nearest_indices if idx < len(labels)]
        if len(neighbor_labels) > 0:
            point_label = labels[i]
            agreement = sum(1 for nl in neighbor_labels if nl == point_label)
            confidence = agreement / len(neighbor_labels)
        else:
            confidence = 0.5

        # Higher confidence = more aligned with local neighborhood
        confidence_scores.append((confidence, i))

    # Sort by confidence DESCENDING: high-confidence points first
    # This prioritizes examples that are well-embedded in their decision boundary
    # Deterministic tie-breaking using index
    confidence_scores.sort(key=lambda x: (-x[0], x[1]))
    return [idx for _, idx in confidence_scores]


def compute_adaptive_k(n_samples: int, distances: list) -> int:
    """
    Compute adaptive k based on training set size and local density.
    Uses the distribution of distances to nearby neighbors to adapt k.
    """
    # Base k: roughly sqrt(n), bounded to [3, 15]
    base_k = max(3, min(15, int(math.sqrt(n_samples))))

    # Adjust based on local density: if distances grow slowly, we can use smaller k
    # If distances grow quickly, we need larger k to capture enough neighbors
    if len(distances) >= base_k + 2:
        # Look at distance to k-th neighbor vs 2*k-th neighbor
        dist_at_k = distances[base_k - 1][0]
        dist_at_2k = distances[min(2 * base_k - 1, len(distances) - 1)][0]

        if dist_at_k > 1e-10:
            density_ratio = dist_at_2k / dist_at_k
            # If distances double quickly (sparse region), use smaller k
            # If distances grow slowly (dense region), use larger k
            if density_ratio > 2.5:
                base_k = max(3, base_k - 2)
            elif density_ratio < 1.5:
                base_k = min(15, base_k + 2)

    return min(base_k, len(distances))
