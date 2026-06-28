#!/usr/bin/env python3
"""Shared helpers for minimal CodeStable gate scripts."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def repo_root() -> Path:
    current = Path.cwd()
    for path in (current, *current.parents):
        if (path / ".git").exists() or (path / ".codestable").exists():
            return path
    return current


def read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def gate_result(
    gate_id: str,
    stage: str,
    status: str,
    blocking: list[str] | None = None,
    warnings: list[str] | None = None,
    evidence: list[Any] | None = None,
) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "stage": stage,
        "status": status,
        "blocking": blocking or [],
        "warnings": warnings or [],
        "evidence": evidence or [],
        "providers": {},
    }


def print_json(data: dict[str, Any]) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def exit_for_status(status: str) -> int:
    return 0 if status in {"passed", "skipped"} else 1


def parse_args(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--json-out", help="Optional path to write JSON result")
    return parser


def write_optional_json(result: dict[str, Any], json_out: str | None) -> None:
    if json_out:
        Path(json_out).parent.mkdir(parents=True, exist_ok=True)
        Path(json_out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_command(command: str, cwd: Path) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        shell=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return {
        "command": command,
        "exit_code": completed.returncode,
        "stdout": completed.stdout[-4000:],
        "stderr": completed.stderr[-4000:],
    }


def load_yaml(path: Path) -> Any:
    try:
        import yaml  # type: ignore
    except ImportError:
        raise SystemExit("PyYAML is required for this gate script")
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def main_exit(result: dict[str, Any], json_out: str | None = None) -> None:
    write_optional_json(result, json_out)
    print_json(result)
    sys.exit(exit_for_status(str(result.get("status", "blocked"))))
