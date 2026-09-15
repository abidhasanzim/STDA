"""End-to-end smoke test on the committed fixture: train a source model, adapt it, audit it."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("SFDA_NO_TRACKING", "1")
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src.experiments import audit_checkpoint  # noqa: E402
from src.mapu.adapt import adapt  # noqa: E402
from src.mapu.train_source import train_source  # noqa: E402
from src.utils.config import load_yaml  # noqa: E402

FIXTURE = REPO / "tests/fixtures/tiny_har.npz"


def main() -> int:
    if not FIXTURE.exists():
        print(f"missing fixture {FIXTURE}")
        return 1

    with tempfile.TemporaryDirectory() as tmp:
        data_cfg = {
            "name": "har",
            "npz_path": str(FIXTURE),
            "source_subject": 2,
            "target_subject": 11,
            "batch_size": 16,
            "test_ratio": 0.25,
            "seed": 0,
            "n_channels": 9,
            "n_classes": 6,
        }
        model_cfg = load_yaml(REPO / "configs/model/cnn.yaml")
        attack_cfg = load_yaml(REPO / "configs/attack/patch.yaml")

        src_cfg = {
            "epochs": 3,
            "batch_size": 16,
            "pre_learning_rate": 1e-3,
            "weight_decay": 1e-4,
            "label_smoothing": 0.1,
            "seed": 0,
            "device": "cpu",
            "log_every": 1,
            "num_splits": 8,
            "num_masked": 1,
            "detach_clean_target": True,
            "out_dir": tmp,
            "data": data_cfg,
            "model": model_cfg,
            "attack": attack_cfg,
        }
        ckpt, m = train_source(src_cfg, tag="smoke")
        print(f"[smoke] source trained: acc={m['source_test_acc']:.3f}")

        adapt_cfg = {
            "epochs": 2,
            "batch_size": 16,
            "learning_rate": 1e-4,
            "weight_decay": 1e-4,
            "step_size": 50,
            "lr_decay": 0.5,
            "seed": 0,
            "device": "cpu",
            "log_every": 1,
            "method": "mapu",
            "ent_loss_wt": 0.05897,
            "im": 0.2759,
            "tov_wt": 0.5,
            "num_splits": 8,
            "num_masked": 1,
            "out_dir": tmp,
            "data": data_cfg,
        }
        adapted, am = adapt(ckpt, adapt_cfg, tag="smoke")
        print(f"[smoke] adapted: target_mf1={am['target_test_mf1']:.3f}")

        r = audit_checkpoint(
            adapted,
            exp_id="smoke",
            model_type="backdoored",
            adaptation="mapu",
            defense="none",
            seed=0,
            eval_cfg={
                "triggers": ["configs/attack/patch.yaml"],
                "target_class": 0,
                "bootstrap_n": 50,
            },
            device="cpu",
        )
        print(f"[smoke] audited: clean_mf1={r.clean_mf1:.3f} ASR={r.asr['patch'].asr:.3f}")

        assert 0.0 <= r.clean_mf1 <= 1.0
        assert 0.0 <= r.asr["patch"].asr <= 1.0
        assert r.n_clean > 0
    print("[smoke] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
