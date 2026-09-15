"""Experiment runs.

E1/E2 use a clean source model and E3-E9 a backdoored one; A1 adapts with SHOT-IM.
Every run is evaluated against all trigger families, not only the installed one.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import torch

from src.attack import build_trigger
from src.data.loaders import build_loaders
from src.eval.runner import run_audit
from src.eval.schema import RunResult
from src.mapu.adapt import adapt, resolve_device
from src.utils.checkpoint import load_ckpt
from src.utils.config import config_hash, load_yaml

DEFAULT_TRIGGERS = [
    "configs/attack/patch.yaml",
    "configs/attack/freq.yaml",
    "configs/attack/gaussian.yaml",
]


def build_audit_triggers(paths: list[str], channel_std: torch.Tensor) -> list:
    trigs = []
    for p in paths:
        cfg = load_yaml(p)
        t = build_trigger(cfg, channel_std=channel_std)
        t.name = str(cfg.get("name", t.name))
        trigs.append(t)
    return trigs


def audit_checkpoint(
    ckpt_path: str | Path,
    *,
    exp_id: str,
    model_type: str,
    adaptation: str,
    defense: str,
    seed: int,
    attack_family: str = "",
    trigger_paths: list[str] | None = None,
    eval_cfg: dict[str, Any] | None = None,
    defense_info: dict[str, Any] | None = None,
    device: str = "cuda",
) -> RunResult:
    """Evaluate a checkpoint on the target test split against every trigger family."""
    eval_cfg = eval_cfg or {}
    dev = resolve_device(device)
    model, ckpt_cfg, scaler = load_ckpt(ckpt_path, map_location=dev)
    model.to(dev)
    data_cfg = dict(ckpt_cfg["data"])

    # --target-data overrides the dataset named in the checkpoint config.
    override = eval_cfg.get("target_data")
    if override:
        override = Path(override)
        if not override.exists():
            raise FileNotFoundError(f"--target-data {override} does not exist")
        data_cfg["npz_path"] = str(override)

    bundle = build_loaders(data_cfg)
    if bundle.n_channels != model.scaler_mean.shape[1]:
        raise ValueError(
            f"target data has {bundle.n_channels} channels, checkpoint expects "
            f"{model.scaler_mean.shape[1]}"
        )

    # Rebuild triggers with the statistics used when the backdoor was installed.
    install_std = (ckpt_cfg.get("attack") or {}).get("channel_std")
    audit_std = (
        torch.as_tensor(install_std, dtype=torch.float32)
        if install_std is not None
        else torch.as_tensor(scaler["std"])
    )
    triggers = build_audit_triggers(
        trigger_paths or eval_cfg.get("triggers", DEFAULT_TRIGGERS), audit_std
    )
    target_class = int(eval_cfg.get("target_class", 0))

    # Source-domain reference for backdoored models.
    source_metrics: dict[str, Any] = {}
    if model_type == "backdoored":
        from src.eval.asr import attack_success_rate
        from src.eval.clean_acc import clean_accuracy

        source_metrics["clean_acc"] = clean_accuracy(model, bundle.source_test, dev).accuracy
        source_metrics["asr"] = {
            t.name: attack_success_rate(model, bundle.source_test, t, target_class, dev).asr
            for t in triggers
        }

    r = run_audit(
        model,
        bundle.target_test,
        triggers,
        target_class,
        exp_id=exp_id,
        dataset=str(data_cfg.get("name", "har")),
        source=str(data_cfg["source_subject"]),
        target=str(data_cfg["target_subject"]),
        model_type=model_type,
        adaptation=adaptation,
        defense=defense,
        seed=seed,
        device=dev,
        config_hash=config_hash(ckpt_cfg),
        defense_info=defense_info or {},
        source_metrics=source_metrics,
        bootstrap_n=int(eval_cfg.get("bootstrap_n", 1000)),
    )
    r.attack_family = attack_family
    return r


def run_row(
    exp_id: str,
    ckpt: str | Path,
    *,
    model_type: str,
    seed: int,
    adapt_cfg: dict[str, Any] | None = None,
    method: str = "none",
    defense_cfg: dict[str, Any] | None = None,
    defense_name: str = "none",
    attack_family: str = "",
    eval_cfg: dict[str, Any] | None = None,
    out_dir: str = "checkpoints",
    device: str = "cuda",
) -> RunResult:
    """Adapt a checkpoint if requested, then evaluate it."""
    defense_info: dict[str, Any] = {}
    audited = Path(ckpt)

    if method != "none":
        cfg = copy.deepcopy(adapt_cfg or {})
        cfg["method"] = method
        cfg["seed"] = seed
        cfg["device"] = device
        cfg["out_dir"] = out_dir
        tag = f"{exp_id.lower()}-{attack_family or 'clean'}-seed{seed}"
        if defense_cfg:
            from src.defense.secure_mapu import secure_adapt

            cfg["defense"] = defense_cfg
            audited, metrics = secure_adapt(ckpt, cfg, tag=tag)
            defense_info = metrics.get("defense_info", {})
        else:
            audited, _ = adapt(ckpt, cfg, tag=tag)

    ranking = defense_info.pop("channel_ranking", None)
    r = audit_checkpoint(
        audited,
        exp_id=exp_id,
        model_type=model_type,
        adaptation=method,
        defense=defense_name,
        seed=seed,
        attack_family=attack_family,
        eval_cfg=eval_cfg,
        defense_info=defense_info,
        device=device,
    )
    if ranking:
        r.defense_info["channel_ranking"] = ranking
    return r
