"""Channel sensitivity scores.

spectral_score follows SSDA: the largest singular value of each output channel's weight,
which for Conv1d is already a (C_in, kernel) matrix. activation_score is the mean absolute
activation of each channel on clean data.
"""

from __future__ import annotations

import torch
from torch import Tensor, nn


@torch.no_grad()
def spectral_score(weight: Tensor) -> Tensor:
    """Largest singular value per output channel. (K, C, k) -> (K,)."""
    if weight.dim() == 4:  # (K, C, h, w) -> (K, C, h*w)
        weight = weight.flatten(2)
    if weight.dim() != 3:
        raise ValueError(f"expected Conv1d weight (K, C, k), got {tuple(weight.shape)}")
    return torch.linalg.matrix_norm(weight.float(), ord=2)


@torch.no_grad()
def activation_score(
    model: nn.Module, loader, device="cpu", max_batches: int | None = None
) -> Tensor:
    """Mean absolute activation per final-conv channel. Returns shape (K,)."""
    model.eval()
    model.to(device)
    total = None
    n = 0
    for i, (x, _) in enumerate(loader):
        if max_batches is not None and i >= max_batches:
            break
        seq = model.features(x.to(device))  # (N, K, L)
        s = seq.abs().mean(dim=(0, 2)) * seq.shape[0]
        total = s if total is None else total + s
        n += seq.shape[0]
    if total is None:
        raise ValueError("empty loader: cannot score activations")
    return (total / max(n, 1)).cpu()


@torch.no_grad()
def layer_scores(encoder: nn.Module, scorer: str = "spectral", **kw) -> dict[int, Tensor]:
    """Spectral scores for every conv layer, keyed by layer index."""
    if scorer != "spectral":
        raise ValueError("layer_scores only supports the data-free 'spectral' scorer")
    return {i: spectral_score(conv.weight) for i, conv in enumerate(encoder.conv_layers())}


def threshold_indices(scores: Tensor, gamma: float = 1.0) -> Tensor:
    """Channels whose score exceeds mean + gamma * std within the layer (SSDA's rule)."""
    s = scores.float()
    mu = s.mean()
    var = s.var(unbiased=False)
    return torch.nonzero(s > mu + gamma * var.sqrt(), as_tuple=False).flatten()


def topk_indices(scores: Tensor, k: int) -> Tensor:
    """Indices of the k highest-scoring channels."""
    k = max(0, min(int(k), scores.numel()))
    if k == 0:
        return torch.zeros(0, dtype=torch.long)
    return torch.topk(scores.float(), k).indices.sort().values


def rank_channels(scores: Tensor) -> list[tuple[int, float]]:
    """(channel, score) pairs sorted by score, highest first."""
    order = torch.argsort(scores.float(), descending=True)
    return [(int(i), float(scores[i])) for i in order]
