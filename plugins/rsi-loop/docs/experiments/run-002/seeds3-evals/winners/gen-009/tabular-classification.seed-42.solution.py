def predict(train: list[list[float]], test: list[list[float]]) -> list[int]:
    """Robust distance-weighted k-NN with principled feature normalization.

    Strategy:
    1. Robustly parse and normalize all features (handles scale/distribution variation)
    2. Compute feature importance via correlation, with numerical stability
    3. Adaptively select k with conservative default (resists overfitting)
    4. Distance-weighted voting with stable exponential weighting
    5. Graceful fallback for edge cases (empty data, degenerate features, malformed rows)

    Focus: generalization across input distributions and scales via principled
    normalization and conservative heuristics.
    """

    # Edge case: empty input
    if not train or not test:
        return [0] * len(test)

    # Step 1: Robustly extract features and labels
    X_train = []
    y_train = []

    for row in train:
        if len(row) < 7:
            continue
        try:
            # Coerce all to float for robustness
            features = [float(x) for x in row[:6]]
            label = int(row[6])

            # Validate label is 0 or 1
            if label not in (0, 1):
                continue

            X_train.append(features)
            y_train.append(label)
        except (ValueError, TypeError):
            continue

    if not X_train:
        return [0] * len(test)

    n_samples = len(X_train)
    n_features = 6

    # Step 2: Principled feature normalization
    # Compute robust statistics: min/max for scale, mean/std for location
    feature_min = [float('inf')] * n_features
    feature_max = [float('-inf')] * n_features
    feature_sum = [0.0] * n_features
    feature_sum_sq = [0.0] * n_features

    for features in X_train:
        for i in range(n_features):
            val = features[i]
            feature_min[i] = min(feature_min[i], val)
            feature_max[i] = max(feature_max[i], val)
            feature_sum[i] += val
            feature_sum_sq[i] += val * val

    # Compute mean and std for each feature
    feature_mean = [feature_sum[i] / n_samples for i in range(n_features)]
    feature_var = [(feature_sum_sq[i] / n_samples - feature_mean[i] ** 2)
                   for i in range(n_features)]
    feature_std = [var ** 0.5 for var in feature_var]

    # Normalize features using Z-score (mean=0, std=1)
    # This handles scale and distribution variation gracefully
    def normalize_row(row):
        """Z-score normalization using training statistics."""
        normalized = []
        for i in range(n_features):
            val = float(row[i])
            # If std is near zero, use [0, 1] normalization as fallback
            if feature_std[i] > 1e-9:
                norm_val = (val - feature_mean[i]) / feature_std[i]
            elif feature_max[i] > feature_min[i]:
                norm_val = (val - feature_min[i]) / (feature_max[i] - feature_min[i])
            else:
                norm_val = 0.0
            normalized.append(norm_val)
        return normalized

    # Apply normalization to training data
    X_train_normalized = [normalize_row(row) for row in X_train]

    # Step 3: Compute feature importance via correlation
    # Use standardized (normalized) values for more stable correlation computation
    feature_importance = []
    y_mean = sum(y_train) / n_samples
    y_centered = [y - y_mean for y in y_train]
    y_std = (sum(y_c ** 2 for y_c in y_centered) / max(1, n_samples - 1)) ** 0.5

    for feat_idx in range(n_features):
        feat_vals = [X_train_normalized[i][feat_idx] for i in range(n_samples)]
        feat_mean_norm = sum(feat_vals) / n_samples
        feat_centered = [f - feat_mean_norm for f in feat_vals]
        feat_std_norm = (sum(f_c ** 2 for f_c in feat_centered) / max(1, n_samples - 1)) ** 0.5

        # Pearson correlation
        if feat_std_norm > 1e-9 and y_std > 1e-9:
            cov = sum(feat_centered[i] * y_centered[i] for i in range(n_samples)) / max(1, n_samples - 1)
            corr = cov / (feat_std_norm * y_std)
            corr = max(-1.0, min(1.0, corr))  # Clamp to [-1, 1]
        else:
            corr = 0.0

        feature_importance.append(abs(corr))

    # Normalize importance weights
    total_importance = sum(feature_importance)
    if total_importance > 1e-9:
        feature_weights = [imp / total_importance * n_features for imp in feature_importance]
    else:
        # All features equally important if no signal
        feature_weights = [1.0] * n_features

    # Step 4: Define weighted Euclidean distance
    def weighted_euclidean_distance(x1, x2):
        """Weighted L2 distance with feature importance scaling."""
        dist_sq = sum(feature_weights[i] * ((x1[i] - x2[i]) ** 2) for i in range(n_features))
        return dist_sq ** 0.5

    # Step 5: Adaptive k selection (conservative)
    # Use sqrt(n) as principled default; cap at 20 to avoid overfitting
    label_counts = [0, 0]
    for y in y_train:
        label_counts[y] += 1

    k_base = max(3, int(n_samples ** 0.5))

    # If highly imbalanced, use slightly larger k to avoid memorizing minority class
    label_ratio = min(label_counts) / max(1, max(label_counts))
    if label_ratio < 0.25:
        k = min(int(k_base * 1.3), 25)
    else:
        k = min(k_base, 20)

    k = min(k, n_samples - 1)
    k = max(1, k)

    # Step 6: Make predictions with distance-weighted voting
    predictions = []

    for test_row in test:
        # Parse test row robustly
        try:
            test_features = [float(x) for x in test_row[:6]]
        except (ValueError, TypeError, IndexError):
            # If malformed, predict majority class
            pred = 1 if sum(y_train) >= len(y_train) / 2 else 0
            predictions.append(pred)
            continue

        # Normalize test row
        test_normalized = normalize_row(test_features)

        # Compute distances to all training samples
        distances = []
        for i, train_point in enumerate(X_train_normalized):
            d = weighted_euclidean_distance(test_normalized, train_point)
            distances.append((d, i))

        # Sort by distance and get k nearest neighbors
        distances.sort()
        k_nearest = distances[:k]

        # Extract distances for weighting scheme
        nearest_distances = [d for d, _ in k_nearest]

        # Compute median distance for stable weighting
        # This normalizes the exponential decay scale
        median_dist = nearest_distances[len(nearest_distances) // 2]

        # Use a principled weighting scheme:
        # weight = exp(-(d / scale)^2) where scale is chosen adaptively
        # Avoid singularities with small epsilon
        scale = max(median_dist, 1e-9)

        vote_sum = 0.0
        weight_sum = 0.0

        for dist, idx in k_nearest:
            # Exponential decay based on normalized distance
            # This gives more influence to closer neighbors while staying smooth
            normalized_dist = dist / scale
            weight = (2.71828 ** (-normalized_dist ** 2)) + 1e-10

            vote_sum += weight * y_train[idx]
            weight_sum += weight

        # Threshold at 0.5 for final prediction
        if weight_sum > 0:
            avg_vote = vote_sum / weight_sum
        else:
            avg_vote = sum(y_train) / len(y_train)

        prediction = 1 if avg_vote >= 0.5 else 0
        predictions.append(prediction)

    return predictions
