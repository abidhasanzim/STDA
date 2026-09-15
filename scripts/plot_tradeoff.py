"""Plot ASR against clean macro-F1 for every experiment, one panel per trigger family.

Writes results/tradeoff.png from results/runs.jsonl.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from src.eval.schema import load_runs  # noqa: E402

MARKERS = {
    "E1": "o",
    "E2": "s",
    "E3": "X",
    "E4": "D",
    "E5": "^",
    "E6": "v",
    "E7": "*",
    "E8": "H",
    "E9": "d",
    "A1": "P",
    "E10": "p",
}
FALLBACK_MARKERS = ["8", "<", ">", "h", "1", "2"]
LABELS = {
    "E1": "E1 clean / no adapt",
    "E2": "E2 clean / MAPU",
    "E3": "E3 backdoored / no adapt",
    "E4": "E4 backdoored / MAPU",
    "E5": "E5 + compression only",
    "E6": "E6 + Secure-MAPU",
    "E7": "E7 + consistency",
    "E8": "E8 + compress & consistency",
    "E9": "E9 + FT-SAM",
    "A1": "A1 backdoored / SHOT-IM",
    "E10": "E10 + compress & consistency & KT",
}


def marker_for(exp: str, known: list[str]) -> str:
    if exp in MARKERS:
        return MARKERS[exp]
    extra = sorted(e for e in known if e not in MARKERS)
    return FALLBACK_MARKERS[extra.index(exp) % len(FALLBACK_MARKERS)]


FAMILY_COLOR = {"patch": "#1f77b4", "freq": "#d62728", "gaussian": "#2ca02c", "": "#7f7f7f"}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", type=Path, default=Path("results/runs.jsonl"))
    ap.add_argument("--out", type=Path, default=Path("results/tradeoff.png"))
    args = ap.parse_args()

    runs = load_runs(args.runs)
    if not runs:
        raise SystemExit(f"no runs in {args.runs}")

    # Mean over seeds per (experiment, family).
    agg: dict[tuple[str, str], list[tuple[float, float]]] = defaultdict(list)
    for r in runs:
        fam = r.attack_family
        t = r.asr.get(fam)
        asr = t.asr if t else max((v.asr for v in r.asr.values()), default=0.0)
        agg[(r.exp_id, fam)].append((r.clean_mf1, asr))

    families = sorted({f for _, f in agg if f})
    exp_ids = sorted(
        {e for e, _ in agg}, key=lambda e: (e[0] != "E", int(e[1:]) if e[1:].isdigit() else 0, e)
    )
    fig, axes = plt.subplots(
        1,
        max(len(families), 1),
        figsize=(5.2 * max(len(families), 1), 4.8),
        sharey=True,
        squeeze=False,
    )

    for ax, fam in zip(axes[0], families):
        for (exp, f), vals in sorted(agg.items()):
            if f not in (fam, ""):
                continue
            xs = [v[0] for v in vals]
            ys = [v[1] for v in vals]
            mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
            ex = (max(xs) - min(xs)) / 2 if len(xs) > 1 else 0
            ey = (max(ys) - min(ys)) / 2 if len(ys) > 1 else 0
            ax.errorbar(
                mx,
                my,
                xerr=ex,
                yerr=ey,
                fmt=marker_for(exp, exp_ids),
                markersize=10,
                color=FAMILY_COLOR.get(f or fam, "#7f7f7f"),
                alpha=0.55 if f == "" else 0.95,
                label=LABELS.get(exp, exp),
                capsize=3,
                linewidth=1.2,
            )
            # Offset labels for points that often coincide.
            dx, dy = {"E2": (7, -12), "E4": (7, 6), "E5": (-26, 6), "E6": (7, -6)}.get(exp, (7, 6))
            ax.annotate(exp, (mx, my), textcoords="offset points", xytext=(dx, dy), fontsize=9)

        ax.set_title(f"trigger family: {fam}")
        ax.set_xlabel("Clean macro-F1 on target  →  better")
        ax.grid(alpha=0.25, linestyle=":")
        ax.set_ylim(-0.05, 1.05)
        ax.axhspan(-0.05, 0.2, color="#2e7d32", alpha=0.06)
        ax.axhspan(0.5, 1.05, color="#c62828", alpha=0.06)

    axes[0][0].set_ylabel("Attack success rate  ←  better")
    # Colour encodes the trigger family, so the legend uses neutral markers.
    from matplotlib.lines import Line2D

    proxies = [
        Line2D(
            [],
            [],
            marker=marker_for(e, exp_ids),
            color="none",
            markerfacecolor="#444",
            markeredgecolor="#444",
            markersize=9,
            label=LABELS.get(e, e),
        )
        for e in exp_ids
    ]
    fig.legend(handles=proxies, loc="lower center", ncol=4, frameon=False, fontsize=9)
    fig.suptitle("Backdoor persistence through source-free adaptation (UCI HAR, 2→11)", fontsize=12)
    fig.tight_layout(rect=(0, 0.13, 1, 0.97))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=160)
    print(f"[plot_tradeoff] wrote {args.out}")


if __name__ == "__main__":
    main()
