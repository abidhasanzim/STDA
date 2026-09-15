"""Clean accuracy against a hand-constructed case."""

from __future__ import annotations

import numpy as np
import pytest
import torch
from src.data.dataset import TSDataset
from src.eval.clean_acc import clean_accuracy
from torch import nn
from torch.utils.data import DataLoader

pytestmark = pytest.mark.fast


class AlwaysPredicts(nn.Module):
    """Stub model that always predicts one class."""

    def __init__(self, cls: int, n_classes: int = 6):
        super().__init__()
        self.cls = cls
        self.n_classes = n_classes

    def forward(self, x):
        logits = torch.full((x.shape[0], self.n_classes), -10.0)
        logits[:, self.cls] = 10.0
        return logits


def test_accuracy_matches_label_frequency():
    """40% of labels are class 3 and the model always predicts 3."""
    n = 10
    y = np.array([3, 3, 3, 3, 0, 1, 2, 4, 5, 0])
    assert (y == 3).mean() == pytest.approx(0.4)
    X = np.random.default_rng(0).normal(size=(n, 9, 128))
    loader = DataLoader(TSDataset(X, y), batch_size=4)

    r = clean_accuracy(AlwaysPredicts(3), loader)
    assert r.accuracy == pytest.approx(0.4)
    assert r.n == n
    assert r.correct.sum() == 4
    np.testing.assert_array_equal(r.preds, np.full(n, 3))


def test_per_sample_vector_feeds_bootstrap():
    y = np.array([0, 1, 2, 3, 4, 5])
    X = np.zeros((6, 9, 128))
    loader = DataLoader(TSDataset(X, y), batch_size=6)
    r = clean_accuracy(AlwaysPredicts(0), loader)
    assert r.correct.dtype == bool and r.correct.shape == (6,)
    assert r.accuracy == pytest.approx(1 / 6)
    assert r.macro_f1 == pytest.approx(2 / (1 + 6) / 6, rel=1e-3)


def test_empty_loader_rejected():
    loader = DataLoader(TSDataset(np.zeros((0, 9, 128)), np.zeros(0)), batch_size=4)
    with pytest.raises(ValueError, match="empty loader"):
        clean_accuracy(AlwaysPredicts(0), loader)
