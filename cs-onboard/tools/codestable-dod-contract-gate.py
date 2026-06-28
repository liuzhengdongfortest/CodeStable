#!/usr/bin/env python3
"""Check that a feature design contains a minimal DoD Contract."""

from __future__ import annotations

import os
import sys
from pathlib import Path

if os.environ.get("PYTHONDONTWRITEBYTECODE") != "1":
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    os.execvpe(sys.executable, [sys.executable, *sys.argv], os.environ)
sys.dont_write_bytecode = True

from codestable_gate_common import gate_result, main_exit, parse_args, read_text


STRUCTURE_CHECKS = {
    "validation command id": ("CMD-",),
    "command core marker": ("core", "核心性"),
    "failure handling marker": ("failure_handling", "失败处理"),
}


def contract_block(text: str) -> str | None:
    lines = text.splitlines()
    start = None
    start_level = 99
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#") and "DoD Contract" in stripped:
            start = index
            start_level = len(stripped) - len(stripped.lstrip("#"))
            break
    if start is None:
        for index, line in enumerate(lines):
            stripped = line.strip()
            if stripped.rstrip(":") != "DoD Contract":
                continue
            start = index
            start_level = 99
            break
    if start is None:
        return None
    end = len(lines)
    for index in range(start + 1, len(lines)):
        stripped = lines[index].strip()
        if not stripped.startswith("#"):
            continue
        level = len(stripped) - len(stripped.lstrip("#"))
        if level <= start_level:
            end = index
            break
    return "\n".join(lines[start:end])


def artifacts_have_content(block: str) -> bool:
    for line in block.splitlines():
        stripped = line.strip().lstrip("-*").strip()
        if not stripped.startswith("Required Artifacts"):
            continue
        _, _, value = stripped.partition(":")
        return bool(value.strip())
    return False


def main() -> None:
    parser = parse_args("Check a design document for minimal DoD Contract structure.")
    parser.add_argument("--design", required=True, help="Path to feature design markdown")
    parser.add_argument("--stage", default="feature_design.before_approve")
    args = parser.parse_args()

    path = Path(args.design)
    if not path.exists():
        result = gate_result("dod-contract-gate", args.stage, "blocked", [f"design not found: {path}"])
        main_exit(result, args.json_out)

    text = read_text(path)
    block = contract_block(text)
    missing = []
    if block is None:
        missing.append("DoD Contract section")
        block = ""
    if "Validation Commands" not in block:
        missing.append("Validation Commands in DoD Contract")
    if "Required Artifacts" not in block:
        missing.append("Required Artifacts in DoD Contract")
    elif not artifacts_have_content(block):
        missing.append("non-empty Required Artifacts")
    missing.extend(
        f"missing minimal DoD structure: {name}"
        for name, needles in STRUCTURE_CHECKS.items()
        if not any(needle in block for needle in needles)
    )
    status = "failed" if missing else "passed"
    result = gate_result(
        "dod-contract-gate",
        args.stage,
        status,
        [
            item if item.startswith("missing minimal DoD structure:")
            else f"missing required DoD contract item: {item}"
            for item in missing
        ],
        evidence=[{
            "design": str(path),
            "checked_block": "DoD Contract",
            "structure_checks": STRUCTURE_CHECKS,
            "strength": "minimal DoD Contract section check",
        }],
    )
    main_exit(result, args.json_out)


if __name__ == "__main__":
    main()
