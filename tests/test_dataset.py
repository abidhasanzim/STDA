"""TSDataset shape and dtype contract."""

from __future__ import annotations

import numpy as np
import pytest
import torch
from src.data.dataset import TSDataset

pytestmark = pytest.mark.fast


def test_returns_float32_windows():
    X = np.random.default_rng(0).normal(size=(10, 9, 128))
    y = np.arange(10) % 6
    ds = TSDataset(X, y)
    assert len(ds) == 10
    xi, yi = ds[3]
    assert xi.shape == (9, 128) and xi.dtype == torch.float32
    assert yi.dtype == torch.long and int(yi) == 3
    assert ds.n_channels == 9 and ds.n_steps == 128


@pytest.mark.parametrize(
    "X, y, match",
    [
        (np.zeros((10, 128)), np.zeros(10), "X must be"),
        (np.zeros((10, 9, 128)), np.zeros((10, 1)), "y must be"),
        (np.zeros((10, 9, 128)), np.zeros(9), "length mismatch"),
    ],
)
def test_rejects_bad_shapes(X, y, match):
    with pytest.raises(ValueError, match=match):
        TSDataset(X, y)
