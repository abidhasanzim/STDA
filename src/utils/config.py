"""YAML config loading.

Top-level data/model/attack/defense/train keys may name another YAML file, which is loaded
in place. apply_overrides handles dotted key=value overrides from the command line.
"""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

REF_KEYS = ("data", "model", "attack", "defense", "train")


def load_yaml(path: str | Path) -> dict[str, Any]:
    with open(path) as f:
        out = yaml.safe_load(f)
    if not isinstance(out, dict):
        raise ValueError(f"{path}: expected a mapping at the top level")
    return out


def load_config(path: str | Path) -> dict[str, Any]:
    cfg = load_yaml(path)
    for key in REF_KEYS:
        val = cfg.get(key)
        if isinstance(val, str):
            cfg[key] = load_yaml(val)
            cfg[key]["_source"] = val
    return cfg


def _coerce(text: str) -> Any:
    try:
        return ast.literal_eval(text)
    except (ValueError, SyntaxError):
        return text


def apply_overrides(cfg: dict[str, Any], overrides: list[str] | None) -> dict[str, Any]:
    """Apply ``a.b.c=value`` overrides in place and return the config."""
    for item in overrides or []:
        if "=" not in item:
            raise ValueError(f"override {item!r} is not of the form key=value")
        dotted, raw = item.split("=", 1)
        node = cfg
        parts = dotted.split(".")
        for p in parts[:-1]:
            node = node.setdefault(p, {})
            if not isinstance(node, dict):
                raise ValueError(f"override {dotted!r} traverses non-mapping {p!r}")
        node[parts[-1]] = _coerce(raw)
    return cfg


def config_hash(cfg: dict[str, Any]) -> str:
    """Short stable hash of a config."""
    blob = json.dumps(cfg, sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()[:12]


def flatten(cfg: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Flatten to dotted keys, for parameter logging."""
    out: dict[str, Any] = {}
    for k, v in cfg.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(flatten(v, f"{key}."))
        elif isinstance(v, (list, tuple)):
            out[key] = json.dumps(list(v))
        else:
            out[key] = v
    return out
