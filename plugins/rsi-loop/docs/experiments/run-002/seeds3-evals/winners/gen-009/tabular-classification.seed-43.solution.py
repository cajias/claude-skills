def predict(train: list[list[float]], test: list[list[float]]) -> list[int]:
    """Train on `train` and return one predicted label (0 or 1) per test row.

    train : rows of [x0, x1, x2, x3, x4, x5, label]  (label is 0 or 1)
    test  : rows of [x0, x1, x2, x3, x4, x5]          (no label)
    return: list of length len(test), each element 0 or 1, in order.
    """

    if not train:
        return [0] * len(test)

    if len(train) == 1:
        return [int(train[0][-1])] * len(test)

    # Extract features and labels
    train_features = [row[:-1] for row in train]
    train_labels = [int(row[-1]) for row in train]

    n_features = len(train_features[0])
    n_train = len(train_features)

    # Normalize features using robust scaling with adaptive epsilon
    feature_min = [float('inf')] * n_features
    feature_max = [float('-inf')] * n_features

    for row in train_features:
        for i, val in enumerate(row):
            feature_min[i] = min(feature_min[i], val)
            feature_max[i] = max(feature_max[i], val)

    # Adaptive epsilon based on global data range
    feature_range = [feature_max[i] - feature_min[i] for i in range(n_features)]
    global_range = max(feature_range) if feature_range else 1.0
    eps = max(1e-14, 1e-10 * max(1.0, global_range))

    for i in range(n_features):
        if feature_max[i] - feature_min[i] < eps:
            feature_max[i] = feature_min[i] + eps

    def normalize_row(row):
        return [(row[i] - feature_min[i]) / (feature_max[i] - feature_min[i])
                for i in range(n_features)]

    norm_train_features = [normalize_row(row) for row in train_features]
    norm_test_features = [normalize_row(row) for row in test]

    def distance(a, b, weights=None):
        if weights is None:
            weights = [1.0] * len(a)
        dist_sq = sum((w * (a[i] - b[i])) ** 2 for i, w in enumerate(weights))
        return dist_sq ** 0.5

    def evaluate_cv(features, labels, weights, k=3):
        correct = 0
        total = len(features)

        for i in range(total):
            test_point = features[i]
            test_label = labels[i]

            distances = []
            for j in range(total):
                if i != j:
                    d = distance(test_point, features[j], weights)
                    distances.append((d, j, labels[j]))

            distances.sort(key=lambda x: (x[0], x[1]))
            k_neighbors = distances[:min(k, len(distances))]

            votes = [label for _, _, label in k_neighbors]
            vote_sum = sum(votes)
            vote_len = len(votes)

            if vote_sum > vote_len / 2.0:
                prediction = 1
            elif vote_sum < vote_len / 2.0:
                prediction = 0
            else:
                prediction = k_neighbors[0][2]

            if prediction == test_label:
                correct += 1

        return correct / total if total > 0 else 0.0

    # Find best k and weights
    best_weights = [1.0] * n_features
    best_k = 5
    best_k_score = 0.0

    # Quick k scan
    for k in [1, 3, 5, 7, 9]:
        k_candidate = min(k, n_train - 1)
        if k_candidate > 0:
            score = evaluate_cv(norm_train_features, train_labels, best_weights, k=k_candidate)
            if score > best_k_score:
                best_k_score = score
                best_k = k_candidate

    best_cv_score = best_k_score

    # Local search with fewer iterations (for speed)
    improved = True
    iterations = 0
    max_iterations = 20

    while improved and iterations < max_iterations:
        improved = False
        iterations += 1

        for feature_idx in range(n_features):
            for multiplier in [0.5, 0.8, 1.2, 1.5, 2.0]:
                test_weights = best_weights[:]
                test_weights[feature_idx] = max(0.1, best_weights[feature_idx] * multiplier)

                score = evaluate_cv(norm_train_features, train_labels, test_weights, k=best_k)
                if score > best_cv_score + 1e-6:
                    best_cv_score = score
                    best_weights = test_weights
                    improved = True
                    break

            if improved:
                break

    # Fine-tune k
    final_k = best_k
    final_k_score = best_cv_score
    for k in range(1, min(16, n_train)):
        score = evaluate_cv(norm_train_features, train_labels, best_weights, k=k)
        if score > final_k_score + 1e-6:
            final_k_score = score
            final_k = k

    # Predict on test set
    predictions = []
    for test_row in norm_test_features:
        distances = []
        for i, train_row in enumerate(norm_train_features):
            d = distance(test_row, train_row, best_weights)
            distances.append((d, i, train_labels[i]))

        distances.sort(key=lambda x: (x[0], x[1]))
        k_neighbors = distances[:final_k]

        votes = [label for _, _, label in k_neighbors]
        vote_sum = sum(votes)
        vote_len = len(votes)

        if vote_sum > vote_len / 2.0:
            prediction = 1
        elif vote_sum < vote_len / 2.0:
            prediction = 0
        else:
            prediction = k_neighbors[0][2]

        predictions.append(prediction)

    return predictions
