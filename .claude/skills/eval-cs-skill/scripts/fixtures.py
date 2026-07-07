#!/usr/bin/env python3
"""加载与校验 experiments/<name>/fixtures/<class>/*.json。"""

from __future__ import annotations

import json
from pathlib import Path

from _model import Fixture


def load_fixtures(experiment_dir: Path, classes: list[str]) -> list[Fixture]:
    out: list[Fixture] = []
    seen: set[str] = set()
    for cls in classes:
        cls_dir = experiment_dir / "fixtures" / cls
        if not cls_dir.is_dir():
            continue
        for path in sorted(cls_dir.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            fixture = Fixture.from_dict(data)
            if fixture.id in seen:
                raise ValueError(f"重复 fixture id: {fixture.id} ({path})")
            seen.add(fixture.id)
            out.append(fixture)
    return out


def validate_fixture_dict(data: dict) -> list[str]:
    """返回问题列表，空=合规。供 tests 复用。"""
    problems: list[str] = []
    if "id" not in data:
        problems.append("缺 id")
    at = data.get("answerType")
    if at not in {"findings-recall", "dod-gate", "dimensions-judge"}:
        problems.append(f"answerType 非法: {at!r}")
    if at == "findings-recall" and not data.get("answer"):
        problems.append("findings-recall 必须有非空 answer")
    if at == "dod-gate" and not data.get("checklist_path"):
        problems.append("dod-gate 必须有 checklist_path")
    if "task" not in data:
        problems.append("缺 task")
    return problems
