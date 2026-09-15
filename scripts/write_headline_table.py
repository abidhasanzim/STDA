"""Print the headline defense table from a runs file.

With --check, fail if the copy of the table embedded in the given files is out of date.
Runs from several subject pairs are pooled; the caption says so. --summary prints one row
per defense with the worst-trigger ASR averaged over pairs instead.
"""

from __future__ import annotations

import argparse
import re
import statistics as st
from collections import defaultdict
from pathlib import Path

from src.eval.schema import load_runs

ROWS = [
    ("E3", "no adaptation"),
    ("E4", "MAPU (no defense)"),
    ("A1", "SHOT-IM (ablation)"),
    ("E5", "+ spectral-norm compression"),
    ("E6", "+ Secure-MAPU (SSDA, ICCV'23)"),
    ("E9", "+ FT-SAM (ICCV'23)"),
    ("E7", "+ perturbation consistency"),
    ("E8", "+ compression & consistency"),
    ("E10", "+ compression & consistency & KT"),
]
FAMILIES = ["patch", "gaussian", "freq"]


def _fmt(vals: list[float]) -> str:
    if not vals:
        return "—"
    m = st.mean(vals) * 100
    s = (st.stdev(vals) if len(vals) > 1 else 0.0) * 100
    return f"{m:.1f} ± {s:.1f}"


def _pairs(runs) -> list[str]:
    return sorted({r.scenario for r in runs}, key=lambda s: int(s.split("->")[0]))


def build(runs_path: Path, marker: str) -> str:
    runs = load_runs(runs_path)
    if not runs:
        raise SystemExit(f"no runs in {runs_path}")
    asr = defaultdict(list)
    mf1 = defaultdict(list)
    for r in runs:
        if not r.attack_family:
            continue
        t = r.asr.get(r.attack_family)
        if t is not None:
            asr[(r.exp_id, r.attack_family)].append(t.asr)
        mf1[r.exp_id].append(r.clean_mf1)

    seeds = sorted({r.seed for r in runs})
    scen = _pairs(runs)
    if len(scen) == 1:
        spread = f"{len(seeds)} seeds, mean ± std"
        where = f"Scenario {scen[0]}."
    else:
        spread = f"{len(scen)} subject pairs × {len(seeds)} seeds, mean ± std over all runs"
        where = f"Scenarios {', '.join(scen)}."
    out = [
        marker,
        "Attack success rate (%) on the target domain, lower is better.",
        f"{spread}; clean MF1 is pooled over the three triggers. {where}",
        "",
        "| Defense | patch | gaussian | freq | Clean MF1 |",
        "|---|---|---|---|---|",
    ]
    for exp, label in ROWS:
        if exp not in mf1:
            continue
        cells = [_fmt(asr.get((exp, f), [])) for f in FAMILIES]
        best = exp == "E8"
        wrap = (lambda x: f"**{x}**") if best else (lambda x: x)
        body = " | ".join(wrap(c) for c in cells)
        out.append(f"| **{exp}** {label} | {body} | {wrap(_fmt(mf1[exp]))} |")
    out.append(marker)
    return "\n".join(out)


def build_summary(runs_path: Path, marker: str) -> str:
    runs = load_runs(runs_path)
    if not runs:
        raise SystemExit(f"no runs in {runs_path}")
    cells = defaultdict(list)
    mf1 = defaultdict(list)
    for r in runs:
        if r.attack_family:
            cells[(r.exp_id, r.scenario, r.attack_family)].append(r.asr[r.attack_family].asr)
            mf1[r.exp_id].append(r.clean_mf1)

    pairs = _pairs(runs)
    out = [
        marker,
        f"Summary over {len(pairs)} subject pairs ({', '.join(pairs)}). Worst-trigger ASR is the",
        "highest seed-mean ASR of the three triggers on a pair; clean MF1 is pooled over all runs.",
        "",
        "| Defense | Mean worst-trigger ASR (%) | Pairs with worst-trigger ASR ≤ 20% | Clean MF1 |",
        "|---|---|---|---|",
    ]
    for exp, label in ROWS:
        if exp not in mf1:
            continue
        worst = [
            max(st.mean(cells[(exp, p, f)]) for f in FAMILIES if cells[(exp, p, f)]) for p in pairs
        ]
        n_ok = sum(w <= 0.2 for w in worst)
        out.append(
            f"| **{exp}** {label} | {100 * st.mean(worst):.1f} | {n_ok} of {len(pairs)} "
            f"| {100 * st.mean(mf1[exp]):.1f} |"
        )
    out.append(marker)
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", type=Path, default=Path("results/runs.jsonl"))
    ap.add_argument(
        "--marker", type=str, default="headline-table", help="name of the embedded block"
    )
    ap.add_argument("--summary", action="store_true", help="one row per defense, pooled over pairs")
    ap.add_argument(
        "--check",
        type=Path,
        nargs="*",
        default=None,
        help="files whose embedded copy must match; exits 1 on drift",
    )
    ap.add_argument(
        "--update", type=Path, nargs="*", default=None, help="rewrite the embedded copy in place"
    )
    args = ap.parse_args()

    marker = f"<!-- {args.marker} -->"
    table = (build_summary if args.summary else build)(args.runs, marker)
    pattern = re.escape(marker) + r".*?" + re.escape(marker)
    if args.update:
        for f in args.update:
            text = Path(f).read_text()
            if len(re.findall(pattern, text, re.S)) != 1:
                raise SystemExit(f"{f}: expected exactly one {marker} block")
            Path(f).write_text(re.sub(pattern, lambda _: table, text, flags=re.S))
        print(f"{args.marker} updated in: {', '.join(str(f) for f in args.update)}")
        return
    if not args.check:
        print(table)
        return

    stale = []
    for f in args.check:
        text = Path(f).read_text()
        blocks = re.findall(re.escape(marker) + r"(.*?)" + re.escape(marker), text, re.S)
        if not blocks:
            stale.append(f"{f}: no {marker} block")
        elif blocks[0].strip() != table[len(marker) : -len(marker)].strip():
            stale.append(f"{f}: embedded table is stale")
    if stale:
        print("\n".join(stale))
        raise SystemExit(1)
    print(f"{args.marker} is current in: {', '.join(str(f) for f in args.check)}")


if __name__ == "__main__":
    main()
