def predict(train: list[list[float]], test: list[list[float]]) -> list[int]:
    """
    k-NN classifier with feature normalization and robust input handling.

    Strategy:
    1. Robust input parsing with lenient handling of None and type coercion
    2. Feature scaling (min-max normalization) for fair distance computation
    3. Deterministic local search for optimal k on normalized data
    4. Inverse-distance-weighted voting with tie-breaking
    5. Graceful fallbacks for malformed input
    """
    if not train or not test:
        return [0] * len(test)

    # Robustly extract training data with lenient parsing
    train_data = []

    for row in train:
        if row is None:
            continue
        try:
            if not hasattr(row, '__len__'):
                continue
            if len(row) < 7:
                continue

            features = []
            for i in range(6):
                val = row[i]
                if val is None:
                    features.append(None)  # Mark as missing for later handling
                else:
                    try:
                        features.append(float(val))
                    except (ValueError, TypeError):
                        features.append(None)

            label_val = row[6]
            if label_val is None:
                continue

            label = int(round(float(label_val)))
            label = max(0, min(1, label))
            train_data.append((features, label))
        except (ValueError, TypeError, IndexError, AttributeError):
            continue

    if not train_data:
        return [0] * len(test)

    # Compute feature statistics for normalization
    # Handle None values by computing min/max over valid values only
    feature_mins = [float('inf')] * 6
    feature_maxs = [float('-inf')] * 6

    for features, _ in train_data:
        for i in range(6):
            if features[i] is not None:
                feature_mins[i] = min(feature_mins[i], features[i])
                feature_maxs[i] = max(feature_maxs[i], features[i])

    # Replace infinities with defaults (if all values for a feature were None)
    for i in range(6):
        if feature_mins[i] == float('inf'):
            feature_mins[i] = 0.0
        if feature_maxs[i] == float('-inf'):
            feature_maxs[i] = 1.0

    # If all values are the same for a feature, set range to 1
    for i in range(6):
        if feature_maxs[i] == feature_mins[i]:
            feature_maxs[i] = feature_mins[i] + 1.0

    # Normalize training features
    normalized_train = []
    for features, label in train_data:
        norm_features = []
        for i in range(6):
            if features[i] is None:
                # Impute None as the midpoint of the range
                norm_features.append(0.5)
            else:
                norm_val = (features[i] - feature_mins[i]) / (feature_maxs[i] - feature_mins[i])
                # Clamp to [0, 1] to handle potential floating-point edge cases
                norm_val = max(0.0, min(1.0, norm_val))
                norm_features.append(norm_val)
        normalized_train.append((norm_features, label))

    train_features = [f for f, _ in normalized_train]
    train_labels = [l for _, l in normalized_train]
    n_samples = len(normalized_train)

    if n_samples < 5:
        k = min(n_samples, 3)
        return knn_predict_normalized(train_features, train_labels, test, k, feature_mins, feature_maxs)

    # Split for hyperparameter tuning (75/25)
    split_idx = int(0.75 * n_samples)
    tune_features = train_features[:split_idx]
    tune_labels = train_labels[:split_idx]
    val_features = train_features[split_idx:]
    val_labels = train_labels[split_idx:]

    # Find best k through local search
    best_k = find_best_k_local_search(tune_features, tune_labels, val_features, val_labels)

    # Make final predictions using best k on full training data
    return knn_predict_normalized(train_features, train_labels, test, best_k, feature_mins, feature_maxs)


