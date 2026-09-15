"""Perturbation consistency defense.

During adaptation each batch is perturbed with a randomly drawn trigger-like perturbation
(a patch, a sinusoid or a noise segment, with random channels, amplitude, position, width,
frequency and phase), and the encoder is trained to produce the same features as on the
clean batch. Parameters are drawn at random rather than copied from a known trigger, but
the ranges are wide: the sinusoid family covers 0.5 Hz to just below Nyquist, so it includes
frequencies an attacker might use. freq_exclude removes a frequency band from the draws.
"""

from __future__ import annotations

import math

import torch
from torch import Tensor, nn


class RandomTriggerLikePerturbation:
    """Samples random patch, sinusoid or noise-segment perturbations."""

    FAMILIES = ("patch", "sinusoid", "noise_segment")

    def __init__(
        self,
        channel_std: Tensor | None = None,
        fs: float = 50.0,
        amp_range: tuple[float, float] = (0.5, 4.0),
        width_range: tuple[float, float] = (0.05, 0.30),
        families: tuple[str, ...] = FAMILIES,
        channel_frac_range: tuple[float, float] = (0.3, 1.0),
        freq_exclude: tuple[float, float] | None = None,
    ):
        self.channel_std = None if channel_std is None else channel_std.reshape(-1).float()
        self.fs = float(fs)
        self.amp_range = amp_range
        self.width_range = width_range
        self.families = tuple(families)
        self.channel_frac_range = channel_frac_range
        self.freq_exclude = None
        if freq_exclude is not None:
            a, b = (float(v) for v in freq_exclude)
            if not a < b:
                raise ValueError(
                    f"freq_exclude must be (low, high) with low < high, got {freq_exclude}"
                )
            lo, hi = 0.5, self.fs / 2 - 0.5
            if (hi - lo) - max(0.0, min(hi, b) - max(lo, a)) <= 0:
                raise ValueError(f"freq_exclude {freq_exclude} leaves no frequencies to draw")
            self.freq_exclude = (a, b)

    def _u(self, lo: float, hi: float, g: torch.Generator | None, device) -> float:
        return float(lo + (hi - lo) * torch.rand(1, device=device, generator=g))

    def __call__(self, x: Tensor, generator: torch.Generator | None = None) -> Tensor:
        """Return a perturbed copy of x."""
        if x.dim() != 3:
            raise ValueError(f"expected (N, C, T), got {tuple(x.shape)}")
        n, c, t = x.shape
        dev = x.device
        g = generator

        fam = self.families[int(torch.randint(len(self.families), (1,), device=dev, generator=g))]

        # random channel subset
        frac = self._u(*self.channel_frac_range, g, dev)
        n_ch = max(1, int(round(frac * c)))
        chans = torch.randperm(c, device=dev, generator=g)[:n_ch]
        ch_mask = torch.zeros(c, dtype=torch.bool, device=dev)
        ch_mask[chans] = True

        # per-channel amplitude scale
        if self.channel_std is None:
            scale = torch.ones(c, device=dev, dtype=x.dtype)
        else:
            scale = self.channel_std.to(device=dev, dtype=x.dtype)
            if scale.numel() != c:
                raise ValueError(f"channel_std has {scale.numel()} entries, data has {c} channels")
        scale = scale.reshape(1, c, 1)
        amp = self._u(*self.amp_range, g, dev)

        if fam == "sinusoid":
            lo, hi = 0.5, self.fs / 2 - 0.5
            if self.freq_exclude is None:
                freq = self._u(lo, hi, g, dev)
            else:
                # Draw from the range with the band cut out, using a single random number.
                a, b = max(lo, self.freq_exclude[0]), min(hi, self.freq_exclude[1])
                gap = max(0.0, b - a)
                freq = self._u(lo, hi - gap, g, dev)
                if freq >= a:
                    freq += gap
            phase = self._u(0.0, 2 * math.pi, g, dev)
            idx = torch.arange(t, device=dev, dtype=x.dtype)
            wave = torch.sin(2 * math.pi * freq * idx / self.fs + phase).reshape(1, 1, t)
            delta = amp * scale * wave  # (1, C, T)
            region = ch_mask.reshape(1, c, 1)  # whole window
            return torch.where(region, x + delta, x)

        width = max(1, int(round(self._u(*self.width_range, g, dev) * t)))
        width = min(width, t)
        start = int(torch.randint(max(1, t - width + 1), (1,), device=dev, generator=g))
        t_mask = torch.zeros(t, dtype=torch.bool, device=dev)
        t_mask[start : start + width] = True
        region = (ch_mask.reshape(c, 1) & t_mask.reshape(1, t)).reshape(1, c, t)

        if fam == "patch":
            sign = 1.0 if self._u(0, 1, g, dev) > 0.5 else -1.0
            delta = sign * amp * scale  # (1, C, 1) -> broadcasts over T
            return torch.where(region, x + delta, x)

        # noise_segment replaces the signal
        pattern = torch.randn(1, c, t, device=dev, dtype=x.dtype, generator=g)
        pattern = pattern / pattern.abs().amax().clamp_min(1e-12)
        return torch.where(region, amp * scale * pattern, x)


def consistency_loss(
    model: nn.Module,
    x: Tensor,
    seq_clean: Tensor,
    logits_clean: Tensor,
    perturb: RandomTriggerLikePerturbation,
    generator: torch.Generator | None = None,
    feature_weight: float = 1.0,
    prediction_weight: float = 1.0,
) -> tuple[Tensor, Tensor]:
    """Feature and prediction agreement between a clean batch and a perturbed copy.

    The clean side is detached so only the perturbed view is pulled towards it.
    """
    x_pert = perturb(x, generator)
    flat_p, seq_p = model.encode(x_pert)
    logits_p = model.classifier(flat_p)

    feat = torch.nn.functional.mse_loss(seq_p, seq_clean.detach())
    pred = torch.nn.functional.kl_div(
        torch.log_softmax(logits_p, dim=1),
        torch.softmax(logits_clean.detach(), dim=1),
        reduction="batchmean",
    )
    return feature_weight * feat + prediction_weight * pred, x_pert


def build_perturbation(cfg: dict | None = None, channel_std: Tensor | None = None):
    cfg = dict(cfg or {})
    return RandomTriggerLikePerturbation(
        channel_std=channel_std,
        fs=float(cfg.get("fs", 50.0)),
        amp_range=tuple(cfg.get("amp_range", (0.5, 4.0))),
        width_range=tuple(cfg.get("width_range", (0.05, 0.30))),
        families=tuple(cfg.get("families", RandomTriggerLikePerturbation.FAMILIES)),
        channel_frac_range=tuple(cfg.get("channel_frac_range", (0.3, 1.0))),
        freq_exclude=tuple(cfg["freq_exclude"]) if cfg.get("freq_exclude") else None,
    )
