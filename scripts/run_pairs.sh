#!/usr/bin/env bash
# Run the experiment matrix on extra UCI HAR subject pairs with the configs unchanged.
#
#   PAIRS="6-23 7-13" OUT=results/dev_runs.jsonl bash scripts/run_pairs.sh
set -euo pipefail

PY="${PY:-python}"
SEEDS="${SEEDS:-42 43 44}"
: "${PAIRS:?set PAIRS, for example PAIRS=\"6-23 7-13\"}"
: "${OUT:?set OUT, for example OUT=results/dev_runs.jsonl}"

cd "$(dirname "${BASH_SOURCE[0]}")/.."
: > "$OUT"
for pair in $PAIRS; do
  src="${pair%-*}"
  tgt="${pair#*-}"
  echo "==> subject $src -> $tgt"
  $PY scripts/run_experiment.py --matrix --seeds $SEEDS --force-sources \
      --ckpt-dir "checkpoints/pairs/s${src}t${tgt}" --out "$OUT" \
      --set "data.source_subject=$src" "data.target_subject=$tgt"
done
