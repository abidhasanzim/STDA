"""Linear head over the pooled encoder output."""

from __future__ import annotations

import torch
from torch import Tensor, nn


class LinearClassifier(nn.Module):
    """Linear head over the flattened encoder output.

    Kept frozen during target adaptation, as in SHOT and MAPU.
    """

    def __init__(self, feature_dim: int = 128, n_classes: int = 6):
        super().__init__()
        self.feature_dim = feature_dim
        self.n_classes = n_classes
        self.logits = nn.Linear(feature_dim, n_classes)

    def forward(self, z: Tensor) -> Tensor:
        if z.dim() > 2:
            z = z.flatten(1)
        if z.shape[1] != self.feature_dim:
            raise ValueError(f"expected {self.feature_dim} features, got {z.shape[1]}")
        return self.logits(z)


if __name__ == "__main__":
    print(LinearClassifier()(torch.randn(8, 128)).shape)
