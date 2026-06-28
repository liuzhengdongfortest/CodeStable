#!/usr/bin/env python3
"""Minimal scope and cleanliness gate for roadmap goal features."""

from __future__ import annotations

import os
import sys
from pathlib import Path

if os.environ.get("PYTHONDONTWRITEBYTECODE") != "1":
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    os.execvpe(sys.executable, [sys.executable, *sys.argv], os.environ)
sys.dont_write_bytecode = True

from codestable_gate_common import gate_result, main_exit, parse_args, repo_root, run_command


CLEAN_PATTERNS = ("TODO", "FIXME", "XXX")
DEFAULT_CLEAN_SUFFIXES = {".py", ".sh", ".yaml", ".yml"}
MACHINE_ARTIFACT_SUFFIXES = (
    "-gate-results.json",
    "-dod-results.json",
    "-evidence-pack-results.json",
)


def is_machine_artifact(path: str) -> bool:
    parts = Path(path).parts
    return (
        "__pycache__" in parts
        or path.endswith(".pyc")
        or path.endswith(MACHINE_ARTIFACT_SUFFIXES)
    )


def is_under(path: str, prefix: str) -> bool:
    clean = prefix.rstrip("/")
    return path == clean or path.startswith(clean + "/")


def changed_files(root: Path, paths: list[str]) -> list[str]:
    quoted = " ".join(f"'{path}'" for path in paths)
    command = "git status --porcelain -uall"
    if quoted:
        command = f"{command} -- {quoted}"
    status = run_command(command, root)
    if status["exit_code"] != 0:
        return []
    files: list[str] = []
    for line in str(status["stdout"]).splitlines():
        if not line:
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        files.append(path.strip('"'))
    return files


def main() -> None:
    parser = parse_args("Check current diff for coarse scope and cleanliness issues.")
    parser.add_argument("--feature-dir", required=True, help="Feature directory expected in scope")
    parser.add_argument("--allow", action="append", default=[], help="Allowed path prefix; repeatable")
    parser.add_argument("--allow-file", help="File containing one allowed path prefix per line")
    parser.add_argument("--check-path", action="append", default=[], help="Limit git status to this path; repeatable")
    parser.add_argument(
        "--cleanliness-path",
        action="append",
        default=[],
        help="Additional path prefix to scan for TODO/FIXME/XXX; repeatable. Markdown is scanned only when included here.",
    )
    parser.add_argument("--stage", default="implementation.before_review")
    args = parser.parse_args()

    root = repo_root()
    allowed = [args.feature_dir, *args.allow]
    if args.allow_file:
        allow_path = Path(args.allow_file)
        if not allow_path.exists():
            result = gate_result("scope-gate", args.stage, "blocked", [f"allow file not found: {allow_path}"])
            main_exit(result, args.json_out)
        allowed.extend(
            line.strip()
            for line in allow_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        )
    check_paths = args.check_path or allowed
    raw_files = changed_files(root, check_paths)
    files = [path for path in raw_files if not is_machine_artifact(path)]
    ignored = [path for path in raw_files if is_machine_artifact(path)]
    out_of_scope = [
        path for path in files
        if not any(is_under(path, prefix) for prefix in allowed)
    ]

    clean_hits = []
    for path in files:
        full = root / path
        explicit_cleanliness = any(is_under(path, prefix) for prefix in args.cleanliness_path)
        if full.is_file() and (full.suffix in DEFAULT_CLEAN_SUFFIXES or explicit_cleanliness):
            try:
                text = full.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for pattern in CLEAN_PATTERNS:
                if pattern in text:
                    clean_hits.append({"path": path, "pattern": pattern})

    blocking = [f"out-of-scope changed file: {path}" for path in out_of_scope]
    warnings = [f"cleanliness marker {hit['pattern']} in {hit['path']}" for hit in clean_hits]
    status = "failed" if blocking else "passed"
    result = gate_result(
        "scope-gate",
        args.stage,
        status,
        blocking,
        warnings,
        [{"changed_files": files, "ignored_machine_artifacts": ignored, "allowed_prefixes": allowed}],
    )
    main_exit(result, args.json_out)


if __name__ == "__main__":
    main()
