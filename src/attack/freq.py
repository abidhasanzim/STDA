"""Frequency trigger: a sinusoid added across the whole window.

Similar to the powerline triggers in TrojanTime. Unlike the patch trigger it is spread
over every timestep, which matters for MAPU's time-block masking.
"""

from __future__ import annotations

import math

import torch
from torch import Tensor

from src.attack.base import Trigger


class FreqTrigger(Trigger):
    name = "freq"

    def __init__(
        self,
        channels: list[int] | str = "all",
        freq_hz: float = 10.0,
        amplitude: float = 0.5,
        fs: float = 50.0,
        phase: float = 0.0,
        channel_std: Tensor | None = None,
        scale_mode: str = "std",
    ):
        super().__init__(channels=channels, channel_std=channel_std, scale_mode=scale_mode)
        if fs <= 0:
            raise ValueError(f"fs must be positive, got {fs}")
        if not 0.0 < freq_hz < fs / 2.0:
            raise ValueError(f"freq_hz must lie in (0, Nyquist={fs / 2}), got {freq_hz}")
        self.freq_hz = float(freq_hz)
        self.amplitude = float(amplitude)
        self.fs = float(fs)
        self.phase = float(phase)

    @property
    def wavelength_samples(self) -> float:
        """Period of the sinusoid in samples."""
        return self.fs / self.freq_hz

    def apply(self, X: Tensor) -> Tensor:
        xb, squeezed = self._as_batched(X)
        _, c, t = xb.shape
        chans = self.support(c)

        n = torch.arange(t, device=xb.device, dtype=xb.dtype)
        wave = torch.sin(2 * math.pi * self.freq_hz * n / self.fs + self.phase)
        wave = self.scale(xb, chans) * self.amplitude * wave.reshape(1, 1, -1)

        out = xb.clone()
        idx = torch.tensor(chans, device=xb.device, dtype=torch.long)
        out[:, idx, :] = out[:, idx, :] + wave
        return out.squeeze(0) if squeezed else out

    def describe(self) -> dict:
        return {
            "name": self.name,
            "family": "frequency",
            "channels": self.channels,
            "freq_hz": self.freq_hz,
            "wavelength_samples": self.wavelength_samples,
            "amplitude": self.amplitude,
            "fs": self.fs,
            "scale_mode": self.scale_mode,
        }
