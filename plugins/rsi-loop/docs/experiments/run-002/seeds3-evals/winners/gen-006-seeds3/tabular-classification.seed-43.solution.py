def predict(train: list[list[float]], test: list[list[float]]) -> list[int]:
    """Train on `train` and return one predicted label (0 or 1) per test row.

    train : rows of [x0, x1, x2, x3, x4, x5, label]  (label is 0 or 1)
    test  : rows of [x0, x1, x2, x3, x4, x5]          (no label)
    return: list of length len(test), each element 0 or 1, in order.
    """
    # k-NN classifier: k=5, Euclidean distance, majority vote
    k = 5
    predictions = []

    for test_row in test:
        # Compute Euclidean distance to each training sample
        distances = []
        for train_row in train:
            # Extract features (all but last element which is label)
            train_features = train_row[:-1]
            dist = sum((t - te) ** 2 for t, te in zip(train_features, test_row)) ** 0.5
            label = int(train_row[-1])
            distances.append((dist, label))

        # Sort by distance and take k nearest neighbors
        distances.sort(key=lambda x: x[0])
        k_nearest = distances[:k]

        # Majority vote among k nearest neighbors
        label_counts = {0: 0, 1: 0}
        for _, label in k_nearest:
            label_counts[label] += 1

        # Predict the label with higher count
        pred_label = 1 if label_counts[1] > label_counts[0] else 0
        predictions.append(pred_label)

    return predictions
