#!/usr/bin/env bash
# Run the whole pipeline from raw data to tables and figures.
#
#   bash scripts/reproduce.sh          # everything (several hours on one RTX 3090)
#   bash scripts/reproduce.sh --fast   # subject 2 -> 11 only, without the sweeps
#
# Set PY to choose the Python interpreter and SEEDS to change the seeds.
set -euo pipefail

PY="${PY:-python}"
SEEDS="${SEEDS:-42 43 44}"
FAST=0
[ "${1:-}" = "--fast" ] && FAST=1

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export SFDA_NO_TRACKING="${SFDA_NO_TRACKING:-1}"
mkdir -p results

step() { printf '\n==> %s\n' "$1"; }

# backdoor-audit exits with 2 when the verdict is FAIL; only other non-zero codes are errors.
audit() {
  set +e
  "$@"
  local rc=$?
  set -e
  if [ "$rc" -ne 0 ] && [ "$rc" -ne 2 ]; then exit "$rc"; fi
}

step "Data"
bash scripts/download_har.sh
$PY -m src.data.parse_har

step "Lint and tests"
$PY -m ruff check .
$PY -m ruff format --check .
$PY -m pytest -q -m fast

step "Experiments (seeds: $SEEDS)"
: > results/runs.jsonl
$PY scripts/run_experiment.py --matrix --seeds $SEEDS --force-sources --out results/runs.jsonl

if [ "$FAST" -eq 0 ]; then
  step "SSDA ablation"
  : > results/ablation.jsonl
  $PY scripts/ablate_defense.py --family patch --seed 42 --out results/ablation.jsonl

  step "Compression sweep"
  : > results/tradeoff_curve.jsonl
  $PY scripts/sweep_spectral_defense.py --curve --family freq --seeds $SEEDS \
      --out results/tradeoff_curve.jsonl

  step "Development subject pairs"
  PY="$PY" SEEDS="$SEEDS" PAIRS="6-23 7-13 9-18 12-16" OUT=results/dev_runs.jsonl \
      bash scripts/run_pairs.sh

  step "Defense selection"
  $PY scripts/select_defense.py --seeds $SEEDS

  step "Test subject pairs"
  PY="$PY" SEEDS="$SEEDS" PAIRS="18-27 20-5 24-8 28-27 30-20" OUT=results/test_runs.jsonl \
      bash scripts/run_pairs.sh

  step "Consistency band ablation"
  $PY scripts/ablate_consistency_band.py --seeds $SEEDS
fi

step "Tables and figures"
$PY -m src.cli table --runs results/runs.jsonl --out results/table.md
if [ -s results/dev_runs.jsonl ]; then
  $PY -m src.cli table --runs results/dev_runs.jsonl --out results/dev_table.md \
      --title "Development subject pairs"
fi
if [ -s results/test_runs.jsonl ]; then
  $PY -m src.cli table --runs results/test_runs.jsonl --out results/test_table.md \
      --title "Test subject pairs"
fi
$PY scripts/plot_tradeoff.py --runs results/runs.jsonl --out results/tradeoff.png
if [ -s results/ablation.jsonl ]; then $PY scripts/write_ablation_table.py; fi
if [ -s results/tradeoff_curve.jsonl ]; then $PY scripts/plot_compression_curve.py; fi

step "Example audit reports"
audit $PY -m src.cli run --checkpoint checkpoints/source_bd-patch_har_s2_seed42.pt \
    --out results/demo/
audit $PY -m src.cli run --checkpoint checkpoints/source_bd-freq_har_s2_seed42.pt \
    --adapt mapu --defense combined --out results/demo_defended/

step "Smoke test"
$PY scripts/smoke_e2e.py

step "Done"
$PY -c "from src.eval.schema import load_runs; r = load_runs('results/runs.jsonl'); print(len(r), 'runs written to results/runs.jsonl')"
