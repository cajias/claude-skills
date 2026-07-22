def predict(train: list[list[float]], test: list[list[float]]) -> list[int]:
    """
    Deterministic local search classifier with robust input handling.

    Strategy:
    1. Tolerant input parsing: handle malformed/None/incomplete rows gracefully
    2. Keep core k-NN with feature importance weights (from node-3, best performer)
    3. Add numerical robustness: safe normalization, avoid division by zero
    4. Iterative refinement of k and feature weights via local search
    """

    # Robust input validation: tolerate None, empty, malformed inputs
    if not train or not test:
        return [0] * len(test) if test else []

    # Parse training data with robustness: skip malformed rows
    train_features = []
    train_labels = []

    for row in train:
        try:
            # Tolerate None, short rows, non-numeric values
            if row is None or len(row) < 7:
                continue
            # Extract 6 features and label, coercing to float/int
            features = []
            for i in range(6):
                try:
                    features.append(float(row[i]))
                except (TypeError, ValueError):
                    features.append(0.0)  # Safe default for bad value

            label = int(float(row[6]))
            train_features.append(features)
            train_labels.append(label)
        except (TypeError, ValueError, IndexError):
            # Skip malformed rows gracefully
            continue

    if not train_features:
        return [0] * len(test)

    # Parse test data robustly
    test_features = []
    for row in test:
        try:
            if row is None or len(row) < 6:
                test_features.append([0.0] * 6)
                continue
            features = []
            for i in range(6):
                try:
                    features.append(float(row[i]))
                except (TypeError, ValueError):
                    features.append(0.0)
            test_features.append(features)
        except (TypeError, ValueError, IndexError):
            test_features.append([0.0] * 6)

    n_features = 6
    if not train_features or not train_labels:
        return [0] * len(test)

    # Compute initial feature importance based on class separation
    # (same as node-3, which achieved 0.855)
    feature_weights = []
    for f in range(n_features):
        pos_vals = []
        neg_vals = []
        for i, features in enumerate(train_features):
            if train_labels[i] == 1:
                pos_vals.append(features[f])
            else:
                neg_vals.append(features[f])

        # Compute separation metric
        if pos_vals and neg_vals:
            pos_mean = sum(pos_vals) / len(pos_vals)
            neg_mean = sum(neg_vals) / len(neg_vals)
            separation = abs(pos_mean - neg_mean)
            # Normalize by range to get relative importance
            all_vals = pos_vals + neg_vals
            val_min = min(all_vals)
            val_max = max(all_vals)
            val_range = max(1e-6, val_max - val_min)
            importance = separation / val_range
        else:
            importance = 0.1

        feature_weights.append(max(0.1, importance))

    # Normalize weights
    total_w = sum(feature_weights)
    if total_w > 1e-10:
        feature_weights = [w / total_w for w in feature_weights]

    # Find best k through local search
    best_k = 5
    best_acc = score_with_params(train_features, train_labels, best_k, feature_weights)

    for k_try in [1, 3, 5, 7, 9, 11, 13, 15]:
        acc = score_with_params(train_features, train_labels, k_try, feature_weights)
        if acc > best_acc:
            best_acc = acc
            best_k = k_try

    # Refine feature weights through grid search and local descent
    best_weights = feature_weights[:]

    # Multiple passes with decreasing step sizes for finer optimization
    for pass_num in range(3):
        step_sizes = [0.2, 0.1, 0.05] if pass_num == 0 else ([0.1, 0.05] if pass_num == 1 else [0.05, 0.02])
        max_iters = 120

        for iteration in range(max_iters):
            improved = False

            for f_idx in range(n_features):
                for step_size in step_sizes:
                    # Try increase
                    new_weights = best_weights[:]
                    new_weights[f_idx] += step_size
                    new_weights[f_idx] = max(0.01, new_weights[f_idx])
                    ws = sum(new_weights)
                    if ws > 1e-10:
                        new_weights = [w / ws for w in new_weights]

                        acc = score_with_params(train_features, train_labels, best_k, new_weights)
                        if acc > best_acc:
                            best_acc = acc
                            best_weights = new_weights[:]
                            improved = True

                    # Try decrease
                    new_weights = best_weights[:]
                    new_weights[f_idx] -= step_size
                    new_weights[f_idx] = max(0.01, new_weights[f_idx])
                    ws = sum(new_weights)
                    if ws > 1e-10:
                        new_weights = [w / ws for w in new_weights]

                        acc = score_with_params(train_features, train_labels, best_k, new_weights)
                        if acc > best_acc:
                            best_acc = acc
                            best_weights = new_weights[:]
                            improved = True

            if not improved:
                break

    # Final refinement pass: re-optimize k with optimized weights
    for k_try in [best_k - 2, best_k - 1, best_k, best_k + 1, best_k + 2]:
        if k_try >= 1:
            acc = score_with_params(train_features, train_labels, k_try, best_weights)
            if acc > best_acc:
                best_acc = acc
                best_k = k_try

    # Generate predictions with best configuration
    predictions = []
    for test_row in test_features:
        pred = knn_predict(train_features, train_labels, test_row, best_k, best_weights)
        predictions.append(pred)

    return predictions


def score_with_params(train_features: list[list[float]], train_labels: list[int],
                      k: int, weights: list[float]) -> float:
    """Evaluate model on training set (leave-one-out style)."""
    correct = 0
    n = len(train_features)

    for i in range(n):
        test_row = train_features[i]
        # Find k nearest neighbors from all training data
        distances = []
        for j in range(n):
            if i != j:  # Exclude self in evaluation
                dist = weighted_distance(test_row, train_features[j], weights)
                distances.append((dist, train_labels[j]))

        if not distances:
            pred = 0
        else:
            distances.sort()
            k_neighbors = min(k, len(distances))
            votes = [label for _, label in distances[:k_neighbors]]
            pred = 1 if sum(votes) > len(votes) / 2.0 else 0

        if pred == train_labels[i]:
            correct += 1

    return correct / float(n) if n > 0 else 0.0


def knn_predict(train_features: list[list[float]], train_labels: list[int],
                test_row: list[float], k: int, weights: list[float]) -> int:
    """Predict label for a test row using k-NN."""
    distances = []
    for i, train_row in enumerate(train_features):
        dist = weighted_distance(test_row, train_row, weights)
        distances.append((dist, train_labels[i]))

    distances.sort()
    k_neighbors = min(k, len(distances))
    votes = [label for _, label in distances[:k_neighbors]]

    if not votes:
        return 0
    return 1 if sum(votes) > len(votes) / 2.0 else 0


def weighted_distance(a: list[float], b: list[float], weights: list[float]) -> float:
    """Compute weighted Euclidean distance with numerical robustness."""
    dist_sq = 0.0
    for i in range(min(len(a), len(b), len(weights))):
        diff = a[i] - b[i]
        dist_sq += (weights[i] * diff * diff)

    # Safe sqrt: avoid issues with numerical precision
    if dist_sq < 0:
        dist_sq = 0.0
    return dist_sq ** 0.5
