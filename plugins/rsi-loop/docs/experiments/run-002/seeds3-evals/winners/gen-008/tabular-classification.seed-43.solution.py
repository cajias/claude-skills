def predict(train: list[list[float]], test: list[list[float]]) -> list[int]:
    """Weighted k-NN with local search over feature weights."""

    train_features = [row[:-1] for row in train]
    train_labels = [row[-1] for row in train]

    if not train_features:
        return [0] * len(test)

    nf = len(train_features[0])

    # Normalize features
    fmin = [float('inf')] * nf
    fmax = [float('-inf')] * nf

    for row in train_features:
        for i in range(nf):
            fmin[i] = min(fmin[i], row[i])
            fmax[i] = max(fmax[i], row[i])

    def norm(row):
        return [(row[i] - fmin[i]) / (fmax[i] - fmin[i] + 1e-10) for i in range(nf)]

    ntrain = [norm(row) for row in train_features]
    ntest = [norm(row) for row in test]

    # Start with unit weights
    w = [1.0] * nf
    best_w = w[:]
    best_acc = eval_sample(ntrain, train_labels, w, 5)
    best_k = 5

    # Try different k and search for better weights
    for k in [5, 3, 7]:
        cur_w = [1.0] * nf
        cur_acc = eval_sample(ntrain, train_labels, cur_w, k)

        # Local search with iterations
        for itr in range(5):
            upd = False

            for fi in range(nf):
                for d in [1.0, 0.5, -0.5, 2.0, -1.0, 0.3]:
                    cand_w = cur_w[:]
                    cand_w[fi] = max(0.1, cand_w[fi] + d)
                    acc = eval_sample(ntrain, train_labels, cand_w, k)

                    if acc > cur_acc:
                        cur_acc = acc
                        cur_w = cand_w
                        upd = True
                        break

                if upd:
                    break

            if not upd:
                break

        if cur_acc > best_acc:
            best_acc = cur_acc
            best_w = cur_w[:]
            best_k = k

    # Refinement pass: fine-tune best weights
    refine_w = best_w[:]
    refine_acc = best_acc
    for itr in range(3):
        upd = False
        for fi in range(nf):
            for d in [0.2, -0.2, 0.1, -0.1]:
                cand_w = refine_w[:]
                cand_w[fi] = max(0.1, cand_w[fi] + d)
                acc = eval_sample(ntrain, train_labels, cand_w, best_k)
                if acc > refine_acc:
                    refine_acc = acc
                    refine_w = cand_w
                    upd = True
                    break
            if upd:
                break
        if not upd:
            break
    best_w = refine_w

    # Predict
    out = []
    for tpt in ntest:
        dsts = []
        for tpt2, lbl in zip(ntrain, train_labels):
            d = sum((tpt[i] - tpt2[i]) ** 2 * best_w[i] for i in range(nf)) ** 0.5
            dsts.append((d, lbl))
        dsts.sort()
        v = sum(1 for _, lbl in dsts[:best_k] if lbl == 1)
        out.append(1 if v * 2 > best_k else 0)

    return out


def eval_sample(train_features, train_labels, weights, k):
    """Evaluate on all training points (LOO)."""
    c = 0
    t = 0
    n = len(train_features)

    for i in range(n):
        tpt = train_features[i]
        tbl = train_labels[i]

        dsts = []
        for j in range(n):
            if i != j:
                d = sum((tpt[m] - train_features[j][m]) ** 2 * weights[m]
                       for m in range(len(weights))) ** 0.5
                dsts.append((d, train_labels[j]))

        if dsts:
            dsts.sort()
            ku = min(k, len(dsts))
            v = sum(1 for _, lbl in dsts[:ku] if lbl == 1)
            pred = 1 if v * 2 > ku else 0
            if pred == tbl:
                c += 1
            t += 1

    return c / t if t > 0 else 0.5
