"""Checkpoint round-trip: weights, config and scaler all survive."""

from __future__ import annotations

import numpy as np
import pytest
import torch
from src.models.model import build_model
from src.utils.checkpoint import load_ckpt, save_ckpt

pytestmark = pytest.mark.fast


def test_roundtrip(tmp_path, tiny_batch):
    x, _ = tiny_batch
    cfg = {
        "data": {"n_channels": 9, "n_classes": 6, "name": "har"},
        "model": {},
        "train": {"epochs": 1},
    }
    scaler = {
        "mean": np.linspace(-1, 1, 9).astype(np.float32),
        "std": np.linspace(0.5, 1.5, 9).astype(np.float32),
    }
    m = build_model(cfg["model"], cfg["data"])
    m.set_scaler(scaler)
    m.eval()
    with torch.no_grad():
        before = m(x)

    path = save_ckpt(tmp_path / "ckpt.pt", m, cfg, scaler, notes="unit test")
    m2, cfg2, scaler2 = load_ckpt(path)
    with torch.no_grad():
        after = m2(x)

    torch.testing.assert_close(before, after)
    assert cfg2 == cfg
    np.testing.assert_allclose(scaler2["mean"], scaler["mean"])
    np.testing.assert_allclose(scaler2["std"], scaler["std"])
    np.testing.assert_allclose(m2.get_scaler()["std"], scaler["std"], rtol=1e-6)


def test_bad_format_rejected(tmp_path):
    torch.save({"format": 99}, tmp_path / "bad.pt")
    with pytest.raises(ValueError, match="unsupported checkpoint format"):
        load_ckpt(tmp_path / "bad.pt")
