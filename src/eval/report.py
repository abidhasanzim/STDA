"""Markdown tables and audit reports built from run results."""

from __future__ import annotations

import statistics
from collections import defaultdict
from pathlib import Path

from src.eval.schema import RunResult
from src.eval.verdict import Verdict, decide

EXP_LABELS = {
    "E1": ("Clean", "None", "-"),
    "E2": ("Clean", "MAPU", "-"),
    "E3": ("Backdoored", "None", "-"),
    "E4": ("Backdoored", "MAPU", "-"),
    "E5": ("Backdoored", "MAPU", "Compression"),
    "E6": ("Backdoored", "MAPU", "Secure-MAPU"),
    "E7": ("Backdoored", "MAPU", "Consistency"),
    "E8": ("Backdoored", "MAPU", "Compress+Consistency"),
    "E9": ("Backdoored", "MAPU", "FT-SAM"),
    "A1": ("Backdoored", "SHOT-IM", "-"),
    "E10": ("Backdoored", "MAPU", "Compression + consistency + KT"),
}


def _fmt(mean: float | None, std: float | None, pct: bool = True) -> str:
    if mean is None:
        return "-"
    scale = 100.0 if pct else 1.0
    if std is None or std != std:
        return f"{mean * scale:.1f}"
    return f"{mean * scale:.1f} ± {std * scale:.1f}"


def _agg(values: list[float]) -> tuple[float, float]:
    vals = [v for v in values if v is not None and v == v]
    if not vals:
        return (float("nan"), float("nan"))
    return (statistics.mean(vals), statistics.stdev(vals) if len(vals) > 1 else 0.0)


def group_runs(results: list[RunResult]) -> dict[tuple, list[RunResult]]:
    """Group runs that differ only by seed.

    attack_family is part of the key so models poisoned with different triggers are never
    averaged together.
    """
    groups: dict[tuple, list[RunResult]] = defaultdict(list)
    for r in results:
        groups[
            (
                r.dataset,
                r.scenario,
                r.exp_id,
                r.attack_family,
                r.adaptation,
                r.defense,
                r.model_type,
            )
        ].append(r)
    return dict(groups)


