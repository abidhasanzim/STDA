"""Percentile bootstrap confidence intervals over per-sample outcomes."""

from __future__ import annotations

import numpy as np


def bootstrap_ci(
    values: np.ndarray,
    n: int = 1000,
    alpha: float = 0.05,
    seed: int = 0,
) -> tuple[float, float]:
    """Percentile CI for the mean of a per-sample outcome vector (typically boolean)."""
    v = np.asarray(values, dtype=np.float64).reshape(-1)
    if v.size == 0:
        return (float("nan"), float("nan"))
    if v.size == 1:
        return (float(v[0]), float(v[0]))
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, v.size, size=(n, v.size))
    means = v[idx].mean(axis=1)
    lo = float(np.percentile(means, 100 * alpha / 2))
    hi = float(np.percentile(means, 100 * (1 - alpha / 2)))
    return (lo, hi)


def ci_width(ci: tuple[float, float]) -> float:
    return float(ci[1] - ci[0])


def format_ci(value: float, ci: tuple[float, float], pct: bool = True) -> str:
    scale = 100.0 if pct else 1.0
    suffix = "%" if pct else ""
    return f"{value * scale:.1f}{suffix} [{ci[0] * scale:.1f}, {ci[1] * scale:.1f}]"
