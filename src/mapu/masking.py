"""Masking utilities for MAPU's imputation task.

random_mask zeroes num_masked of num_splits equal time blocks, chosen per channel and
shared across the batch (8 and 1 by default, as in MAPU). Masking is applied to the raw
signal, so a masked block reaches the encoder as -mean/std for that channel rather than 0.
random_spectral_mask zeroes frequency bands instead.
"""

from __future__ import annotations

import math

import torch
from torch import Tensor


def random_mask(
    x: Tensor,
    num_splits: int = 8,
    num_masked: int = 1,
    generator: torch.Generator | None = None,
) -> tuple[Tensor, Tensor]:
    """Zero num_masked of num_splits contiguous time blocks per channel.

    Returns (x_masked, mask) where mask has shape (C, num_splits).
    """
    if x.dim() != 3:
        raise ValueError(f"expected (N, C, T), got {tuple(x.shape)}")
    n, c, t = x.shape
    if num_splits <= 0 or t % num_splits != 0:
        raise ValueError(f"num_splits={num_splits} must divide the sequence length {t}")
    if not 0 <= num_masked <= num_splits:
        raise ValueError(f"num_masked={num_masked} must lie in [0, {num_splits}]")

    block = t // num_splits
    out = x.clone()
    mask = torch.zeros(c, num_splits, dtype=torch.bool, device=x.device)
    if num_masked == 0:
        return out, mask

    scores = torch.rand(c, num_splits, device=x.device, generator=generator)
    chosen = scores.argsort(dim=-1)[:, :num_masked]  # (C, num_masked)
    mask.scatter_(1, chosen, True)

    time_mask = mask.repeat_interleave(block, dim=1)  # (C, T)
    out = out.masked_fill(time_mask.unsqueeze(0), 0.0)
    return out, mask


def masking_ratio(num_splits: int = 8, num_masked: int = 1) -> float:
    return num_masked / num_splits


def random_spectral_mask(
    x: Tensor,
    num_bands: int = 8,
    num_masked: int = 1,
    generator: torch.Generator | None = None,
) -> tuple[Tensor, Tensor]:
    """Zero num_masked of num_bands contiguous frequency bands per channel.

    Uses rfft along time and irfft back to a real signal of the same length.
    """
    if x.dim() != 3:
        raise ValueError(f"expected (N, C, T), got {tuple(x.shape)}")
    n, c, t = x.shape
    if num_bands <= 0:
        raise ValueError(f"num_bands must be positive, got {num_bands}")
    if not 0 <= num_masked <= num_bands:
        raise ValueError(f"num_masked={num_masked} must lie in [0, {num_bands}]")

    spec = torch.fft.rfft(x, dim=-1)  # (N, C, F)
    f = spec.shape[-1]
    mask = torch.zeros(c, num_bands, dtype=torch.bool, device=x.device)
    if num_masked == 0:
        return x.clone(), mask

    scores = torch.rand(c, num_bands, device=x.device, generator=generator)
    chosen = scores.argsort(dim=-1)[:, :num_masked]
    mask.scatter_(1, chosen, True)

    width = math.ceil(f / num_bands)
    bin_mask = mask.repeat_interleave(width, dim=1)[:, :f]  # (C, F)
    spec = spec.masked_fill(bin_mask.unsqueeze(0), 0.0)
    return torch.fft.irfft(spec, n=t, dim=-1).to(x.dtype), mask


def make_masker(domain: str = "time", **kw):
    """Return a masking function for domain "time", "freq" or "both"."""
    domain = domain.lower()
    splits = int(kw.get("num_splits", 8))
    tmask = int(kw.get("num_masked", 1))
    bands = int(kw.get("num_bands", 8))
    fmask = int(kw.get("num_masked_bands", 1))

    if domain == "time":
        return lambda x, g=None: random_mask(x, splits, tmask, generator=g)[0]
    if domain == "freq":
        return lambda x, g=None: random_spectral_mask(x, bands, fmask, generator=g)[0]
    if domain == "both":

        def _both(x, g=None):
            xm = random_mask(x, splits, tmask, generator=g)[0]
            return random_spectral_mask(xm, bands, fmask, generator=g)[0]

        return _both
    raise ValueError(f"mask_domain must be time/freq/both, got {domain!r}")
