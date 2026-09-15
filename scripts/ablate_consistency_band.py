"""Does E8 depend on its perturbations covering the evaluated freq trigger?

The consistency defense draws sinusoids from 0.5 Hz to just below Nyquist, which includes the
10 Hz freq trigger. This reruns E8 with 5-15 Hz removed from the draws on every subject pair,
trigger and seed, appends to results/band_ablation_runs.jsonl, and compares with E8.

    python scripts/ablate_consistency_band.py            # run, then report
    python scripts/ablate_consistency_band.py --report   # report from the existing results
"""

from __future__ import annotations

import argparse
import copy
import statistics as st
from pathlib import Path

from src.eval.schema import load_runs
from src.experiments import run_row
from src.utils.config import apply_overrides, load_config, load_yaml

from run_experiment import ATTACK_FAMILIES, ensure_sources
from select_defense import pair_ckpt_dir, pair_overrides, summarize

GROUPS = {
    "tuning": ("results/runs.jsonl", [(2, 11)]),
    "development": ("results/dev_runs.jsonl", [(6, 23), (7, 13), (9, 18), (12, 16)]),
    "test": ("results/test_runs.jsonl", [(18, 27), (20, 5), (24, 8), (28, 27), (30, 20)]),
}
EXCLUDE = [5.0, 15.0]
NAME = "compress+consistency, 5-15 Hz excluded"


def run_all(args) -> None:
    dcfg = {
        **load_yaml("configs/defense/combined.yaml"),
        "name": NAME,
        "cons_freq_exclude": EXCLUDE,
    }
    eval_cfg = load_yaml("configs/eval/audit.yaml")
    pairs = [p for _, (_, ps) in GROUPS.items() for p in ps]
    if args.pairs:
        pairs = [tuple(map(int, p.split("-"))) for p in args.pairs]
    for src, tgt in pairs:
        over = pair_overrides(src, tgt)
        ckpt_dir = pair_ckpt_dir(src, tgt)
        train_cfg = apply_overrides(load_config("configs/train/source.yaml"), over)
        train_cfg["device"] = args.device
        sources = ensure_sources(train_cfg, args.seeds, ATTACK_FAMILIES, ckpt_dir)
        adapt_cfg = apply_overrides(load_config("configs/train/mapu.yaml"), over)
        adapt_cfg["device"] = args.device
        for seed in args.seeds:
            for fam in ATTACK_FAMILIES:
                r = run_row(
                    "BAND:E8",
                    sources[(seed, fam)],
                    model_type="backdoored",
                    seed=seed,
                    adapt_cfg=copy.deepcopy(adapt_cfg),
                    method="mapu",
                    defense_cfg=dcfg,
                    defense_name=NAME,
                    attack_family=fam,
                    eval_cfg=eval_cfg,
                    out_dir=ckpt_dir,
                    device=args.device,
                )
                r.notes = "consistency band ablation"
                r.append_to(args.out)
                print(
                    f"[band] {src}->{tgt} seed={seed} {fam:8s} "
                    f"MF1={r.clean_mf1:.3f} ASR={r.asr[fam].asr:.3f}"
                )


def report(args) -> None:
    ablated = load_runs(args.out)
    lines = [
        "### E8 with 5-15 Hz removed from the consistency perturbations",
        "",
        "Freq ASR is pooled over pairs and seeds for models poisoned with the 10 Hz trigger.",
        "Worst-trigger ASR is the highest seed-mean ASR of the three triggers on a pair,",
        "averaged over pairs. Clean MF1 is pooled over all runs.",
        "",
        "| Pairs | Variant | Freq ASR (%) | Mean worst-trigger ASR (%) | Clean MF1 |",
        "|---|---|---|---|---|",
    ]
    for group, (path, pairs) in GROUPS.items():
        names = {f"{s}->{t}" for s, t in pairs}
        e8 = [r for r in load_runs(path) if r.exp_id == "E8" and r.scenario in names]
        band = [r for r in ablated if r.scenario in names]
        expected = len(pairs) * len(args.seeds) * len(ATTACK_FAMILIES)
        if len(band) != expected or len(e8) != expected:
            raise SystemExit(
                f"{group}: {len(band)} ablation and {len(e8)} E8 runs, expected {expected}"
            )
        for label, runs in (("E8", e8), ("E8, 5-15 Hz excluded", band)):
            s = summarize(runs, lambda r: "x")["x"]
            freq = st.mean(r.asr["freq"].asr for r in runs if r.attack_family == "freq")
            lines.append(
                f"| {group} ({len(pairs)}) | {label} | {100 * freq:.1f} | "
                f"{100 * s['worst_asr']:.1f} | {100 * s['mf1']:.1f} |"
            )
    text = "\n".join(lines) + "\n"
    if args.check:
        if not args.table.exists() or args.table.read_text() != text:
            raise SystemExit(f"{args.table} does not match {args.out}")
        print(f"{args.table} is current")
        return
    args.table.write_text(text)
    print(text)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    ap.add_argument("--out", type=Path, default=Path("results/band_ablation_runs.jsonl"))
    ap.add_argument("--table", type=Path, default=Path("results/band_ablation.md"))
    ap.add_argument("--device", type=str, default="cuda")
    ap.add_argument("--pairs", nargs="+", default=None, help="run only these pairs, e.g. 6-23")
    ap.add_argument("--report", action="store_true", help="only summarize existing results")
    ap.add_argument("--check", action="store_true", help="fail if the table is out of date")
    args = ap.parse_args()

    if not (args.report or args.check):
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text("")
        run_all(args)
    if not args.pairs:
        report(args)


if __name__ == "__main__":
    main()
