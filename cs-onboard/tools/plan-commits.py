#!/usr/bin/env python3
"""Plan logical commit buckets without staging or committing."""

from __future__ import annotations

import argparse
import fnmatch
import json
import time
from dataclasses import asdict
from pathlib import Path

from codestable_common import (
    Finding,
    bucket_paths,
    git_status,
    path_bucket,
    run_git,
    tracked_ignored_paths,
)


DEFAULT_LARGE_FILE_BYTES = 1024 * 1024


def changed_paths(root: Path) -> list[str]:
    return [item.path for item in git_status(root)]


def parse_doc_mapping(root: Path) -> dict[str, list[str]]:
    agents = root / "AGENTS.md"
    if not agents.exists():
        return {}
    mapping: dict[str, list[str]] = {}
    for line in agents.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        doc = cells[0].strip("` ")
        if not doc.startswith("docs/"):
            continue
        sources = [part.strip().strip("`") for part in cells[1].split(",") if part.strip()]
        for source in sources:
            mapping.setdefault(source, []).append(doc)
    return mapping


def normalize_source_path(path: str) -> str:
    prefixes = ("src/gammasource/", "src/")
    for prefix in prefixes:
        if path.startswith(prefix):
            return path[len(prefix) :]
    return path


def required_docs_for_path(doc_mapping: dict[str, list[str]], path: str) -> list[str]:
    required: list[str] = []
    for source, docs in doc_mapping.items():
        if source == path or fnmatch.fnmatch(path, source):
            required.extend(docs)
    return sorted(set(required))


def file_size(root: Path, path: str) -> int:
    target = root / path
    if not target.exists() or not target.is_file():
        return 0
    return target.stat().st_size


def changing_size_paths(root: Path, paths: list[str]) -> list[str]:
    first = {path: file_size(root, path) for path in paths}
    time.sleep(0.05)
    second = {path: file_size(root, path) for path in paths}
    return sorted(path for path in paths if first[path] != second[path])


def plan(root: Path, large_file_bytes: int = DEFAULT_LARGE_FILE_BYTES) -> dict[str, object]:
    root = root.resolve()
    paths = changed_paths(root)
    buckets = bucket_paths(paths)
    findings: list[Finding] = []

    if "migrations" in buckets and "database_docs" not in buckets:
        findings.append(
            Finding(
                severity="P1",
                message="Migration changes are present without database contract docs.",
                path=", ".join(buckets["migrations"]),
            )
        )

    doc_mapping = parse_doc_mapping(root)
    if doc_mapping:
        changed_set = set(paths)
        for path in paths:
            normalized = normalize_source_path(path)
            required_docs = required_docs_for_path(doc_mapping, normalized)
            if required_docs and not any(doc in changed_set for doc in required_docs):
                findings.append(
                    Finding(
                        severity="P2",
                        message="Source file has mapped docs that are not changed in this tree.",
                        path=f"{path} -> {', '.join(required_docs)}",
                    )
                )

    tracked_ignored = tracked_ignored_paths(root)
    if tracked_ignored:
        findings.append(
            Finding(
                severity="P2",
                message="Tracked files are ignored by the current ignore rules.",
                path=", ".join(tracked_ignored),
            )
        )

    large_paths = sorted(path for path in paths if file_size(root, path) > large_file_bytes)
    if large_paths:
        findings.append(
            Finding(severity="P2", message="Large changed files need intentional commit handling.", path=", ".join(large_paths))
        )

    if "unknown" in buckets:
        findings.append(
            Finding(
                severity="P2",
                message="Some changed files do not match a known CodeStable commit bucket.",
                path=", ".join(buckets["unknown"]),
            )
        )

    changing_paths = changing_size_paths(root, paths)
    if changing_paths:
        findings.append(
            Finding(severity="P2", message="Some changed files are still changing; live writer may be active.", path=", ".join(changing_paths))
        )

    suggested_commits = [
        {"bucket": bucket, "paths": bucket_paths}
        for bucket, bucket_paths in buckets.items()
    ]

    return {
        "ok": not any(finding.severity == "P1" for finding in findings),
        "changed_files": paths,
        "buckets": buckets,
        "suggested_commits": suggested_commits,
        "findings": [asdict(finding) for finding in findings],
        "mutates": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--json", action="store_true", help="Print machine-readable output")
    parser.add_argument("--large-file-bytes", type=int, default=DEFAULT_LARGE_FILE_BYTES)
    args = parser.parse_args()

    payload = plan(Path(args.root), args.large_file_bytes)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("CodeStable commit plan:")
        for item in payload["suggested_commits"]:
            print(f"- {item['bucket']}: {len(item['paths'])} paths")
        for finding in payload["findings"]:
            path = f" ({finding['path']})" if finding.get("path") else ""
            print(f"- {finding['severity']}: {finding['message']}{path}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
