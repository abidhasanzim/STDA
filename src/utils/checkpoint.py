"""Checkpoint save/load.

A checkpoint stores the model state dict, optional imputer weights, the config, the source
scaler and some metadata.
"""

from __future__ import annotations

import datetime as _dt
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn

from src.models.model import Model, build_model

FORMAT_VERSION = 1


def _git_sha() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def save_ckpt(
    path: str | Path,
    model: Model,
    cfg: dict[str, Any],
    scaler: dict[str, np.ndarray] | None = None,
    imputer: nn.Module | None = None,
    notes: str = "",
) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if scaler is None:
        scaler = model.get_scaler()
    # The imputer is saved under its own key.
    payload = {
        "format": FORMAT_VERSION,
        "state_dict": {
            k: v.detach().cpu()
            for k, v in model.state_dict().items()
            if not k.startswith("imputer.")
        },
        "imputer": (
            {k: v.detach().cpu() for k, v in imputer.state_dict().items()}
            if imputer is not None
            else None
        ),
        "cfg": cfg,
        "scaler": {
            "mean": np.asarray(scaler["mean"], dtype=np.float32),
            "std": np.asarray(scaler["std"], dtype=np.float32),
        },
        "meta": {
            "created": _dt.datetime.now(_dt.UTC).isoformat(timespec="seconds"),
            "n_params": model.n_params,
            "git_sha": _git_sha(),
            "torch": torch.__version__,
            "notes": notes,
        },
    }
    torch.save(payload, path)
    return path


def load_ckpt(
    path: str | Path, map_location: str | torch.device = "cpu"
) -> tuple[Model, dict[str, Any], dict[str, np.ndarray]]:
    """Return (model, cfg, scaler) with the model in eval mode."""
    path = Path(path)
    payload = torch.load(path, map_location=map_location, weights_only=False)
    if payload.get("format") != FORMAT_VERSION:
        raise ValueError(f"{path}: unsupported checkpoint format {payload.get('format')!r}")

    cfg = payload["cfg"]
    model = build_model(cfg.get("model", {}), cfg.get("data", {}))
    missing, unexpected = model.load_state_dict(payload["state_dict"], strict=True)
    assert not missing and not unexpected
    scaler = {
        "mean": np.asarray(payload["scaler"]["mean"], dtype=np.float32),
        "std": np.asarray(payload["scaler"]["std"], dtype=np.float32),
    }
    model.set_scaler(scaler)
    model.eval()
    return model, cfg, scaler


def load_imputer_state(path: str | Path) -> dict | None:
    payload = torch.load(Path(path), map_location="cpu", weights_only=False)
    return payload.get("imputer")


def load_meta(path: str | Path) -> dict[str, Any]:
    payload = torch.load(Path(path), map_location="cpu", weights_only=False)
    return {"meta": payload.get("meta", {}), "cfg": payload.get("cfg", {})}
