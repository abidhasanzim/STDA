"""Seeding and deterministic settings.

Uses torch.use_deterministic_algorithms(warn_only=True), so a few CUDA ops without
deterministic kernels fall back with a warning. CPU runs are fully reproducible.
"""

from __future__ import annotations

import os
import random

import numpy as np
import torch


def set_seed(seed: int, deterministic: bool = True, warn_only: bool = True) -> None:
    os.environ["PYTHONHASHSEED"] = str(seed)
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    if deterministic:
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        torch.use_deterministic_algorithms(True, warn_only=warn_only)


def worker_init_fn(worker_id: int) -> None:
    seed = (torch.initial_seed() + worker_id) % 2**31
    np.random.seed(seed)
    random.seed(seed)
