"""Choose the defense variant on the development subject pairs.

Each candidate is run on every development pair, trigger and seed with MAPU adaptation, and
appended to results/selection_runs.jsonl as it finishes. The rule, fixed before the test
pairs were run: among candidates whose pooled clean macro-F1 is within 2 points of MAPU
without a defense (E4), pick the lowest mean worst-trigger ASR across pairs; if none is,
pick the lowest mean worst-trigger ASR overall.

    python scripts/select_defense.py            # run candidates, then report
    python scripts/select_defense.py --report   # report from the existing results
    python scripts/select_defense.py --check    # fail if results/selection.md is out of date
"""

from __future__ import annotations

import argparse
import copy
import statistics as st
from collections import defaultdict
from pathlib import Path

from src.eval.schema import load_runs
from src.experiments import run_row
from src.utils.config import apply_overrides, load_config, load_yaml

from run_experiment import ATTACK_FAMILIES, ensure_sources

DEV_PAIRS = [(2, 11), (6, 23), (7, 13), (9, 18), (12, 16)]
CANDIDATES = {
    "compress+consistency": {},
    "compress+consistency+kt": {"knowledge_transfer": True},
    "consistency+kt": {"compress": False, "k": None, "knowledge_transfer": True},
    "compress8+consistency": {"k": 8},
    "compress8+consistency+kt": {"k": 8, "knowledge_transfer": True},
}
MF1_TOLERANCE = 0.02


def pair_ckpt_dir(src: int, tgt: int) -> str:
    return "checkpoints" if (src, tgt) == (2, 11) else f"checkpoints/pairs/s{src}t{tgt}"


def pair_overrides(src: int, tgt: int) -> list[str]:
    return [f"data.source_subject={src}", f"data.target_subject={tgt}"]


def run_candidates(args) -> None:
    base = load_yaml("configs/defense/combined.yaml")
    eval_cfg = load_yaml("configs/eval/audit.yaml")
    pairs = DEV_PAIRS
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
        for name, change in CANDIDATES.items():
            dcfg = {**base, **change, "name": name}
            for seed in args.seeds:
                for fam in ATTACK_FAMILIES:
                    r = run_row(
                        f"SEL:{name}",
                        sources[(seed, fam)],
                        model_type="backdoored",
                        seed=seed,
                        adapt_cfg=copy.deepcopy(adapt_cfg),
                        method="mapu",
                        defense_cfg=dcfg,
                        defense_name=name,
                        attack_family=fam,
                        eval_cfg=eval_cfg,
                        out_dir=ckpt_dir,
                        device=args.device,
                    )
                    r.notes = "defense selection"
                    r.append_to(args.out)
                    print(
                        f"[select] {src}->{tgt} {name:26s} seed={seed} {fam:8s} "
                        f"MF1={r.clean_mf1:.3f} ASR={r.asr[fam].asr:.3f}"
                    )


def summarize(runs, label_of) -> dict[str, dict]:
    """Mean worst-trigger ASR across pairs and pooled clean MF1 for each label."""
    cells = defaultdict(list)
    mf1 = defaultdict(list)
    for r in runs:
        label = label_of(r)
        if label is None or not r.attack_family:
            continue
        cells[(label, r.scenario, r.attack_family)].append(r.asr[r.attack_family].asr)
        mf1[label].append(r.clean_mf1)

    out = {}
    for label in mf1:
        worst = {}
        for (lab, scen, _fam), vals in cells.items():
            if lab == label:
                worst[scen] = max(worst.get(scen, 0.0), st.mean(vals))
        out[label] = {
            "worst_asr": st.mean(worst.values()),
            "per_pair": dict(sorted(worst.items())),
            "mf1": st.mean(mf1[label]),
            "n": len(mf1[label]),
        }
    return out


def report(args) -> None:
    pairs = {f"{s}->{t}" for s, t in DEV_PAIRS}
    sel = load_runs(args.out)
    baseline = [
        r
        for path in args.baseline_runs
        for r in load_runs(path)
        if r.exp_id == "E4" and r.scenario in pairs
    ]
    summary = summarize(sel, lambda r: r.exp_id.removeprefix("SEL:"))
    ref = summarize(baseline, lambda r: "E4")["E4"]

    expected = len(DEV_PAIRS) * len(args.seeds) * len(ATTACK_FAMILIES)
    for name in CANDIDATES:
        n = summary.get(name, {}).get("n", 0)
        if n != expected:
            raise SystemExit(f"{name}: {n} runs, expected {expected}")
    if ref["n"] != expected:
        raise SystemExit(f"E4 baseline: {ref['n']} runs, expected {expected}")

    ok = [n for n in CANDIDATES if summary[n]["mf1"] >= ref["mf1"] - MF1_TOLERANCE]
    pool = ok or list(CANDIDATES)
    chosen = min(pool, key=lambda n: summary[n]["worst_asr"])

    lines = [
        "### Defense selection on the development pairs",
        "",
        f"Pairs {', '.join(sorted(pairs))}; 3 triggers x {len(args.seeds)} seeds each. "
        "Worst-trigger ASR is the highest seed-mean ASR",
        "of the three installed triggers on a pair, averaged over pairs. Clean MF1 is pooled.",
        "",
        "| Variant | Mean worst-trigger ASR | Clean MF1 | " + " | ".join(sorted(pairs)) + " |",
        "|---|---|---|" + "---|" * len(pairs),
    ]
    rows = [("E4 (MAPU, no defense)", ref)] + [(n, summary[n]) for n in CANDIDATES]
    for name, s in rows:
        mark = " (selected)" if name == chosen else ""
        per = " | ".join(f"{100 * v:.1f}" for v in s["per_pair"].values())
        lines.append(
            f"| {name}{mark} | {100 * s['worst_asr']:.1f} | {100 * s['mf1']:.1f} | {per} |"
        )
    rule = "within 2 points of E4's clean MF1" if ok else "none within 2 points of E4's MF1"
    lines += ["", f"Selected by the rule in scripts/select_defense.py ({rule}): `{chosen}`."]
    text = "\n".join(lines) + "\n"
    if args.check:
        if not args.table.exists() or args.table.read_text() != text:
            raise SystemExit(f"{args.table} does not match {args.out}")
        print(f"{args.table} is current")
        return
    args.table.write_text(text)
    print(text, end="")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    ap.add_argument("--out", type=Path, default=Path("results/selection_runs.jsonl"))
    ap.add_argument("--table", type=Path, default=Path("results/selection.md"))
    ap.add_argument(
        "--baseline-runs",
        type=Path,
        nargs="+",
        default=[Path("results/runs.jsonl"), Path("results/dev_runs.jsonl")],
    )
    ap.add_argument("--device", type=str, default="cuda")
    ap.add_argument("--pairs", nargs="+", default=None, help="run only these pairs, e.g. 6-23")
    ap.add_argument("--report", action="store_true", help="only summarize existing results")
    ap.add_argument("--check", action="store_true", help="fail if the table is out of date")
    args = ap.parse_args()

    if not (args.report or args.check):
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text("")
        run_candidates(args)
    if not args.pairs:
        report(args)


if __name__ == "__main__":
    main()
