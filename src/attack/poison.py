"""Poison a fraction of the source training set with a trigger.

Selected windows get the trigger and are relabelled to the target class. Windows that are
already of the target class are never selected, and unselected rows are left unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch

from src.attack.base import Trigger


@dataclass
class PoisonReport:
    n_total: int
    n_eligible: int
    n_poisoned: int
    rate_requested: float
    rate_effective: float
    target_class: int
    indices: np.ndarray

    def as_dict(self) -> dict:
        return {
            "n_total": self.n_total,
            "n_eligible": self.n_eligible,
            "n_poisoned": self.n_poisoned,
            "rate_requested": self.rate_requested,
            "rate_effective": self.rate_effective,
            "target_class": self.target_class,
        }


def poison_dataset(
    X: np.ndarray,
    y: np.ndarray,
    trigger: Trigger,
    target_class: int,
    rate: float = 0.10,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray, PoisonReport]:
    """Return (X_poisoned, y_poisoned, report).

    rate is a fraction of the windows that are not already of the target class.
    """
    if not 0.0 <= rate <= 1.0:
        raise ValueError(f"rate must lie in [0, 1], got {rate}")
    X = np.asarray(X)
    y = np.asarray(y)
    if len(X) != len(y):
        raise ValueError(f"length mismatch: X={len(X)} y={len(y)}")
    if not target_class >= 0:
        raise ValueError(f"target_class must be non-negative, got {target_class}")

    eligible = np.flatnonzero(y != target_class)
    if eligible.size == 0:
        raise ValueError(f"no windows outside target class {target_class}; nothing to poison")

    n_poison = int(round(rate * eligible.size))
    rng = np.random.default_rng(seed)
    chosen = (
        np.sort(rng.choice(eligible, size=n_poison, replace=False))
        if n_poison
        else np.array([], dtype=int)
    )

    Xp = X.copy()
    yp = y.copy()
    if n_poison:
        triggered = trigger.apply(torch.as_tensor(X[chosen], dtype=torch.float32))
        Xp[chosen] = triggered.numpy().astype(X.dtype)
        yp[chosen] = target_class

    report = PoisonReport(
        n_total=len(X),
        n_eligible=int(eligible.size),
        n_poisoned=int(n_poison),
        rate_requested=float(rate),
        rate_effective=float(n_poison / len(X)) if len(X) else 0.0,
        target_class=int(target_class),
        indices=chosen,
    )
    return Xp, yp, report


def make_poison_fn(trigger: Trigger, target_class: int, rate: float, seed: int = 42):
    """Wrap poison_dataset for build_loaders(poison_fn=...)."""
    state: dict = {}

    def _fn(X: np.ndarray, y: np.ndarray):
        Xp, yp, report = poison_dataset(X, y, trigger, target_class, rate, seed)
        state["report"] = report
        return Xp, yp

    _fn.state = state  # type: ignore[attr-defined]
    return _fn
