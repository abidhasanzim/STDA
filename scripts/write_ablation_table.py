"""Write results/ablation.md from results/ablation.jsonl."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.eval.schema import load_runs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", type=Path, default=Path("results/ablation.jsonl"))
    ap.add_argument("--out", type=Path, default=Path("results/ablation.md"))
    ap.add_argument("--family", type=str, default="patch")
    args = ap.parse_args()

    runs = load_runs(args.runs)
    if not runs:
        raise SystemExit(f"no runs in {args.runs}")

    lines = [
        "### Secure-MAPU component and lambda ablation",
        "",
        f"{args.family} family, seed 42, subject 2 -> 11. `C1`/`C0` = compression on/off,",
        "`KT1`/`KT0` = knowledge transfer on/off, `lam` = spectral penalty weight.",
        "",
        "| Condition | Compression | Knowledge transfer | lambda | Clean MF1 | ASR | "
        "Channels zeroed | Compressed abs-mean final |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in runs:
        d = r.defense_info
        t = r.asr.get(args.family)
        if t is None:
            continue
        mag = d.get("compressed_channel_absmean_final")
        lines.append(
            f"| `{r.exp_id.replace('AB:', '')}` "
            f"| {'yes' if d.get('compress') else 'no'} "
            f"| {'yes' if d.get('knowledge_transfer') else 'no'} "
            f"| {d.get('spectral_weight')} "
            f"| {r.clean_mf1 * 100:.1f} | **{t.asr * 100:.1f}** "
            f"| {d.get('n_zeroed', 0)} | {f'{mag:.1e}' if mag is not None else '-'} |"
        )
    lines += [
        "",
        "Single seed, so differences of a few points are within noise. lambda = 100 is SSDA's",
        "published value. The last column checks that compressed channels stay at zero during",
        "adaptation. See docs/report.md for discussion.",
    ]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n")
    print(f"[write_ablation_table] wrote {args.out} ({len(runs)} conditions)")


if __name__ == "__main__":
    main()
