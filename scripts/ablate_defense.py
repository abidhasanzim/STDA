"""Ablation of the SSDA-style defense.

Toggles compression and knowledge transfer with the spectral penalty off, then sweeps the
penalty weight lambda with and without knowledge transfer.
"""

from __future__ import annotations

import argparse
import copy
from pathlib import Path

from src.experiments import run_row
from src.utils.config import load_config, load_yaml


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--family", type=str, default="patch")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--ckpt-dir", type=str, default="checkpoints")
    ap.add_argument("--dataset", type=str, default="har")
    ap.add_argument("--source-subject", type=int, default=2)
    ap.add_argument("--out", type=Path, default=Path("results/ablation.jsonl"))
    ap.add_argument("--device", type=str, default="cuda")
    ap.add_argument(
        "--lambdas",
        type=float,
        nargs="+",
        default=[0.0, 1e-4, 1e-3, 1e-2, 1e-1, 1.0, 100.0],
    )
    args = ap.parse_args()

    ckpt = (
        Path(args.ckpt_dir)
        / f"source_bd-{args.family}_{args.dataset}_s{args.source_subject}_seed{args.seed}.pt"
    )
    if not ckpt.exists():
        raise SystemExit(f"missing {ckpt}; run scripts/run_experiment.py --matrix first")

    adapt_cfg = load_config("configs/train/mapu.yaml")
    adapt_cfg["device"] = args.device
    eval_cfg = load_yaml("configs/eval/audit.yaml")
    base = load_yaml("configs/defense/dynamic.yaml")

    conditions: list[tuple[str, dict]] = []
    # components, penalty off
    for compress in (True, False):
        for kt in (True, False):
            if not compress and not kt:
                continue
            d = {**base, "compress": compress, "knowledge_transfer": kt, "spectral_weight": 0.0}
            conditions.append((f"C{int(compress)}-KT{int(kt)}-lam0", d))
    # lambda sweep, full pipeline
    for lam in args.lambdas:
        d = {**base, "compress": True, "knowledge_transfer": True, "spectral_weight": lam}
        conditions.append((f"full-lam{lam:g}", d))
    # lambda sweep without knowledge transfer
    for lam in args.lambdas:
        d = {**base, "compress": True, "knowledge_transfer": False, "spectral_weight": lam}
        conditions.append((f"noKT-lam{lam:g}", d))

    print(f"{'condition':22s} {'MF1':>6s} {'ASR':>6s}  zeroed  note")
    for name, dcfg in conditions:
        r = run_row(
            f"AB:{name}",
            ckpt,
            model_type="backdoored",
            seed=args.seed,
            adapt_cfg=copy.deepcopy(adapt_cfg),
            method="mapu",
            defense_cfg=dcfg,
            defense_name=name,
            attack_family=args.family,
            eval_cfg=eval_cfg,
            out_dir=args.ckpt_dir,
            device=args.device,
        )
        r.notes = "defense ablation"
        r.append_to(args.out)
        t = r.asr.get(args.family)
        nz = r.defense_info.get("n_zeroed", 0)
        mag = r.defense_info.get("compressed_channel_absmean_final")
        note = f"compressed |w| final={mag:.2e}" if mag is not None else ""
        print(f"{name:22s} {r.clean_mf1:6.3f} {t.asr if t else float('nan'):6.3f}  {nz:>6}  {note}")

    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