def write_markdown_table(
    results: list[RunResult],
    path: str | Path,
    trigger_names: list[str] | None = None,
    title: str = "Results table",
) -> Path:
    """Write a mean +/- std table with one row per experiment and trigger family."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if trigger_names is None:
        names: list[str] = []
        for r in results:
            for k in r.asr:
                if k not in names:
                    names.append(k)
        trigger_names = names

    groups = group_runs(results)
    header = (
        ["Exp", "Attack", "Source", "Adapt", "Defense", "Clean MF1", "ASR (installed)"]
        + [f"ctrl: {n}" for n in trigger_names]
        + ["Seeds"]
    )
    lines = [f"### {title}", "", "| " + " | ".join(header) + " |", "|" + "---|" * len(header)]

    def _order(k):
        exp = k[2]
        num = int(exp[1:]) if exp[1:].isdigit() else 0
        return (k[0], k[1], k[3] or "", exp[0], num, exp)

    for key in sorted(groups, key=_order):
        _dataset, _scenario, exp_id, family, adaptation, defense, model_type = key
        runs = groups[key]
        src_lbl, adapt_lbl, def_lbl = EXP_LABELS.get(
            exp_id, (model_type.title(), adaptation.upper(), defense)
        )
        installed = [r.asr[family].asr for r in runs if family and family in r.asr]
        row = [
            exp_id,
            family or "—",
            src_lbl,
            adapt_lbl,
            def_lbl,
            _fmt(*_agg([r.clean_mf1 for r in runs])),
            f"**{_fmt(*_agg(installed))}**" if installed else "—",
        ]
        for name in trigger_names:
            vals = [r.asr[name].asr for r in runs if name in r.asr]
            cell = _fmt(*_agg(vals)) if vals else "-"
            row.append(f"_{cell}_" if name == family else cell)
        row.append(str(len(runs)))
        lines.append("| " + " | ".join(row) + " |")

    ds = sorted({r.dataset for r in results})
    sc = sorted({r.scenario for r in results})
    lines += [
        "",
        f"Dataset {', '.join(ds)} · scenario {', '.join(sc)} · "
        "mean ± std across seeds, all values %.",
        "",
        "*Attack* is the trigger the source model was poisoned with and *ASR (installed)* is",
        "its attack success rate. The `ctrl:` columns apply every trigger to every model as a",
        "control. E1 and E2 use a clean source model.",
        "",
        "Clean MF1 is macro-F1 on the target test split. ASR excludes windows whose true label",
        "is already the target class.",
    ]
    path.write_text("\n".join(lines) + "\n")
    return path


def write_audit_report(
    result: RunResult,
    path: str | Path,
    verdict: Verdict | None = None,
    channel_ranking: list[tuple[int, float]] | None = None,
    thresholds: dict[str, float] | None = None,
    checkpoint: str = "",
) -> Path:
    """Write the markdown report produced by the CLI."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if verdict is None:
        rate = next((t.clean_target_rate for t in result.asr.values()), None)
        verdict = decide({k: t.asr for k, t in result.asr.items()}, thresholds, rate)

    L: list[str] = []
    L += [f"# Backdoor audit report — {verdict.emoji} **{verdict.label}**", ""]
    L += [f"**Verdict:** {verdict.label}. {verdict.rationale}.", ""]
    L += [
        "| | |",
        "|---|---|",
        f"| Checkpoint | `{checkpoint or 'n/a'}` |",
        f"| Dataset | {result.dataset} |",
        f"| Scenario | {result.scenario} (source -> target) |",
        f"| Adaptation | {result.adaptation} |",
        f"| Defense | {result.defense} |",
        f"| Attacker target class | {result.target_class} |",
        f"| Seed | {result.seed} |",
        f"| Config hash | `{result.config_hash or 'n/a'}` |",
        "",
    ]

    L += [
        "## Threat model",
        "",
        "The model owner receives a pretrained source model and unlabeled target data, with",
        "no access to the source data. A malicious source owner could have trained a backdoor",
        "into the model. This report measures whether known trigger types still control the",
        "model's predictions on the target domain.",
        "",
    ]

    L += [
        "## Utility on the target domain",
        "",
        "| Metric | Value | 95% CI | n |",
        "|---|---|---|---|",
        f"| Clean accuracy | {result.clean_acc:.1%} | "
        f"[{result.clean_acc_ci[0]:.1%}, {result.clean_acc_ci[1]:.1%}] | {result.n_clean} |",
        f"| Clean macro-F1 | {result.clean_mf1:.1%} | - | {result.n_clean} |",
        "",
    ]

    L += [
        "## Attack success rate by trigger family",
        "",
        "| Trigger | Family | ASR | 95% CI | Inclusive ASR | Untriggered target rate | Lift | n |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for name, t in result.asr.items():
        L.append(
            f"| {name} | {t.family} | **{t.asr:.1%}** | [{t.asr_ci[0]:.1%}, {t.asr_ci[1]:.1%}] | "
            f"{t.asr_inclusive:.1%} | {t.clean_target_rate:.1%} | {t.lift:+.1%} | {t.n_eligible} |"
        )
    L += [
        "",
        "ASR: fraction of triggered test windows predicted as the target class, excluding",
        "windows already of that class. Inclusive ASR keeps them. Untriggered target rate is",
        "the same fraction without the trigger, and lift is ASR minus that rate.",
        "",
    ]

    if any(t.stealth for t in result.asr.values()):
        L += [
            "## Perturbation size",
            "",
            "| Trigger | rel. L2 | L-inf | % of signal range | elements touched |",
            "|---|---|---|---|---|",
        ]
        for name, t in result.asr.items():
            s = t.stealth or {}
            L.append(
                f"| {name} | {s.get('relative_l2', float('nan')):.3f} | "
                f"{s.get('linf', float('nan')):.3f} | "
                f"{s.get('relative_range', float('nan')):.1%} | "
                f"{s.get('frac_elements_touched', float('nan')):.1%} |"
            )
        L.append("")

    if channel_ranking:
        L += [
            "## Most backdoor-sensitive encoder channels",
            "",
            "Ranked by the spectral norm of each channel in the last conv layer.",
            "",
            "| Rank | Channel | Spectral norm |",
            "|---|---|---|",
        ]
        for i, (ch, score) in enumerate(channel_ranking[:10], 1):
            L.append(f"| {i} | {ch} | {score:.4f} |")
        L.append("")

    if result.defense_info:
        L += ["## Defense", "", "| Setting | Value |", "|---|---|"]
        for k, v in result.defense_info.items():
            L.append(f"| {k} | {v} |")
        L.append("")

    L += [
        "## Thresholds",
        "",
        f"- **FAIL** when worst-family ASR > {verdict.thresholds['fail_above']:.0%}",
        f"- **WARN** when worst-family ASR > {verdict.thresholds['warn_above']:.0%}",
        "- **PASS** otherwise",
        "",
        "Thresholds are set in configs/eval/audit.yaml.",
        "",
        "## Limitations",
        "",
        "A FAIL shows that a tested trigger works; a PASS does not prove the model is clean.",
        "Only the configured trigger families are tested, at fixed amplitudes, and triggers",
        "designed to evade these checks are not covered. See docs/limitations.md.",
        "",
    ]
    path.write_text("\n".join(L) + "\n")
    return path
