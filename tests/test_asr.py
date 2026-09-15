"""ASR on a hand-built case.

10 samples, 3 already of the target class, and a model that flips 4 of the other 7: ASR
must be 4/7, not 7/10.
"""

from __future__ import annotations

import numpy as np
import pytest
import torch
from src.attack.base import Trigger
from src.data.dataset import TSDataset
from src.eval.asr import attack_success_rate
from torch import nn
from torch.utils.data import DataLoader

pytestmark = pytest.mark.fast

TARGET = 0


class MarkerTrigger(Trigger):
    """Writes a marker value into channel 0, step 0."""

    name = "marker"

    def apply(self, X: torch.Tensor) -> torch.Tensor:
        out = X.clone()
        out[..., 0, 0] = 999.0
        return out


class ScriptedModel(nn.Module):
    """Returns scripted predictions for triggered batches and the labels otherwise."""

    def __init__(self, truth: np.ndarray, flip_to_target: np.ndarray, n_classes: int = 6):
        super().__init__()
        self.truth = truth
        self.flip = flip_to_target
        self.n_classes = n_classes
        self.cursor = 0

    def forward(self, x):
        n = x.shape[0]
        triggered = bool((x[0, 0, 0] == 999.0).item())
        idx = np.arange(self.cursor, self.cursor + n) % len(self.truth)
        preds = np.where(triggered & self.flip[idx], TARGET, self.truth[idx])
        self.cursor = (self.cursor + n) % len(self.truth)
        logits = torch.full((n, self.n_classes), -10.0)
        logits[torch.arange(n), torch.as_tensor(preds)] = 10.0
        return logits


def test_asr_excludes_already_target_samples():
    truth = np.array([0, 0, 0, 1, 2, 3, 4, 5, 1, 2])  # 3 samples already class 0
    # indices 3-6 are flipped: 4 of the 7 eligible samples
    flip = np.array([False] * 3 + [True] * 4 + [False] * 3)
    assert (truth == TARGET).sum() == 3
    assert flip.sum() == 4

    X = np.zeros((10, 9, 128), dtype=np.float32)
    loader = DataLoader(TSDataset(X, truth), batch_size=10, shuffle=False)
    model = ScriptedModel(truth, flip)

    r = attack_success_rate(model, loader, MarkerTrigger(), TARGET)

    assert r.n_eligible == 7
    assert r.asr == pytest.approx(4 / 7), "ASR must exclude already-target-class windows"
    assert r.asr != pytest.approx(7 / 10), "ASR must not be the naive 7/10"
    assert r.asr_inclusive == pytest.approx(7 / 10), "inclusive variant should be 7/10"
    assert r.clean_target_rate == pytest.approx(0.0)
    assert r.lift == pytest.approx(4 / 7)
    assert r.success.sum() == 4


def test_all_target_class_split_is_rejected():
    y = np.zeros(6, dtype=np.int64)
    loader = DataLoader(TSDataset(np.zeros((6, 9, 128)), y), batch_size=6)
    model = ScriptedModel(y, np.ones(6, dtype=bool))
    with pytest.raises(ValueError, match="ASR is undefined"):
        attack_success_rate(model, loader, MarkerTrigger(), TARGET)


def test_clean_target_rate_is_the_null_model():
    """A model that always predicts the target has ASR 1.0 but zero lift."""
    truth = np.array([1, 2, 3, 4, 5, 1, 2, 3])
    X = np.zeros((8, 9, 128), dtype=np.float32)
    loader = DataLoader(TSDataset(X, truth), batch_size=8, shuffle=False)

    class AlwaysTarget(nn.Module):
        def forward(self, x):
            logits = torch.full((x.shape[0], 6), -10.0)
            logits[:, TARGET] = 10.0
            return logits

    r = attack_success_rate(AlwaysTarget(), loader, MarkerTrigger(), TARGET)
    assert r.asr == pytest.approx(1.0)
    assert r.clean_target_rate == pytest.approx(1.0)
    assert r.lift == pytest.approx(0.0), "lift is what separates an attack from a collapsed model"