def find_best_k_local_search(tune_features, tune_labels, val_features, val_labels):
    """
    Deterministic local search to find optimal k.
    Two-phase approach: coarse grid followed by fine local search.
    """
    if len(tune_features) < 3:
        return 3

    best_k = 5
    best_accuracy = -1.0

    # Phase 1: Coarse grid search (odd values for binary classification)
    for k in range(3, min(len(tune_features), 70), 2):
        accuracy = evaluate_k(tune_features, tune_labels, val_features, val_labels, k)
        if accuracy > best_accuracy:
            best_accuracy = accuracy
            best_k = k

    # Phase 2: Fine local search around best_k (try all integers nearby)
    for k in range(max(3, best_k - 3), min(len(tune_features) + 1, best_k + 4)):
        accuracy = evaluate_k(tune_features, tune_labels, val_features, val_labels, k)
        if accuracy > best_accuracy:
            best_accuracy = accuracy
            best_k = k

    return best_k


def evaluate_k(train_features, train_labels, val_features, val_labels, k):
    """Evaluate k-NN classifier with given k on validation set."""
    if len(val_labels) == 0:
        return 0.0

    correct_count = 0
    for i in range(len(val_features)):
        predicted = knn_classify(train_features, train_labels, val_features[i], k)
        if predicted == val_labels[i]:
            correct_count += 1

    return correct_count / len(val_labels)


def knn_classify(train_features, train_labels, test_point, k):
    """
    Classify a single test point using k-NN with inverse distance weighting.
    Handles numeric precision and tie-breaking robustly.
    """
    # Calculate distances to all training points
    distances = []
    for i, train_point in enumerate(train_features):
        # Euclidean distance (squared for efficiency, then square-rooted for weighting)
        dist_squared = sum((test_point[j] - train_point[j]) ** 2 for j in range(len(test_point)))
        distances.append((dist_squared, train_labels[i]))

    # Sort by distance and keep k nearest neighbors
    distances.sort(key=lambda x: x[0])
    k_nearest = distances[:k]

    # Weighted voting based on inverse distance
    vote_class_0 = 0.0
    vote_class_1 = 0.0

    for dist_squared, label in k_nearest:
        # Compute distance and weight
        distance = dist_squared ** 0.5
        # Use inverse distance as weight, with epsilon for numerical stability
        # epsilon protects against division by zero when test_point == train_point
        weight = 1.0 / (distance + 1e-10)

        if label == 0:
            vote_class_0 += weight
        else:
            vote_class_1 += weight

    # Return class with higher weighted vote
    # In case of exact tie (unlikely due to floating point), default to 0
    return 1 if vote_class_1 > vote_class_0 else 0


def knn_predict_normalized(train_features, train_labels, test, k, feature_mins, feature_maxs):
    """
    Predict with robust input handling and feature normalization.
    Gracefully handles None, malformed, and non-numeric test rows.
    """
    label_counts = [train_labels.count(0), train_labels.count(1)]
    majority_label = 1 if label_counts[1] > label_counts[0] else 0

    predictions = []
    for test_row in test:
        try:
            if test_row is None:
                predictions.append(majority_label)
                continue

            if not hasattr(test_row, '__len__'):
                predictions.append(majority_label)
                continue

            if len(test_row) < 6:
                predictions.append(majority_label)
                continue

            # Parse test features with tolerance for None and type coercion
            features = []
            for i in range(6):
                val = test_row[i]
                if val is None:
                    features.append(None)  # Mark as missing
                else:
                    try:
                        features.append(float(val))
                    except (ValueError, TypeError):
                        features.append(None)

            # Normalize test features using training statistics
            norm_features = []
            for i in range(6):
                if features[i] is None:
                    # Impute None as the midpoint of the training range
                    norm_features.append(0.5)
                else:
                    norm_val = (features[i] - feature_mins[i]) / (feature_maxs[i] - feature_mins[i])
                    # Clamp to [0, 1] to handle outliers gracefully
                    norm_val = max(0.0, min(1.0, norm_val))
                    norm_features.append(norm_val)

            if len(norm_features) < 6:
                predictions.append(majority_label)
                continue

            # Classify using k-NN on normalized features
            pred = knn_classify(train_features, train_labels, norm_features, k)
            predictions.append(pred)

        except Exception:
            predictions.append(majority_label)

    return predictions
