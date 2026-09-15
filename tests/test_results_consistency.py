"""Check that the committed results match the committed configs."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from src.eval.schema import load_runs

pytestmark = pytest.mark.fast

REPO = Path(__file__).resolve().parents[1]
RUNS = REPO / "results/runs.jsonl"


@pytest.fixture(scope="module")
def runs():
    if not RUNS.exists():
        pytest.skip(f"{RUNS} not present")
    rs = load_runs(RUNS)
    if not rs:
        pytest.skip("no runs recorded")
    return rs


def test_consistency_weight_matches_the_shipped_config(runs):
    """E7/E8 rows must use the consistency weight in the defense configs."""
    cons = yaml.safe_load((REPO / "configs/defense/consistency.yaml").read_text())
    combo = yaml.safe_load((REPO / "configs/defense/combined.yaml").read_text())
    assert cons["consistency_wt"] == combo["consistency_wt"], (
        "consistency.yaml and combined.yaml disagree on consistency_wt"
    )

    for exp in ("E7", "E8"):
        recorded = {r.defense_info.get("consistency_wt") for r in runs if r.exp_id == exp}
        recorded.discard(None)
        if not recorded:
            continue
        assert recorded == {cons["consistency_wt"]}, (
            f"{exp} rows were produced with consistency_wt={recorded}, "
            f"but the shipped config declares {cons['consistency_wt']}"
        )


def test_every_row_has_three_seeds(runs):
    from collections import defaultdict

    seeds = defaultdict(set)
    for r in runs:
        seeds[(r.exp_id, r.attack_family)].add(r.seed)
    bad = {k: sorted(v) for k, v in seeds.items() if len(v) != 3}
    assert not bad, f"rows without exactly 3 seeds: {bad}"


def test_no_duplicate_rows(runs):
    """Re-running without truncating the results file would duplicate rows."""
    keys = [(r.exp_id, r.attack_family, r.seed, r.defense) for r in runs]
    dupes = {k for k in keys if keys.count(k) > 1}
    assert not dupes, f"duplicated rows in results/runs.jsonl: {sorted(dupes)[:5]}"


def test_results_come_from_the_leakage_free_split(runs):
    """Committed results must come from the segment-level split."""
    sizes = {r.n_clean for r in runs}
    assert 63 not in sizes, (
        "n_clean=63 is what split_mode='window' produces; "
        f"segment-level splits give 86-88. Sizes present: {sorted(sizes)}"
    )


PAIR_FILES = {
    "results/dev_runs.jsonl": {"6->23", "7->13", "9->18", "12->16"},
    "results/test_runs.jsonl": {"18->27", "20->5", "24->8", "28->27", "30->20"},
}
# Values measured during a run rather than set in a config.
MEASURED = {
    "aux_target_mf1",
    "channel_ranking",
    "compressed_channel_absmean_final",
    "n_zeroed",
    "pseudo_label_hist",
    "zeroed_per_layer",
}


@pytest.fixture(scope="module", params=sorted(PAIR_FILES))
def pair_runs(request):
    path = REPO / request.param
    if not path.exists():
        pytest.skip(f"{path} not present")
    rs = load_runs(path)
    if not rs:
        pytest.skip(f"no runs in {path}")
    return request.param, rs


def test_pair_runs_cover_every_pair_experiment_and_seed(runs, pair_runs):
    from collections import Counter, defaultdict

    name, rs = pair_runs
    assert {r.scenario for r in rs} == PAIR_FILES[name]
    seeds = defaultdict(set)
    for r in rs:
        seeds[(r.scenario, r.exp_id, r.attack_family)].add(r.seed)
    bad = {k: sorted(v) for k, v in seeds.items() if len(v) != 3}
    assert not bad, f"{name}: rows without exactly 3 seeds: {bad}"
    per_pair = Counter(r.scenario for r in rs)
    assert set(per_pair.values()) == {len(runs)}, f"{name}: rows per pair {dict(per_pair)}"


def test_pair_runs_use_the_same_defense_settings(runs, pair_runs):
    """Other subject pairs must be run with the settings used for subject 2 -> 11."""

    def settings(r):
        return {k: v for k, v in r.defense_info.items() if k not in MEASURED}

    name, rs = pair_runs
    reference = {}
    for r in runs:
        reference.setdefault(r.exp_id, settings(r))
    for r in rs:
        assert settings(r) == reference[r.exp_id], (
            f"{name}: {r.exp_id} on {r.scenario} seed {r.seed} used different defense settings"
        )


def test_e10_is_the_variant_chosen_on_the_development_pairs(runs):
    import re

    table = REPO / "results/selection.md"
    if not table.exists():
        pytest.skip(f"{table} not present")
    chosen = re.search(r"\): `([^`]+)`\.", table.read_text()).group(1)
    config = yaml.safe_load((REPO / "configs/defense/combined_kt.yaml").read_text())
    assert chosen == config["name"]

    selected = [
        r for r in load_runs(REPO / "results/selection_runs.jsonl") if r.exp_id == f"SEL:{chosen}"
    ]
    e10 = [r for r in runs if r.exp_id == "E10"]
    if not e10:
        pytest.skip("no E10 rows recorded")

    def settings(r):
        return {k: v for k, v in r.defense_info.items() if k not in MEASURED}

    assert {str(settings(r)) for r in selected} == {str(settings(r)) for r in e10}
