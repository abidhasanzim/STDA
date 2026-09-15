"""Optional MLflow tracking; becomes a no-op when MLflow is unavailable or disabled."""

from __future__ import annotations

import contextlib
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]


class _NullRun:
    def log_params(self, params: dict[str, Any]) -> None: ...
    def log_metrics(self, metrics: dict[str, float], step: int | None = None) -> None: ...
    def log_artifact(self, path: str | Path) -> None: ...
    def set_tags(self, tags: dict[str, Any]) -> None: ...


class _MlflowRun:
    def __init__(self, mlflow):
        self._mlflow = mlflow

    def log_params(self, params: dict[str, Any]) -> None:
        # MLflow rejects params over 500 chars and non-scalars.
        clean = {k: str(v)[:500] for k, v in params.items() if not k.startswith("_")}
        self._mlflow.log_params(clean)

    def log_metrics(self, metrics: dict[str, float], step: int | None = None) -> None:
        clean = {k: float(v) for k, v in metrics.items() if v is not None}
        self._mlflow.log_metrics(clean, step=step)

    def log_artifact(self, path: str | Path) -> None:
        self._mlflow.log_artifact(str(path))

    def set_tags(self, tags: dict[str, Any]) -> None:
        self._mlflow.set_tags({k: str(v)[:500] for k, v in tags.items()})


@contextlib.contextmanager
def start_run(
    experiment: str = "sfda-audit",
    run_name: str | None = None,
    enabled: bool = True,
) -> Iterator[Any]:
    """Yield a run handle. Falls back to a no-op if mlflow is missing or disabled."""
    if not enabled or os.environ.get("SFDA_NO_TRACKING"):
        yield _NullRun()
        return
    try:
        import mlflow
    except ImportError:
        yield _NullRun()
        return

    # MLflow 3.16 no longer supports the file store, so use a local SQLite database.
    uri = os.environ.get("MLFLOW_TRACKING_URI", f"sqlite:///{REPO_ROOT / 'mlruns' / 'mlflow.db'}")
    artifacts = os.environ.get("MLFLOW_ARTIFACT_ROOT", str(REPO_ROOT / "mlruns" / "artifacts"))
    (REPO_ROOT / "mlruns").mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri(uri)
    if mlflow.get_experiment_by_name(experiment) is None:
        with contextlib.suppress(Exception):
            mlflow.create_experiment(experiment, artifact_location=f"file://{artifacts}")
    mlflow.set_experiment(experiment)
    with mlflow.start_run(run_name=run_name):
        yield _MlflowRun(mlflow)
