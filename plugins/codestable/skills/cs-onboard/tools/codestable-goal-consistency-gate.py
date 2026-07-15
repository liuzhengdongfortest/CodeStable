#!/usr/bin/env python3
"""Final consistency gate for roadmap goal completion."""

from __future__ import annotations

import os
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

if os.environ.get("PYTHONDONTWRITEBYTECODE") != "1":
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    os.execvpe(sys.executable, [sys.executable, *sys.argv], os.environ)
sys.dont_write_bytecode = True

from codestable_gate_common import (
    gate_result,
    load_yaml,
    load_yaml_text,
    main_exit,
    named_authorization_state,
    parse_args,
)


def record_parse_error(blocking: list[str], path: Path, error: Exception) -> None:
    message = f"invalid YAML artifact: {path} ({type(error).__name__})"
    if message not in blocking:
        blocking.append(message)


def frontmatter(path: Path, blocking: list[str]) -> dict[str, Any]:
    if not path.exists() or path.suffix != ".md":
        return {}
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as error:
        record_parse_error(blocking, path, error)
        return {}
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    try:
        parsed = load_yaml_text(text[3:end].strip()) or {}
    except Exception as error:
        record_parse_error(blocking, path, error)
        return {}
    return parsed if isinstance(parsed, dict) else {}


