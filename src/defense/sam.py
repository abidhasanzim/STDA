"""Sharpness-aware minimization, following FT-SAM (Zhu et al., ICCV 2023).

FT-SAM fine-tunes on labelled clean data; here the same optimizer is applied to MAPU's
unsupervised adaptation loss. The adaptive (ASAM) variant is used, with one global gradient
norm, and BatchNorm running statistics are frozen during the perturbed forward pass.
"""

from __future__ import annotations

from collections.abc import Callable

import torch
from torch import nn


class SAM(torch.optim.Optimizer):
    """Two-step sharpness-aware wrapper around a base optimizer.

    With adaptive=True the perturbation is scaled by |w|, so rho is relative to the weight
    magnitude rather than an absolute radius.
    """

    def __init__(self, params, base_optimizer_cls, rho: float = 2.0, adaptive: bool = True, **kw):
        if rho < 0.0:
            raise ValueError(f"rho must be non-negative, got {rho}")
        defaults = dict(rho=rho, adaptive=adaptive, **kw)
        super().__init__(params, defaults)
        self.base_optimizer = base_optimizer_cls(self.param_groups, **kw)
        self.param_groups = self.base_optimizer.param_groups
        self.defaults.update(self.base_optimizer.defaults)

    def _grad_norm(self) -> torch.Tensor:
        """Global norm over all parameters, |w|-scaled when adaptive."""
        shared = self.param_groups[0]["params"][0].device
        return torch.norm(
            torch.stack(
                [
                    ((torch.abs(p) if group["adaptive"] else 1.0) * p.grad).norm(p=2).to(shared)
                    for group in self.param_groups
                    for p in group["params"]
                    if p.grad is not None
                ]
            ),
            p=2,
        )

    @torch.no_grad()
    def first_step(self, zero_grad: bool = False) -> None:
        """Ascend to w + eps."""
        grad_norm = self._grad_norm()
        for group in self.param_groups:
            scale = group["rho"] / (grad_norm + 1e-12)
            for p in group["params"]:
                if p.grad is None:
                    continue
                e_w = (torch.pow(p, 2) if group["adaptive"] else 1.0) * p.grad * scale.to(p)
                p.add_(e_w)
                self.state[p]["e_w"] = e_w
        if zero_grad:
            self.zero_grad(set_to_none=True)

    @torch.no_grad()
    def second_step(self, zero_grad: bool = False) -> None:
        """Restore w, then step with the gradient measured at w + eps."""
        for group in self.param_groups:
            for p in group["params"]:
                if p.grad is None or "e_w" not in self.state[p]:
                    continue
                p.sub_(self.state[p]["e_w"])
        self.base_optimizer.step()
        if zero_grad:
            self.zero_grad(set_to_none=True)

    @torch.no_grad()
    def step(self, closure: Callable[[], torch.Tensor] | None = None):  # type: ignore[override]
        if closure is None:
            raise ValueError("SAM.step requires a closure that reevaluates the loss")
        closure = torch.enable_grad()(closure)
        loss = closure()
        self.first_step(zero_grad=True)
        closure()
        self.second_step()
        return loss


def _set_bn_momentum(model: nn.Module, momentum) -> None:
    for m in model.modules():
        if isinstance(m, nn.modules.batchnorm._BatchNorm):
            if momentum is None:  # restore
                if hasattr(m, "_sam_backup_momentum"):
                    m.momentum = m._sam_backup_momentum
            else:
                if not hasattr(m, "_sam_backup_momentum"):
                    m._sam_backup_momentum = m.momentum
                m.momentum = momentum


def disable_running_stats(model: nn.Module) -> None:
    """Freeze BatchNorm running statistics for the perturbed forward pass."""
    _set_bn_momentum(model, 0.0)


def enable_running_stats(model: nn.Module) -> None:
    _set_bn_momentum(model, None)


def build_sam(
    params,
    rho: float = 2.0,
    lr: float = 1e-4,
    weight_decay: float = 1e-4,
    adaptive: bool = True,
    base: str = "adam",
) -> SAM:
    cls = {"adam": torch.optim.Adam, "sgd": torch.optim.SGD}[base.lower()]
    kw = {"lr": lr, "weight_decay": weight_decay}
    if base.lower() == "sgd":
        kw["momentum"] = 0.9
    return SAM(params, cls, rho=rho, adaptive=adaptive, **kw)
