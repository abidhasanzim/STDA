"""Build tests/fixtures/tiny_har.npz, a small stratified subset of UCI HAR for fast tests.

Takes an equal number of windows per (subject, class) cell from subjects 2 and 11, which
gives 192 windows with the default --total 200.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from src.data.split import load_npz


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", type=Path, default=Path("data/processed/har.npz"))
    ap.add_argument("--out", type=Path, default=Path("tests/fixtures/tiny_har.npz"))
    ap.add_argument("--subjects", type=int, nargs="+", default=[2, 11])
    ap.add_argument("--total", type=int, default=200)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    d = load_npz(args.src)
    rng = np.random.default_rng(args.seed)
    n_classes = int(d["y"].max()) + 1
    per_cell = args.total // (len(args.subjects) * n_classes)

    keep: list[np.ndarray] = []
    for s in args.subjects:
        for c in range(n_classes):
            idx = np.flatnonzero((d["subject"] == s) & (d["y"] == c))
            if len(idx) == 0:
                raise SystemExit(f"subject {s} has no class {c}")
            keep.append(rng.choice(idx, size=min(per_cell, len(idx)), replace=False))
    sel = np.sort(np.concatenate(keep))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        args.out,
        X=d["X"][sel].astype(np.float32),
        y=d["y"][sel].astype(np.int64),
        subject=d["subject"][sel].astype(np.int64),
    )
    size_kb = args.out.stat().st_size / 1024
    print(f"[make_tiny_fixture] wrote {args.out}  n={len(sel)}  {size_kb:.0f} KB")
    print(f"    subjects={sorted(set(d['subject'][sel].tolist()))}")
    print(f"    class counts={np.bincount(d['y'][sel], minlength=n_classes).tolist()}")


if __name__ == "__main__":
    main()
