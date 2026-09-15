"""Shared test fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
TINY_HAR = REPO_ROOT / "tests" / "fixtures" / "tiny_har.npz"


@pytest.fixture
def tiny_batch() -> tuple[torch.Tensor, torch.Tensor]:
    """A single batch shaped like real HAR data, with a fixed seed."""
    g = torch.Generator().manual_seed(0)
    x = torch.randn(8, 9, 128, generator=g)
    y = torch.randint(0, 6, (8,), generator=g)
    return x, y


@pytest.fixture
def tiny_har_path() -> Path:
    """Path to the committed HAR subset used by the fast tests."""
    if not TINY_HAR.exists():
        pytest.skip(f"{TINY_HAR} missing; run scripts/make_tiny_fixture.py")
    return TINY_HAR
