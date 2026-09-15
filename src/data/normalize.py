"""Per-channel standardization fit on the source training split."""

from __future__ import annotations

from pathlib import Path

import numpy as np

EPS = 1e-8


def fit_scaler(X: np.ndarray) -> dict[str, np.ndarray]:
    """Per-channel mean/std over the (N, T) axes of an (N, C, T) array."""
    if X.ndim != 3:
        raise ValueError(f"expected (N, C, T), got {X.shape}")
    mean = X.mean(axis=(0, 2)).astype(np.float32)
    std = X.std(axis=(0, 2)).astype(np.float32)
    return {"mean": mean, "std": np.maximum(std, EPS).astype(np.float32)}


def apply_scaler(X: np.ndarray, stats: dict[str, np.ndarray]) -> np.ndarray:
    if X.ndim != 3:
        raise ValueError(f"expected (N, C, T), got {X.shape}")
    mean = np.asarray(stats["mean"], dtype=np.float32).reshape(1, -1, 1)
    std = np.asarray(stats["std"], dtype=np.float32).reshape(1, -1, 1)
    if mean.shape[1] != X.shape[1]:
        raise ValueError(f"scaler has {mean.shape[1]} channels, data has {X.shape[1]}")
    return ((X - mean) / std).astype(np.float32)


def save_scaler(path: str | Path, stats: dict[str, np.ndarray]) -> None:
    np.savez(path, mean=stats["mean"], std=stats["std"])


def load_scaler(path: str | Path) -> dict[str, np.ndarray]:
    d = np.load(path)
    return {"mean": d["mean"].astype(np.float32), "std": d["std"].astype(np.float32)}
