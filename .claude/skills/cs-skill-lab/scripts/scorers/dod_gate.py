#!/usr/bin/env python3
"""dod_gate scorer：确定性 DoD 门。

复用 cs-onboard dod-runner 的**判据模式**（按 core 命令真实 exit_code 判 pass/fail），
但 self-contained：读 experiment 内 JSON checklist，在隔离 workdir 执行，不 import 其他 skill。
用于 golden fixtures——验证「产物/契约」是否满足，[measured]。
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from _model import MEASURED, tagged
from scorers.base import register


def _load_checklist(fixture, root: Path | None) -> dict:
    path = Path(fixture.checklist_path or "")
    if not path.is_absolute() and root is not None:
        # checklist_path 相对 experiment 目录（约定放 fixtures 同级）
        for base in (root, Path.cwd()):
            cand = base / path
            if cand.is_file():
                path = cand
                break
    return json.loads(Path(path).read_text(encoding="utf-8"))


@register("dod_gate", applies_to={"dod-gate"})
def score(fixture, result, config=None, root=None) -> dict[str, Any]:
    try:
        checklist = _load_checklist(fixture, root)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        return {
            "scores": {"dod_pass": tagged(0.0, MEASURED, evidence=f"checklist 不可读: {exc}")},
            "evidence": [{"error": str(exc)}],
            "status": "failed",
        }

    commands = checklist.get("commands", [])
    evidence, failed_core = [], False
    with tempfile.TemporaryDirectory(prefix="cs-dod-") as tmp:
        workdir = Path(tmp)
        # fixture.task.setup: {relpath: content} 预置产物
        for rel, content in (fixture.task.get("setup", {}) or {}).items():
            fp = workdir / rel
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(content, encoding="utf-8")
        for cmd in commands:
            completed = subprocess.run(
                cmd["command"], cwd=workdir, shell=True, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=120,
            )
            core = bool(cmd.get("core", True))
            ok = completed.returncode == 0
            if core and not ok:
                failed_core = True
            evidence.append({
                "id": cmd.get("id"), "command": cmd["command"], "exit_code": completed.returncode,
                "core": core, "stderr": completed.stderr[-500:],
            })

    passed = not failed_core
    return {
        "scores": {"dod_pass": tagged(1.0 if passed else 0.0, MEASURED,
                                      evidence=f"{sum(1 for e in evidence if e['exit_code'] == 0)}/{len(evidence)} commands ok")},
        "evidence": evidence,
        "status": "passed" if passed else "failed",
    }
