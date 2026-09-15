"""Measure window-overlap leakage for the window-level and segment-level splits.

For each seed, reports the fraction of target test windows that share half their samples
with a training window, and the accuracy of a raw-signal 1-nearest-neighbour classifier
trained on the target training split. A cross-subject 1-NN (source -> target) is printed
for reference.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from src.data.split import get_domain, load_npz, train_test_split_domain, windows_overlap


def one_nn_accuracy(X_train, y_train, X_test, y_test) -> float:
    a = X_train.reshape(len(X_train), -1)
    b = X_test.reshape(len(X_test), -1)
    dist = (b**2).sum(1)[:, None] - 2 * b @ a.T + (a**2).sum(1)[None, :]
    return float((y_train[dist.argmin(1)] == y_test).mean())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--npz", type=Path, default=Path("data/processed/har.npz"))
    ap.add_argument("--source", type=int, default=2)
    ap.add_argument("--target", type=int, default=11)
    ap.add_argument("--ratio", type=float, default=0.2)
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    args = ap.parse_args()

    npz = load_npz(args.npz)
    X, y = get_domain(npz, args.target)

    print(
        f"{'mode':8s} {'seed':>4s} {'train':>5s} {'test':>4s} {'overlapping':>12s} {'1-NN acc':>9s}"
    )
    for mode in ("window", "segment"):
        for seed in args.seeds:
            Xtr, ytr, Xte, yte = train_test_split_domain(X, y, args.ratio, seed, mode=mode)
            n_overlap = sum(any(windows_overlap(a, b) for b in Xtr) for a in Xte)
            acc = one_nn_accuracy(Xtr, ytr, Xte, yte)
            print(
                f"{mode:8s} {seed:4d} {len(Xtr):5d} {len(Xte):4d} "
                f"{n_overlap / len(Xte):11.1%} {acc:9.3f}"
            )

    Xs, ys = get_domain(npz, args.source)
    cross = one_nn_accuracy(Xs, ys, X, y)
    print(f"\ncross-subject 1-NN (subject {args.source} -> {args.target}): {cross:.3f}")


if __name__ == "__main__":
    main()