def load_yaml_artifact(path: Path, blocking: list[str]) -> Any:
    try:
        return load_yaml(path)
    except Exception as error:
        record_parse_error(blocking, path, error)
        return {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def validate_checklist_entries(
    feature_slug: str,
    checklist: dict[str, Any],
    key: str,
    expected_status: str,
    blocking: list[str],
) -> None:
    entries = checklist.get(key)
    if not isinstance(entries, list) or not entries:
        blocking.append(f"{feature_slug}: checklist {key} must be a non-empty list")
        return
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            blocking.append(f"{feature_slug}: checklist {key}[{index}] is not a mapping")
            continue
        if entry.get("status") != expected_status:
            label = entry.get("id") or entry.get("name") or index
            blocking.append(
                f"{feature_slug}: checklist {key[:-1]} not {expected_status}: {label}"
            )


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


def json_result(path: Path) -> tuple[str, dict[str, Any]]:
    if not path.exists():
        return "missing", {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "invalid", {}
    if not isinstance(data, dict):
        return "invalid", {}
    return str(data.get("status", "missing")), data


def input_digests(paths: dict[str, Path]) -> dict[str, str]:
    return {
        name: hashlib.sha256(path.read_bytes()).hexdigest()
        for name, path in paths.items()
        if path.is_file() and not path.is_symlink()
    }


def item_slug(row: dict[str, Any]) -> str:
    return str(row.get("slug") or row.get("id") or row.get("name") or "").strip()


def canonical_feature_directory(root: Path, slug: str, value: Any, blocking: list[str]) -> Path:
    features_root = (root / ".codestable/features").resolve()
    directory = resolve_path(root, value).resolve()
    expected_name = re.compile(rf"^\d{{4}}-\d{{2}}-\d{{2}}-{re.escape(slug)}$")
    try:
        directory.relative_to(features_root)
    except ValueError:
        blocking.append(f"{slug}: feature_dir escapes .codestable/features: {directory}")
        return features_root / f"invalid-{slug}"
    if not expected_name.fullmatch(directory.name):
        blocking.append(f"{slug}: feature_dir is not canonical for the feature slug: {directory}")
    return directory


def validate_markdown_identity(
    path: Path,
    blocking: list[str],
    feature_slug: str,
    feature_identity: str,
    doc_type: str,
) -> dict[str, Any]:
    metadata = frontmatter(path, blocking)
    if metadata.get("doc_type") != doc_type:
        blocking.append(f"{feature_slug}: {path.name} doc_type is not {doc_type}")
    if metadata.get("feature") != feature_identity:
        blocking.append(f"{feature_slug}: {path.name} feature identity does not match {feature_identity}")
    return metadata


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
    for required in (items_path, state_path):
        if not required.exists():
            blocking.append(f"missing required roadmap artifact: {required}")

    items_artifact = load_yaml_artifact(items_path, blocking) if items_path.exists() else {}
    state_artifact = load_yaml_artifact(state_path, blocking) if state_path.exists() else {}
    if not isinstance(items_artifact, dict):
        blocking.append(f"roadmap items artifact is not a mapping: {items_path}")
    if not isinstance(state_artifact, dict):
        blocking.append(f"goal-state artifact is not a mapping: {state_path}")
    items = items_artifact if isinstance(items_artifact, dict) else {}
    state = state_artifact if isinstance(state_artifact, dict) else {}
    feature_rows = state.get("features")
    if not isinstance(feature_rows, list):
        blocking.append("goal-state features is not a list")
    features = as_list(feature_rows)

    authorization_evidence: dict[str, dict[str, str]] = {}
    for field, decision_id in (
        ("acceptance_authorization", "goal-acceptance"),
        ("commit_authorization", "goal-commits"),
    ):
        authorization, reference, reason = named_authorization_state(
            roadmap, state, field, decision_id, lambda path: frontmatter(path, blocking)
        )
        authorization_evidence[field] = {
            "status": authorization,
            "reference": reference,
            "reason": reason,
        }
        if authorization != "approved":
            blocking.append(reason or f"{field} was rejected")
    evidence.append({"authorizations": authorization_evidence})

    if state.get("status") not in {"ready-to-dispatch", "complete", "completed"}:
        blocking.append("goal-state status is not ready for final audit")
    if state.get("current_feature_index") != len(features):
        blocking.append("goal-state current_feature_index does not equal feature count")

    raw_item_rows = items.get("items") if "items" in items else items.get("features")
    if not isinstance(raw_item_rows, list):
        blocking.append("roadmap items is not a list")
    item_rows = as_list(raw_item_rows)
    if not item_rows:
        blocking.append("roadmap items is empty")
    expected_features: set[str] = set()
    item_feature_identities: dict[str, str] = {}
    seen_items: set[str] = set()
    for index, row in enumerate(item_rows):
        if not isinstance(row, dict):
            blocking.append(f"roadmap item #{index + 1} is not a mapping")
            continue
        slug = item_slug(row)
        status = row.get("status")
        if not slug:
            blocking.append(f"roadmap item #{index + 1} has no slug")
            continue
        if slug in seen_items:
            blocking.append(f"duplicate roadmap item slug: {slug}")
        seen_items.add(slug)
        if status not in {"done", "dropped"}:
            blocking.append(f"roadmap item not terminal: {slug} status={status}")
        if status != "dropped":
            expected_features.add(slug)
            item_feature_identities[slug] = str(row.get("feature") or "").strip()

    seen_features: set[str] = set()
    for index, feature in enumerate(features):
        if not isinstance(feature, dict):
            continue
        slug = str(feature.get("slug") or "").strip()
        if not slug:
            blocking.append(f"goal-state feature #{index + 1} has no slug")
            continue
        if slug in seen_features:
            blocking.append(f"duplicate goal-state feature slug: {slug}")
        seen_features.add(slug)
        if str(feature.get("roadmap_item") or "").strip() != slug:
            blocking.append(f"{slug}: roadmap_item does not match feature slug")

    for slug in sorted(expected_features - seen_features):
        blocking.append(f"roadmap item has no goal-state feature: {slug}")
    for slug in sorted(seen_features - expected_features):
        blocking.append(f"goal-state feature has no non-dropped roadmap item: {slug}")

    for index, feature in enumerate(features):
        if not isinstance(feature, dict):
            blocking.append(f"goal-state feature #{index + 1} is not a mapping")
            continue
        feature_slug = str(feature.get("slug") or f"feature-{index + 1}").strip()
        if feature.get("status") != "accepted":
            blocking.append(f"{feature_slug}: goal-state status is not accepted")
        feature_dir = canonical_feature_directory(root, feature_slug, feature.get("feature_dir"), blocking)
        if item_feature_identities.get(feature_slug) != feature_dir.name:
            blocking.append(
                f"{feature_slug}: roadmap item feature pointer does not match {feature_dir.name}"
            )
        canonical_paths = {
            "design": feature_dir / f"{feature_slug}-design.md",
            "checklist": feature_dir / f"{feature_slug}-checklist.yaml",
            "review": feature_dir / f"{feature_slug}-review.md",
            "qa": feature_dir / f"{feature_slug}-qa.md",
            "acceptance": feature_dir / f"{feature_slug}-acceptance.md",
        }
        resolved_paths = {
            label: resolve_path(root, feature.get(label)).resolve()
            for label in canonical_paths
        }
        for label, canonical_path in canonical_paths.items():
            if resolved_paths[label] != canonical_path:
                blocking.append(
                    f"{feature_slug}: {label} path is not canonical: "
                    f"{resolved_paths[label]} != {canonical_path}"
                )
        checklist_path = canonical_paths["checklist"]
        review_path = canonical_paths["review"]
        qa_path = canonical_paths["qa"]
        acceptance_path = canonical_paths["acceptance"]
        expected = {
            "design": canonical_paths["design"],
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
        feature_identity = feature_dir.name
        markdown_contracts = {
            "design": (expected["design"], "feature-design", "approved"),
            "review": (review_path, "feature-review", "passed"),
            "qa": (qa_path, "feature-qa", "passed"),
            "acceptance": (acceptance_path, "feature-acceptance", "passed"),
            "evidence_pack": (expected["evidence_pack"], "feature-evidence-pack", "generated"),
        }
        for label, (path, doc_type, expected_status) in markdown_contracts.items():
            if path.exists():
                metadata = validate_markdown_identity(
                    path, blocking, feature_slug, feature_identity, doc_type
                )
                if metadata.get("status") != expected_status:
                    blocking.append(f"{feature_slug}: {label} is not status={expected_status}")
        result_contracts = {
            "evidence_pack_results": (
                "evidence-pack",
                {"implementation.before_review", "acceptance"},
                {
                    "design": expected["design"].relative_to(root).as_posix(),
                    "checklist": checklist_path.relative_to(root).as_posix(),
                    "out": expected["evidence_pack"].relative_to(root).as_posix(),
                    "dod_results": expected["dod_results"].relative_to(root).as_posix(),
                    "gate_results": expected["gate_results"].relative_to(root).as_posix(),
                },
                input_digests(
                    {
                        "design": expected["design"],
                        "checklist": checklist_path,
                        "out": expected["evidence_pack"],
                        "dod_results": expected["dod_results"],
                        "gate_results": expected["gate_results"],
                    }
                ),
            ),
            "gate_results": (
                "scope-gate",
                {"implementation.before_review", "acceptance"},
                {"feature_dir": feature_dir.relative_to(root).as_posix()},
                {},
            ),
            "dod_results": (
                "dod-runner",
                {"implementation.before_review", "acceptance"},
                {"checklist": checklist_path.relative_to(root).as_posix()},
                input_digests({"checklist": checklist_path}),
            ),
            "dod_contract_results": (
                "dod-contract-gate",
                {"feature_design.before_approve", "acceptance"},
                {"design": expected["design"].relative_to(root).as_posix()},
                input_digests({"design": expected["design"]}),
            ),
        }
        for label, (
            expected_gate_id,
            allowed_stages,
            expected_inputs,
            expected_input_digests,
        ) in result_contracts.items():
            path = expected[label]
            status_value, result_data = json_result(path)
            if status_value != "passed":
                blocking.append(f"{feature_slug}: {label} JSON is not passed: status={status_value}")
            if result_data and result_data.get("gate_id") != expected_gate_id:
                blocking.append(
                    f"{feature_slug}: {label} gate_id is not {expected_gate_id}"
                )
            if result_data and result_data.get("feature") != feature_identity:
                blocking.append(
                    f"{feature_slug}: {label} feature identity does not match {feature_identity}"
                )
            if result_data and result_data.get("stage") not in allowed_stages:
                blocking.append(
                    f"{feature_slug}: {label} stage is not valid for final audit"
                )
            if result_data and result_data.get("inputs") != expected_inputs:
                blocking.append(
                    f"{feature_slug}: {label} inputs do not match canonical feature artifacts"
                )
            if result_data and result_data.get("input_digests") != expected_input_digests:
                blocking.append(
                    f"{feature_slug}: {label} input digests do not match current canonical artifacts"
                )
        if checklist_path.exists():
            checklist = load_yaml_artifact(checklist_path, blocking)
            if not isinstance(checklist, dict):
                blocking.append(f"{feature_slug}: checklist is not a mapping: {checklist_path}")
                checklist = {}
            if checklist.get("feature") != feature_identity:
                blocking.append(
                    f"{feature_slug}: checklist feature identity does not match {feature_identity}"
                )
            validate_checklist_entries(feature_slug, checklist, "steps", "done", blocking)
            validate_checklist_entries(feature_slug, checklist, "checks", "passed", blocking)
        evidence.append({"feature": feature_slug, "artifacts_checked": sorted(expected)})

    status = "failed" if blocking else "passed"
    result = gate_result("goal-consistency-gate", args.stage, status, blocking, warnings, evidence)
    main_exit(result, args.json_out)


if __name__ == "__main__":
    main()
