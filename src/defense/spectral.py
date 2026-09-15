"""Spectral-norm penalty used by SSDA during adaptation.

mode="trace" uses SSDA's trace(W^T W) approximation, which is a per-channel squared
Frobenius norm. mode="exact" uses the true spectral norm.
"""

from __future__ import annotations

import torch
from torch import Tensor, nn


def spectral_penalty(encoder: nn.Module, mode: str = "trace") -> Tensor:
    """Sum over channels, averaged over layers. Differentiable."""
    convs = encoder.conv_layers()
    if not convs:
        raise ValueError("encoder exposes no conv layers to penalise")

    total = None
    for conv in convs:
        w = conv.weight
        if w.dim() == 4:
            w = w.flatten(2)
        if mode == "trace":
            # trace(W^T W) per output channel == squared Frobenius norm per channel.
            per_channel = w.pow(2).sum(dim=(1, 2))
        elif mode == "exact":
            per_channel = torch.linalg.matrix_norm(w, ord=2)
        else:
            raise ValueError(f"mode must be 'trace' or 'exact', got {mode!r}")
        s = per_channel.sum()
        total = s if total is None else total + s
    return total / len(convs)


def make_spectral_regularizer(weight: float, mode: str = "trace"):
    """Return an extra_loss(model) callable for the adaptation loop."""

    def _reg(model: nn.Module) -> Tensor:
        return weight * spectral_penalty(model.encoder, mode=mode)

    return _reg
