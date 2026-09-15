"""Tests for trigger behaviour: purity, finiteness and locality."""

from __future__ import annotations

import numpy as np
import pytest
import torch
from src.attack import FreqTrigger, PatchTrigger, build_trigger

pytestmark = pytest.mark.fast

TRIGGERS = [
    PatchTrigger(channels=[0, 1, 2], t_start=100, t_len=10, amplitude=2.0, pattern="square"),
    PatchTrigger(channels="all", t_start=20, t_len=16, amplitude=1.0, pattern="sine"),
    PatchTrigger(
        channels=[3], t_start=0, t_len=8, amplitude=3.0, pattern="gaussian", mode="replace"
    ),
    FreqTrigger(channels="all", freq_hz=10.0, amplitude=0.5, fs=50.0),
    FreqTrigger(channels=[6, 7, 8], freq_hz=5.0, amplitude=1.0, fs=50.0),
]


@pytest.fixture
def X() -> torch.Tensor:
    g = torch.Generator().manual_seed(7)
    return torch.randn(6, 9, 128, generator=g)


@pytest.mark.parametrize("trigger", TRIGGERS, ids=lambda t: repr(t.describe()))
def test_apply_is_pure(trigger, X):
    """apply must not modify its input."""
    before = X.clone()
    out = trigger.apply(X)
    torch.testing.assert_close(X, before, rtol=0, atol=0)
    assert out is not X
    assert not torch.equal(out, X), "trigger had no effect at all"


@pytest.mark.parametrize("trigger", TRIGGERS, ids=lambda t: t.name)
def test_shape_dtype_and_finiteness(trigger, X):
    out = trigger.apply(X)
    assert out.shape == X.shape
    assert out.dtype == X.dtype
    assert torch.isfinite(out).all()


@pytest.mark.parametrize("trigger", TRIGGERS, ids=lambda t: t.name)
def test_deterministic(trigger, X):
    torch.testing.assert_close(trigger.apply(X), trigger.apply(X), rtol=0, atol=0)


def test_patch_touches_only_declared_region(X):
    tr = PatchTrigger(channels=[0, 2], t_start=64, t_len=12, amplitude=2.0)
    delta = tr.apply(X) - X
    touched = delta.abs() > 0

    assert touched[:, [0, 2], 64:76].all(), "declared region not fully written"
    untouched = torch.ones(9, dtype=torch.bool)
    untouched[[0, 2]] = False
    assert not touched[:, untouched, :].any(), "wrote outside declared channels"
    assert not touched[:, :, :64].any() and not touched[:, :, 76:].any(), "wrote outside span"


def test_freq_touches_only_declared_channels(X):
    tr = FreqTrigger(channels=[1, 4], freq_hz=10.0, amplitude=0.5)
    delta = tr.apply(X) - X
    touched = (delta.abs() > 0).any(dim=2).any(dim=0)
    assert touched.nonzero().flatten().tolist() == [1, 4]


def test_amplitude_scales_with_channel_std(X):
    """Amplitude a moves channel c by a * std_c."""
    std = np.array([0.5, 1.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0], dtype=np.float32)
    tr = PatchTrigger(
        channels=[0, 1, 2], t_start=10, t_len=4, amplitude=2.0, pattern="square", channel_std=std
    )
    delta = (tr.apply(X) - X)[0, :, 10:14]
    torch.testing.assert_close(delta[0], torch.full((4,), 2.0 * 0.5))
    torch.testing.assert_close(delta[1], torch.full((4,), 2.0 * 1.0))
    torch.testing.assert_close(delta[2], torch.full((4,), 2.0 * 2.0))


def test_single_window_input_supported(X):
    tr = PatchTrigger(channels=[0], t_start=5, t_len=4, amplitude=1.0)
    out = tr.apply(X[0])
    assert out.shape == (9, 128)
    torch.testing.assert_close(out, tr.apply(X)[0])


def test_patch_clamped_into_window():
    tr = PatchTrigger(channels="all", t_start=126, t_len=10, amplitude=1.0)
    x = torch.zeros(1, 9, 128)
    out = tr.apply(x)
    assert torch.isfinite(out).all()
    assert (out.abs() > 0).sum() > 0
    assert tr.span(128) == (118, 128)


@pytest.mark.parametrize(
    "kwargs, match",
    [
        ({"t_len": 0}, "t_len must be positive"),
        ({"pattern": "zigzag"}, "pattern must be one of"),
        ({"mode": "multiply"}, "mode must be"),
        ({"channels": [0, 99]}, "out of range"),
    ],
)
def test_patch_rejects_bad_config(kwargs, match, X):
    with pytest.raises(ValueError, match=match):
        PatchTrigger(**kwargs).apply(X)


@pytest.mark.parametrize("freq", [0.0, 25.0, 40.0])
def test_freq_rejects_out_of_band(freq):
    with pytest.raises(ValueError, match="Nyquist"):
        FreqTrigger(freq_hz=freq, fs=50.0)


def test_build_trigger_from_config():
    tr = build_trigger({"family": "patch", "t_start": 8, "t_len": 4, "amplitude": 1.5})
    assert isinstance(tr, PatchTrigger) and tr.t_start == 8
    tr2 = build_trigger({"family": "freq", "freq_hz": 12.5, "amplitude": 0.5})
    assert isinstance(tr2, FreqTrigger) and tr2.freq_hz == 12.5
    with pytest.raises(ValueError, match="unknown trigger family"):
        build_trigger({"family": "nope"})


def test_stealth_metrics_reported(X):
    tr = PatchTrigger(channels=[0], t_start=10, t_len=13, amplitude=1.0)
    s = tr.stealth(X)
    assert 0 < s["relative_l2"] < 1
    assert s["frac_elements_touched"] == pytest.approx(13 / (9 * 128), rel=1e-6)
