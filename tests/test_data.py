"""Tests for the data pipeline."""

from __future__ import annotations

import numpy as np
import pytest
import torch
from src.data.loaders import build_loaders
from src.data.normalize import apply_scaler, fit_scaler
from src.data.split import get_domain, load_npz, train_test_split_domain

pytestmark = pytest.mark.fast


@pytest.fixture
def cfg(tiny_har_path):
    return {
        "npz_path": str(tiny_har_path),
        "source_subject": 2,
        "target_subject": 11,
        "batch_size": 16,
        "test_ratio": 0.25,
        "seed": 42,
    }


def test_batch_contract(cfg):
    """Every loader yields (B, 9, 128) float32 with labels in [0, 5]."""
    bundle = build_loaders(cfg)
    for name in bundle.loader_names():
        loader = bundle[name]
        assert len(loader.dataset) > 0, name
        X, y = next(iter(loader))
        assert X.dim() == 3 and X.shape[1:] == (9, 128), f"{name}: {tuple(X.shape)}"
        assert X.dtype == torch.float32, f"{name}: {X.dtype}"
        assert y.dtype == torch.long, f"{name}: {y.dtype}"
        assert X.shape[0] == y.shape[0], name
        assert int(y.min()) >= 0 and int(y.max()) <= 5, f"{name}: labels {y.unique()}"
        assert torch.isfinite(X).all(), name


def test_domains_share_no_subjects(cfg):
    """Source and target domains must not share subjects."""
    bundle = build_loaders(cfg)
    assert bundle.source_subjects & bundle.target_subjects == set()


def test_overlapping_domains_rejected(cfg):
    cfg = {**cfg, "target_subject": 2}
    with pytest.raises(ValueError, match="share subjects"):
        build_loaders(cfg)


def test_no_target_leakage(cfg):
    """The scaler must be fit on source training data only."""
    bundle = build_loaders(cfg)
    npz = load_npz(cfg["npz_path"])

    Xs, ys = get_domain(npz, cfg["source_subject"])
    Xs_tr, _, _, _ = train_test_split_domain(Xs, ys, cfg["test_ratio"], cfg["seed"])
    source_stats = fit_scaler(Xs_tr)

    Xt, _ = get_domain(npz, cfg["target_subject"])
    target_stats = fit_scaler(Xt)

    np.testing.assert_allclose(bundle.scaler["mean"], source_stats["mean"], rtol=0, atol=0)
    np.testing.assert_allclose(bundle.scaler["std"], source_stats["std"], rtol=0, atol=0)
    assert not np.allclose(bundle.scaler["mean"], target_stats["mean"]), (
        "source and target scaler stats are identical — the domain gap or the split is broken"
    )


def test_split_is_stratified_and_disjoint(cfg):
    npz = load_npz(cfg["npz_path"])
    X, y = get_domain(npz, cfg["source_subject"])
    Xtr, ytr, Xte, yte = train_test_split_domain(X, y, 0.25, 42)
    assert len(Xtr) + len(Xte) == len(X)
    assert set(np.unique(ytr)) == set(np.unique(y))
    assert set(np.unique(yte)) == set(np.unique(y))
    # Same seed reproduces the split exactly.
    Xtr2, ytr2, _, _ = train_test_split_domain(X, y, 0.25, 42)
    np.testing.assert_array_equal(ytr, ytr2)
    np.testing.assert_array_equal(Xtr, Xtr2)


def test_scaler_roundtrip_standardizes():
    rng = np.random.default_rng(0)
    X = rng.normal(loc=3.0, scale=2.0, size=(64, 9, 128)).astype(np.float32)
    stats = fit_scaler(X)
    Z = apply_scaler(X, stats)
    np.testing.assert_allclose(Z.mean(axis=(0, 2)), 0.0, atol=1e-5)
    np.testing.assert_allclose(Z.std(axis=(0, 2)), 1.0, atol=1e-5)


def test_scaler_rejects_channel_mismatch():
    stats = fit_scaler(np.zeros((4, 9, 128), dtype=np.float32) + 1.0)
    with pytest.raises(ValueError, match="channels"):
        apply_scaler(np.zeros((4, 3, 128), dtype=np.float32), stats)


def test_no_overlapping_window_leaks_into_the_test_split(cfg):
    """No test window may share samples with a training window.

    HAR windows overlap by 50%, so index-disjoint splits are not enough; this compares the
    samples themselves.
    """
    from src.data.split import windows_overlap

    bundle = build_loaders(cfg)
    for split_a, split_b in (("target_train", "target_test"), ("source_train", "source_test")):
        Xtr = bundle[split_a].dataset.X.numpy()
        Xte = bundle[split_b].dataset.X.numpy()
        leaks = [i for i, a in enumerate(Xte) if any(windows_overlap(a, b) for b in Xtr)]
        assert not leaks, f"{split_b}: {len(leaks)}/{len(Xte)} windows overlap a {split_a} window"


def test_window_mode_is_the_leaky_one_and_says_so(cfg):
    """Window mode leaks at least as much as segment mode and warns."""
    from src.data.split import get_domain, load_npz, train_test_split_domain, windows_overlap

    npz = load_npz(cfg["npz_path"])
    X, y = get_domain(npz, cfg["target_subject"])

    Xtr, _, Xte, _ = train_test_split_domain(X, y, 0.25, 42, mode="window", purge=False)
    leaky = sum(1 for a in Xte if any(windows_overlap(a, b) for b in Xtr))

    Xtr2, _, Xte2, _ = train_test_split_domain(X, y, 0.25, 42, mode="segment")
    clean = sum(1 for a in Xte2 if any(windows_overlap(a, b) for b in Xtr2))

    assert clean == 0, "segment mode must not leak"
    assert leaky >= clean, "window mode is expected to leak at least as much"

    with pytest.warns(UserWarning, match="LEAKS"):
        build_loaders({**cfg, "split_mode": "window"})


def test_segments_are_contiguous_single_label_runs(cfg):
    from src.data.split import get_domain, load_npz, segment_ids

    npz = load_npz(cfg["npz_path"])
    X, y = get_domain(npz, cfg["target_subject"])
    seg = segment_ids(X, y)
    assert seg.min() == 0 and len(np.unique(seg)) > 1
    for s in np.unique(seg):
        m = seg == s
        assert len(np.unique(y[m])) == 1, f"segment {s} spans more than one label"
        assert np.all(np.diff(np.flatnonzero(m)) == 1), f"segment {s} is not contiguous"
