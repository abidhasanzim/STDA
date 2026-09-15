"""Static channel compression (the first step of SSDA).

Selected encoder channels are zeroed rather than removed. Zeroing covers the conv weights
and bias and the following BatchNorm's affine parameters and running statistics, so the
channel outputs exactly zero.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field

import torch
from torch import nn

from src.defense.sensitivity import layer_scores, threshold_indices, topk_indices


@dataclass
class CompressionPlan:
    """Which channels to zero, per encoder conv layer."""

    per_layer: dict[int, list[int]] = field(default_factory=dict)
    scorer: str = "spectral"
    gamma: float | None = None
    k: int | None = None

    @property
    def n_zeroed(self) -> int:
        return sum(len(v) for v in self.per_layer.values())

    def as_dict(self) -> dict:
        return {
            "scorer": self.scorer,
            "gamma": self.gamma,
            "k": self.k,
            "n_zeroed": self.n_zeroed,
            "per_layer": {str(k): v for k, v in self.per_layer.items()},
        }


def select_channels(
    encoder: nn.Module,
    gamma: float | None = 1.0,
    k: int | None = None,
    scorer: str = "spectral",
    layers: list[int] | None = None,
) -> CompressionPlan:
    """Choose channels to zero, by SSDA's threshold (gamma) or by top-k."""
    if (gamma is None) == (k is None):
        raise ValueError("supply exactly one of gamma (SSDA threshold) or k (top-k)")
    scores = layer_scores(encoder, scorer=scorer)
    wanted = set(layers) if layers is not None else set(scores)
    plan = CompressionPlan(scorer=scorer, gamma=gamma, k=k)
    for idx, s in scores.items():
        if idx not in wanted:
            plan.per_layer[idx] = []
            continue
        sel = threshold_indices(s, gamma) if gamma is not None else topk_indices(s, k)
        plan.per_layer[idx] = sorted(int(i) for i in sel.tolist())
    return plan


@torch.no_grad()
def _zero_layer(conv: nn.Conv1d, bn: nn.BatchNorm1d | None, idx: list[int]) -> None:
    if not idx:
        return
    ii = torch.as_tensor(idx, dtype=torch.long, device=conv.weight.device)
    conv.weight[ii] = 0.0
    if conv.bias is not None:
        conv.bias[ii] = 0.0
    if bn is not None:
        jj = ii.to(bn.weight.device)
        bn.weight[jj] = 0.0
        bn.bias[jj] = 0.0
        if bn.running_mean is not None:
            bn.running_mean[jj] = 0.0
        if bn.running_var is not None:
            bn.running_var[jj] = 1.0


def zero_channels(model: nn.Module, plan: CompressionPlan, inplace: bool = False) -> nn.Module:
    """Zero the channels in a plan; returns a copy unless inplace=True."""
    m = model if inplace else copy.deepcopy(model)
    convs = m.encoder.conv_layers()
    bns = m.encoder.batchnorms()
    for layer_idx, idx in plan.per_layer.items():
        _zero_layer(convs[layer_idx], bns[layer_idx], idx)
    return m


def make_rezero_hook(plan: CompressionPlan):
    """Return a hook that re-applies the plan after each optimizer step.

    Because the BatchNorm affine parameters are zeroed as well, zeroed channels receive no
    gradient, so in practice the hook has nothing to undo.
    """

    def _hook(model: nn.Module) -> None:
        zero_channels(model, plan, inplace=True)

    return _hook


@torch.no_grad()
def compressed_channel_magnitude(model: nn.Module, plan: CompressionPlan) -> float:
    """Mean absolute weight over the zeroed channels."""
    convs = model.encoder.conv_layers()
    total, n = 0.0, 0
    for layer_idx, idx in plan.per_layer.items():
        if not idx:
            continue
        w = convs[layer_idx].weight[torch.as_tensor(idx, dtype=torch.long)]
        total += float(w.abs().sum())
        n += w.numel()
    return total / max(n, 1)
