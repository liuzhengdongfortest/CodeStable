#!/usr/bin/env python3
"""Shared helpers for minimal CodeStable gate scripts."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True


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


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        return [item.strip().strip("'\"") for item in value[1:-1].split(",") if item.strip()]
    lower = value.lower()
    if lower in {"true", "yes"}:
        return True
    if lower in {"false", "no"}:
        return False
    if lower in {"null", "~"}:
        return None
    return value.strip("'\"")


def _minimal_yaml(text: str) -> Any:
    lines: list[tuple[int, str]] = []
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        lines.append((indent, raw.strip()))

    def parse_block(index: int, indent: int) -> tuple[Any, int]:
        if index >= len(lines):
            return {}, index
        if lines[index][1].startswith("- "):
            return parse_list(index, indent)
        return parse_dict(index, indent)

    def parse_dict(index: int, indent: int) -> tuple[dict[str, Any], int]:
        result: dict[str, Any] = {}
        while index < len(lines):
            current_indent, line = lines[index]
            if current_indent < indent or current_indent != indent or line.startswith("- "):
                break
            if ":" not in line:
                index += 1
                continue
            key, _, value = line.partition(":")
            key = key.strip()
            if value.strip():
                result[key] = _parse_scalar(value)
                index += 1
                continue
            index += 1
            if index < len(lines) and lines[index][0] > current_indent:
                result[key], index = parse_block(index, lines[index][0])
            else:
                result[key] = {}
        return result, index

    def parse_list(index: int, indent: int) -> tuple[list[Any], int]:
        result: list[Any] = []
        while index < len(lines):
            current_indent, line = lines[index]
            if current_indent < indent or current_indent != indent or not line.startswith("- "):
                break
            item_text = line[2:].strip()
            index += 1
            if not item_text:
                item: Any = {}
            elif ":" in item_text:
                key, _, value = item_text.partition(":")
                item = {key.strip(): _parse_scalar(value)}
                if not value.strip() and index < len(lines) and lines[index][0] > current_indent:
                    item[key.strip()], index = parse_block(index, lines[index][0])
            else:
                item = _parse_scalar(item_text)
            if index < len(lines) and lines[index][0] > current_indent:
                child, index = parse_block(index, lines[index][0])
                if isinstance(item, dict) and isinstance(child, dict):
                    item.update(child)
                elif isinstance(item, dict):
                    item["items"] = child
                else:
                    item = {"value": item, "items": child}
            result.append(item)
        return result, index

    if not lines:
        return {}
    parsed, _ = parse_block(0, lines[0][0])
    return parsed


def load_yaml(path: Path) -> Any:
    return load_yaml_text(path.read_text(encoding="utf-8"))


def load_yaml_text(text: str) -> Any:
    try:
        import yaml  # type: ignore
    except ImportError:
        return _minimal_yaml(text)
    return yaml.safe_load(text) or {}


def main_exit(result: dict[str, Any], json_out: str | None = None) -> None:
    write_optional_json(result, json_out)
    print_json(result)
    sys.exit(exit_for_status(str(result.get("status", "blocked"))))
