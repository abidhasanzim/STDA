"""CLI tests on the committed fixture (CPU only)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from src.cli import main
from src.mapu.train_source import train_source
from src.utils.config import load_yaml

pytestmark = pytest.mark.fast

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _no_tracking(monkeypatch):
    monkeypatch.setenv("SFDA_NO_TRACKING", "1")


def _train_tiny(tmp_path, tiny_har_path, attack: bool):
    data_cfg = {
        "name": "har",
        "npz_path": str(tiny_har_path),
        "source_subject": 2,
        "target_subject": 11,
        "batch_size": 16,
        "test_ratio": 0.25,
        "seed": 0,
        "n_channels": 9,
        "n_classes": 6,
    }
    cfg = {
        "epochs": 3,
        "batch_size": 16,
        "pre_learning_rate": 1e-3,
        "weight_decay": 1e-4,
        "label_smoothing": 0.1,
        "seed": 0,
        "device": "cpu",
        "log_every": 5,
        "num_splits": 8,
        "num_masked": 1,
        "detach_clean_target": True,
        "out_dir": str(tmp_path),
        "data": data_cfg,
        "model": load_yaml(REPO / "configs/model/cnn.yaml"),
    }
    if attack:
        cfg["attack"] = load_yaml(REPO / "configs/attack/patch.yaml")
    ckpt, _ = train_source(cfg, tag="cli-bd" if attack else "cli-clean")
    return ckpt


def _run_cli(ckpt, out, extra=None):
    argv = ["run", "--checkpoint", str(ckpt), "--out", str(out), "--device", "cpu", "--seed", "0"]
    return main(argv + (extra or []))


def test_cli_writes_report_and_json(tmp_path, tiny_har_path, capsys):
    ckpt = _train_tiny(tmp_path, tiny_har_path, attack=True)
    out = tmp_path / "audit"
    code = _run_cli(ckpt, out)

    assert code in (0, 2), f"unexpected exit code {code}"
    report = (out / "report.md").read_text()
    for section in ("Threat model", "Attack success rate", "Thresholds", "Limitations", "Verdict"):
        assert section in report, f"report is missing '{section}'"

    payload = json.loads((out / "result.json").read_text())
    assert payload["verdict"]["label"] in {"PASS", "WARN", "FAIL"}
    assert set(payload["asr"]) == {"patch", "freq", "gaussian"}
    assert 0.0 <= payload["clean_acc"] <= 1.0
    assert payload["verdict"]["thresholds"]["fail_above"] == 0.5

    printed = capsys.readouterr().out
    assert "VERDICT" in printed


def test_exit_code_signals_fail(tmp_path, tiny_har_path):
    """A FAIL verdict should give a non-zero exit code."""
    ckpt = _train_tiny(tmp_path, tiny_har_path, attack=True)
    out = tmp_path / "audit_bd"
    code = _run_cli(ckpt, out)
    payload = json.loads((out / "result.json").read_text())
    assert (code == 2) == (payload["verdict"]["label"] == "FAIL")


def test_table_subcommand(tmp_path, tiny_har_path):
    ckpt = _train_tiny(tmp_path, tiny_har_path, attack=False)
    out = tmp_path / "audit_clean"
    _run_cli(ckpt, out)

    from src.eval.schema import RunResult

    runs = tmp_path / "runs.jsonl"
    payload = json.loads((out / "result.json").read_text())
    payload.pop("verdict", None)
    RunResult.from_dict(payload).append_to(runs)

    code = main(["table", "--runs", str(runs), "--out", str(tmp_path / "table.md")])
    assert code == 0
    table = (tmp_path / "table.md").read_text()
    assert "ASR (installed)" in table and "ctrl: patch" in table


def test_table_on_missing_runs_is_a_clean_error(tmp_path, capsys):
    code = main(["table", "--runs", str(tmp_path / "nope.jsonl"), "--out", str(tmp_path / "t.md")])
    assert code == 1
    assert "no runs found" in capsys.readouterr().err


@pytest.mark.parametrize(
    "extra, match",
    [
        (["--defense", "combined"], "add --adapt"),
        (["--adapt", "mapu", "--defense", "typo"], "unknown defense"),
    ],
)
def test_bad_defense_arguments_fail_before_auditing(tmp_path, capsys, extra, match):
    ckpt = tmp_path / "model.pt"
    ckpt.touch()
    code = _run_cli(ckpt, tmp_path / "audit", extra)
    captured = capsys.readouterr()
    assert code == 1
    assert match in captured.err
    assert "auditing" not in captured.out
