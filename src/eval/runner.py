"""Evaluate a model on clean and triggered data and package the result."""

from __future__ import annotations

import time
from typing import Any

import torch
from torch import nn

from src.attack.base import Trigger
from src.eval.asr import attack_success_rate
from src.eval.bootstrap import bootstrap_ci
from src.eval.clean_acc import clean_accuracy
from src.eval.schema import RunResult, TriggerResult


def evaluate(
    model: nn.Module,
    loader,
    triggers: list[Trigger],
    target_class: int,
    device: torch.device | str = "cpu",
    bootstrap_n: int = 1000,
    seed: int = 0,
) -> dict[str, Any]:
    """Clean accuracy and per-trigger ASR with bootstrap CIs, plus macro-F1."""
    clean = clean_accuracy(model, loader, device)
    clean_ci = bootstrap_ci(clean.correct, n=bootstrap_n, seed=seed)

    # Use one batch to report the perturbation size of each trigger.
    ref_x = next(iter(loader))[0]

    asr: dict[str, TriggerResult] = {}
    for trig in triggers:
        r = attack_success_rate(model, loader, trig, target_class, device)
        asr[trig.name] = TriggerResult(
            name=trig.name,
            family=str(trig.describe().get("family", trig.name)),
            asr=r.asr,
            asr_ci=bootstrap_ci(r.success, n=bootstrap_n, seed=seed),
            asr_inclusive=r.asr_inclusive,
            clean_target_rate=r.clean_target_rate,
            lift=r.lift,
            n_eligible=r.n_eligible,
            stealth=trig.stealth(ref_x),
            config=trig.describe(),
        )

    return {
        "clean_acc": clean.accuracy,
        "clean_mf1": clean.macro_f1,
        "clean_acc_ci": clean_ci,
        "n_clean": clean.n,
        "asr": asr,
        "target_class": target_class,
    }


def run_audit(
    model: nn.Module,
    loader,
    triggers: list[Trigger],
    target_class: int,
    *,
    exp_id: str,
    dataset: str,
    source: str,
    target: str,
    model_type: str,
    adaptation: str = "none",
    defense: str = "none",
    seed: int = 42,
    device: torch.device | str = "cpu",
    config_hash: str = "",
    defense_info: dict[str, Any] | None = None,
    source_metrics: dict[str, Any] | None = None,
    notes: str = "",
    bootstrap_n: int = 1000,
) -> RunResult:
    """Evaluate one model and return a RunResult."""
    t0 = time.time()
    m = evaluate(model, loader, triggers, target_class, device, bootstrap_n, seed)
    src = source_metrics or {}
    return RunResult(
        exp_id=exp_id,
        dataset=dataset,
        source=str(source),
        target=str(target),
        model_type=model_type,
        adaptation=adaptation,
        defense=defense,
        seed=seed,
        clean_acc=m["clean_acc"],
        clean_mf1=m["clean_mf1"],
        clean_acc_ci=m["clean_acc_ci"],
        n_clean=m["n_clean"],
        asr=m["asr"],
        target_class=target_class,
        source_clean_acc=src.get("clean_acc"),
        source_asr=src.get("asr", {}),
        defense_info=defense_info or {},
        config_hash=config_hash,
        duration_s=time.time() - t0,
        notes=notes,
    )
