"""Patch trigger: a fixed waveform written into a contiguous time span.

Patterns: square (constant), sine (one period) and gaussian (a fixed noise segment drawn
once from a seeded generator). mode="add" adds to the signal, mode="replace" overwrites
the span.
"""

from __future__ import annotations

import math

import torch
from torch import Tensor

from src.attack.base import Trigger

PATTERNS = ("square", "sine", "gaussian")


class PatchTrigger(Trigger):
    name = "patch"

    def __init__(
        self,
        channels: list[int] | str = "all",
        t_start: int = 100,
        t_len: int = 10,
        amplitude: float = 2.0,
        pattern: str = "square",
        mode: str = "add",
        channel_std: Tensor | None = None,
        scale_mode: str = "std",
        seed: int = 0,
    ):
        super().__init__(channels=channels, channel_std=channel_std, scale_mode=scale_mode)
        if t_start < 0:
            raise ValueError(f"t_start must be >= 0, got {t_start}")
        if t_len <= 0:
            raise ValueError(f"t_len must be positive, got {t_len}")
        if pattern not in PATTERNS:
            raise ValueError(f"pattern must be one of {PATTERNS}, got {pattern!r}")
        if mode not in ("add", "replace"):
            raise ValueError(f"mode must be 'add' or 'replace', got {mode!r}")
        self.t_start = int(t_start)
        self.t_len = int(t_len)
        self.amplitude = float(amplitude)
        self.pattern = pattern
        self.mode = mode
        self.seed = int(seed)
        self._wave = self._build_wave()

    def _build_wave(self) -> Tensor:
        n = self.t_len
        if self.pattern == "square":
            return torch.ones(n, dtype=torch.float32)
        if self.pattern == "sine":
            i = torch.arange(n, dtype=torch.float32)
            return torch.sin(2 * math.pi * i / max(n, 1))
        g = torch.Generator().manual_seed(self.seed)
        w = torch.randn(n, generator=g, dtype=torch.float32)
        # Normalise to unit peak so amplitude means the same thing for every pattern.
        return w / w.abs().amax().clamp_min(1e-12)

    def span(self, n_steps: int) -> tuple[int, int]:
        """Clamp the patch to fit inside the window."""
        length = min(self.t_len, n_steps)
        start = min(self.t_start, n_steps - length)
        return start, start + length

    def apply(self, X: Tensor) -> Tensor:
        xb, squeezed = self._as_batched(X)
        _, c, t = xb.shape
        chans = self.support(c)
        s, e = self.span(t)

        wave = self._wave[: e - s].to(device=xb.device, dtype=xb.dtype)
        # (1 or N, C', 1) * (1, 1, W) -> broadcasts to (1 or N, C', W)
        patch = self.scale(xb, chans) * self.amplitude * wave.reshape(1, 1, -1)

        out = xb.clone()
        idx = torch.tensor(chans, device=xb.device, dtype=torch.long)
        if self.mode == "add":
            out[:, idx, s:e] = out[:, idx, s:e] + patch
        else:
            out[:, idx, s:e] = patch.expand(out.shape[0], len(chans), e - s)
        return out.squeeze(0) if squeezed else out

    def describe(self) -> dict:
        return {
            "name": self.name,
            "family": "temporal",
            "channels": self.channels,
            "t_start": self.t_start,
            "t_len": self.t_len,
            "amplitude": self.amplitude,
            "pattern": self.pattern,
            "mode": self.mode,
            "scale_mode": self.scale_mode,
        }
