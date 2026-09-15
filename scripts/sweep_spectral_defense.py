"""Defense sweeps on the freq trigger.

By default compares frequency-domain masking, spectral consistency, compression strength
and combinations. With --curve it runs only the compression-strength sweep used for
results/compression_curve.png.
"""

from __future__ import annotations

import argparse
import copy
from pathlib import Path

from src.experiments import run_row
from src.utils.config import load_config, load_yaml


def conditions(base_def: dict, curve_only: bool = False) -> list[tuple[str, dict, dict | None]]:
    """List of (label, adapt-config overrides, defense config or None)."""
    out: list[tuple[str, dict, dict | None]] = []

    out.append(("baseline (time mask)", {}, None))
    if curve_only:
        # compression-strength curve only
        res = []
        for k in (4, 8, 16, 24, 32, 40, 48, 64):
            d = {
                **base_def,
                "compress": True,
                "knowledge_transfer": False,
                "spectral_weight": 0.0,
                "gamma": None,
                "k": k,
            }
            res.append((f"compress top-k={k}", {}, d))
        return [out[0]] + res

    # frequency-domain masking
    for bands in (1, 2, 4):
        out.append(
            (f"freq mask {bands}/8", {"mask_domain": "freq", "num_masked_bands": bands}, None)
        )
    out.append(("both masks 1/8", {"mask_domain": "both", "num_masked_bands": 1}, None))
    out.append(("both masks 2/8", {"mask_domain": "both", "num_masked_bands": 2}, None))

    # spectral consistency
    for wt in (0.5, 1.0, 5.0):
        out.append((f"spec-consistency w={wt}", {"spec_consistency_wt": wt}, None))

    # compression strength
    for gamma in (0.5, 1.0, 1.5, 2.0):
        d = {
            **base_def,
            "compress": True,
            "knowledge_transfer": False,
            "spectral_weight": 0.0,
            "gamma": gamma,
            "k": None,
        }
        out.append((f"compress gamma={gamma}", {}, d))
    for k in (8, 16, 32, 64):
        d = {
            **base_def,
            "compress": True,
            "knowledge_transfer": False,
            "spectral_weight": 0.0,
            "gamma": None,
            "k": k,
        }
        out.append((f"compress top-k={k}", {}, d))

    # combinations
    best_compress = {
        **base_def,
        "compress": True,
        "knowledge_transfer": False,
        "spectral_weight": 0.0,
        "gamma": 1.0,
        "k": None,
    }
    out.append(
        (
            "compress + freq mask 2/8",
            {"mask_domain": "freq", "num_masked_bands": 2},
            dict(best_compress),
        )
    )
    out.append(
        ("compress + both 2/8", {"mask_domain": "both", "num_masked_bands": 2}, dict(best_compress))
    )
    out.append(
        ("compress + spec-consistency w=1", {"spec_consistency_wt": 1.0}, dict(best_compress))
    )
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--family", type=str, default="freq")
    ap.add_argument("--seeds", type=int, nargs="+", default=[42])
    ap.add_argument("--ckpt-dir", type=str, default="checkpoints")
    ap.add_argument("--out", type=Path, default=Path("results/spectral_defense.jsonl"))
    ap.add_argument("--device", type=str, default="cuda")
    ap.add_argument("--only", type=str, nargs="+", default=None, help="substring filter on labels")
    ap.add_argument(
        "--curve",
        action="store_true",
        help="run only the dense compression-strength sweep used for "
        "results/compression_curve.png (pass --out results/tradeoff_curve.jsonl)",
    )
    args = ap.parse_args()

    adapt_base = load_config("configs/train/mapu.yaml")
    adapt_base["device"] = args.device
    eval_cfg = load_yaml("configs/eval/audit.yaml")
    base_def = load_yaml("configs/defense/static.yaml")

    conds = conditions(base_def, curve_only=args.curve)
    if args.only:
        conds = [c for c in conds if any(o.lower() in c[0].lower() for o in args.only)]

    print(f"{'condition':32s} {'seed':>4s} {'MF1':>6s} {'ASR':>7s}  zeroed")
    for label, over, dcfg in conds:
        for seed in args.seeds:
            cfg = copy.deepcopy(adapt_base)
            cfg.update(over)
            cfg["seed"] = seed
            ckpt = Path(args.ckpt_dir) / f"source_bd-{args.family}_har_s2_seed{seed}.pt"
            if not ckpt.exists():
                raise SystemExit(f"missing {ckpt}")
            r = run_row(
                f"SD:{label}",
                ckpt,
                model_type="backdoored",
                seed=seed,
                adapt_cfg=cfg,
                method="mapu",
                defense_cfg=dcfg,
                defense_name=label if dcfg else "none",
                attack_family=args.family,
                eval_cfg=eval_cfg,
                out_dir=args.ckpt_dir,
                device=args.device,
            )
            r.notes = f"spectral-defense sweep | {label}"
            r.append_to(args.out)
            t = r.asr.get(args.family)
            nz = r.defense_info.get("n_zeroed", 0)
            print(f"{label:32s} {seed:>4d} {r.clean_mf1:6.3f} {t.asr:7.3f}  {nz:>6}")

    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
