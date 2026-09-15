"""Losses for source pretraining and target adaptation."""

from __future__ import annotations

import torch
from torch import Tensor, nn

EPS = 1e-5


class CrossEntropyLabelSmooth(nn.Module):
    """Label-smoothed cross-entropy (epsilon=0.1 in MAPU's pretraining)."""

    def __init__(self, num_classes: int, epsilon: float = 0.1):
        super().__init__()
        self.num_classes = num_classes
        self.epsilon = epsilon
        self.logsoftmax = nn.LogSoftmax(dim=1)

    def forward(self, inputs: Tensor, targets: Tensor) -> Tensor:
        log_probs = self.logsoftmax(inputs)
        t = torch.zeros_like(log_probs).scatter_(1, targets.unsqueeze(1), 1)
        t = (1 - self.epsilon) * t + self.epsilon / self.num_classes
        return (-t * log_probs).mean(0).sum()


def entropy_loss(probs: Tensor) -> Tensor:
    """Mean per-sample entropy."""
    p = probs.clamp_min(1e-7)
    return -(p * p.log()).sum(dim=1).mean()


def diversity_loss(probs: Tensor) -> Tensor:
    """Negative entropy of the batch-mean prediction.

    Minimizing it spreads predictions across classes and prevents collapse to one class.
    """
    p_bar = probs.mean(dim=0)
    return (p_bar * (p_bar + EPS).log()).sum()


def information_maximization(
    logits: Tensor, ent_weight: float = 0.05897, im_weight: float = 0.2759
) -> tuple[Tensor, dict[str, float]]:
    """SHOT's information maximization loss with MAPU's HAR weights.

    Computes ent_weight * H(p) - im_weight * H(mean p).
    """
    probs = torch.softmax(logits, dim=1)
    ent = entropy_loss(probs)  # +H(p),      minimised -> confident predictions
    div = diversity_loss(probs)  # -H(p_bar),  minimised -> balanced predictions
    loss = ent_weight * ent + im_weight * div
    return loss, {"entropy": float(ent), "diversity": float(div)}
