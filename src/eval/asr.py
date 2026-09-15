"""Attack success rate.

ASR is the fraction of triggered test windows predicted as the target class, computed
only over windows whose true label is not already the target class. The inclusive rate
and the untriggered target-class rate (the baseline an attack has to beat) are returned
alongside it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import torch
from torch import nn

from src.attack.base import Trigger


@dataclass
class ASRResult:
    asr: float
    asr_inclusive: float
    clean_target_rate: float
    lift: float
    n_eligible: int
    n_total: int
    success: np.ndarray = field(repr=False)  # per-sample bool over eligible windows
    preds: np.ndarray = field(repr=False)
    labels: np.ndarray = field(repr=False)


@torch.no_grad()
def attack_success_rate(
    model: nn.Module,
    loader,
    trigger: Trigger,
    target_class: int,
    device: torch.device | str = "cpu",
) -> ASRResult:
    model.eval()
    device = torch.device(device)
    model.to(device)

    trig_preds, clean_preds, labels = [], [], []
    for x, y in loader:
        xt = trigger.apply(x).to(device)
        trig_preds.append(model(xt).argmax(1).cpu())
        clean_preds.append(model(x.to(device)).argmax(1).cpu())
        labels.append(y)
    if not labels:
        raise ValueError("empty loader: nothing to evaluate")

    tp = torch.cat(trig_preds).numpy()
    cp = torch.cat(clean_preds).numpy()
    y = torch.cat(labels).numpy()

    eligible = y != target_class
    n_eligible = int(eligible.sum())
    if n_eligible == 0:
        raise ValueError(
            f"every window has true label {target_class}; ASR is undefined for this split"
        )

    success = tp[eligible] == target_class
    clean_rate = float((cp[eligible] == target_class).mean())
    asr = float(success.mean())
    return ASRResult(
        asr=asr,
        asr_inclusive=float((tp == target_class).mean()),
        clean_target_rate=clean_rate,
        lift=asr - clean_rate,
        n_eligible=n_eligible,
        n_total=int(y.size),
        success=success,
        preds=tp,
        labels=y,
    )
