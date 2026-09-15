"""Plot clean macro-F1 and ASR as channel compression strength increases.

Reads results/tradeoff_curve.jsonl (produced by sweep_spectral_defense.py --curve) and
writes results/compression_curve.png.
"""

from __future__ import annotations

import argparse
import statistics as st
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from src.eval.schema import load_runs  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", type=Path, default=Path("results/tradeoff_curve.jsonl"))
    ap.add_argument("--family", type=str, default="freq")
    ap.add_argument("--out", type=Path, default=Path("results/compression_curve.png"))
    args = ap.parse_args()

    runs = load_runs(args.runs)
    if not runs:
        raise SystemExit(f"no runs in {args.runs}")

    grouped: dict[int, list[tuple[float, float]]] = defaultdict(list)
    zeroed: dict[int, int] = {}
    for r in runs:
        label = r.exp_id.replace("SD:", "")
        k = 0 if "baseline" in label else int(label.split("=")[1])
        t = r.asr.get(args.family)
        if t is None:
            continue
        grouped[k].append((r.clean_mf1, t.asr))
        zeroed[k] = r.defense_info.get("n_zeroed", 0)

    ks = sorted(grouped)
    mf1 = [st.mean([a for a, _ in grouped[k]]) for k in ks]
    mf1e = [st.stdev([a for a, _ in grouped[k]]) if len(grouped[k]) > 1 else 0 for k in ks]
    asr = [st.mean([b for _, b in grouped[k]]) for k in ks]
    asre = [st.stdev([b for _, b in grouped[k]]) if len(grouped[k]) > 1 else 0 for k in ks]

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12.5, 5.0))

    # left: ASR against clean macro-F1
    ax.axhspan(-0.05, 0.20, color="#2e7d32", alpha=0.07)
    ax.axhspan(0.50, 1.05, color="#c62828", alpha=0.07)
    ax.errorbar(
        mf1,
        asr,
        xerr=mf1e,
        yerr=asre,
        fmt="-o",
        color="#1f77b4",
        markersize=7,
        capsize=3,
        linewidth=1.4,
        zorder=3,
    )
    for k, x, y in zip(ks, mf1, asr):
        lbl = "no defense" if k == 0 else f"k={k}"
        ax.annotate(lbl, (x, y), textcoords="offset points", xytext=(6, 7), fontsize=8.5)
    ax.set_xlabel("Clean macro-F1 on target  →  better")
    ax.set_ylabel("Attack success rate  ←  better")
    ax.set_title("Tradeoff plane: compressing harder stops helping")
    ax.grid(alpha=0.25, linestyle=":")
    ax.set_ylim(-0.05, 1.0)
    ax.text(
        0.02,
        0.205,
        "PASS threshold",
        fontsize=8,
        color="#2e7d32",
        transform=ax.get_yaxis_transform(),
        va="bottom",
    )

    # right: both metrics against k
    ax2.errorbar(ks, asr, yerr=asre, fmt="-o", color="#c62828", capsize=3, label="ASR")
    ax2.errorbar(ks, mf1, yerr=mf1e, fmt="-s", color="#1f77b4", capsize=3, label="clean macro-F1")
    ax2.axhline(
        0.20, color="#2e7d32", linestyle="--", linewidth=1, label="PASS threshold (ASR 20%)"
    )
    floor = min(range(len(ks)), key=lambda i: asr[i] if ks[i] < 64 else 9)
    ax2.annotate(
        f"ASR floors at {asr[floor]:.0%}\n(k={ks[floor]}), then rises\nas accuracy collapses",
        xy=(ks[floor], asr[floor]),
        xytext=(ks[floor] + 6, 0.45),
        fontsize=8.5,
        arrowprops=dict(arrowstyle="->", color="#555", lw=1),
    )
    ax2.set_xlabel("channels zeroed per layer (top-k)")
    ax2.set_ylabel("rate")
    ax2.set_title("The far end is a destroyed model, not a defense")
    ax2.grid(alpha=0.25, linestyle=":")
    ax2.legend(fontsize=8.5, loc="center left")
    ax2.set_ylim(-0.05, 1.05)

    fig.suptitle(
        f"Spectral-norm channel compression against the surviving spectral trigger "
        f"(UCI HAR 2→11, {args.family}, {len({r.seed for r in runs})} seeds)",
        fontsize=12,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=160)
    print(f"[plot_compression_curve] wrote {args.out}")

    print(f"\n{'k':>4s} {'zeroed':>7s} {'clean MF1':>12s} {'ASR':>12s}")
    for i, k in enumerate(ks):
        print(
            f"{k:>4d} {zeroed[k]:>7d} {mf1[i] * 100:7.1f} ± {mf1e[i] * 100:3.1f} "
            f"{asr[i] * 100:7.1f} ± {asre[i] * 100:3.1f}"
        )


if __name__ == "__main__":
    main()
