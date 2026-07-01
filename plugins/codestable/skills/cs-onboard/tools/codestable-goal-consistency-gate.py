#!/usr/bin/env python3
"""Final consistency gate for roadmap goal completion."""

from __future__ import annotations

import os
import json
import sys
from pathlib import Path
from typing import Any

if os.environ.get("PYTHONDONTWRITEBYTECODE") != "1":
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    os.execvpe(sys.executable, [sys.executable, *sys.argv], os.environ)
sys.dont_write_bytecode = True

from codestable_gate_common import gate_result, load_yaml, load_yaml_text, main_exit, parse_args


def frontmatter(path: Path) -> dict[str, Any]:
    if not path.exists() or path.suffix != ".md":
        return {}
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    return load_yaml_text(text[3:end].strip()) or {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def project_root(roadmap: Path) -> Path:
    resolved = roadmap.resolve()
    for parent in (resolved, *resolved.parents):
        if parent.name == ".codestable":
            return parent.parent
    return Path.cwd()


def resolve_path(root: Path, value: Any) -> Path:
    path = Path(str(value or ""))
    return path if path.is_absolute() else root / path


def items_file(roadmap: Path) -> Path:
    direct = roadmap / f"{roadmap.name}-items.yaml"
    if direct.exists():
        return direct
    matches = sorted(roadmap.glob("*-items.yaml"))
    return matches[0] if matches else direct


def status_of(path: Path) -> str:
    return str(frontmatter(path).get("status", "missing"))


def json_status(path: Path) -> str:
    if not path.exists():
        return "missing"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "invalid"
    return str(data.get("status", "missing"))


def main() -> None:
    parser = parse_args("Check roadmap goal final state against required artifacts.")
    parser.add_argument("--roadmap", required=True, help="Roadmap goal directory")
    parser.add_argument("--stage", default="roadmap_audit.before_complete")
    args = parser.parse_args()

    roadmap = Path(args.roadmap)
    blocking: list[str] = []
    warnings: list[str] = []
    evidence: list[dict[str, Any]] = []

    if not roadmap.is_dir():
        result = gate_result("goal-consistency-gate", args.stage, "blocked", [f"roadmap dir not found: {roadmap}"])
        main_exit(result, args.json_out)

    root = project_root(roadmap)
    items_path = items_file(roadmap)
    state_path = roadmap / "goal-state.yaml"
    audit_path = roadmap / "goal-audit.md"
    for required in (items_path, state_path, audit_path):
        if not required.exists():
            blocking.append(f"missing required roadmap artifact: {required}")

    items = load_yaml(items_path) if items_path.exists() else {}
    state = load_yaml(state_path) if state_path.exists() else {}
    features = as_list(state.get("features"))

    if state.get("status") != "completed":
        blocking.append("goal-state status is not completed")
    if state.get("current_feature_index") != len(features):
        blocking.append("goal-state current_feature_index does not equal feature count")
    if status_of(audit_path) != "passed":
        blocking.append("goal-audit.md is missing or not status=passed")

    item_rows = as_list(items.get("items") or items.get("features"))
    for row in item_rows:
        if not isinstance(row, dict):
            continue
        item_slug = row.get("slug") or row.get("id") or row.get("name")
        status = row.get("status")
        if status not in {"done", "dropped"}:
            blocking.append(f"roadmap item not terminal: {item_slug or '<unknown>'} status={status}")

    for index, feature in enumerate(features):
        if not isinstance(feature, dict):
            blocking.append(f"goal-state feature #{index + 1} is not a mapping")
            continue
        feature_slug = str(feature.get("slug", f"feature-{index + 1}"))
        if feature.get("status") != "accepted":
            blocking.append(f"{feature_slug}: goal-state status is not accepted")
        checklist_path = resolve_path(root, feature.get("checklist"))
        review_path = resolve_path(root, feature.get("review"))
        qa_path = resolve_path(root, feature.get("qa"))
        acceptance_path = resolve_path(root, feature.get("acceptance"))
        feature_dir = resolve_path(root, feature.get("feature_dir"))
        expected = {
            "review": review_path,
            "qa": qa_path,
            "acceptance": acceptance_path,
            "checklist": checklist_path,
            "evidence_pack": feature_dir / f"{feature_slug}-evidence-pack.md",
            "evidence_pack_results": feature_dir / f"{feature_slug}-evidence-pack-results.json",
            "gate_results": feature_dir / f"{feature_slug}-gate-results.json",
            "dod_results": feature_dir / f"{feature_slug}-dod-results.json",
            "dod_contract_results": feature_dir / f"{feature_slug}-dod-contract-results.json",
        }
        for label, path in expected.items():
            if not path.exists():
                blocking.append(f"{feature_slug}: missing {label}: {path}")
        if review_path.exists() and status_of(review_path) != "passed":
            blocking.append(f"{feature_slug}: review is not status=passed")
        if qa_path.exists() and status_of(qa_path) != "passed":
            blocking.append(f"{feature_slug}: QA is not status=passed")
        if acceptance_path.exists() and status_of(acceptance_path) != "passed":
            blocking.append(f"{feature_slug}: acceptance is not status=passed")
        for label in ("evidence_pack_results", "gate_results", "dod_results", "dod_contract_results"):
            path = expected[label]
            status_value = json_status(path)
            if status_value not in {"passed", "generated"}:
                blocking.append(f"{feature_slug}: {label} JSON is not passed/generated: status={status_value}")
        if checklist_path.exists():
            checklist = load_yaml(checklist_path)
            for step in as_list(checklist.get("steps")):
                if isinstance(step, dict) and step.get("status") != "done":
                    blocking.append(f"{feature_slug}: checklist step not done: {step.get('id') or step.get('name')}")
            for check in as_list(checklist.get("checks")):
                if isinstance(check, dict) and check.get("status") != "passed":
                    blocking.append(f"{feature_slug}: checklist check not passed: {check.get('id') or check.get('name')}")
        evidence.append({"feature": feature_slug, "artifacts_checked": sorted(expected)})

    status = "failed" if blocking else "passed"
    result = gate_result("goal-consistency-gate", args.stage, status, blocking, warnings, evidence)
    main_exit(result, args.json_out)


if __name__ == "__main__":
    main()
