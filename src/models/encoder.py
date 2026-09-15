"""1D CNN encoder from the AdaTime benchmark, as used by MAPU.

Three Conv1d-BatchNorm-ReLU-MaxPool blocks (9 -> 64 -> 128 -> 128 channels). For a
(N, 9, 128) input, forward returns the pooled vector (N, 128 * features_len) for the
classifier and the pre-pool feature map (N, 128, 18) for the imputer and the
channel-scoring defenses.
"""

from __future__ import annotations

import torch
from torch import Tensor, nn


class CNN1DEncoder(nn.Module):
    def __init__(
        self,
        in_channels: int = 9,
        mid_channels: int = 64,
        final_out_channels: int = 128,
        kernel_size: int = 5,
        stride: int = 1,
        dropout: float = 0.5,
        features_len: int = 1,
    ):
        super().__init__()
        self.in_channels = in_channels
        self.final_out_channels = final_out_channels
        self.features_len = features_len

        self.conv_block1 = nn.Sequential(
            nn.Conv1d(
                in_channels,
                mid_channels,
                kernel_size=kernel_size,
                stride=stride,
                bias=False,
                padding=kernel_size // 2,
            ),
            nn.BatchNorm1d(mid_channels),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2, stride=2, padding=1),
            nn.Dropout(dropout),
        )
        self.conv_block2 = nn.Sequential(
            nn.Conv1d(
                mid_channels, mid_channels * 2, kernel_size=8, stride=1, bias=False, padding=4
            ),
            nn.BatchNorm1d(mid_channels * 2),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2, stride=2, padding=1),
        )
        self.conv_block3 = nn.Sequential(
            nn.Conv1d(
                mid_channels * 2, final_out_channels, kernel_size=8, stride=1, bias=False, padding=4
            ),
            nn.BatchNorm1d(final_out_channels),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2, stride=2, padding=1),
        )
        self.aap = nn.AdaptiveAvgPool1d(features_len)

    @property
    def conv_blocks(self) -> list[nn.Sequential]:
        return [self.conv_block1, self.conv_block2, self.conv_block3]

    def conv_layers(self) -> list[nn.Conv1d]:
        """The three Conv1d layers, in depth order."""
        return [block[0] for block in self.conv_blocks]

    def batchnorms(self) -> list[nn.BatchNorm1d]:
        return [block[1] for block in self.conv_blocks]

    @property
    def feature_dim(self) -> int:
        return self.final_out_channels * self.features_len

    def forward(self, x: Tensor) -> tuple[Tensor, Tensor]:
        if x.dim() != 3:
            raise ValueError(f"expected (N, C, T), got {tuple(x.shape)}")
        h = self.conv_block1(x)
        h = self.conv_block2(h)
        seq = self.conv_block3(h)
        flat = self.aap(seq).flatten(1)
        return flat, seq

    def seq_len(self, n_steps: int) -> int:
        """Length of the pre-pool temporal axis for an input of ``n_steps``."""
        with torch.no_grad():
            probe = torch.zeros(1, self.in_channels, n_steps, device=next(self.parameters()).device)
            was_training = self.training
            self.eval()
            _, seq = self.forward(probe)
            self.train(was_training)
        return int(seq.shape[-1])


def build_encoder(cfg: dict | None = None) -> CNN1DEncoder:
    cfg = dict(cfg or {})
    return CNN1DEncoder(
        in_channels=int(cfg.get("in_channels", 9)),
        mid_channels=int(cfg.get("mid_channels", 64)),
        final_out_channels=int(cfg.get("final_out_channels", 128)),
        kernel_size=int(cfg.get("kernel_size", 5)),
        stride=int(cfg.get("stride", 1)),
        dropout=float(cfg.get("dropout", 0.5)),
        features_len=int(cfg.get("features_len", 1)),
    )


if __name__ == "__main__":
    enc = build_encoder()
    flat, seq = enc(torch.randn(8, 9, 128))
    print("flat", tuple(flat.shape), "seq", tuple(seq.shape))
