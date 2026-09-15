"""End-to-end harness test with random models on the committed fixture.

A random model should score at chance on both clean accuracy and ASR. Individual random
models collapse to one class, so the check is on the mean over several models and target
classes.
"""

from __future__ import annotations

import numpy as np
import pytest
import torch
from src.attack import FreqTrigger, PatchTrigger
from src.data.loaders import build_loaders
from src.eval.report import write_audit_report, write_markdown_table
from src.eval.runner import run_audit
from src.eval.schema import RunResult, load_runs
from src.models.model import build_model
from src.utils.seed import set_seed

pytestmark = pytest.mark.fast

CHANCE = 1 / 6
TOL = 0.09  # chance +- 9 points, over 8 inits x 6 target classes


@pytest.fixture
def bundle(tiny_har_path):
    return build_loaders(
        {
            "npz_path": str(tiny_har_path),
            "source_subject": 2,
            "target_subject": 11,
            "batch_size": 16,
            "test_ratio": 0.25,
            "seed": 42,
        }
    )


def _triggers(bundle):
    std = torch.as_tensor(bundle.scaler["std"])
    return [
        PatchTrigger(channels=[0, 1, 2], t_start=100, t_len=10, amplitude=2.0, channel_std=std),
        FreqTrigger(channels="all", freq_hz=10.0, amplitude=0.5, channel_std=std),
    ]


def test_random_model_scores_at_chance(bundle):
    accs, asrs = [], []
    for seed in range(8):
        set_seed(seed)
        m = build_model({}, {"n_channels": 9, "n_classes": 6})
        m.set_scaler(bundle.scaler)
        for target_class in range(6):
            r = run_audit(
                m,
                bundle.target_test,
                _triggers(bundle),
                target_class=target_class,
                exp_id="E0-random",
                dataset="har",
                source="2",
                target="11",
                model_type="random",
                seed=seed,
                bootstrap_n=50,
            )
            if target_class == 0:
                accs.append(r.clean_acc)
            asrs += [t.asr for t in r.asr.values()]

    mean_acc, mean_asr = float(np.mean(accs)), float(np.mean(asrs))
    z = np.asarray(asrs)
    # printed so the calibration numbers can be read with pytest -s
    print(
        f"\n[calibration] clean_acc={mean_acc:.4f} asr={mean_asr:.4f} chance={CHANCE:.4f} "
        f"at~0={(z < 0.02).mean():.1%} at~1={(z > 0.98).mean():.1%} n_asr={z.size}"
    )
    assert abs(mean_acc - CHANCE) < TOL, f"random clean acc {mean_acc:.3f} is not chance"
    assert abs(mean_asr - CHANCE) < TOL, (
        f"random ASR {mean_asr:.3f} is not chance — the harness is manufacturing signal"
    )


def test_audit_produces_a_complete_row(bundle):
    set_seed(0)
    m = build_model({}, {"n_channels": 9, "n_classes": 6})
    m.set_scaler(bundle.scaler)
    r = run_audit(
        m,
        bundle.target_test,
        _triggers(bundle),
        target_class=0,
        exp_id="E0",
        dataset="har",
        source="2",
        target="11",
        model_type="random",
        seed=0,
        bootstrap_n=50,
    )
    assert set(r.asr) == {"patch", "freq"}
    assert r.n_clean == len(bundle.target_test.dataset)
    for t in r.asr.values():
        assert 0.0 <= t.asr <= 1.0
        assert t.asr_ci[0] <= t.asr <= t.asr_ci[1] + 1e-9
        assert t.n_eligible > 0
        assert t.stealth["relative_l2"] > 0


def test_schema_roundtrip_and_jsonl(bundle, tmp_path):
    set_seed(0)
    m = build_model({}, {"n_channels": 9, "n_classes": 6})
    m.set_scaler(bundle.scaler)
    r = run_audit(
        m,
        bundle.target_test,
        _triggers(bundle),
        0,
        exp_id="E0",
        dataset="har",
        source="2",
        target="11",
        model_type="random",
        seed=0,
        bootstrap_n=50,
    )
    back = RunResult.from_json(r.to_json())
    assert back.exp_id == r.exp_id and back.seed == r.seed
    assert back.clean_acc == pytest.approx(r.clean_acc)
    assert back.asr["patch"].asr == pytest.approx(r.asr["patch"].asr)
    assert back.asr["patch"].asr_ci == pytest.approx(r.asr["patch"].asr_ci)

    p = tmp_path / "runs.jsonl"
    r.append_to(p)
    r.append_to(p)
    assert len(load_runs(p)) == 2


def test_report_artifacts_render(bundle, tmp_path):
    set_seed(0)
    m = build_model({}, {"n_channels": 9, "n_classes": 6})
    m.set_scaler(bundle.scaler)
    r = run_audit(
        m,
        bundle.target_test,
        _triggers(bundle),
        0,
        exp_id="E0",
        dataset="har",
        source="2",
        target="11",
        model_type="random",
        seed=0,
        bootstrap_n=50,
    )
    table = write_markdown_table([r], tmp_path / "table.md")
    report = write_audit_report(r, tmp_path / "report.md", channel_ranking=[(3, 1.2), (7, 1.1)])
    t, rep = table.read_text(), report.read_text()
    assert "ASR (installed)" in t and "ctrl: patch" in t and "2->11" in t
    for needed in ("Threat model", "Attack success rate", "Thresholds", "Limitations", "Verdict"):
        assert needed in rep, f"report missing section: {needed}"
