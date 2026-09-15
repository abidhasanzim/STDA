"""Convert the raw UCI HAR download into data/processed/har.npz.

The archive holds X (N, 9, 128) unnormalized inertial signals, y (N,) activity labels in
[0, 6) and subject (N,) ids in [1, 30]. The official train and test files are merged;
domains are defined later by subject.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

CHANNELS = [
    "body_acc_x",
    "body_acc_y",
    "body_acc_z",
    "body_gyro_x",
    "body_gyro_y",
    "body_gyro_z",
    "total_acc_x",
    "total_acc_y",
    "total_acc_z",
]

ACTIVITIES = [
    "WALKING",
    "WALKING_UPSTAIRS",
    "WALKING_DOWNSTAIRS",
    "SITTING",
    "STANDING",
    "LAYING",
]

N_CHANNELS = len(CHANNELS)
N_STEPS = 128
N_CLASSES = len(ACTIVITIES)
SAMPLE_RATE_HZ = 50.0


def _load_split(root: Path, split: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    sig_dir = root / split / "Inertial Signals"
    chans = [np.loadtxt(sig_dir / f"{name}_{split}.txt", dtype=np.float32) for name in CHANNELS]
    x = np.stack(chans, axis=1)
    y = np.loadtxt(root / split / f"y_{split}.txt", dtype=np.int64) - 1
    subject = np.loadtxt(root / split / f"subject_{split}.txt", dtype=np.int64)
    return x, y, subject


def parse(raw_root: Path) -> dict[str, np.ndarray]:
    if not raw_root.exists():
        raise SystemExit(f"raw HAR not found at {raw_root}; run scripts/download_har.sh")

    xs, ys, ss = [], [], []
    for split in ("train", "test"):
        x, y, s = _load_split(raw_root, split)
        print(f"[parse_har] {split}: X={x.shape} subjects={sorted(np.unique(s).tolist())}")
        xs.append(x)
        ys.append(y)
        ss.append(s)

    X = np.concatenate(xs, axis=0)
    y = np.concatenate(ys, axis=0)
    subject = np.concatenate(ss, axis=0)

    # Stable sort by subject so the archive layout is deterministic.
    order = np.lexsort((np.arange(len(subject)), subject))
    X, y, subject = X[order], y[order], subject[order]

    assert X.shape[1:] == (N_CHANNELS, N_STEPS), X.shape
    assert y.min() == 0 and y.max() == N_CLASSES - 1
    assert np.isfinite(X).all()
    return {"X": X.astype(np.float32), "y": y.astype(np.int64), "subject": subject.astype(np.int64)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw", type=Path, default=Path("data/raw/UCI HAR Dataset"))
    ap.add_argument("--out", type=Path, default=Path("data/processed/har.npz"))
    args = ap.parse_args()

    d = parse(args.raw)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.out,
        **d,
        channels=np.array(CHANNELS),
        classes=np.array(ACTIVITIES),
        sample_rate_hz=np.array(SAMPLE_RATE_HZ),
    )
    counts = np.bincount(d["y"], minlength=N_CLASSES)
    print(f"[parse_har] wrote {args.out}  X={d['X'].shape}")
    for name, c in zip(ACTIVITIES, counts):
        print(f"    {name:<20s} {c}")


if __name__ == "__main__":
    main()
