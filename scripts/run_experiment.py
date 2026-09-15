"""Run experiments and append the results to results/runs.jsonl.

Single run:
    python scripts/run_experiment.py --exp E4 --ckpt CKPT --adapt mapu --attack-family patch

Full matrix (trains any missing source checkpoints):
    python scripts/run_experiment.py --matrix --seeds 42 43 44
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from src.experiments import run_row
from src.mapu.train_source import train_source
from src.utils.config import apply_overrides, load_config, load_yaml

ATTACK_FAMILIES = ["patch", "freq", "gaussian"]


def source_ckpt(out_dir: str, tag: str, dataset: str, src: int, seed: int) -> Path:
    return Path(out_dir) / f"source_{tag}_{dataset}_s{src}_seed{seed}.pt"


def ensure_sources(train_cfg, seeds, families, out_dir, force=False):
    """Train the clean and per-family backdoored source checkpoints if absent."""
    data = train_cfg["data"]
    made = {}
    for seed in seeds:
        for fam in ["clean", *families]:
            tag = "clean" if fam == "clean" else f"bd-{fam}"
            path = source_ckpt(out_dir, tag, data["name"], data["source_subject"], seed)
            if path.exists() and not force:
                print(f"[sources] reuse {path}")
            else:
                cfg = {**train_cfg, "seed": seed, "out_dir": out_dir}
                if fam != "clean":
                    cfg["attack"] = load_yaml(f"configs/attack/{fam}.yaml")
                else:
                    cfg.pop("attack", None)
                print(f"[sources] training {tag} seed={seed}")
                train_source(cfg, tag=tag)
            made[(seed, fam)] = path
    return made


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exp", type=str, default=None)
    ap.add_argument("--ckpt", type=Path, default=None)
    ap.add_argument("--adapt", type=str, default="none", choices=["none", "mapu", "shot"])
    ap.add_argument("--defense", type=Path, default=None)
    ap.add_argument("--attack-family", type=str, default="")
    ap.add_argument("--model-type", type=str, default="backdoored", choices=["clean", "backdoored"])
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--matrix", action="store_true", help="run the full E1-E10 + A1 matrix")
    ap.add_argument("--seeds", type=int, nargs="+", default=[42])
    ap.add_argument("--families", type=str, nargs="+", default=ATTACK_FAMILIES)
    ap.add_argument("--exps", type=str, nargs="+", default=None, help="subset of rows to run")
    ap.add_argument("--source-config", type=Path, default=Path("configs/train/source.yaml"))
    ap.add_argument("--adapt-config", type=Path, default=Path("configs/train/mapu.yaml"))
    ap.add_argument("--eval-config", type=Path, default=Path("configs/eval/audit.yaml"))
    ap.add_argument("--out", type=Path, default=Path("results/runs.jsonl"))
    ap.add_argument("--ckpt-dir", type=str, default="checkpoints")
    ap.add_argument("--device", type=str, default="cuda")
    ap.add_argument("--force-sources", action="store_true")
    ap.add_argument("--set", nargs="*", default=None)
    args = ap.parse_args()

    eval_cfg = load_yaml(args.eval_config)
    adapt_cfg = apply_overrides(load_config(args.adapt_config), args.set)
    adapt_cfg["device"] = args.device

    if not args.matrix:
        if args.ckpt is None or args.exp is None:
            raise SystemExit("--exp and --ckpt are required unless --matrix is given")
        r = run_row(
            args.exp,
            args.ckpt,
            model_type=args.model_type,
            seed=args.seed,
            adapt_cfg=adapt_cfg,
            method=args.adapt,
            defense_cfg=load_yaml(args.defense) if args.defense else None,
            defense_name=load_yaml(args.defense)["name"] if args.defense else "none",
            attack_family=args.attack_family,
            eval_cfg=eval_cfg,
            out_dir=args.ckpt_dir,
            device=args.device,
        )
        r.append_to(args.out)
        print(
            f"[run] {r.exp_id} clean_mf1={r.clean_mf1:.3f} "
            + " ".join(f"ASR({k})={v.asr:.3f}" for k, v in r.asr.items())
        )
        return

    train_cfg = apply_overrides(load_config(args.source_config), args.set)
    train_cfg["device"] = args.device
    sources = ensure_sources(
        train_cfg, args.seeds, args.families, args.ckpt_dir, args.force_sources
    )

    static_def = load_yaml("configs/defense/static.yaml")
    dynamic_def = load_yaml("configs/defense/dynamic.yaml")
    cons_def = load_yaml("configs/defense/consistency.yaml")
    sam_def = load_yaml("configs/defense/sam.yaml")
    combo_def = load_yaml("configs/defense/combined.yaml")
    combo_kt_def = load_yaml("configs/defense/combined_kt.yaml")

    all_exps = {"E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "E9", "A1", "E10"}
    wanted = set(args.exps) if args.exps else all_exps
    t0 = time.time()
    n = 0
    for seed in args.seeds:
        clean = sources[(seed, "clean")]
        plan: list[tuple] = []
        if "E1" in wanted:
            plan.append(("E1", clean, "clean", "none", None, "none", ""))
        if "E2" in wanted:
            plan.append(("E2", clean, "clean", "mapu", None, "none", ""))
        for fam in args.families:
            bd = sources[(seed, fam)]
            if "E3" in wanted:
                plan.append(("E3", bd, "backdoored", "none", None, "none", fam))
            if "E4" in wanted:
                plan.append(("E4", bd, "backdoored", "mapu", None, "none", fam))
            if "E5" in wanted:
                plan.append(("E5", bd, "backdoored", "mapu", static_def, static_def["name"], fam))
            if "E6" in wanted:
                plan.append(("E6", bd, "backdoored", "mapu", dynamic_def, dynamic_def["name"], fam))
            if "E7" in wanted:
                plan.append(("E7", bd, "backdoored", "mapu", cons_def, cons_def["name"], fam))
            if "E8" in wanted:
                plan.append(("E8", bd, "backdoored", "mapu", combo_def, combo_def["name"], fam))
            if "E9" in wanted:
                plan.append(("E9", bd, "backdoored", "mapu", sam_def, sam_def["name"], fam))
            if "A1" in wanted:
                plan.append(("A1", bd, "backdoored", "shot", None, "none", fam))
            if "E10" in wanted:
                plan.append(
                    ("E10", bd, "backdoored", "mapu", combo_kt_def, combo_kt_def["name"], fam)
                )

        for exp, ck, mtype, method, dcfg, dname, fam in plan:
            print(
                f"\n===== {exp} seed={seed} family={fam or '-'} "
                f"method={method} defense={dname} ====="
            )
            r = run_row(
                exp,
                ck,
                model_type=mtype,
                seed=seed,
                adapt_cfg=adapt_cfg,
                method=method,
                defense_cfg=dcfg,
                defense_name=dname,
                attack_family=fam,
                eval_cfg=eval_cfg,
                out_dir=args.ckpt_dir,
                device=args.device,
            )
            r.append_to(args.out)
            n += 1
            print(
                f"[{exp}] clean_mf1={r.clean_mf1:.3f} acc={r.clean_acc:.3f} "
                + " ".join(f"ASR({k})={v.asr:.3f}" for k, v in r.asr.items())
            )

    print(f"\n[matrix] {n} rows in {(time.time() - t0) / 60:.1f} min -> {args.out}")


if __name__ == "__main__":
    main()
