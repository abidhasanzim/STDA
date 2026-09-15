"""Source and target loaders for the domain adaptation setting.

build_loaders returns source_train, source_test, target_train (used without labels during
adaptation) and target_test (evaluation), plus target_train_ordered, an unshuffled copy of
target_train used for pseudo-labels. Loaders yield raw signals; normalization happens inside
the model with statistics fit on source_train.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader

from src.data.dataset import TSDataset
from src.data.normalize import fit_scaler
from src.data.split import get_domain, load_npz, subjects_of, train_test_split_domain


@dataclass
class DomainBundle:
    """The loaders plus the source-fit scaler and split bookkeeping."""

    source_train: DataLoader
    source_test: DataLoader
    target_train: DataLoader
    target_train_ordered: DataLoader
    target_test: DataLoader
    scaler: dict[str, np.ndarray]
    source_subjects: set[int]
    target_subjects: set[int]
    n_classes: int
    n_channels: int
    n_steps: int
    split_mode: str = "segment"

    def __getitem__(self, key: str) -> DataLoader:
        return getattr(self, key)

    def loader_names(self) -> tuple[str, ...]:
        return ("source_train", "source_test", "target_train", "target_test")

    def sizes(self) -> dict[str, int]:
        return {k: len(self[k].dataset) for k in self.loader_names()}


def _loader(
    X, y, batch_size: int, shuffle: bool, seed: int, return_index: bool = False
) -> DataLoader:
    g = torch.Generator()
    g.manual_seed(seed)
    return DataLoader(
        TSDataset(X, y, return_index=return_index),
        batch_size=batch_size,
        shuffle=shuffle,
        drop_last=False,
        num_workers=0,
        generator=g if shuffle else None,
    )


def build_loaders(cfg: dict, poison_fn=None, target_train_index: bool = False) -> DomainBundle:
    """Build the source and target loaders.

    Args:
        cfg: data config with npz_path, source_subject, target_subject, batch_size,
            test_ratio, seed and an optional split_mode.
        poison_fn: optional (X, y) -> (X, y) applied to the source training split before
            the scaler is fit.
    """
    npz = load_npz(Path(cfg["npz_path"]))
    seed = int(cfg.get("seed", 42))
    ratio = float(cfg.get("test_ratio", 0.2))
    bs = int(cfg.get("batch_size", 32))

    src_subj, tgt_subj = cfg["source_subject"], cfg["target_subject"]
    overlap = subjects_of(npz, src_subj) & subjects_of(npz, tgt_subj)
    if overlap:
        raise ValueError(f"source and target domains share subjects {sorted(overlap)}")

    Xs, ys = get_domain(npz, src_subj)
    Xt, yt = get_domain(npz, tgt_subj)
    # Windows overlap by 50%, so split by recording segment by default (see split.py).
    split_mode = str(cfg.get("split_mode", "segment"))
    if split_mode == "window":
        warnings.warn(
            "split_mode='window' shuffles window indices and LEAKS through 50% window "
            "overlap; numbers produced with it are optimistic. Use 'segment'.",
            stacklevel=2,
        )
    Xs_tr, ys_tr, Xs_te, ys_te = train_test_split_domain(Xs, ys, ratio, seed, mode=split_mode)
    Xt_tr, yt_tr, Xt_te, yt_te = train_test_split_domain(Xt, yt, ratio, seed, mode=split_mode)

    if poison_fn is not None:
        Xs_tr, ys_tr = poison_fn(Xs_tr, ys_tr)

    # Fit on the (possibly poisoned) source training split only.
    scaler = fit_scaler(Xs_tr)

    return DomainBundle(
        source_train=_loader(Xs_tr, ys_tr, bs, True, seed),
        source_test=_loader(Xs_te, ys_te, bs, False, seed),
        target_train=_loader(Xt_tr, yt_tr, bs, True, seed + 1, return_index=target_train_index),
        target_train_ordered=_loader(Xt_tr, yt_tr, bs, False, seed),
        target_test=_loader(Xt_te, yt_te, bs, False, seed),
        scaler=scaler,
        source_subjects=subjects_of(npz, src_subj),
        target_subjects=subjects_of(npz, tgt_subj),
        n_classes=int(npz["y"].max()) + 1,
        n_channels=int(Xs.shape[1]),
        n_steps=int(Xs.shape[2]),
        split_mode=split_mode,
    )
