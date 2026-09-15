"""Subject domains and leakage-free train/test splits.

UCI HAR windows are 128 samples with 50% overlap, so shuffling window indices places test
windows next to their overlapping neighbours in the training set. The default
mode="segment" assigns whole contiguous recording segments to one side and then drops any
test window that still overlaps a training window. mode="window" is the naive shuffled
split, kept for comparison.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

SubjectSpec = int | list[int]


def load_npz(path: str | Path) -> dict[str, np.ndarray]:
    d = np.load(path, allow_pickle=False)
    return {k: d[k] for k in d.files}


def _as_list(spec: SubjectSpec) -> list[int]:
    return [int(spec)] if isinstance(spec, (int, np.integer)) else [int(s) for s in spec]


def get_domain(
    npz: dict[str, np.ndarray], subject_id: SubjectSpec
) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(X, y)`` for one subject, or for a group of subjects."""
    wanted = _as_list(subject_id)
    known = set(npz["subject"].tolist())
    missing = [s for s in wanted if s not in known]
    if missing:
        raise ValueError(f"subject(s) {missing} not present; available: {sorted(known)}")
    mask = np.isin(npz["subject"], wanted)
    return npz["X"][mask], npz["y"][mask]


def subjects_of(npz: dict[str, np.ndarray], subject_id: SubjectSpec) -> set[int]:
    return set(_as_list(subject_id))


OVERLAP_TOL = 1e-6


def windows_overlap(a: np.ndarray, b: np.ndarray, tol: float = OVERLAP_TOL) -> bool:
    """True if two ``(C, T)`` windows share half their samples in either direction."""
    half = a.shape[-1] // 2
    return bool(
        np.allclose(a[:, half:], b[:, :half], atol=tol)
        or np.allclose(a[:, :half], b[:, half:], atol=tol)
    )


def segment_ids(X: np.ndarray, y: np.ndarray, tol: float = OVERLAP_TOL) -> np.ndarray:
    """Assign each window to a contiguous recording segment.

    A new segment starts when the label changes or consecutive windows stop overlapping.
    """
    n, _, t = X.shape
    half = t // 2
    seg = np.zeros(n, dtype=np.int64)
    cur = 0
    for i in range(1, n):
        contiguous = y[i] == y[i - 1] and np.allclose(X[i - 1][:, half:], X[i][:, :half], atol=tol)
        if not contiguous:
            cur += 1
        seg[i] = cur
    return seg


def _purge_overlapping(Xtr: np.ndarray, Xte: np.ndarray, tol: float = OVERLAP_TOL) -> np.ndarray:
    """Boolean keep-mask over test windows that overlap no training window."""
    half = Xtr.shape[-1] // 2
    tr_head = Xtr[:, :, :half].reshape(len(Xtr), -1)
    tr_tail = Xtr[:, :, half:].reshape(len(Xtr), -1)
    keep = np.ones(len(Xte), dtype=bool)
    for i, w in enumerate(Xte):
        head = w[:, :half].reshape(1, -1)
        tail = w[:, half:].reshape(1, -1)
        if (np.abs(tr_head - tail).max(axis=1) <= tol).any() or (
            np.abs(tr_tail - head).max(axis=1) <= tol
        ).any():
            keep[i] = False
    return keep


def train_test_split_domain(
    X: np.ndarray,
    y: np.ndarray,
    ratio: float = 0.2,
    seed: int = 42,
    mode: str = "segment",
    purge: bool | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Stratified split within one domain.

    Args:
        ratio: target test fraction. In segment mode whole segments are assigned, so the
            realised fraction is coarser (about 0.27 at ratio=0.2 on UCI HAR).
        seed: shuffle seed; the split is deterministic given the seed.
        mode: "segment" (default, no overlap leakage) or "window" (shuffled indices).
        purge: drop test windows that overlap a training window. Defaults to True in
            segment mode and False in window mode.
    """
    if not 0.0 < ratio < 1.0:
        raise ValueError(f"ratio must lie in (0, 1), got {ratio}")
    if purge is None:
        purge = mode == "segment"
    if mode not in ("segment", "window"):
        raise ValueError(f"mode must be 'segment' or 'window', got {mode!r}")
    rng = np.random.default_rng(seed)

    if mode == "window":
        test_idx: list[np.ndarray] = []
        train_idx: list[np.ndarray] = []
        for cls in np.unique(y):
            idx = np.flatnonzero(y == cls)
            rng.shuffle(idx)
            n_test = max(1, int(round(ratio * len(idx))))
            if n_test >= len(idx):
                n_test = len(idx) - 1
            test_idx.append(idx[:n_test])
            train_idx.append(idx[n_test:])
        tr = np.sort(np.concatenate(train_idx))
        te = np.sort(np.concatenate(test_idx))
    else:
        seg = segment_ids(X, y)
        tr_parts: list[np.ndarray] = []
        te_parts: list[np.ndarray] = []
        for cls in np.unique(y):
            cls_mask = y == cls
            segs = np.unique(seg[cls_mask])
            rng.shuffle(segs)
            n_cls = int(cls_mask.sum())
            target = ratio * n_cls
            taken, chosen = 0, []
            for sg in segs:
                if taken >= target or len(chosen) == len(segs) - 1:
                    break
                chosen.append(sg)
                taken += int((seg == sg).sum())
            te_mask = cls_mask & np.isin(seg, chosen)
            # A class recorded as a single segment cannot be split without emptying one side.
            if not te_mask.any() or not (cls_mask & ~te_mask).any():
                raise ValueError(
                    f"class {int(cls)} has {len(segs)} contiguous segment(s); cannot make a "
                    f"segment-level train/test split without dropping one side. Use more "
                    f"data for this domain, or mode='window' with its documented leakage."
                )
            tr_parts.append(np.flatnonzero(cls_mask & ~te_mask))
            te_parts.append(np.flatnonzero(te_mask))
        tr = np.sort(np.concatenate(tr_parts))
        te = np.sort(np.concatenate(te_parts))

    assert len(np.intersect1d(tr, te)) == 0
    Xtr, ytr, Xte, yte = X[tr], y[tr], X[te], y[te]

    if purge and len(Xte) and len(Xtr):
        keep = _purge_overlapping(Xtr, Xte)
        Xte, yte = Xte[keep], yte[keep]
    if len(Xte) == 0:
        raise ValueError("split left an empty test set after purging overlapping windows")
    return Xtr, ytr, Xte, yte
