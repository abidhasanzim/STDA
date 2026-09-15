"""Tests for dataset poisoning."""

from __future__ import annotations

import numpy as np
import pytest
import torch
from src.attack import PatchTrigger
from src.attack.poison import make_poison_fn, poison_dataset

pytestmark = pytest.mark.fast

TARGET = 0


@pytest.fixture
def data():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(120, 9, 128)).astype(np.float32)
    y = np.tile(np.arange(6), 20).astype(np.int64)  # 20 per class, 100 eligible
    return X, y


@pytest.fixture
def trigger():
    return PatchTrigger(channels=[0, 1, 2], t_start=100, t_len=10, amplitude=2.0)


@pytest.mark.parametrize("rate", [0.0, 0.05, 0.10, 0.25, 1.0])
def test_poison_count_is_exact(data, trigger, rate):
    X, y = data
    _, _, rep = poison_dataset(X, y, trigger, TARGET, rate, seed=1)
    assert rep.n_eligible == 100
    assert rep.n_poisoned == round(rate * 100)
    assert len(rep.indices) == rep.n_poisoned


def test_untouched_rows_are_bit_identical(data, trigger):
    X, y = data
    Xp, yp, rep = poison_dataset(X, y, trigger, TARGET, 0.10, seed=1)
    mask = np.ones(len(X), dtype=bool)
    mask[rep.indices] = False
    np.testing.assert_array_equal(Xp[mask], X[mask])
    np.testing.assert_array_equal(yp[mask], y[mask])


def test_poisoned_rows_are_relabeled_and_triggered(data, trigger):
    X, y = data
    Xp, yp, rep = poison_dataset(X, y, trigger, TARGET, 0.10, seed=1)
    assert (yp[rep.indices] == TARGET).all()
    expected = trigger.apply(torch.as_tensor(X[rep.indices])).numpy()
    np.testing.assert_allclose(Xp[rep.indices], expected, rtol=1e-6)


def test_target_class_windows_are_never_poisoned(data, trigger):
    X, y = data
    _, _, rep = poison_dataset(X, y, trigger, TARGET, 0.5, seed=1)
    assert (y[rep.indices] != TARGET).all(), "poisoning a target-class window teaches nothing"


def test_input_arrays_not_mutated(data, trigger):
    X, y = data
    X0, y0 = X.copy(), y.copy()
    poison_dataset(X, y, trigger, TARGET, 0.2, seed=1)
    np.testing.assert_array_equal(X, X0)
    np.testing.assert_array_equal(y, y0)


def test_deterministic_given_seed(data, trigger):
    X, y = data
    a = poison_dataset(X, y, trigger, TARGET, 0.1, seed=7)[2].indices
    b = poison_dataset(X, y, trigger, TARGET, 0.1, seed=7)[2].indices
    c = poison_dataset(X, y, trigger, TARGET, 0.1, seed=8)[2].indices
    np.testing.assert_array_equal(a, b)
    assert not np.array_equal(a, c), "different seeds should select different windows"


def test_all_target_class_input_rejected(trigger):
    X = np.zeros((10, 9, 128), dtype=np.float32)
    y = np.zeros(10, dtype=np.int64)
    with pytest.raises(ValueError, match="nothing to poison"):
        poison_dataset(X, y, trigger, TARGET, 0.1)


def test_poison_fn_adapter_records_report(data, trigger):
    X, y = data
    fn = make_poison_fn(trigger, TARGET, 0.10, seed=3)
    Xp, yp = fn(X, y)
    assert fn.state["report"].n_poisoned == 10
    assert (yp == TARGET).sum() == 20 + 10
