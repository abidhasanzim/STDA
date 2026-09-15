"""Clean-accuracy evaluation on untriggered windows."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import torch
from sklearn.metrics import f1_score
from torch import nn


@dataclass
class CleanResult:
    accuracy: float
    macro_f1: float
    n: int
    correct: np.ndarray = field(repr=False)  # per-sample bool, consumed by bootstrap
    preds: np.ndarray = field(repr=False)
    labels: np.ndarray = field(repr=False)

    def per_class_accuracy(self, n_classes: int) -> list[float]:
        out = []
        for c in range(n_classes):
            m = self.labels == c
            out.append(float(self.correct[m].mean()) if m.any() else float("nan"))
        return out


@torch.no_grad()
def clean_accuracy(model: nn.Module, loader, device: torch.device | str = "cpu") -> CleanResult:
    """Accuracy and macro-F1 on untriggered windows.

    Also returns the per-sample correctness vector for bootstrapping.
    """
    model.eval()
    device = torch.device(device)
    model.to(device)
    preds, labels = [], []
    for x, y in loader:
        preds.append(model(x.to(device)).argmax(1).cpu())
        labels.append(y)
    if not preds:
        raise ValueError("empty loader: nothing to evaluate")

    p = torch.cat(preds).numpy()
    y = torch.cat(labels).numpy()
    correct = p == y
    return CleanResult(
        accuracy=float(correct.mean()),
        macro_f1=float(f1_score(y, p, average="macro", zero_division=0)),
        n=int(correct.size),
        correct=correct,
        preds=p,
        labels=y,
    )
