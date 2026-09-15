"""Audit a time-series checkpoint for backdoors.

Example:

    backdoor-audit run --checkpoint checkpoints/source_bd-patch_har_s2_seed42.pt --out results/demo/

Writes report.md and result.json with clean accuracy, attack success rate per trigger
family, the most sensitive encoder channels and a pass/warn/fail verdict.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DEFENSES = {
    "none": None,
    "compress": "configs/defense/static.yaml",
    "secure-mapu": "configs/defense/dynamic.yaml",
    "consistency": "configs/defense/consistency.yaml",
    "sam": "configs/defense/sam.yaml",
    "combined": "configs/defense/combined.yaml",
    "combined-kt": "configs/defense/combined_kt.yaml",
}


def _repo_path(p: str | Path) -> Path:
    p = Path(p)
    return p if p.is_absolute() else Path(__file__).resolve().parents[1] / p


def cmd_run(args: argparse.Namespace) -> int:
    import torch

    from src.eval.report import write_audit_report
    from src.eval.verdict import decide
    from src.experiments import audit_checkpoint
    from src.utils.config import load_yaml
    from src.utils.seed import set_seed

    if not Path(args.checkpoint).exists():
        print(
            f"[backdoor-audit] checkpoint not found: {args.checkpoint}\n"
            "  checkpoints/ is gitignored, so a fresh clone has none. Build them with:\n"
            "    make reproduce-fast   # subject 2 -> 11 experiments\n"
            "  or train a single source model:\n"
            "    python -m src.mapu.train_source --attack configs/attack/patch.yaml --tag bd-patch",
            file=sys.stderr,
        )
        return 1

    dpath = DEFENSES.get(args.defense, args.defense)
    if dpath and args.adapt == "none":
        print(
            "[backdoor-audit] --defense is applied during adaptation; "
            "add --adapt mapu or --adapt shot",
            file=sys.stderr,
        )
        return 1
    if dpath and not _repo_path(dpath).exists():
        print(
            f"[backdoor-audit] unknown defense {args.defense!r} (no file at {_repo_path(dpath)}); "
            f"use one of {', '.join(DEFENSES)} or a path to a defense yaml "
            "(relative paths resolve against the repo root)",
            file=sys.stderr,
        )
        return 1

    set_seed(args.seed)
    eval_cfg = load_yaml(_repo_path(args.eval_config))
    if args.target_data:
        eval_cfg["target_data"] = str(args.target_data)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    device = args.device
    if device == "cuda" and not torch.cuda.is_available():
        print("[backdoor-audit] cuda unavailable, using cpu", file=sys.stderr)
        device = "cpu"

    print(f"[backdoor-audit] auditing {args.checkpoint}")
    before = audit_checkpoint(
        args.checkpoint,
        exp_id="audit",
        model_type="unknown",
        adaptation="none",
        defense="none",
        seed=args.seed,
        eval_cfg=eval_cfg,
        device=device,
    )
    result = before
    defense_info: dict = {}
    ranking = None

    if args.adapt != "none":
        from src.experiments import run_row
        from src.utils.config import load_config

        adapt_cfg = load_config(_repo_path(args.adapt_config))
        if args.target_data:
            adapt_cfg["data"] = {**adapt_cfg.get("data", {}), "npz_path": str(args.target_data)}
        adapt_cfg["device"] = device
        adapt_cfg["seed"] = args.seed
        if args.epochs:
            adapt_cfg["epochs"] = args.epochs
        dcfg = load_yaml(_repo_path(dpath)) if dpath else None
        print(f"[backdoor-audit] adapting with method={args.adapt} defense={args.defense}")
        result = run_row(
            "audit",
            args.checkpoint,
            model_type="unknown",
            seed=args.seed,
            adapt_cfg=adapt_cfg,
            method=args.adapt,
            defense_cfg=dcfg,
            defense_name=args.defense,
            eval_cfg=eval_cfg,
            out_dir=str(out_dir / "checkpoints"),
            device=device,
        )
        ranking = result.defense_info.pop("channel_ranking", None)
        defense_info = dict(result.defense_info)

    if ranking is None:
        from src.defense.sensitivity import layer_scores, rank_channels
        from src.utils.checkpoint import load_ckpt

        m, _, _ = load_ckpt(args.checkpoint)
        scores = layer_scores(m.encoder)
        ranking = rank_channels(scores[max(scores)])

    thresholds = eval_cfg.get("thresholds")
    verdict = decide(
        {k: t.asr for k, t in result.asr.items()},
        thresholds,
        next((t.clean_target_rate for t in result.asr.values()), None),
    )

    report = write_audit_report(
        result,
        out_dir / "report.md",
        verdict=verdict,
        channel_ranking=ranking,
        thresholds=thresholds,
        checkpoint=str(args.checkpoint),
    )
    payload = result.to_dict()
    payload["verdict"] = {
        "label": verdict.label,
        "worst_trigger": verdict.worst_trigger,
        "worst_asr": verdict.worst_asr,
        "thresholds": verdict.thresholds,
        "rationale": verdict.rationale,
    }
    if args.adapt != "none":
        payload["before_adaptation"] = before.to_dict()
        payload["defense_info"] = defense_info
    (out_dir / "result.json").write_text(json.dumps(payload, indent=2, default=str))

    print()
    print(f"  {verdict.emoji} VERDICT: {verdict.label}")
    print(f"  {verdict.rationale}")
    print(
        f"  clean acc {result.clean_acc:.1%}  macro-F1 {result.clean_mf1:.1%}  (n={result.n_clean})"
    )
    for name, t in sorted(result.asr.items(), key=lambda kv: -kv[1].asr):
        print(
            f"  ASR[{name:9s}] {t.asr:6.1%}  95% CI [{t.asr_ci[0]:.1%}, {t.asr_ci[1]:.1%}]"
            f"   untriggered target rate {t.clean_target_rate:.1%}"
        )
    if args.adapt != "none":
        print("\n  before adaptation:")
        for name, t in sorted(before.asr.items(), key=lambda kv: -kv[1].asr):
            delta = result.asr[name].asr - t.asr
            print(f"  ASR[{name:9s}] {t.asr:6.1%}  ->  {result.asr[name].asr:6.1%}  ({delta:+.1%})")
    print(f"\n  report: {report}\n  json:   {out_dir / 'result.json'}")
    return 0 if verdict.label != "FAIL" else 2


def cmd_table(args: argparse.Namespace) -> int:
    from src.eval.report import write_markdown_table
    from src.eval.schema import load_runs

    runs = load_runs(args.runs)
    if not runs:
        print(f"[backdoor-audit] no runs found in {args.runs}", file=sys.stderr)
        return 1
    p = write_markdown_table(runs, args.out, title=args.title)
    print(p.read_text())
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="backdoor-audit",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = ap.add_subparsers(dest="command", required=True)

    r = sub.add_parser("run", help="audit a checkpoint and write a report")
    r.add_argument("--checkpoint", type=Path, required=True)
    r.add_argument(
        "--target-data",
        type=Path,
        default=None,
        help="processed .npz; defaults to the one named in the checkpoint config",
    )
    r.add_argument(
        "--defense",
        type=str,
        default="none",
        help=(
            "none | compress | consistency | combined | combined-kt | sam | secure-mapu, or a "
            "path to a defense yaml; requires --adapt. See README.md for how each one performs."
        ),
    )
    r.add_argument(
        "--adapt",
        type=str,
        default="none",
        choices=["none", "mapu", "shot"],
        help="run source-free adaptation before auditing",
    )
    r.add_argument("--out", type=Path, default=Path("results/audit"))
    r.add_argument("--eval-config", type=Path, default=Path("configs/eval/audit.yaml"))
    r.add_argument("--adapt-config", type=Path, default=Path("configs/train/mapu.yaml"))
    r.add_argument("--epochs", type=int, default=None)
    r.add_argument("--seed", type=int, default=42)
    r.add_argument("--device", type=str, default="cuda")
    r.set_defaults(func=cmd_run)

    t = sub.add_parser("table", help="regenerate results/table.md from runs.jsonl")
    t.add_argument("--runs", type=Path, default=Path("results/runs.jsonl"))
    t.add_argument("--out", type=Path, default=Path("results/table.md"))
    t.add_argument("--title", type=str, default="Results table")
    t.set_defaults(func=cmd_table)

    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
