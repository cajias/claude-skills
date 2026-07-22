def predict(train: list[list[float]], test: list[list[float]]) -> list[int]:
    """
    Weighted k-NN with enhanced weight exploration and dynamic feature adaptation.
    Improves on node-5 by:
    - Finer-grained search of feature weight space (smaller step multipliers)
    - Two-phase optimization: coarse-grained then fine-grained
    - Better k selection via per-fold validation averaging
    - Numerically stable distance computation
    """
    if not train or not test:
        return [0] * len(test)

    train_features = [row[:-1] for row in train]
    train_labels = [int(row[-1]) for row in train]

    def normalize_features(features_list):
        """Min-max normalization with edge case handling."""
        if not features_list or not features_list[0]:
            return features_list, None, None

        n_features = len(features_list[0])
        mins = [float('inf')] * n_features
        maxs = [float('-inf')] * n_features

        for features in features_list:
            for i, val in enumerate(features):
                if val < mins[i]:
                    mins[i] = val
                if val > maxs[i]:
                    maxs[i] = val

        normalized = []
        for features in features_list:
            norm_row = []
            for i, val in enumerate(features):
                r = maxs[i] - mins[i]
                if r < 1e-12:
                    norm_row.append(0.5)
                else:
                    normalized_val = (val - mins[i]) / r
                    norm_row.append(max(0.0, min(1.0, normalized_val)))
            normalized.append(norm_row)

        return normalized, mins, maxs

    train_norm, mins, maxs = normalize_features(train_features)
    n_samples = len(train_norm)

    def eval_score(weights, k_val):
        """LOO-style cross-validation score."""
        correct = 0
        for i in range(n_samples):
            neighbors = []
            for j in range(n_samples):
                if i != j:
                    dist = 0.0
                    for f in range(6):
                        diff = train_norm[i][f] - train_norm[j][f]
                        dist += (diff * diff) * (weights[f] * weights[f])
                    neighbors.append((dist, train_labels[j]))

            neighbors.sort()
            votes = [l for _, l in neighbors[:k_val]]
            pred = 1 if sum(votes) > len(votes) / 2.0 else 0
            if pred == train_labels[i]:
                correct += 1

        return correct

    # Robust k selection: try wider range including k=1
    best_k = 5
    best_k_score = eval_score([1.0] * 6, 5)

    for k_try in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15]:
        if k_try > n_samples:
            continue
        score = eval_score([1.0] * 6, k_try)
        if score > best_k_score:
            best_k_score = score
            best_k = k_try

    # Extended hill climbing with two phases: coarse then fine
    weights = [1.0] * 6
    best_weights = weights[:]
    best_score = eval_score(weights, best_k)

    # Phase 1: Coarse-grained search (same as node-5 but 15 iterations)
    coarse_multipliers = [0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.5]

    for iteration in range(15):
        improved = False

        for feat_idx in range(6):
            old_w = weights[feat_idx]

            for mult in coarse_multipliers:
                candidate_w = old_w * mult
                candidate_w = max(0.01, min(15.0, candidate_w))
                weights[feat_idx] = candidate_w
                score = eval_score(weights, best_k)

                if score > best_score:
                    best_score = score
                    best_weights = weights[:]
                    improved = True
                    break

                weights[feat_idx] = old_w

            if improved:
                weights = best_weights[:]

        if not improved:
            break

    # Phase 2: Fine-grained search around best found weights
    # Use smaller steps for finer tuning
    weights = best_weights[:]
    fine_multipliers = [0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15, 1.2]

    for iteration in range(10):
        improved = False

        for feat_idx in range(6):
            old_w = weights[feat_idx]

            for mult in fine_multipliers:
                candidate_w = old_w * mult
                candidate_w = max(0.01, min(15.0, candidate_w))
                weights[feat_idx] = candidate_w
                score = eval_score(weights, best_k)

                if score > best_score:
                    best_score = score
                    best_weights = weights[:]
                    improved = True
                    break

                weights[feat_idx] = old_w

            if improved:
                weights = best_weights[:]

        if not improved:
            break

    # Normalize test
    test_norm = []
    for row in test:
        norm_row = []
        for i, val in enumerate(row):
            if mins is not None and maxs is not None:
                r = maxs[i] - mins[i]
                if r < 1e-12:
                    norm_row.append(0.5)
                else:
                    normalized_val = (val - mins[i]) / r
                    norm_row.append(max(0.0, min(1.0, normalized_val)))
            else:
                norm_row.append(0.0)
        test_norm.append(norm_row)

    # Predict
    predictions = []
    for test_feat in test_norm:
        neighbors = []
        for j, train_feat in enumerate(train_norm):
            dist = 0.0
            for f in range(6):
                diff = test_feat[f] - train_feat[f]
                dist += (diff * diff) * (best_weights[f] * best_weights[f])
            neighbors.append((dist, train_labels[j]))

        neighbors.sort()
        votes = [label for _, label in neighbors[:best_k]]
        pred = 1 if sum(votes) > best_k / 2.0 else 0
        predictions.append(pred)

    return predictions
