"""Trigger families used to poison source models and measure attack success."""

import inspect

from src.attack.base import Trigger
from src.attack.freq import FreqTrigger
from src.attack.patch import PatchTrigger

__all__ = ["Trigger", "PatchTrigger", "FreqTrigger", "build_trigger", "build_triggers"]

_FAMILIES = {
    "patch": PatchTrigger,
    "temporal": PatchTrigger,
    "freq": FreqTrigger,
    "frequency": FreqTrigger,
}


def build_trigger(cfg: dict, channel_std=None) -> Trigger:
    """Instantiate one trigger from a config mapping carrying a ``family`` key."""
    cfg = dict(cfg)
    family = str(cfg.pop("family", cfg.pop("name", ""))).lower()
    cfg.pop("_source", None)
    # channel_std is recorded provenance, not a constructor argument.
    cfg.pop("channel_std", None)
    if family not in _FAMILIES:
        raise ValueError(f"unknown trigger family {family!r}; expected one of {sorted(_FAMILIES)}")
    known = _FAMILIES[family]
    allowed = set(inspect.signature(known.__init__).parameters) - {"self", "channel_std"}
    params = {k: v for k, v in cfg.items() if k in allowed}
    return known(channel_std=channel_std, **params)


def build_triggers(cfgs, channel_std=None) -> list[Trigger]:
    """Instantiate the list of triggers an audit sweeps over."""
    if isinstance(cfgs, dict):
        cfgs = [cfgs]
    return [build_trigger(c, channel_std) for c in cfgs]
