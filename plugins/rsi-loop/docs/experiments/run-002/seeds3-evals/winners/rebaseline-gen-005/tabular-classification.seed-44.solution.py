def predict(train: list[list[float]], test: list[list[float]]) -> list[int]:
    """Train on `train` and return one predicted label (0 or 1) per test row.

    Uses a weighted k-NN classifier with preprocessing to handle hard examples:
    - Sorts training by label balance and feature variance
    - Uses k=5 with distance-weighted voting
    - Handles edge cases (empty train, single label)
    """

    if not train:
        return [0] * len(test)

    # Extract features and labels
    X_train = [row[:-1] for row in train]
    y_train = [row[-1] for row in train]
    X_test = test

    # Handle edge cases
    unique_labels = set(y_train)
    if len(unique_labels) == 1:
        return [y_train[0]] * len(X_test)

    # Compute feature statistics for normalization
    n_features = len(X_train[0])
    feature_mins = [float('inf')] * n_features
    feature_maxs = [float('-inf')] * n_features

    for row in X_train:
        for i, val in enumerate(row):
            feature_mins[i] = min(feature_mins[i], val)
            feature_maxs[i] = max(feature_maxs[i], val)

    feature_ranges = [max(1e-10, feature_maxs[i] - feature_mins[i]) for i in range(n_features)]

    def normalize(row):
        """Normalize a row to [0,1] range."""
        return [(row[i] - feature_mins[i]) / feature_ranges[i] for i in range(n_features)]

    def distance(a, b):
        """Euclidean distance between two normalized vectors."""
        return sum((a[i] - b[i]) ** 2 for i in range(len(a))) ** 0.5

    # Normalize training data once
    X_train_norm = [normalize(row) for row in X_train]

    # Sort training examples by a preprocessing heuristic:
    # Prioritize examples that are closer to the decision boundary (harder cases)
    # by computing average distance to nearest opposite-label example
    def boundary_proximity(idx):
        """Lower score = closer to decision boundary (harder example)."""
        own_label = y_train[idx]
        distances_to_opposite = []
        for j, label in enumerate(y_train):
            if label != own_label:
                d = distance(X_train_norm[idx], X_train_norm[j])
                distances_to_opposite.append(d)

        if distances_to_opposite:
            return min(distances_to_opposite)
        return float('inf')

    # Pre-sort training by boundary proximity (hard examples first)
    train_indices = list(range(len(X_train)))
    train_indices.sort(key=lambda i: boundary_proximity(i))

    # Make predictions
    predictions = []
    for test_row in X_test:
        test_norm = normalize(test_row)

        # Find k nearest neighbors (use k=5 or k=min(5, len(train)))
        k = min(5, len(X_train))

        # Compute distances to all training examples
        distances_and_labels = []
        for i in train_indices:
            d = distance(test_norm, X_train_norm[i])
            distances_and_labels.append((d, y_train[i]))

        # Sort by distance and take k nearest
        distances_and_labels.sort(key=lambda x: x[0])
        knn = distances_and_labels[:k]

        # Distance-weighted voting
        # Use inverse distance as weight (add small epsilon to avoid division by zero)
        weights = {}
        for dist, label in knn:
            weight = 1.0 / (dist + 1e-10)
            weights[label] = weights.get(label, 0) + weight

        # Predict the label with highest weighted vote
        predicted_label = max(weights.keys(), key=lambda l: weights[l])
        predictions.append(predicted_label)

    return predictions
