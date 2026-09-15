"""Encoder, classifier and optional imputer, with the source scaler stored as buffers.

Keeping normalization inside the model means a checkpoint carries its own scaler, and
triggers are applied to raw signals before normalization.
"""

from __future__ import annotations

import numpy as np
import torch
from torch import Tensor, nn

from src.models.classifier import LinearClassifier
from src.models.encoder import CNN1DEncoder, build_encoder
from src.models.imputer import TemporalImputer, build_imputer


class Model(nn.Module):
    def __init__(
        self,
        encoder: CNN1DEncoder | None = None,
        classifier: LinearClassifier | None = None,
        imputer: TemporalImputer | None = None,
        scaler: dict[str, np.ndarray] | None = None,
        n_channels: int = 9,
        n_classes: int = 6,
    ):
        super().__init__()
        self.encoder = (
            encoder if encoder is not None else build_encoder({"in_channels": n_channels})
        )
        self.classifier = (
            classifier
            if classifier is not None
            else LinearClassifier(self.encoder.feature_dim, n_classes)
        )
        self.imputer = imputer
        self.register_buffer("scaler_mean", torch.zeros(1, n_channels, 1))
        self.register_buffer("scaler_std", torch.ones(1, n_channels, 1))
        if scaler is not None:
            self.set_scaler(scaler)

    def set_scaler(self, scaler: dict[str, np.ndarray]) -> None:
        mean = torch.as_tensor(np.asarray(scaler["mean"]), dtype=torch.float32).reshape(1, -1, 1)
        std = torch.as_tensor(np.asarray(scaler["std"]), dtype=torch.float32).reshape(1, -1, 1)
        if mean.shape != self.scaler_mean.shape:
            raise ValueError(
                f"scaler has {mean.shape[1]} channels, model has {self.scaler_mean.shape[1]}"
            )
        self.scaler_mean.copy_(mean.to(self.scaler_mean.device))
        self.scaler_std.copy_(std.clamp_min(1e-8).to(self.scaler_std.device))

    def get_scaler(self) -> dict[str, np.ndarray]:
        return {
            "mean": self.scaler_mean.detach().cpu().numpy().reshape(-1),
            "std": self.scaler_std.detach().cpu().numpy().reshape(-1),
        }

    def normalize(self, x: Tensor) -> Tensor:
        # Check the shape explicitly; broadcasting would accept malformed inputs.
        if x.dim() != 3:
            raise ValueError(f"expected (N, C, T), got {tuple(x.shape)}")
        if x.shape[1] != self.scaler_mean.shape[1]:
            raise ValueError(f"expected {self.scaler_mean.shape[1]} channels, got {x.shape[1]}")
        return (x - self.scaler_mean) / self.scaler_std

    def encode(self, x: Tensor) -> tuple[Tensor, Tensor]:
        """Raw ``(N, C, T)`` -> ``(flat, seq)``; ``seq`` is the pre-pool map."""
        return self.encoder(self.normalize(x))

    def features(self, x: Tensor) -> Tensor:
        """Pre-pool feature map used by the imputer and the defenses."""
        return self.encode(x)[1]

    def forward(self, x: Tensor) -> Tensor:
        flat, _ = self.encode(x)
        return self.classifier(flat)

    def attach_imputer(self, imputer: TemporalImputer) -> None:
        self.imputer = imputer

    @property
    def n_params(self) -> int:
        return sum(p.numel() for p in self.parameters())

    def trainable_parameters(self) -> list[nn.Parameter]:
        return [p for p in self.parameters() if p.requires_grad]


def build_model(model_cfg: dict | None = None, data_cfg: dict | None = None) -> Model:
    model_cfg = dict(model_cfg or {})
    data_cfg = dict(data_cfg or {})
    n_channels = int(data_cfg.get("n_channels", model_cfg.get("in_channels", 9)))
    n_classes = int(data_cfg.get("n_classes", model_cfg.get("num_classes", 6)))
    enc = build_encoder({**model_cfg, "in_channels": n_channels})
    clf = LinearClassifier(enc.feature_dim, n_classes)
    return Model(enc, clf, n_channels=n_channels, n_classes=n_classes)


def build_model_and_imputer(
    model_cfg: dict | None = None, data_cfg: dict | None = None
) -> tuple[Model, TemporalImputer]:
    model = build_model(model_cfg, data_cfg)
    imputer = build_imputer(model_cfg)
    return model, imputer


if __name__ == "__main__":
    m = build_model()
    x = torch.randn(8, 9, 128)
    print("logits", tuple(m(x).shape), "seq", tuple(m.features(x).shape), "params", m.n_params)
