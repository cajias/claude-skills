def predict(train: list[list[float]], test: list[list[float]]) -> list[int]:
    """Hybrid k-NN: k=3 vs k=7 with three-way selection including k=5.

    Evaluates three k values (3, 5, 7) using majority voting and selects
    the prediction with highest confidence. Ties favor larger k for smoothing.
    """

    if not train:
        return [0] * len(test)

    X_train = [row[:-1] for row in train]
    y_train = [int(row[-1]) for row in train]
    n_features = len(X_train[0])

    predictions = []

    for test_row in test:
        # Compute distances to all training rows
        distances = []
        for i, x in enumerate(X_train):
            dist = sum((test_row[j] - x[j]) ** 2 for j in range(n_features)) ** 0.5
            distances.append((dist, y_train[i]))

        distances.sort(key=lambda x: x[0])

        # k=3: aggressive, tight neighborhoods
        votes_k3 = sum(label for _, label in distances[:3])
        pred_k3 = 1 if votes_k3 >= 2 else 0
        conf_k3 = abs(votes_k3 - 1.5) / 1.5

        # k=5: middle ground
        votes_k5 = sum(label for _, label in distances[:5])
        pred_k5 = 1 if votes_k5 >= 3 else 0
        conf_k5 = abs(votes_k5 - 2.5) / 2.5

        # k=7: smooth, larger neighborhoods
        votes_k7 = sum(label for _, label in distances[:7])
        pred_k7 = 1 if votes_k7 >= 4 else 0
        conf_k7 = abs(votes_k7 - 3.5) / 3.5

        # Select prediction with highest confidence
        # Tie-breaking: prefer larger k for stability
        max_conf = max(conf_k3, conf_k5, conf_k7)
        if conf_k7 == max_conf:
            predictions.append(pred_k7)
        elif conf_k5 == max_conf:
            predictions.append(pred_k5)
        else:
            predictions.append(pred_k3)

    return predictions
