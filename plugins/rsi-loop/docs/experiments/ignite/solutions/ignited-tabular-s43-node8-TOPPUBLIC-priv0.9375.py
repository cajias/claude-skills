def predict(train: list[list[float]], test: list[list[float]]) -> list[int]:
    """Enhanced ensemble: tree + multi-k k-NN with margin-weighted voting.

    Improves on node-7 by:
    1. Using three diverse models (tree, unweighted k-NN, distance-weighted k-NN)
    2. Extending k-NN range: try k=3,5,7,9 to find best unweighted fit
    3. Weighting ensemble votes by prediction margin/confidence
    4. Robust tie-breaking

    Deterministic, standard-library-only, fast.
    """

    if not train:
        return [0] * len(test)

    X_train = [row[:-1] for row in train]
    y_train = [int(row[-1]) for row in train]
    n_features = len(X_train[0])

    # --- Part 1: Train shallow decision tree ---

    def gini(labels):
        if not labels:
            return 0.0
        n = len(labels)
        count_1 = sum(1 for l in labels if l == 1)
        p1 = count_1 / n
        return 1.0 - (p1 ** 2 + (1 - p1) ** 2)

    class TreeNode:
        def __init__(self):
            self.feature = None
            self.threshold = None
            self.left = None
            self.right = None
            self.label = None

    def build_tree(rows, depth):
        if not rows or depth == 0:
            node = TreeNode()
            labels = [int(r[-1]) for r in rows]
            node.label = 1 if sum(labels) > len(labels) / 2 else 0
            return node

        labels = [int(r[-1]) for r in rows]
        if len(set(labels)) == 1:
            node = TreeNode()
            node.label = labels[0]
            return node

        # Greedy split on best feature/threshold
        best_gain = -1
        best_feature = None
        best_threshold = None
        best_left = None
        best_right = None

        for f in range(n_features):
            # Try thresholds: midpoints between consecutive unique values
            vals = sorted(set(r[f] for r in rows))
            thresholds = []
            for i in range(len(vals) - 1):
                thresholds.append((vals[i] + vals[i + 1]) / 2.0)

            for thresh in thresholds:
                left = [r for r in rows if r[f] <= thresh]
                right = [r for r in rows if r[f] > thresh]

                if not left or not right:
                    continue

                left_labels = [int(r[-1]) for r in left]
                right_labels = [int(r[-1]) for r in right]

                # Weighted Gini gain
                n = len(rows)
                weighted_gini = len(left) / n * gini(left_labels) + len(right) / n * gini(right_labels)

                if weighted_gini < best_gain or best_gain < 0:
                    best_gain = weighted_gini
                    best_feature = f
                    best_threshold = thresh
                    best_left = left
                    best_right = right

        if best_feature is None:
            node = TreeNode()
            node.label = 1 if sum(labels) > len(labels) / 2 else 0
            return node

        node = TreeNode()
        node.feature = best_feature
        node.threshold = best_threshold
        node.left = build_tree(best_left, depth - 1)
        node.right = build_tree(best_right, depth - 1)
        return node

    tree = build_tree(train, depth=5)

    def predict_tree(node, sample):
        if node.label is not None:
            return node.label
        if sample[node.feature] <= node.threshold:
            return predict_tree(node.left, sample)
        else:
            return predict_tree(node.right, sample)

    # --- Part 2: Hybrid k-NN with extended range and margin-based weighting ---

    predictions = []

    for test_row in test:
        # Tree prediction with default confidence
        tree_pred = predict_tree(tree, test_row)
        tree_margin = 1.0

        # Compute distances to all training rows
        distances = []
        for i, x in enumerate(X_train):
            dist = sum((test_row[j] - x[j]) ** 2 for j in range(n_features)) ** 0.5
            distances.append((dist, y_train[i]))

        distances.sort(key=lambda x: x[0])

        # k-NN variant 1: unweighted, multi-k (k=3,5,7,9) - select best by margin
        best_knn_unweighted_pred = 0
        best_knn_unweighted_margin = 0.0

        for k_val in [3, 5, 7, 9]:
            neighbors = distances[:k_val]
            votes = sum(label for _, label in neighbors)
            pred = 1 if votes >= k_val / 2.0 else 0
            # Margin: how far from the tie point?
            margin = abs(votes - k_val / 2.0) / (k_val / 2.0)

            if margin > best_knn_unweighted_margin:
                best_knn_unweighted_margin = margin
                best_knn_unweighted_pred = pred

        # k-NN variant 2: distance-weighted k=5
        k_weighted = 5
        neighbors_k5 = distances[:k_weighted]
        weighted_sum = 0.0
        weight_sum = 0.0
        for dist, label in neighbors_k5:
            weight = 1.0 / (dist + 1e-10)
            weighted_sum += weight * label
            weight_sum += weight

        if weight_sum > 0:
            weighted_avg = weighted_sum / weight_sum
            knn_weighted_pred = 1 if weighted_avg >= 0.5 else 0
            knn_weighted_margin = abs(weighted_avg - 0.5)
        else:
            knn_weighted_pred = 0
            knn_weighted_margin = 0.0

        # Margin-weighted ensemble
        ensemble_sum = (tree_pred * tree_margin +
                        best_knn_unweighted_pred * best_knn_unweighted_margin +
                        knn_weighted_pred * knn_weighted_margin)
        total_margin = tree_margin + best_knn_unweighted_margin + knn_weighted_margin

        if total_margin > 0:
            weighted_avg = ensemble_sum / total_margin
            ensemble_pred = 1 if weighted_avg >= 0.5 else 0
        else:
            # Fallback: simple majority vote among the three
            ensemble_pred = 1 if (tree_pred + best_knn_unweighted_pred + knn_weighted_pred) >= 1.5 else 0

        predictions.append(ensemble_pred)

    return predictions
