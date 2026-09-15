"""Result records written to results/runs.jsonl."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TriggerResult:
    """ASR for one trigger family against one model."""

    name: str
    family: str
    asr: float
    asr_ci: tuple[float, float]
    asr_inclusive: float
    clean_target_rate: float
    lift: float
    n_eligible: int
    stealth: dict[str, float] = field(default_factory=dict)
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunResult:
    exp_id: str
    dataset: str
    source: str
    target: str
    model_type: str  # "clean" | "backdoored"
    adaptation: str  # "none" | "mapu" | "shot"
    defense: str  # "none" | "compress" | "secure-mapu" | ...
    seed: int
    clean_acc: float
    clean_mf1: float
    clean_acc_ci: tuple[float, float] = (float("nan"), float("nan"))
    n_clean: int = 0
    asr: dict[str, TriggerResult] = field(default_factory=dict)
    target_class: int | None = None
    attack_family: str = ""  # which trigger the source model was actually poisoned with
    source_clean_acc: float | None = None
    source_asr: dict[str, float] = field(default_factory=dict)
    defense_info: dict[str, Any] = field(default_factory=dict)
    config_hash: str = ""
    duration_s: float = 0.0
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["asr"] = {k: asdict(v) if not isinstance(v, dict) else v for k, v in self.asr.items()}
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, default=str)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> RunResult:
        d = dict(d)
        asr = {}
        for k, v in (d.pop("asr", {}) or {}).items():
            v = dict(v)
            v["asr_ci"] = tuple(v.get("asr_ci", (float("nan"), float("nan"))))
            asr[k] = TriggerResult(**v)
        d["clean_acc_ci"] = tuple(d.get("clean_acc_ci", (float("nan"), float("nan"))))
        known = {f for f in cls.__dataclass_fields__}
        return cls(asr=asr, **{k: v for k, v in d.items() if k in known})

    @classmethod
    def from_json(cls, s: str) -> RunResult:
        return cls.from_dict(json.loads(s))

    def append_to(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a") as f:
            f.write(self.to_json() + "\n")
        return path

    @property
    def scenario(self) -> str:
        return f"{self.source}->{self.target}"


def load_runs(path: str | Path) -> list[RunResult]:
    path = Path(path)
    if not path.exists():
        return []
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(RunResult.from_json(line))
    return out
