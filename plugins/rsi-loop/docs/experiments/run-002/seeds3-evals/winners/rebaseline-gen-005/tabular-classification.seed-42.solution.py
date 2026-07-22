def predict(train: list[list[float]], test: list[list[float]]) -> list[int]:
    """Train on `train` and return one predicted label (0 or 1) per test row.

    Uses deterministic local search: start with greedy k-NN, then refine by
    learning feature weights that minimize training error via greedy hill climbing.
    """
    if not train:
        return [0] * len(test)

    # Extract features and labels
    train_features = [row[:-1] for row in train]
    train_labels = [row[-1] for row in train]
    n_features = len(train_features[0])

    # Weighted Euclidean distance
    def distance(p1, p2, weights):
        return sum(w * (a - b) ** 2 for w, a, b in zip(weights, p1, p2)) ** 0.5

    # Evaluate accuracy with given k and feature weights (leave-one-out CV)
    def evaluate(k, weights):
        if k > len(train_features) - 1:
            k = len(train_features) - 1
        correct = 0
        for i in range(len(train_features)):
            test_feat = train_features[i]
            true_label = train_labels[i]

            # Leave-one-out: find k nearest neighbors excluding the point itself
            distances = [
                (distance(test_feat, train_features[j], weights), train_labels[j])
                for j in range(len(train_features))
                if j != i
            ]
            distances.sort()
            nearest_k = distances[:k]
            votes = [label for _, label in nearest_k]
            pred = 1 if sum(votes) > len(votes) / 2 else 0
            if pred == true_label:
                correct += 1

        return correct / len(train_features)

    # Phase 1: Find best k with uniform weights
    best_k = 5
    best_accuracy = -1.0
    uniform_weights = [1.0] * n_features

    for k_candidate in [1, 3, 5, 7, 9, 11, 13, 15]:
        accuracy = evaluate(k_candidate, uniform_weights)
        if accuracy > best_accuracy:
            best_accuracy = accuracy
            best_k = k_candidate

    # Phase 2: Local search over feature weights (greedy hill climbing)
    weights = list(uniform_weights)
    improved = True
    iteration = 0

    while improved and iteration < 3:
        improved = False
        iteration += 1
        current_accuracy = evaluate(best_k, weights)

        # Try perturbing each feature weight
        for feat_idx in range(n_features):
            best_scale = 1.0
            best_scale_accuracy = current_accuracy

            # Try scaling this feature
            for scale_factor in [0.4, 0.6, 0.8, 1.0, 1.2, 1.5, 2.0, 2.5]:
                new_weights = list(weights)
                new_weights[feat_idx] = max(0.001, weights[feat_idx] * scale_factor)
                weight_sum = sum(new_weights)
                new_weights = [w / weight_sum for w in new_weights]

                new_accuracy = evaluate(best_k, new_weights)
                if new_accuracy > best_scale_accuracy:
                    best_scale_accuracy = new_accuracy
                    best_scale = scale_factor
                    improved = True

            # Apply best scale
            if best_scale != 1.0:
                weights[feat_idx] = max(0.001, weights[feat_idx] * best_scale)
                weight_sum = sum(weights)
                weights = [w / weight_sum for w in weights]

    # Phase 3: Fine-tune k given learned weights
    best_k_final = best_k
    best_accuracy_final = evaluate(best_k, weights)

    for k_candidate in [1, 3, 5, 7, 9, 11, 13, 15, 17]:
        accuracy = evaluate(k_candidate, weights)
        if accuracy > best_accuracy_final:
            best_accuracy_final = accuracy
            best_k_final = k_candidate

    # Final prediction using best k and learned weights
    predictions = []
    for test_point in test:
        # Compute distances to all training points
        distances = [
            (distance(test_point, train_feat, weights), label)
            for train_feat, label in zip(train_features, train_labels)
        ]
        # Sort by distance, take k nearest
        distances.sort()
        best_k_clamped = min(best_k_final, len(distances))
        nearest_k = distances[:best_k_clamped]
        # Majority vote
        votes = [label for _, label in nearest_k]
        prediction = 1 if sum(votes) > len(votes) / 2 else 0
        predictions.append(prediction)

    return predictions
