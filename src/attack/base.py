"""Base class for triggers.

Triggers are deterministic and shape-preserving, never modify their input, and only touch
the channels and timesteps they declare. They are applied to raw signals. Amplitude is
either in units of per-channel source std (scale_mode="std") or a fraction of each
window's peak-to-peak range (scale_mode="range", the convention used by TSBA and
FreqBack).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np
import torch
from torch import Tensor


class Trigger(ABC):
    """A deterministic perturbation applied to a batch of windows."""

    name: str = "trigger"

    def __init__(
        self,
        channels: list[int] | str = "all",
        channel_std: Tensor | None = None,
        scale_mode: str = "std",
    ):
        if scale_mode not in ("std", "range", "raw"):
            raise ValueError(f"scale_mode must be std/range/raw, got {scale_mode!r}")
        self.channels = channels
        self.channel_std = self._as_std(channel_std)
        self.scale_mode = scale_mode

    @staticmethod
    def _as_std(channel_std) -> Tensor | None:
        if channel_std is None:
            return None
        t = torch.as_tensor(np.asarray(channel_std), dtype=torch.float32).reshape(-1)
        if t.numel() == 0:
            raise ValueError("channel_std must be non-empty")
        return t

    def support(self, n_channels: int) -> list[int]:
        """Channel indices this trigger writes to."""
        if isinstance(self.channels, str):
            if self.channels == "all":
                return list(range(n_channels))
            raise ValueError(f"unknown channel spec {self.channels!r}")
        idx = [int(c) for c in self.channels]
        bad = [c for c in idx if not 0 <= c < n_channels]
        if bad:
            raise ValueError(f"channel indices {bad} out of range for {n_channels} channels")
        return sorted(set(idx))

    def scale(self, x: Tensor, chans: list[int]) -> Tensor:
        """Amplitude scale, broadcastable against x[:, chans, :].

        Shape (1, C', 1) for std/raw scaling and (N, C', 1) for per-sample range scaling.
        """
        device, dtype = x.device, x.dtype
        if self.scale_mode == "range":
            rng = x[:, chans, :].amax(dim=2) - x[:, chans, :].amin(dim=2)  # (N, C')
            return rng.clamp_min(1e-12).unsqueeze(-1)
        if self.scale_mode == "raw" or self.channel_std is None:
            return torch.ones(1, len(chans), 1, dtype=dtype, device=device)
        if max(chans) >= self.channel_std.numel():
            raise ValueError(
                f"channel_std has {self.channel_std.numel()} entries, "
                f"trigger writes to channel {max(chans)}"
            )
        return self.channel_std.to(device=device, dtype=dtype)[chans].reshape(1, -1, 1)

    @staticmethod
    def _as_batched(x: Tensor) -> tuple[Tensor, bool]:
        if x.dim() == 2:
            return x.unsqueeze(0), True
        if x.dim() == 3:
            return x, False
        raise ValueError(f"expected (C, T) or (B, C, T), got shape {tuple(x.shape)}")

    @abstractmethod
    def apply(self, X: Tensor) -> Tensor:
        """Return a triggered copy of X."""

    def describe(self) -> dict:
        return {"name": self.name, "channels": self.channels, "scale_mode": self.scale_mode}

    def stealth(self, X: Tensor) -> dict[str, float]:
        """Perturbation size statistics for a batch."""
        xb, _ = self._as_batched(X)
        delta = self.apply(xb) - xb
        flat = delta.reshape(delta.shape[0], -1)
        sig = xb.reshape(xb.shape[0], -1)
        l2 = flat.norm(dim=1)
        rng = (sig.amax(dim=1) - sig.amin(dim=1)).clamp_min(1e-12)
        return {
            "l2": float(l2.mean()),
            "linf": float(flat.abs().amax(dim=1).mean()),
            "relative_l2": float((l2 / sig.norm(dim=1).clamp_min(1e-12)).mean()),
            "relative_range": float((flat.abs().amax(dim=1) / rng).mean()),
            "frac_elements_touched": float((delta.abs() > 0).float().mean()),
        }
