#!/usr/bin/env python3
"""Scorer 基类与注册表。

Scorer 契约：score(fixture, result, config, root) -> dict
  {"scores": {name: tagged(...)}, "evidence": [...], "status": "passed|failed"}
加 scorer = 加一个模块并 register，不改 runner。
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True  # 不污染 plugin 包

from pathlib import Path
from typing import Any, Callable

_SCRIPTS = Path(__file__).resolve().parent.parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

Scorer = Callable[..., dict[str, Any]]
_REGISTRY: dict[str, Scorer] = {}
_APPLIES: dict[str, set[str]] = {}   # scorer → 适用的 answerType 集；空集=适用所有


def register(name: str, applies_to: set[str] | None = None) -> Callable[[Scorer], Scorer]:
    def deco(fn: Scorer) -> Scorer:
        _REGISTRY[name] = fn
        _APPLIES[name] = set(applies_to or [])
        return fn
    return deco


def get_scorer(name: str) -> Scorer:
    if name not in _REGISTRY:
        raise KeyError(f"未知 scorer {name!r}；已注册 {sorted(_REGISTRY)}")
    return _REGISTRY[name]


def applies(name: str, answer_type: str) -> bool:
    aset = _APPLIES.get(name) or set()
    return (not aset) or (answer_type in aset)


def available() -> list[str]:
    return sorted(_REGISTRY)
