PY ?= python
SEEDS ?= 42 43 44
DEV_PAIRS ?= 6-23 7-13 9-18 12-16
TEST_PAIRS ?= 18-27 20-5 24-8 28-27 30-20

.PHONY: help setup data fixture test lint fmt smoke reproduce reproduce-fast table figures ablation dev-pairs selection test-pairs band-ablation curve demo clean

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup:  ## install dependencies and the package
	$(PY) -m pip install -r requirements.txt && $(PY) -m pip install -e . --no-deps

data:  ## download and preprocess UCI HAR
	bash scripts/download_har.sh
	$(PY) -m src.data.parse_har

fixture:  ## rebuild the small test fixture from the processed data
	$(PY) scripts/make_tiny_fixture.py

lint:  ## ruff lint and format check
	$(PY) -m ruff check .
	$(PY) -m ruff format --check .

fmt:  ## apply ruff fixes and formatting
	$(PY) -m ruff check --fix .
	$(PY) -m ruff format .

test:  ## fast test suite
	SFDA_NO_TRACKING=1 $(PY) -m pytest -q -m fast

smoke:  ## quick end-to-end run on the test fixture
	SFDA_NO_TRACKING=1 $(PY) scripts/smoke_e2e.py

reproduce:  ## full pipeline: data, tests, experiments, sweeps, tables, figures
	PY=$(PY) SEEDS="$(SEEDS)" bash scripts/reproduce.sh

reproduce-fast:  ## full pipeline without the sweeps and the extra subject pairs
	PY=$(PY) SEEDS="$(SEEDS)" bash scripts/reproduce.sh --fast

table:  ## rebuild the markdown tables in results/
	$(PY) -m src.cli table --runs results/runs.jsonl --out results/table.md
	@if [ -s results/dev_runs.jsonl ]; then \
		$(PY) -m src.cli table --runs results/dev_runs.jsonl --out results/dev_table.md \
			--title "Development subject pairs"; \
	fi
	@if [ -s results/test_runs.jsonl ]; then \
		$(PY) -m src.cli table --runs results/test_runs.jsonl --out results/test_table.md \
			--title "Test subject pairs"; \
	fi
	@if [ -s results/ablation.jsonl ]; then \
		$(PY) scripts/write_ablation_table.py; \
	else \
		echo "results/ablation.jsonl not found, run 'make ablation' first"; \
	fi

figures:  ## rebuild results/tradeoff.png and results/compression_curve.png
	$(PY) scripts/plot_tradeoff.py --runs results/runs.jsonl --out results/tradeoff.png
	@if [ -s results/tradeoff_curve.jsonl ]; then \
		$(PY) scripts/plot_compression_curve.py; \
	else \
		echo "results/tradeoff_curve.jsonl not found, run 'make curve' first"; \
	fi

ablation:  ## run the SSDA component and lambda ablation
	: > results/ablation.jsonl
	$(PY) scripts/ablate_defense.py --family patch --seed 42 --out results/ablation.jsonl
	$(PY) scripts/write_ablation_table.py

dev-pairs:  ## run the experiment matrix on MAPU's other four subject pairs
	PY=$(PY) SEEDS="$(SEEDS)" PAIRS="$(DEV_PAIRS)" OUT=results/dev_runs.jsonl bash scripts/run_pairs.sh

selection:  ## run the defense candidates on the development pairs and apply the selection rule
	$(PY) scripts/select_defense.py --seeds $(SEEDS)

test-pairs:  ## run the experiment matrix on the five test subject pairs
	PY=$(PY) SEEDS="$(SEEDS)" PAIRS="$(TEST_PAIRS)" OUT=results/test_runs.jsonl bash scripts/run_pairs.sh

band-ablation:  ## rerun E8 on every pair with 5-15 Hz removed from the consistency perturbations
	$(PY) scripts/ablate_consistency_band.py --seeds $(SEEDS)

curve:  ## run the compression-strength sweep
	: > results/tradeoff_curve.jsonl
	$(PY) scripts/sweep_spectral_defense.py --curve --family freq --seeds $(SEEDS) \
		--out results/tradeoff_curve.jsonl
	$(PY) scripts/plot_compression_curve.py

demo:  ## launch the Streamlit dashboard
	$(PY) -m streamlit run dashboard/app.py

clean:  ## remove caches and intermediate checkpoints
	rm -rf .pytest_cache .ruff_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
	rm -f checkpoints/adapted_* checkpoints/aux_* checkpoints/compressed_*
