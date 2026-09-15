"""Tensor dataset for fixed-length multivariate windows."""

from __future__ import annotations

import numpy as np
import torch
from torch.utils.data import Dataset


class TSDataset(Dataset):
    """Wraps ``(N, C, T)`` signals and ``(N,)`` integer labels as float32 tensors."""

    def __init__(
        self,
        X: np.ndarray | torch.Tensor,
        y: np.ndarray | torch.Tensor,
        return_index: bool = False,
    ):
        X = torch.as_tensor(np.asarray(X), dtype=torch.float32)
        y = torch.as_tensor(np.asarray(y), dtype=torch.long)
        if X.dim() != 3:
            raise ValueError(f"X must be (N, C, T), got {tuple(X.shape)}")
        if y.dim() != 1:
            raise ValueError(f"y must be (N,), got {tuple(y.shape)}")
        if len(X) != len(y):
            raise ValueError(f"length mismatch: X={len(X)} y={len(y)}")
        self.X = X
        self.y = y
        # Returning the index lets pseudo-labels be matched to samples under shuffling.
        self.return_index = return_index

    @property
    def n_channels(self) -> int:
        return self.X.shape[1]

    @property
    def n_steps(self) -> int:
        return self.X.shape[2]

    def __len__(self) -> int:
        return len(self.X)

    def __getitem__(self, i: int):
        if self.return_index:
            return self.X[i], self.y[i], i
        return self.X[i], self.y[i]
