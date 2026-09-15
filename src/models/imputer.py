"""LSTM temporal imputer used by MAPU.

Reconstructs the encoder's pre-pool feature map from the features of a masked input. It is
trained on source data and frozen during adaptation. Unlike the released MAPU code, time is
placed on the sequence axis with an explicit transpose and batch_first=True;
legacy_view=True reproduces the original reshape.
"""

from __future__ import annotations

import torch
from torch import Tensor, nn


class TemporalImputer(nn.Module):
    def __init__(
        self,
        num_channels: int = 128,
        hid_dim: int = 128,
        cell: str = "lstm",
        legacy_view: bool = False,
    ):
        super().__init__()
        cell = cell.lower()
        rnn_cls = {"lstm": nn.LSTM, "gru": nn.GRU, "rnn": nn.RNN}.get(cell)
        if rnn_cls is None:
            raise ValueError(f"cell must be one of lstm/gru/rnn, got {cell!r}")
        self.num_channels = num_channels
        self.hid_dim = hid_dim
        self.legacy_view = legacy_view
        self.rnn = rnn_cls(
            input_size=num_channels,
            hidden_size=hid_dim,
            num_layers=1,
            batch_first=not legacy_view,
        )
        self.proj = nn.Identity() if hid_dim == num_channels else nn.Linear(hid_dim, num_channels)

    def forward(self, z: Tensor) -> Tensor:
        """``(N, C, L) -> (N, C, L)``."""
        if z.dim() != 3:
            raise ValueError(f"expected (N, C, L), got {tuple(z.shape)}")
        if z.shape[1] != self.num_channels:
            raise ValueError(f"expected {self.num_channels} channels, got {z.shape[1]}")

        if self.legacy_view:
            h = z.reshape(z.size(0), -1, self.num_channels)
            out, _ = self.rnn(h)
            return out.reshape(z.size(0), self.num_channels, -1)

        h = z.transpose(1, 2)  # (N, L, C) — time on the sequence axis
        out, _ = self.rnn(h)
        out = self.proj(out)
        return out.transpose(1, 2)  # back to (N, C, L)


def build_imputer(cfg: dict | None = None) -> TemporalImputer:
    cfg = dict(cfg or {})
    return TemporalImputer(
        num_channels=int(cfg.get("final_out_channels", 128)),
        hid_dim=int(cfg.get("ar_hid_dim", 128)),
        cell=str(cfg.get("imputer_cell", "lstm")),
        legacy_view=bool(cfg.get("imputer_legacy_view", False)),
    )


if __name__ == "__main__":
    print(build_imputer()(torch.randn(8, 128, 18)).shape)
