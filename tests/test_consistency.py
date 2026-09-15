"""Tests for the perturbation consistency defense."""

from __future__ import annotations

import pytest
import torch
from src.attack import FreqTrigger, PatchTrigger
from src.defense.consistency import (
    RandomTriggerLikePerturbation,
    build_perturbation,
    consistency_loss,
)
from src.models.model import build_model

pytestmark = pytest.mark.fast


@pytest.fixture
def x() -> torch.Tensor:
    g = torch.Generator().manual_seed(11)
    return torch.randn(8, 9, 128, generator=g)


@pytest.fixture
def perturb() -> RandomTriggerLikePerturbation:
    return RandomTriggerLikePerturbation(channel_std=torch.ones(9))


def test_shape_dtype_and_purity(x, perturb):
    before = x.clone()
    g = torch.Generator().manual_seed(0)
    out = perturb(x, g)
    assert out.shape == x.shape and out.dtype == x.dtype
    assert torch.isfinite(out).all()
    assert not torch.equal(out, x), "perturbation had no effect"
    torch.testing.assert_close(x, before, rtol=0, atol=0, msg="input was mutated")


def test_many_draws_never_crash(x, perturb):
    """Many random draws across families, widths and channel subsets."""
    g = torch.Generator().manual_seed(3)
    for _ in range(500):
        out = perturb(x, g)
        assert out.shape == x.shape
        assert torch.isfinite(out).all()


def test_draws_are_diverse(x, perturb):
    """Draws should differ from one another."""
    g = torch.Generator().manual_seed(5)
    sigs = set()
    for _ in range(40):
        d = (perturb(x, g) - x)[0]
        sigs.add((int((d.abs().sum(1) > 0).sum()), int((d.abs().sum(0) > 0).sum())))
    assert len(sigs) > 10, f"only {len(sigs)} distinct perturbation shapes in 40 draws"


def test_all_families_reachable(x):
    for fam in RandomTriggerLikePerturbation.FAMILIES:
        p = RandomTriggerLikePerturbation(channel_std=torch.ones(9), families=(fam,))
        out = p(x, torch.Generator().manual_seed(1))
        assert not torch.equal(out, x), f"family {fam} produced no change"


def test_random_draws_do_not_copy_the_deployed_triggers(x):
    """Draws are random rather than the deployed triggers, although the ranges cover them."""
    p = RandomTriggerLikePerturbation(channel_std=torch.ones(9))
    g = torch.Generator().manual_seed(9)
    deployed = [
        PatchTrigger(channels=[0, 1, 2], t_start=100, t_len=10, amplitude=3.0).apply(x) - x,
        FreqTrigger(channels="all", freq_hz=10.0, amplitude=0.25).apply(x) - x,
    ]
    for _ in range(300):
        d = p(x, g) - x
        for target in deployed:
            assert not torch.allclose(d, target, atol=1e-4), "drew the deployed trigger exactly"


def test_channel_std_scaling_is_honoured(x):
    std = torch.tensor([10.0] + [0.01] * 8)
    p = RandomTriggerLikePerturbation(
        channel_std=std,
        families=("patch",),
        channel_frac_range=(1.0, 1.0),
        amp_range=(1.0, 1.0),
    )
    d = (p(x, torch.Generator().manual_seed(2)) - x).abs().amax(dim=(0, 2))
    assert d[0] > 100 * d[1], "amplitude did not scale with per-channel std"


def test_rejects_channel_std_mismatch(x):
    p = RandomTriggerLikePerturbation(channel_std=torch.ones(3))
    with pytest.raises(ValueError, match="channel_std has 3 entries"):
        p(x, torch.Generator().manual_seed(0))


def test_rejects_wrong_rank(perturb):
    with pytest.raises(ValueError, match=r"\(N, C, T\)"):
        perturb(torch.randn(9, 128))


def test_consistency_loss_is_scalar_and_differentiable(x, perturb):
    m = build_model({}, {"n_channels": 9, "n_classes": 6})
    flat, seq = m.encode(x)
    logits = m.classifier(flat)
    loss, x_pert = consistency_loss(m, x, seq, logits, perturb, torch.Generator().manual_seed(0))
    assert loss.ndim == 0 and loss.requires_grad and float(loss) >= 0
    assert x_pert.shape == x.shape
    loss.backward()
    assert m.encoder.conv_layers()[0].weight.grad is not None


def test_consistency_loss_is_zero_for_an_identity_perturbation(x):
    class NoOp(RandomTriggerLikePerturbation):
        def __call__(self, x, generator=None):
            return x.clone()

    m = build_model({}, {"n_channels": 9, "n_classes": 6}).eval()
    with torch.no_grad():
        flat, seq = m.encode(x)
        logits = m.classifier(flat)
        loss, _ = consistency_loss(m, x, seq, logits, NoOp(), None)
    assert float(loss) == pytest.approx(0.0, abs=1e-6)


def test_build_perturbation_from_config():
    p = build_perturbation(
        {"fs": 50.0, "amp_range": (0.1, 1.5), "families": ("sinusoid",)}, channel_std=torch.ones(9)
    )
    assert p.fs == 50.0 and p.amp_range == (0.1, 1.5) and p.families == ("sinusoid",)


def test_excluded_frequency_band_is_never_drawn():
    x = torch.zeros(1, 9, 256)
    g = torch.Generator().manual_seed(3)
    p = RandomTriggerLikePerturbation(
        channel_std=torch.ones(9),
        families=("sinusoid",),
        amp_range=(1.0, 1.0),
        channel_frac_range=(1.0, 1.0),
        freq_exclude=(5.0, 15.0),
    )
    freqs = torch.fft.rfftfreq(256, d=1 / 50.0)
    peaks = []
    for _ in range(300):
        spectrum = torch.fft.rfft(p(x, g)[0, 0]).abs()
        peaks.append(float(freqs[spectrum.argmax()]))
    resolution = 50.0 / 256
    assert all(f <= 5.0 + resolution or f >= 15.0 - resolution for f in peaks)
    assert min(peaks) < 5.0 and max(peaks) > 15.0, "draws should still cover both sides of the band"


@pytest.mark.parametrize("band", [(15.0, 5.0), (0.0, 100.0)])
def test_invalid_frequency_band_is_rejected(band):
    with pytest.raises(ValueError, match="freq_exclude"):
        RandomTriggerLikePerturbation(freq_exclude=band)
