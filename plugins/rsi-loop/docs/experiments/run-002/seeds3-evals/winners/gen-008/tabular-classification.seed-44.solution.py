def predict(train: list[list[float]], test: list[list[float]]) -> list[int]:
    """
    Decision tree classifier with margin-aware splitting for robust generalization.

    Strategy:
    1. Build greedy decision tree with information gain
    2. Use margin-based split selection: prefer splits with clear separation
    3. Apply local search to optimize thresholds for robustness
    4. Conservative tie-breaking to reduce brittleness to perturbations

    This improves upon node-3 by:
    - Margin-aware thresholds reduce sensitivity to small input changes
    - Balanced split preferences for more stable boundaries
    - Better tie-breaking for reproducible, robust predictions
    """

    if not train:
        return [0] * len(test)

    # Extract features and labels
    features = [row[:-1] for row in train]
    labels = [row[-1] for row in train]
    n_features = len(features[0]) if features else 0
    n_samples = len(features)

    if n_samples == 0:
        return [0] * len(test)

    # Build decision tree node class
    class Node:
        def __init__(self):
            self.feature = None
            self.threshold = None
            self.left = None
            self.right = None
            self.label = None  # for leaf nodes
            self.indices = []  # training indices in this node

    def compute_entropy(pos_count, neg_count):
        """Compute entropy-like measure for a split"""
        total = pos_count + neg_count
        if total == 0 or pos_count == 0 or neg_count == 0:
            return 0
        p = pos_count / total
        n = neg_count / total
        if p > 0 and n > 0:
            return -(p * (p**0.5) + n * (n**0.5))
        return 0

    def compute_margin(left_indices, right_indices, labels):
        """
        Compute a margin score: how balanced and pure is this split?
        Higher margin = better split (more robust to perturbations).
        Considers both balance and label purity.
        """
        if not left_indices or not right_indices:
            return 0.0

        left_labels = [labels[i] for i in left_indices]
        right_labels = [labels[i] for i in right_indices]

        left_pos = sum(left_labels)
        left_neg = len(left_labels) - left_pos
        right_pos = sum(right_labels)
        right_neg = len(right_labels) - right_pos

        # Purity score: how pure is each side?
        left_purity = max(left_pos, left_neg) / len(left_labels) if left_labels else 0
        right_purity = max(right_pos, right_neg) / len(right_labels) if right_labels else 0
        purity_score = (left_purity + right_purity) / 2

        # Balance score: prefer splits that split data roughly equally
        balance = min(len(left_indices), len(right_indices)) / max(len(left_indices), len(right_indices)) if max(len(left_indices), len(right_indices)) > 0 else 0

        # Combined margin: favor purity more, but balance helps
        margin = purity_score * 0.7 + balance * 0.3
        return margin

    def find_best_split(indices):
        """Find best feature and threshold for a split, preferring robust margins"""
        best_gain = -1
        best_feature = None
        best_threshold = None
        best_margin = 0

        if len(indices) <= 1:
            return None, None, -1

        labels_subset = [labels[i] for i in indices]
        pos_count = sum(labels_subset)
        neg_count = len(labels_subset) - pos_count

        if pos_count == 0 or neg_count == 0:
            return None, None, -1

        parent_entropy = compute_entropy(pos_count, neg_count)

        # Try each feature
        for feat_idx in range(n_features):
            feat_values = sorted(set(features[i][feat_idx] for i in indices))

            # Generate candidate thresholds: unique values + midpoints for robustness
            candidates = []
            for val in feat_values:
                candidates.append(val)
            for i in range(len(feat_values) - 1):
                midpoint = (feat_values[i] + feat_values[i + 1]) / 2
                candidates.append(midpoint)

            for threshold in candidates:
                left_indices = [i for i in indices if features[i][feat_idx] < threshold]
                right_indices = [i for i in indices if features[i][feat_idx] >= threshold]

                if not left_indices or not right_indices:
                    continue

                left_labels = [labels[i] for i in left_indices]
                right_labels = [labels[i] for i in right_indices]

                left_pos = sum(left_labels)
                right_pos = sum(right_labels)
                left_neg = len(left_labels) - left_pos
                right_neg = len(right_labels) - right_pos

                left_entropy = compute_entropy(left_pos, left_neg)
                right_entropy = compute_entropy(right_pos, right_neg)

                weighted_entropy = (len(left_indices) * left_entropy +
                                    len(right_indices) * right_entropy) / len(indices)

                gain = parent_entropy - weighted_entropy
                margin = compute_margin(left_indices, right_indices, labels)

                # Prefer high gain, then high margin for robustness
                if gain > best_gain or (abs(gain - best_gain) < 1e-10 and margin > best_margin):
                    best_gain = gain
                    best_feature = feat_idx
                    best_threshold = threshold
                    best_margin = margin

        return best_feature, best_threshold, best_gain

    def build_tree(indices, depth=0):
        """Recursively build decision tree"""
        node = Node()
        node.indices = indices[:]

        # Leaf condition: conservative stopping to reduce overfitting
        if len(indices) <= 5 or depth >= 6:
            labels_subset = [labels[i] for i in indices]
            node.label = 1 if sum(labels_subset) > len(labels_subset) / 2 else 0
            return node

        feature, threshold, gain = find_best_split(indices)

        if feature is None or gain <= 0:
            labels_subset = [labels[i] for i in indices]
            node.label = 1 if sum(labels_subset) > len(labels_subset) / 2 else 0
            return node

        node.feature = feature
        node.threshold = threshold

        left_indices = [i for i in indices if features[i][feature] < threshold]
        right_indices = [i for i in indices if features[i][feature] >= threshold]

        node.left = build_tree(left_indices, depth + 1)
        node.right = build_tree(right_indices, depth + 1)

        return node

    root = build_tree(list(range(n_samples)))

    def predict_sample(node, feat_list):
        """Predict label for a sample"""
        if node.label is not None:
            return node.label

        if node.feature is None or node.feature >= len(feat_list):
            # Fallback: return default label
            return 0

        if feat_list[node.feature] < node.threshold:
            return predict_sample(node.left, feat_list)
        else:
            return predict_sample(node.right, feat_list)

    def compute_accuracy(node):
        """Compute accuracy of tree on training data"""
        if not node.indices:
            return 0.0
        correct = sum(1 for i in node.indices
                      if predict_sample(root, features[i]) == labels[i])
        return correct / len(node.indices)

    def get_all_nodes(node):
        """Collect all nodes in tree"""
        if node is None:
            return []
        result = [node]
        if node.left:
            result.extend(get_all_nodes(node.left))
        if node.right:
            result.extend(get_all_nodes(node.right))
        return result

    # Local search: iteratively optimize thresholds for robustness
    all_nodes = get_all_nodes(root)

    for iteration in range(3):
        improved_any = False

        for node in all_nodes:
            if node.label is not None or node.feature is None:
                continue

            feature_idx = node.feature
            candidate_thresholds = sorted(set(
                features[i][feature_idx] for i in node.indices
            ))

            # Add midpoints for robustness
            robust_candidates = list(candidate_thresholds)
            for i in range(len(candidate_thresholds) - 1):
                midpoint = (candidate_thresholds[i] + candidate_thresholds[i + 1]) / 2
                robust_candidates.append(midpoint)
            robust_candidates = sorted(set(robust_candidates))

            best_accuracy = compute_accuracy(node)
            best_threshold = node.threshold
            best_margin = 0.0

            for new_threshold in robust_candidates:
                if abs(new_threshold - node.threshold) < 1e-10:
                    continue

                node.threshold = new_threshold
                accuracy = compute_accuracy(node)

                left_indices = [i for i in node.indices if features[i][feature_idx] < new_threshold]
                right_indices = [i for i in node.indices if features[i][feature_idx] >= new_threshold]
                margin = compute_margin(left_indices, right_indices, labels)

                # Accept if better accuracy, or same accuracy but better margin
                if accuracy > best_accuracy or (abs(accuracy - best_accuracy) < 1e-10 and margin > best_margin):
                    best_accuracy = accuracy
                    best_threshold = new_threshold
                    best_margin = margin
                    improved_any = True

            node.threshold = best_threshold

        if not improved_any:
            break

    # Make predictions on test data
    predictions = []
    for test_row in test:
        try:
            # Robust parsing: handle various input formats
            feat_list = [float(x) for x in test_row[:n_features]]
            # Pad with zeros if too short
            while len(feat_list) < n_features:
                feat_list.append(0.0)
            pred = predict_sample(root, feat_list)
            predictions.append(pred)
        except (ValueError, TypeError, IndexError):
            # Fallback: return majority class from training
            predictions.append(1 if sum(labels) > len(labels) / 2 else 0)

    return predictions
