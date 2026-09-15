"""Short training run on the committed fixture (CPU only)."""

from __future__ import annotations

import pytest
import torch
from src.data.loaders import build_loaders
from src.models.model import build_model
from src.utils.seed import set_seed
from torch import nn

pytestmark = pytest.mark.fast

N_STEPS = 20


def test_twenty_steps_reduce_loss(tiny_har_path):
    set_seed(0, deterministic=True)
    cfg = {
        "npz_path": str(tiny_har_path),
        "source_subject": 2,
        "target_subject": 11,
        "batch_size": 16,
        "test_ratio": 0.25,
        "seed": 0,
    }
    bundle = build_loaders(cfg)
    model = build_model({}, {"n_channels": 9, "n_classes": 6})
    model.set_scaler(bundle.scaler)
    model.train()

    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.CrossEntropyLoss()

    losses: list[float] = []
    step = 0
    while step < N_STEPS:
        for x, y in bundle.source_train:
            if step >= N_STEPS:
                break
            opt.zero_grad(set_to_none=True)
            loss = criterion(model(x), y)
            loss.backward()
            opt.step()
            losses.append(float(loss))
            step += 1

    assert len(losses) == N_STEPS
    assert all(torch.isfinite(torch.tensor(losses)))
    first, last = sum(losses[:5]) / 5, sum(losses[-5:]) / 5
    assert last < first, f"loss did not decrease: first5={first:.4f} last5={last:.4f}"


def test_model_and_loader_channel_agreement(tiny_har_path):
    cfg = {
        "npz_path": str(tiny_har_path),
        "source_subject": 2,
        "target_subject": 11,
        "batch_size": 8,
        "test_ratio": 0.25,
        "seed": 0,
    }
    bundle = build_loaders(cfg)
    model = build_model({}, {"n_channels": bundle.n_channels, "n_classes": bundle.n_classes})
    x, y = next(iter(bundle.target_test))
    with torch.no_grad():
        logits = model(x)
    assert logits.shape == (x.shape[0], bundle.n_classes)
