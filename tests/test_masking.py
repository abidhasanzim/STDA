"""Temporal masking: contiguous blocks, exact ratio, per-channel selection."""

from __future__ import annotations

import pytest
import torch
from src.mapu.masking import masking_ratio, random_mask

pytestmark = pytest.mark.fast


@pytest.fixture
def x() -> torch.Tensor:
    g = torch.Generator().manual_seed(3)
    # strictly non-zero so that zeros mark masked samples
    return torch.rand(4, 9, 128, generator=g) + 1.0


def test_masks_exactly_one_eighth(x):
    xm, mask = random_mask(x, num_splits=8, num_masked=1)
    assert xm.shape == x.shape
    assert float((xm == 0).float().mean()) == pytest.approx(0.125)
    assert mask.shape == (9, 8)
    assert mask.sum(dim=1).tolist() == [1] * 9
    assert masking_ratio(8, 1) == 0.125


@pytest.mark.parametrize("num_masked", [0, 1, 2, 4, 8])
def test_ratio_scales(x, num_masked):
    xm, _ = random_mask(x, num_splits=8, num_masked=num_masked)
    assert float((xm == 0).float().mean()) == pytest.approx(num_masked / 8)


def test_masked_span_is_contiguous(x):
    xm, mask = random_mask(x, num_splits=8, num_masked=1)
    block = 128 // 8
    for c in range(9):
        zeros = (xm[0, c] == 0).nonzero().flatten()
        assert len(zeros) == block
        assert zeros.max() - zeros.min() == block - 1, "masked span is not contiguous"
        b = int(mask[c].nonzero().flatten()[0])
        assert int(zeros.min()) == b * block


def test_unmasked_positions_are_untouched(x):
    xm, mask = random_mask(x, num_splits=8, num_masked=2)
    keep = ~mask.repeat_interleave(128 // 8, dim=1)  # (C, T): True where the block survives
    assert keep.sum().item() == 9 * 128 * 6 // 8
    for c in range(9):
        torch.testing.assert_close(xm[:, c, keep[c]], x[:, c, keep[c]], rtol=0, atol=0)


def test_selection_is_per_channel_and_shared_across_batch(x):
    """Masks are chosen per channel and shared across the batch."""
    xm, _ = random_mask(x, num_splits=8, num_masked=1)
    zeros_per_sample = [(xm[i] == 0).nonzero()[:, 1].tolist() for i in range(x.shape[0])]
    assert all(z == zeros_per_sample[0] for z in zeros_per_sample), "mask differs across the batch"
    # channels should not all pick the same block
    starts = {int((xm[0, c] == 0).nonzero().flatten().min()) for c in range(9)}
    assert len(starts) > 1, "every channel masked the same block"


def test_input_not_mutated(x):
    before = x.clone()
    random_mask(x, 8, 1)
    torch.testing.assert_close(x, before, rtol=0, atol=0)


def test_generator_makes_it_reproducible(x):
    a, _ = random_mask(x, 8, 1, generator=torch.Generator().manual_seed(5))
    b, _ = random_mask(x, 8, 1, generator=torch.Generator().manual_seed(5))
    torch.testing.assert_close(a, b, rtol=0, atol=0)


@pytest.mark.parametrize(
    "kw, match",
    [
        ({"num_splits": 7}, "must divide"),
        ({"num_masked": 9}, "must lie in"),
        ({"num_masked": -1}, "must lie in"),
    ],
)
def test_rejects_bad_config(x, kw, match):
    with pytest.raises(ValueError, match=match):
        random_mask(x, **{"num_splits": 8, "num_masked": 1, **kw})
