#!/usr/bin/env python3
"""Run checklist dod.commands and report real exit codes."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

if os.environ.get("PYTHONDONTWRITEBYTECODE") != "1":
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    os.execvpe(sys.executable, [sys.executable, *sys.argv], os.environ)
sys.dont_write_bytecode = True

from codestable_gate_common import (
    file_sha256,
    gate_result,
    load_yaml,
    main_exit,
    parse_args,
    repo_relative_path,
    repo_root,
    run_command,
)


def clear_previous_json_out(json_out: str | None) -> None:
    if not json_out:
        return
    path = Path(json_out)
    if (path.exists() or path.is_symlink()) and not (path.is_dir() and not path.is_symlink()):
        path.unlink()


def collect_commands(checklist: dict[str, Any]) -> list[dict[str, Any]]:
    # Authoritative schema: top-level `dod.commands` (cs-feat-design reference §"DoD
    # Contract" — `dod` is a top-level checklist key alongside `steps`/`checks`).
    # If present, it is the single source — do NOT also pull step-level commands,
    # or a checklist carrying both would execute each command twice.
    top_dod = checklist.get("dod") or {}
    if not isinstance(top_dod, dict):
        raise ValueError("checklist dod must be a mapping")
    top_commands = top_dod.get("commands") or []
    if not isinstance(top_commands, list) or any(not isinstance(command, dict) for command in top_commands):
        raise ValueError("checklist dod.commands must be a list of mappings")
    if top_commands:
        return list(top_commands)
    # Backward-compat: no top-level dod → fall back to step-level `dod.commands`.
    commands: list[dict[str, Any]] = []
    steps = checklist.get("steps", []) or []
    if not isinstance(steps, list) or any(not isinstance(step, dict) for step in steps):
        raise ValueError("checklist steps must be a list of mappings")
    for step in steps:
        dod = step.get("dod") or {}
        if not isinstance(dod, dict):
            raise ValueError("checklist step dod must be a mapping")
        step_commands = dod.get("commands", []) or []
        if not isinstance(step_commands, list) or any(
            not isinstance(command, dict) for command in step_commands
        ):
            raise ValueError("checklist step dod.commands must be a list of mappings")
        for command in step_commands:
            commands.append(command)
    return commands


def main() -> None:
    parser = parse_args("Run explicit checklist dod.commands using real subprocess exit codes.")
    parser.add_argument("--checklist", required=True, help="Path to checklist YAML")
    parser.add_argument("--only", action="append", default=[], help="Run only this command id; repeatable")
    parser.add_argument("--stage", default="implementation.before_review")
    args = parser.parse_args()
    clear_previous_json_out(args.json_out)

    root = repo_root()
    checklist_path = Path(args.checklist)
    checklist_input = repo_relative_path(root, checklist_path)
    feature_identity = Path(checklist_input).parent.name
    result_inputs = {"checklist": checklist_input}
    input_digests = {"checklist": file_sha256(checklist_path)} if checklist_path.is_file() else {}
    if not checklist_path.is_file():
        result = gate_result(
            "dod-runner",
            args.stage,
            "blocked",
            [f"checklist not found: {checklist_path}"],
            feature=feature_identity,
            inputs=result_inputs,
            input_digests=input_digests,
        )
        main_exit(result, args.json_out)

    try:
        checklist = load_yaml(checklist_path)
    except Exception as error:
        result = gate_result(
            "dod-runner",
            args.stage,
            "blocked",
            [f"invalid YAML artifact: {checklist_path} ({type(error).__name__}: {error})"],
            feature=feature_identity,
            inputs=result_inputs,
            input_digests=input_digests,
        )
        main_exit(result, args.json_out)
    if not isinstance(checklist, dict):
        result = gate_result(
            "dod-runner",
            args.stage,
            "blocked",
            [f"checklist is not a mapping: {checklist_path}"],
            feature=feature_identity,
            inputs=result_inputs,
            input_digests=input_digests,
        )
        main_exit(result, args.json_out)
    try:
        commands = collect_commands(checklist)
    except ValueError as error:
        result = gate_result(
            "dod-runner",
            args.stage,
            "blocked",
            [str(error)],
            feature=feature_identity,
            inputs=result_inputs,
            input_digests=input_digests,
        )
        main_exit(result, args.json_out)
    if args.only:
        requested = set(args.only)
        commands = [command for command in commands if command.get("id") in requested]
    if not commands:
        result = gate_result(
            "dod-runner",
            args.stage,
            "skipped",
            warnings=["no matching dod.commands found"],
            feature=feature_identity,
            inputs=result_inputs,
            input_digests=input_digests,
        )
        main_exit(result, args.json_out)

    evidence = []
    blocking = []
    warnings = []
    for command in commands:
        run = run_command(str(command.get("command", "")), root)
        run["id"] = command.get("id")
        run["core"] = bool(command.get("core"))
        run["failure_handling"] = command.get("failure_handling")
        evidence.append(run)
        if run["exit_code"] != 0 and run["core"]:
            blocking.append(f"{command.get('id')}: command failed with exit {run['exit_code']}")
        elif run["exit_code"] != 0:
            warnings.append(f"{command.get('id')}: non-core command failed with exit {run['exit_code']}")

    status = "failed" if blocking else "passed"
    result = gate_result(
        "dod-runner",
        args.stage,
        status,
        blocking,
        warnings,
        evidence,
        feature=feature_identity,
        inputs=result_inputs,
        input_digests=input_digests,
    )
    main_exit(result, args.json_out)


if __name__ == "__main__":
    main()
