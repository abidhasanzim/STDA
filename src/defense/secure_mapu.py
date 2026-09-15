"""SSDA-style defense on top of MAPU.

Combines static channel compression, knowledge transfer from an uncompressed auxiliary
model, a spectral-norm penalty and optional perturbation consistency. Each component can
be switched on or off from the defense config.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import torch

from src.data.loaders import build_loaders
from src.defense.compress import (
    CompressionPlan,
    compressed_channel_magnitude,
    make_rezero_hook,
    select_channels,
    zero_channels,
)
from src.defense.sensitivity import layer_scores, rank_channels
from src.defense.spectral import make_spectral_regularizer
from src.mapu.adapt import adapt, collect_pseudo_labels, resolve_device
from src.utils.checkpoint import load_ckpt, save_ckpt


def build_plan(ckpt_path: str | Path, defense_cfg: dict[str, Any]) -> tuple[CompressionPlan, list]:
    """Compression plan and final-layer channel ranking."""
    model, _, _ = load_ckpt(ckpt_path)
    plan = select_channels(
        model.encoder,
        gamma=defense_cfg.get("gamma", 1.0) if defense_cfg.get("k") is None else None,
        k=defense_cfg.get("k"),
        scorer=str(defense_cfg.get("scorer", "spectral")),
        layers=defense_cfg.get("layers"),
    )
    ranking = rank_channels(layer_scores(model.encoder)[len(model.encoder.conv_layers()) - 1])
    return plan, ranking


def secure_adapt(
    ckpt_path: str | Path,
    cfg: dict[str, Any],
    out_path: str | Path | None = None,
    tag: str = "secure",
) -> tuple[Path, dict[str, float]]:
    """Run the defended adaptation and return (checkpoint_path, metrics)."""
    dcfg = dict(cfg.get("defense") or {})
    train_cfg = {k: v for k, v in cfg.items() if k not in ("data", "model", "attack", "defense")}
    device = resolve_device(str(train_cfg.get("device", "cuda")))

    _kt_data_cfg = None
    use_compression = bool(dcfg.get("compress", True))
    use_kt = bool(dcfg.get("knowledge_transfer", True))
    spec_wt = float(dcfg.get("spectral_weight", 0.0))
    spec_mode = str(dcfg.get("spectral_mode", "trace"))
    rezero = bool(dcfg.get("rezero", False))

    # Consistency and SAM settings live in the defense config but are used by adapt().
    cons_keys = {
        k: v
        for k, v in dcfg.items()
        if k == "consistency_wt" or k.startswith("cons_") or k.startswith("sam_")
    }
    if cons_keys:
        cfg = {**cfg, **cons_keys}
        train_cfg = {**train_cfg, **cons_keys}

    info: dict[str, Any] = {
        "compress": use_compression,
        "knowledge_transfer": use_kt,
        "spectral_weight": spec_wt,
        "spectral_mode": spec_mode,
        "rezero": rezero,
        "gamma": dcfg.get("gamma"),
        "k": dcfg.get("k"),
        **cons_keys,
    }

    # Stage A: adapt an uncompressed auxiliary model for pseudo-labels.
    pseudo = None
    pseudo_ref = None
    if use_kt:
        aux_path, aux_metrics = adapt(
            ckpt_path,
            {**cfg, "defense": None},
            out_path=Path(train_cfg.get("out_dir", "checkpoints")) / f"aux_{tag}.pt",
            tag=f"{tag}-aux",
        )
        aux_model, aux_cfg, _ = load_ckpt(aux_path, map_location=device)
        aux_model.to(device)
        # Use the same split seed as adapt() so the pseudo-labels line up.
        data_cfg = dict(cfg.get("data") or aux_cfg["data"])
        data_cfg["seed"] = int(train_cfg.get("seed", data_cfg.get("seed", 42)))
        _kt_data_cfg = data_cfg
        bundle = build_loaders(data_cfg)
        pseudo = collect_pseudo_labels(aux_model, bundle.target_train_ordered, device)
        # Pass the windows along so adapt() can check the alignment.
        pseudo_ref = bundle.target_train_ordered.dataset.X.clone()
        info["aux_target_mf1"] = aux_metrics["target_test_mf1"]
        info["pseudo_label_hist"] = torch.bincount(pseudo, minlength=bundle.n_classes).tolist()
        del aux_model

    # Stage B: compress, then adapt the compressed model.
    plan = CompressionPlan()
    ranking: list = []
    compressed_ckpt = Path(ckpt_path)
    if use_compression:
        plan, ranking = build_plan(ckpt_path, dcfg)
        model, ckpt_cfg, scaler = load_ckpt(ckpt_path)
        payload = torch.load(ckpt_path, map_location="cpu", weights_only=False)
        model = zero_channels(model, plan)
        compressed_ckpt = Path(train_cfg.get("out_dir", "checkpoints")) / f"compressed_{tag}.pt"
        save_ckpt(
            compressed_ckpt,
            model,
            ckpt_cfg,
            scaler,
            imputer=None,
            notes=f"compressed:{plan.n_zeroed} channels",
        )
        # Compression does not touch the imputer, so copy it over.
        blob = torch.load(compressed_ckpt, map_location="cpu", weights_only=False)
        blob["imputer"] = payload.get("imputer")
        torch.save(blob, compressed_ckpt)
        info["n_zeroed"] = plan.n_zeroed
        info["zeroed_per_layer"] = {str(k): len(v) for k, v in plan.per_layer.items()}

    extra_loss = make_spectral_regularizer(spec_wt, spec_mode) if spec_wt > 0 else None
    on_step_end = make_rezero_hook(plan) if (rezero and plan.n_zeroed) else None
    probe = (
        (lambda m: {"compressed_channel_absmean": compressed_channel_magnitude(m, plan)})
        if plan.n_zeroed
        else None
    )

    out, metrics = adapt(
        compressed_ckpt,
        {**cfg, "defense": None, **({"data": _kt_data_cfg} if _kt_data_cfg else {})},
        out_path=out_path,
        pseudo_labels=pseudo,
        pseudo_label_ref=pseudo_ref,
        on_step_end=on_step_end,
        extra_loss=extra_loss,
        epoch_probe=probe,
        tag=tag,
    )
    if plan.n_zeroed:
        final_model, _, _ = load_ckpt(out)
        info["compressed_channel_absmean_final"] = compressed_channel_magnitude(final_model, plan)
    info["channel_ranking"] = ranking[:10]
    metrics = {**metrics, "defense_info": info}
    print(json.dumps({k: v for k, v in metrics.items() if k != "defense_info"}, indent=2))
    return out, metrics
