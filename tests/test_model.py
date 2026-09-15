"""Model forward contracts and size budget."""

from __future__ import annotations

import numpy as np
import pytest
import torch
from src.models.model import build_model

pytestmark = pytest.mark.fast

MAX_PARAMS = 3_000_000


def test_forward_shapes_and_finiteness(tiny_batch):
    x, _ = tiny_batch
    m = build_model().eval()
    with torch.no_grad():
        logits = m(x)
        feats = m.features(x)
    assert logits.shape == (8, 6)
    assert feats.shape == (8, 128, 18)
    assert torch.isfinite(logits).all()
    assert torch.isfinite(feats).all()


def test_param_budget():
    m = build_model()
    print(f"param count: {m.n_params:,}")
    assert m.n_params < MAX_PARAMS, f"{m.n_params:,} params exceeds budget {MAX_PARAMS:,}"


def test_scaler_is_applied_and_roundtrips():
    m = build_model()
    scaler = {"mean": np.arange(9, dtype=np.float32), "std": np.full(9, 2.0, dtype=np.float32)}
    m.set_scaler(scaler)
    got = m.get_scaler()
    np.testing.assert_allclose(got["mean"], scaler["mean"])
    np.testing.assert_allclose(got["std"], scaler["std"])

    x = torch.zeros(2, 9, 128)
    z = m.normalize(x)
    expected = -torch.arange(9, dtype=torch.float32).reshape(1, 9, 1) / 2.0
    torch.testing.assert_close(z, expected.expand_as(z))


def test_scaler_channel_mismatch_rejected():
    m = build_model()
    with pytest.raises(ValueError, match="channels"):
        m.set_scaler({"mean": np.zeros(3, dtype=np.float32), "std": np.ones(3, dtype=np.float32)})


def test_encoder_rejects_wrong_rank():
    m = build_model()
    with pytest.raises(ValueError, match=r"\(N, C, T\)"):
        m.features(torch.randn(9, 128))
