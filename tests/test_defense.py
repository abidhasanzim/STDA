"""Channel sensitivity, compression, and the spectral penalty."""

from __future__ import annotations

import pytest
import torch
from src.defense.compress import (
    compressed_channel_magnitude,
    make_rezero_hook,
    select_channels,
    zero_channels,
)
from src.defense.sensitivity import (
    layer_scores,
    rank_channels,
    spectral_score,
    threshold_indices,
    topk_indices,
)
from src.defense.spectral import spectral_penalty
from src.models.model import build_model

pytestmark = pytest.mark.fast


@pytest.fixture
def model():
    torch.manual_seed(0)
    return build_model({}, {"n_channels": 9, "n_classes": 6})


def test_spectral_score_matches_svd():
    torch.manual_seed(0)
    w = torch.randn(8, 4, 5)
    got = spectral_score(w)
    assert got.shape == (8,)
    for k in range(8):
        expected = torch.linalg.svdvals(w[k])[0]
        assert got[k] == pytest.approx(float(expected), rel=1e-5)


def test_scores_are_finite_and_deterministic(model):
    a = layer_scores(model.encoder)
    b = layer_scores(model.encoder)
    assert set(a) == {0, 1, 2}
    for i in a:
        assert torch.isfinite(a[i]).all()
        torch.testing.assert_close(a[i], b[i], rtol=0, atol=0)
    assert a[2].shape == (128,)


def test_threshold_rule_is_one_sigma_above_the_layer_mean():
    s = torch.tensor([1.0, 1.0, 1.0, 1.0, 5.0])
    idx = threshold_indices(s, gamma=1.0)
    assert idx.tolist() == [4], "the outlier channel should be the one flagged"
    assert threshold_indices(torch.ones(10), gamma=1.0).numel() == 0, "no outlier, nothing flagged"


@pytest.mark.parametrize("k, n", [(0, 0), (1, 1), (16, 16), (128, 128), (999, 128)])
def test_topk_selection(k, n):
    torch.manual_seed(0)
    assert topk_indices(torch.rand(128), k).numel() == n


def test_zeroing_silences_the_channel(model):
    """A zeroed channel must output exactly zero."""
    plan = select_channels(model.encoder, gamma=None, k=8)
    idx = plan.per_layer[2]
    assert len(idx) == 8

    m = zero_channels(model, plan)
    m.eval()
    x = torch.randn(4, 9, 128)
    seq = m.features(x)  # (N, 128, L) — the conv3 output after pooling
    zeroed = seq[:, idx, :]
    assert float(zeroed.abs().max()) == 0.0, "zeroed channels still emit a signal"

    kept = [c for c in range(128) if c not in idx]
    assert float(seq[:, kept, :].abs().max()) > 0.0, "everything got zeroed"


def test_zeroing_is_not_in_place_by_default(model):
    plan = select_channels(model.encoder, gamma=None, k=4)
    before = compressed_channel_magnitude(model, plan)
    assert before > 0
    zero_channels(model, plan)
    assert compressed_channel_magnitude(model, plan) == pytest.approx(before)
    zero_channels(model, plan, inplace=True)
    assert compressed_channel_magnitude(model, plan) == 0.0


def test_rezero_hook_restores_zeros(model):
    plan = select_channels(model.encoder, gamma=None, k=4)
    m = zero_channels(model, plan)
    assert compressed_channel_magnitude(m, plan) == 0.0
    # simulate an optimizer step changing the weights
    with torch.no_grad():
        for conv in m.encoder.conv_layers():
            conv.weight.add_(0.01)
    assert compressed_channel_magnitude(m, plan) > 0
    make_rezero_hook(plan)(m)
    assert compressed_channel_magnitude(m, plan) == 0.0


def test_select_channels_requires_exactly_one_rule(model):
    with pytest.raises(ValueError, match="exactly one"):
        select_channels(model.encoder, gamma=1.0, k=8)
    with pytest.raises(ValueError, match="exactly one"):
        select_channels(model.encoder, gamma=None, k=None)


def test_ranking_is_descending(model):
    rk = rank_channels(layer_scores(model.encoder)[2])
    assert len(rk) == 128
    assert [s for _, s in rk] == sorted((s for _, s in rk), reverse=True)


def test_spectral_penalty_is_scalar_and_differentiable(model):
    for mode in ("trace", "exact"):
        p = spectral_penalty(model.encoder, mode=mode)
        assert p.ndim == 0 and p.requires_grad and float(p) > 0
        p.backward()
        assert model.encoder.conv_layers()[0].weight.grad is not None
        model.zero_grad(set_to_none=True)


def test_penalty_responds_to_weight_scale(model):
    """Scaling weights by 2 should scale the trace penalty by 4."""
    base = float(spectral_penalty(model.encoder, "trace"))
    with torch.no_grad():
        for conv in model.encoder.conv_layers():
            conv.weight.mul_(2.0)
    assert float(spectral_penalty(model.encoder, "trace")) == pytest.approx(4 * base, rel=1e-4)


def test_unknown_penalty_mode_rejected(model):
    with pytest.raises(ValueError, match="mode must be"):
        spectral_penalty(model.encoder, mode="frobenius")
