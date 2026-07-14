#!/usr/bin/env python3
"""Resolve the next CodeStable workflow action from repository artifacts."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

if os.environ.get("PYTHONDONTWRITEBYTECODE") != "1":
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    os.execvpe(sys.executable, [sys.executable, *sys.argv], os.environ)
sys.dont_write_bytecode = True

from codestable_gate_common import load_yaml, load_yaml_text
from codestable_common import SUBAGENT_REVIEWERS, review_has_subagent_evidence


NON_BLOCKING_STATUSES = {"continue", "user_gate", "goal_package", "dispatch_goal", "report_driver", "complete"}
REVIEW_FALLBACK_REVIEWERS = {"ocr", "self"}
VALID_EXECUTION_LANES = {"quick", "standard", "goal"}


class ArtifactParseError(Exception):
    def __init__(self, path: Path, cause: Exception) -> None:
        self.path = path
        self.error_type = type(cause).__name__
        super().__init__(f"{path} ({self.error_type})")


class FeatureLookupError(Exception):
    pass


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def frontmatter(path: Path) -> dict[str, Any]:
    if not path.exists() or path.suffix != ".md":
        return {}
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        raise ArtifactParseError(path, exc) from exc
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    try:
        parsed = load_yaml_text(text[3:end].strip())
    except Exception as exc:
        raise ArtifactParseError(path, exc) from exc
    return parsed if isinstance(parsed, dict) else {}


def load_yaml_artifact(path: Path) -> Any:
    try:
        return load_yaml(path)
    except Exception as exc:
        raise ArtifactParseError(path, exc) from exc


def project_root(path: Path) -> Path:
    resolved = path.resolve()
    for parent in (resolved, *resolved.parents):
        if parent.name == ".codestable":
            return parent.parent
    for parent in (resolved, *resolved.parents):
        if (parent / ".codestable").exists() or (parent / ".git").exists():
            return parent
    return Path.cwd()


def rel(root: Path, path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def tool_command(tool_name: str, *args: str | None) -> str:
    tool_path = Path(__file__).resolve().with_name(tool_name).as_posix()
    return " ".join(["python3", tool_path, *[arg for arg in args if arg is not None]])


def first_existing(*paths: Path) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def single_glob(directory: Path, pattern: str) -> Path | None:
    matches = sorted(directory.glob(pattern))
    return matches[0] if matches else None


def status_of(path: Path | None) -> str:
    if path is None:
        return "missing"
    return str(frontmatter(path).get("status", "missing"))


def review_gate_passed(path: Path | None, meta: dict[str, Any]) -> bool:
    if path is None:
        return False
    reviewer = str(meta.get("reviewer") or "").strip().lower()
    if reviewer in SUBAGENT_REVIEWERS and review_has_subagent_evidence(path):
        return True
    return os.environ.get("CODESTABLE_ALLOW_SELF_REVIEW_FALLBACK") == "1" and reviewer in REVIEW_FALLBACK_REVIEWERS


def feature_slug_from_dir(feature: Path) -> str:
    match = re.match(r"^\d{4}-\d{2}-\d{2}-(.+)$", feature.name)
    return match.group(1) if match else feature.name


def decision(
    *,
    workflow: str,
    status: str,
    next_action: str,
    reason: str,
    blocking: list[str] | None = None,
    warnings: list[str] | None = None,
    missing_artifacts: list[str] | None = None,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    must_continue = status in {"continue", "goal_package", "dispatch_goal"}
    return {
        "ok": status in NON_BLOCKING_STATUSES,
        "workflow": workflow,
        "status": status,
        "next_action": next_action,
        "reason": reason,
        "must_continue": must_continue,
        "final_answer_allowed": not must_continue,
        "blocking": blocking or [],
        "warnings": warnings or [],
        "missing_artifacts": missing_artifacts or [],
        "evidence": evidence or {},
    }


def artifact_parse_decision(
    workflow: str,
    target: Path,
    error: ArtifactParseError,
) -> dict[str, Any]:
    root = project_root(target.resolve())
    invalid_artifact = rel(root, error.path) or error.path.as_posix()
    detail = f"{invalid_artifact} ({error.error_type})"
    return decision(
        workflow=workflow,
        status="blocked",
        next_action=f"fix-{workflow}-artifact-yaml",
        reason=f"cannot parse {workflow} artifact: {detail}",
        blocking=[f"fix invalid YAML artifact: {detail}"],
        evidence={
            "invalid_artifact": detail,
            "artifact_error_type": error.error_type,
        },
    )


def find_roadmap_file(roadmap: Path) -> Path | None:
    return first_existing(roadmap / f"{roadmap.name}-roadmap.md") or single_glob(roadmap, "*-roadmap.md")


def find_items_file(roadmap: Path) -> Path | None:
    return first_existing(roadmap / f"{roadmap.name}-items.yaml") or single_glob(roadmap, "*-items.yaml")


def find_roadmap_review(roadmap: Path) -> Path | None:
    return first_existing(roadmap / f"{roadmap.name}-roadmap-review.md") or single_glob(roadmap, "*-roadmap-review.md")


def roadmap_item_rows(data: Any) -> list[dict[str, Any]] | None:
    if not isinstance(data, dict):
        return None
    rows = data.get("items")
    if rows is None:
        rows = data.get("features")
    if rows is None:
        rows = []
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        return None
    if any(row.get("feature") is not None and not isinstance(row.get("feature"), str) for row in rows):
        return None
    return rows


def load_items(items_path: Path | None) -> list[dict[str, Any]]:
    if items_path is None or not items_path.exists():
        return []
    data = load_yaml_artifact(items_path)
    rows = roadmap_item_rows(data)
    if rows is None:
        raise ArtifactParseError(
            items_path,
            ValueError("roadmap items must be a list of mappings with string or null feature pointers"),
        )
    return rows


def all_checklist_steps_done(checklist: Path | None) -> bool:
    if checklist is None or not checklist.exists():
        return False
    data = load_yaml_artifact(checklist)
    if not isinstance(data, dict):
        return False
    steps = as_list(data.get("steps"))
    return bool(steps) and all(
        isinstance(step, dict) and step.get("status") == "done" for step in steps
    )


def checked_yaml_path(value: Any, field: str) -> Path:
    if not isinstance(value, str) or "\x00" in value:
        raise ValueError(f"{field} must be a string without NUL characters")
    return Path(value)


def feature_pointer_path(root: Path, feature_value: Any) -> Path | None:
    if feature_value is None or feature_value == "" or feature_value == "null":
        return None
    feature_path = checked_yaml_path(feature_value, "feature pointer")
    if feature_path.is_absolute():
        return feature_path
    if feature_path.parts and feature_path.parts[0] == ".codestable":
        return root / feature_path
    return root / ".codestable" / "features" / feature_path


def find_feature_dir(root: Path, roadmap_slug: str, item: dict[str, Any]) -> Path | None:
    feature_value = item.get("feature")
    try:
        feature_path = feature_pointer_path(root, feature_value)
        if feature_path is not None:
            feature_path.resolve()
            return feature_path if feature_path.exists() else None
    except (ValueError, OSError) as exc:
        raise FeatureLookupError(f"invalid feature pointer: {exc}") from exc

    item_slug = str(item.get("slug") or "")
    features_root = root / ".codestable" / "features"
    if not features_root.exists():
        return None
    for design in sorted(features_root.glob("*/**/*-design.md")):
        meta = frontmatter(design)
        if meta.get("roadmap") == roadmap_slug and meta.get("roadmap_item") == item_slug:
            return design.parent
    matches = sorted(
        path
        for path in features_root.iterdir()
        if path.is_dir() and feature_slug_from_dir(path) == item_slug
    )
    if len(matches) > 1:
        match_paths = ", ".join(str(rel(root, path)) for path in matches)
        raise FeatureLookupError(
            f"multiple feature directories match roadmap item {item_slug}: {match_paths}"
        )
    return matches[0] if matches else None


def feature_artifacts(feature: Path, item_slug: str | None = None) -> dict[str, Path | None]:
    slug = item_slug or feature_slug_from_dir(feature)
    design = first_existing(feature / f"{slug}-design.md") or single_glob(feature, "*-design.md")
    checklist = first_existing(feature / f"{slug}-checklist.yaml") or single_glob(feature, "*-checklist.yaml")
    design_review = first_existing(feature / f"{slug}-design-review.md") or single_glob(feature, "*-design-review.md")
    code_review = first_existing(feature / f"{slug}-review.md")
    qa = first_existing(feature / f"{slug}-qa.md")
    acceptance = first_existing(feature / f"{slug}-acceptance.md")
    ff_note = first_existing(feature / f"{slug}-ff-note.md") or single_glob(feature, "*-ff-note.md")
    goal_state = feature / "goal-state.yaml"
    return {
        "design": design,
        "checklist": checklist,
        "design_review": design_review,
        "code_review": code_review,
        "qa": qa,
        "acceptance": acceptance,
        "ff_note": ff_note,
        "goal_state": goal_state if goal_state.exists() else None,
    }


def standard_feature_next(
    *,
    checklist_steps_done: bool,
    code_review: Path | None,
    code_review_meta: dict[str, Any],
    code_review_gate_passed: bool,
    qa: Path | None,
    qa_meta: dict[str, Any],
    acceptance: Path | None,
    acceptance_meta: dict[str, Any],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    code_review_status = str(code_review_meta.get("status") or "missing")
    qa_status = str(qa_meta.get("status") or "missing")
    acceptance_status = str(acceptance_meta.get("status") or "missing")
    if not checklist_steps_done:
        return decision(
            workflow="feature",
            status="continue",
            next_action="cs-feat implementation",
            reason="standard feature still has pending implementation steps",
            evidence=evidence,
        )
    if code_review is not None and code_review_meta.get("doc_type") != "feature-review":
        return decision(
            workflow="feature",
            status="blocked",
            next_action="fix-feature-code-review-evidence",
            reason="standard feature code-review has an invalid doc_type",
            blocking=["code review evidence must use doc_type: feature-review"],
            evidence=evidence,
        )
    if code_review_status == "changes-requested":
        return decision(
            workflow="feature",
            status="continue",
            next_action="cs-feat implementation review-fix",
            reason="standard feature code review requested changes",
            evidence=evidence,
        )
    if code_review_status != "passed":
        return decision(
            workflow="feature",
            status="continue",
            next_action="cs-code-review",
            reason=f"standard feature code-review status is {code_review_status}",
            evidence=evidence,
        )
    if not code_review_gate_passed:
        return decision(
            workflow="feature",
            status="blocked",
            next_action="fix-feature-code-review-evidence",
            reason="passed code review lacks independent Task agent evidence",
            blocking=["passed code review must have reviewer: subagent or subagent+ocr"],
            evidence=evidence,
        )
    if qa is not None and qa_meta.get("doc_type") != "feature-qa":
        return decision(
            workflow="feature",
            status="blocked",
            next_action="fix-feature-qa-evidence",
            reason="standard feature QA artifact has an invalid doc_type",
            blocking=["QA evidence must use doc_type: feature-qa"],
            evidence=evidence,
        )
    if qa_status in {"failed", "blocked"}:
        return decision(
            workflow="feature",
            status="continue",
            next_action="cs-feat --stage impl qa-fix",
            reason=f"standard feature QA is {qa_status} and requires qa-fix",
            evidence=evidence,
        )
    if qa is not None and qa_status != "passed":
        return decision(
            workflow="feature",
            status="continue",
            next_action="cs-feat --stage qa",
            reason=f"standard feature QA status is {qa_status}",
            evidence=evidence,
        )
    if acceptance is not None and acceptance_meta.get("doc_type") != "feature-acceptance":
        return decision(
            workflow="feature",
            status="blocked",
            next_action="fix-feature-acceptance-evidence",
            reason="standard feature acceptance has an invalid doc_type",
            blocking=["acceptance evidence must use doc_type: feature-acceptance"],
            evidence=evidence,
        )
    if acceptance_status == "passed":
        return decision(
            workflow="feature",
            status="complete",
            next_action="CS_FEATURE_STANDARD_COMPLETE",
            reason="standard feature review and acceptance are passed",
            evidence=evidence,
        )
    return decision(
        workflow="feature",
        status="continue",
        next_action="cs-feat --stage accept",
        reason="standard feature review passed and needs inline verification and acceptance",
        evidence=evidence,
    )


def quick_feature_next(
    *,
    ff_note: Path | None,
    ff_note_meta: dict[str, Any],
    code_review: Path | None,
    code_review_meta: dict[str, Any],
    code_review_gate_passed: bool,
    qa: Path | None,
    qa_meta: dict[str, Any],
    acceptance: Path | None,
    acceptance_meta: dict[str, Any],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    quality_artifacts = (
        ("QA", qa, qa_meta, "feature-qa", evidence.get("qa")),
        ("acceptance", acceptance, acceptance_meta, "feature-acceptance", evidence.get("acceptance")),
    )
    for label, path, meta, expected_doc_type, artifact_path in quality_artifacts:
        if path is None:
            continue
        status = str(meta.get("status") or "missing")
        doc_type = meta.get("doc_type")
        if doc_type == expected_doc_type and status == "passed":
            continue
        detail = f"doc_type={doc_type or 'missing'}, status={status}"
        return decision(
            workflow="feature",
            status="blocked",
            next_action="resolve-quick-quality-conflict",
            reason=f"Quick feature has conflicting existing {label} evidence",
            blocking=[f"reconcile {artifact_path} before Quick can complete ({detail})"],
            evidence=evidence,
        )
    if ff_note is None:
        return decision(
            workflow="feature",
            status="continue",
            next_action="cs-feat --mode quick",
            reason="quick feature implementation and ff-note are still pending",
            evidence=evidence,
        )
    if ff_note_meta.get("doc_type") != "feature-ff-note":
        return decision(
            workflow="feature",
            status="blocked",
            next_action="fix-feature-ff-note",
            reason="quick feature ff-note has an invalid doc_type",
            blocking=["Quick evidence must use doc_type: feature-ff-note"],
            evidence=evidence,
        )
    if code_review is not None and code_review_meta.get("doc_type") != "feature-review":
        return decision(
            workflow="feature",
            status="blocked",
            next_action="fix-feature-code-review-evidence",
            reason="quick feature code-review has an invalid doc_type",
            blocking=["code review evidence must use doc_type: feature-review"],
            evidence=evidence,
        )
    code_review_status = str(code_review_meta.get("status") or "missing")
    if code_review_status == "changes-requested":
        return decision(
            workflow="feature",
            status="continue",
            next_action="cs-feat --mode quick",
            reason="quick feature review-fix is required before review can pass",
            evidence=evidence,
        )
    if code_review_status != "passed":
        return decision(
            workflow="feature",
            status="continue",
            next_action="cs-code-review",
            reason=f"quick feature code-review status is {code_review_status}",
            evidence=evidence,
        )
    if not code_review_gate_passed:
        return decision(
            workflow="feature",
            status="blocked",
            next_action="fix-feature-code-review-evidence",
            reason="passed Quick review lacks independent Task agent evidence",
            blocking=["passed code review must have reviewer: subagent or subagent+ocr"],
            evidence=evidence,
        )
    return decision(
        workflow="feature",
        status="complete",
        next_action="CS_FEATURE_QUICK_COMPLETE",
        reason="quick feature ff-note and independent code review are complete",
        evidence=evidence,
    )


def roadmap_owner_evidence(
    root: Path,
    roadmap: Path,
    goal_state: Path,
    state: dict[str, Any],
    row: dict[str, Any],
    roadmap_item: str,
) -> dict[str, Any]:
    return {
        "owner_workflow": "epic",
        "roadmap_owner_source": "roadmap-goal-state",
        "roadmap": rel(root, roadmap),
        "roadmap_item": roadmap_item,
        "roadmap_goal_state": rel(root, goal_state),
        "roadmap_goal_status": state.get("status"),
        "roadmap_feature_status": row.get("status"),
        "epic_command": tool_command(
            "codestable-workflow-next.py",
            "epic",
            "--roadmap",
            rel(root, roadmap),
            "--json",
        ),
    }


def roadmap_items_owner_evidence(
    root: Path,
    roadmap: Path,
    items_path: Path,
    goal_state: Path,
    row: dict[str, Any],
    roadmap_item: str,
) -> dict[str, Any]:
    return {
        "owner_workflow": "epic",
        "roadmap_owner_source": "roadmap-items",
        "roadmap": rel(root, roadmap),
        "roadmap_item": roadmap_item,
        "roadmap_items": rel(root, items_path),
        "roadmap_goal_state": rel(root, goal_state),
        "roadmap_goal_status": "missing",
        "roadmap_feature_status": row.get("status"),
        "epic_command": tool_command(
            "codestable-workflow-next.py",
            "epic",
            "--roadmap",
            rel(root, roadmap),
            "--json",
        ),
    }


def roadmap_items_owner(
    root: Path,
    roadmap: Path,
    roadmap_item: str,
    feature: Path,
    goal_state: Path,
) -> tuple[dict[str, Any] | None, str | None]:
    items_path = find_items_file(roadmap)
    if items_path is None:
        expected = roadmap / f"{roadmap.name}-items.yaml"
        return None, f"feature design references roadmap without items: {rel(root, expected)}"
    data = load_yaml_artifact(items_path)
    rows = roadmap_item_rows(data)
    if rows is None:
        return None, f"roadmap items must be a list of mappings: {rel(root, items_path)}"
    items_roadmap = str(data.get("roadmap") or "").strip()
    if items_roadmap and items_roadmap != roadmap.name:
        return None, f"roadmap items identity does not match feature design: {rel(root, items_path)}"
    matching_rows = [
        row
        for row in rows
        if str(row.get("roadmap_item") or row.get("slug") or "").strip() == roadmap_item
    ]
    if len(matching_rows) != 1:
        return None, f"roadmap items do not uniquely own this feature: {rel(root, items_path)}"
    row = matching_rows[0]
    try:
        owner_path = feature_pointer_path(root, row.get("feature"))
        if owner_path is not None and owner_path.resolve() != feature.resolve():
            return None, f"roadmap items feature pointer does not match this feature: {rel(root, items_path)}"
    except (ValueError, OSError) as exc:
        return None, f"roadmap items feature pointer is invalid in {rel(root, items_path)} ({exc})"
    owner = roadmap_items_owner_evidence(root, roadmap, items_path, goal_state, row, roadmap_item)
    reverse_owner, reverse_error = reverse_roadmap_items_owner(
        root,
        feature,
        exclude_items_claim=(items_path, roadmap_item),
    )
    expected_path = str(rel(root, items_path))
    if reverse_error is not None:
        return None, f"roadmap items {expected_path} owns this feature; {reverse_error}"
    if reverse_owner is not None:
        actual_path = reverse_owner.get("roadmap_items")
        return None, f"multiple roadmap items claim this feature: {expected_path}, {actual_path}"
    return owner, None


def reverse_roadmap_items_owner(
    root: Path,
    feature: Path,
    exclude_items_claim: tuple[Path, str] | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    roadmap_root = root / ".codestable" / "roadmap"
    if not roadmap_root.exists():
        return None, None

    owners: list[tuple[Path, Path, dict[str, Any], str]] = []
    invalid_items: list[str] = []
    for roadmap in sorted(path for path in roadmap_root.iterdir() if path.is_dir()):
        items_path = find_items_file(roadmap)
        if items_path is None:
            continue
        items_path_text = str(rel(root, items_path))
        try:
            data = load_yaml(items_path)
        except Exception as exc:
            invalid_items.append(f"{items_path_text} ({type(exc).__name__})")
            continue
        rows = roadmap_item_rows(data)
        if rows is None:
            invalid_items.append(items_path_text)
            continue
        identity_matches = str(data.get("roadmap") or "").strip() in {"", roadmap.name}
        for row in rows:
            try:
                owner_path = find_feature_dir(root, roadmap.name, row)
                owner_matches = owner_path is not None and owner_path.resolve() == feature.resolve()
            except (FeatureLookupError, ValueError, OSError) as exc:
                invalid_items.append(f"{items_path_text} ({exc})")
                continue
            if not owner_matches:
                continue
            roadmap_item = str(row.get("roadmap_item") or row.get("slug") or "").strip()
            if (
                exclude_items_claim is not None
                and items_path.resolve() == exclude_items_claim[0].resolve()
                and roadmap_item == exclude_items_claim[1]
            ):
                continue
            if not identity_matches or not roadmap_item:
                invalid_items.append(items_path_text)
                continue
            owners.append((roadmap, items_path, row, roadmap_item))

    if invalid_items:
        invalid_paths = ", ".join(sorted(set(invalid_items)))
        return None, f"cannot prove unique legacy roadmap ownership; invalid items: {invalid_paths}"
    if len(owners) > 1:
        owner_paths = ", ".join(sorted({str(rel(root, owner[1])) for owner in owners}))
        return None, f"multiple roadmap items claim this legacy feature_dir: {owner_paths}"
    if not owners:
        return None, None
    roadmap, items_path, row, roadmap_item = owners[0]
    goal_state = roadmap / "goal-state.yaml"
    return roadmap_items_owner_evidence(root, roadmap, items_path, goal_state, row, roadmap_item), None


def reverse_roadmap_goal_owner(
    root: Path,
    feature: Path,
    exclude_goal_state_claim: tuple[Path, str] | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    roadmap_root = root / ".codestable" / "roadmap"
    if not roadmap_root.exists():
        return None, None

    owners: list[tuple[Path, Path, dict[str, Any], dict[str, Any], str]] = []
    invalid_states: list[str] = []
    for goal_state in sorted(roadmap_root.glob("*/goal-state.yaml")):
        roadmap = goal_state.parent
        goal_state_path = str(rel(root, goal_state))
        try:
            state = load_yaml(goal_state)
        except Exception as exc:  # Legacy recovery cannot silently skip an unreadable possible owner.
            invalid_states.append(f"{goal_state_path} ({type(exc).__name__})")
            continue
        if not isinstance(state, dict):
            invalid_states.append(goal_state_path)
            continue
        identity_matches = str(state.get("roadmap") or "").strip() == roadmap.name
        feature_rows = state.get("features")
        if not isinstance(feature_rows, list) or any(not isinstance(row, dict) for row in feature_rows):
            invalid_states.append(goal_state_path)
            continue
        for row in feature_rows:
            feature_dir = row.get("feature_dir")
            if feature_dir is None or feature_dir == "" or feature_dir == "null":
                continue
            if not isinstance(feature_dir, str):
                invalid_states.append(goal_state_path)
                continue
            try:
                owner_path = checked_yaml_path(feature_dir, "feature_dir")
                if not owner_path.is_absolute():
                    owner_path = root / owner_path
                owner_matches = owner_path.resolve() == feature.resolve()
            except (ValueError, OSError) as exc:
                invalid_states.append(f"{goal_state_path} ({type(exc).__name__})")
                continue
            if not owner_matches:
                continue
            if not identity_matches:
                invalid_states.append(goal_state_path)
                continue
            roadmap_item = str(row.get("roadmap_item") or row.get("slug") or "").strip()
            if not roadmap_item:
                invalid_states.append(goal_state_path)
                continue
            if (
                exclude_goal_state_claim is not None
                and goal_state.resolve() == exclude_goal_state_claim[0].resolve()
                and roadmap_item == exclude_goal_state_claim[1]
            ):
                continue
            owners.append((roadmap, goal_state, state, row, roadmap_item))

    if invalid_states:
        invalid_paths = ", ".join(sorted(set(invalid_states)))
        return None, f"cannot prove unique legacy roadmap ownership; invalid goal-state: {invalid_paths}"
    if len(owners) > 1:
        owner_paths = ", ".join(sorted({str(rel(root, owner[1])) for owner in owners}))
        return None, f"multiple roadmap goal-states claim this legacy feature_dir: {owner_paths}"
    if not owners:
        return None, None
    roadmap, goal_state, state, row, roadmap_item = owners[0]
    return roadmap_owner_evidence(root, roadmap, goal_state, state, row, roadmap_item), None


def roadmap_goal_owner(
    root: Path,
    feature: Path,
    design_meta: dict[str, Any],
) -> tuple[dict[str, Any] | None, str | None]:
    roadmap_slug = str(design_meta.get("roadmap") or "").strip()
    roadmap_item = str(design_meta.get("roadmap_item") or "").strip()
    if bool(roadmap_slug) != bool(roadmap_item):
        return None, "feature design must define roadmap and roadmap_item together"
    if not roadmap_slug:
        reverse_owner, reverse_error = reverse_roadmap_goal_owner(root, feature)
        if reverse_owner is not None or reverse_error is not None:
            return reverse_owner, reverse_error
        return reverse_roadmap_items_owner(root, feature)
    try:
        roadmap_path = checked_yaml_path(roadmap_slug, "roadmap")
    except (ValueError, OSError):
        return None, "feature design has an invalid roadmap owner path"
    if roadmap_path.name != roadmap_slug:
        return None, "feature design has an invalid roadmap owner path"

    roadmap = root / ".codestable" / "roadmap" / roadmap_slug
    goal_state = roadmap / "goal-state.yaml"
    if not goal_state.exists():
        reverse_owner, reverse_error = reverse_roadmap_goal_owner(root, feature)
        expected_path = str(rel(root, goal_state))
        if reverse_error is not None:
            return None, f"feature design expects missing roadmap goal-state {expected_path}; {reverse_error}"
        if reverse_owner is not None:
            actual_path = reverse_owner.get("roadmap_goal_state")
            return None, (
                f"feature design expects missing roadmap goal-state {expected_path}; "
                f"conflicting roadmap goal-state claims this feature: {actual_path}"
            )
        return roadmap_items_owner(root, roadmap, roadmap_item, feature, goal_state)
    try:
        state = load_yaml(goal_state)
    except Exception as exc:  # Parser errors must become a recoverable workflow decision.
        return None, f"cannot parse roadmap goal-state {rel(root, goal_state)} ({type(exc).__name__})"
    if not isinstance(state, dict):
        return None, f"roadmap goal-state must be a mapping: {rel(root, goal_state)}"
    if str(state.get("roadmap") or "").strip() != roadmap_slug:
        return None, f"roadmap goal-state identity does not match feature design: {rel(root, goal_state)}"

    matching_rows = []
    for row in as_list(state.get("features")):
        if not isinstance(row, dict):
            continue
        row_item = str(row.get("roadmap_item") or row.get("slug") or "").strip()
        if row_item == roadmap_item:
            matching_rows.append(row)
    if len(matching_rows) != 1:
        return None, f"roadmap goal-state does not uniquely own this feature: {rel(root, goal_state)}"

    row = matching_rows[0]
    feature_dir = row.get("feature_dir")
    if feature_dir is not None and feature_dir != "" and feature_dir != "null":
        if not isinstance(feature_dir, str):
            return None, f"roadmap goal-state feature_dir must be a string: {rel(root, goal_state)}"
        try:
            owner_path = checked_yaml_path(feature_dir, "feature_dir")
            if not owner_path.is_absolute():
                owner_path = root / owner_path
            owner_matches = owner_path.resolve() == feature.resolve()
        except (ValueError, OSError) as exc:
            return None, (
                f"roadmap goal-state feature_dir is invalid: {rel(root, goal_state)} "
                f"({type(exc).__name__})"
            )
        if not owner_matches:
            return None, f"roadmap goal-state feature_dir does not match this feature: {rel(root, goal_state)}"

    owner = roadmap_owner_evidence(root, roadmap, goal_state, state, row, roadmap_item)
    reverse_owner, reverse_error = reverse_roadmap_goal_owner(
        root,
        feature,
        exclude_goal_state_claim=(goal_state, roadmap_item),
    )
    expected_path = str(rel(root, goal_state))
    if reverse_error is not None:
        return None, f"roadmap goal-state {expected_path} owns this feature; {reverse_error}"
    if reverse_owner is not None:
        actual_path = reverse_owner.get("roadmap_goal_state")
        return None, (
            f"multiple roadmap goal-states claim this feature: {expected_path}, {actual_path}"
        )
    items_path = find_items_file(roadmap)
    reverse_items_owner, reverse_items_error = reverse_roadmap_items_owner(
        root,
        feature,
        exclude_items_claim=(items_path, roadmap_item) if items_path is not None else None,
    )
    expected_items_path = str(rel(root, items_path)) if items_path is not None else expected_path
    if reverse_items_error is not None:
        return None, (
            f"roadmap goal-state {expected_path} owns this feature via {expected_items_path}; "
            f"{reverse_items_error}"
        )
    if reverse_items_owner is not None:
        actual_items_path = reverse_items_owner.get("roadmap_items")
        return None, (
            f"multiple roadmap items claim this feature: {expected_items_path}, {actual_items_path}"
        )
    return owner, None


def item_evidence(root: Path, item: dict[str, Any], feature: Path | None, artifacts: dict[str, Path | None]) -> dict[str, Any]:
    return {
        "item": item.get("slug"),
        "item_status": item.get("status"),
        "item_feature": item.get("feature"),
        "feature_dir": rel(root, feature) if feature else None,
        "design": rel(root, artifacts.get("design")),
        "design_status": status_of(artifacts.get("design")),
        "checklist": rel(root, artifacts.get("checklist")),
        "design_review": rel(root, artifacts.get("design_review")),
        "design_review_status": status_of(artifacts.get("design_review")),
    }


def _epic_next(roadmap: Path) -> dict[str, Any]:
    roadmap = roadmap.resolve()
    root = project_root(roadmap)
    if not roadmap.is_dir():
        return decision(
            workflow="epic",
            status="blocked",
            next_action="fix-roadmap-path",
            reason="roadmap directory is missing",
            blocking=[f"roadmap dir not found: {roadmap}"],
        )

    roadmap_file = find_roadmap_file(roadmap)
    review_file = find_roadmap_review(roadmap)
    items_path = find_items_file(roadmap)
    goal_state = roadmap / "goal-state.yaml"

    if roadmap_file is None:
        return decision(
            workflow="epic",
            status="continue",
            next_action="cs-epic planning",
            reason="roadmap document is missing",
            missing_artifacts=[rel(root, roadmap / f"{roadmap.name}-roadmap.md") or f"{roadmap.name}-roadmap.md"],
        )

    roadmap_status = status_of(roadmap_file)
    review_status = status_of(review_file)
    if roadmap_status == "active" and review_status == "missing":
        return decision(
            workflow="epic",
            status="blocked",
            next_action="fix-roadmap-review-state",
            reason="active roadmap lacks a passed roadmap review",
            blocking=["active roadmap has no roadmap review artifact"],
            evidence={
                "roadmap": rel(root, roadmap_file),
                "roadmap_status": roadmap_status,
                "roadmap_review": rel(root, review_file),
                "roadmap_review_status": review_status,
            },
        )
    if review_status != "passed":
        if review_status in {"blocking", "blocked", "changes-requested"}:
            return decision(
                workflow="epic",
                status="continue",
                next_action="cs-epic planning/update then review",
                reason=f"roadmap review is {review_status}",
                evidence={"roadmap_review": rel(root, review_file), "roadmap_review_status": review_status},
            )
        return decision(
            workflow="epic",
            status="continue",
            next_action="cs-epic review",
            reason="roadmap review has not passed",
            missing_artifacts=[] if review_file else [rel(root, roadmap / f"{roadmap.name}-roadmap-review.md") or ""],
            evidence={"roadmap_review": rel(root, review_file), "roadmap_review_status": review_status},
        )

    if roadmap_status != "active":
        return decision(
            workflow="epic",
            status="user_gate",
            next_action="epic-roadmap-confirmation",
            reason="roadmap review passed but roadmap is not active",
            evidence={"roadmap": rel(root, roadmap_file), "roadmap_status": roadmap_status},
        )

    items = load_items(items_path)
    if not items:
        return decision(
            workflow="epic",
            status="blocked",
            next_action="fix-roadmap-items",
            reason="items.yaml is missing or empty",
            blocking=["roadmap items are required before child feature design"],
            missing_artifacts=[] if items_path else [rel(root, roadmap / f"{roadmap.name}-items.yaml") or ""],
        )

    completed: list[dict[str, Any]] = []
    warnings: list[str] = []
    for item in items:
        item_slug = str(item.get("slug") or "")
        if not item_slug:
            warnings.append("roadmap item without slug ignored")
            continue
        if item.get("status") == "dropped":
            completed.append({"item": item_slug, "status": "dropped"})
            continue
        try:
            feature = find_feature_dir(root, roadmap.name, item)
        except FeatureLookupError as exc:
            return decision(
                workflow="epic",
                status="blocked",
                next_action="fix-roadmap-items",
                reason=str(exc),
                blocking=[f"resolve ambiguous feature ownership in {rel(root, items_path)}"],
                evidence={"roadmap": rel(root, roadmap), "items": rel(root, items_path)},
            )
        artifacts = feature_artifacts(feature, item_slug) if feature else {"design": None, "checklist": None, "design_review": None}
        missing = [
            label
            for label in ("design", "checklist", "design_review")
            if artifacts.get(label) is None
        ]
        review_status = status_of(artifacts.get("design_review"))
        if missing or review_status != "passed":
            return decision(
                workflow="epic",
                status="continue",
                next_action="cs-feat design/design-review",
                reason="next child feature design is incomplete",
                warnings=warnings,
                missing_artifacts=missing,
                evidence={
                    "roadmap": rel(root, roadmap),
                    "items": rel(root, items_path),
                    "next_item": item_evidence(root, item, feature, artifacts),
                    "completed_items": completed,
                },
            )
        completed.append(item_evidence(root, item, feature, artifacts))

    unapproved = [item for item in completed if item.get("status") != "dropped" and item.get("design_status") != "approved"]
    if unapproved:
        return decision(
            workflow="epic",
            status="user_gate",
            next_action="all-feature-designs-confirmation",
            reason="all child design reviews passed, but designs are not batch-approved",
            warnings=warnings,
            evidence={"roadmap": rel(root, roadmap), "items": rel(root, items_path), "unapproved_items": unapproved},
        )

    if not goal_state.exists():
        return decision(
            workflow="epic",
            status="goal_package",
            next_action="cs-epic goal-package",
            reason="all child designs are approved and the epic goal package is missing",
            warnings=warnings,
            missing_artifacts=[rel(root, goal_state) or "goal-state.yaml"],
            evidence={"roadmap": rel(root, roadmap), "items": rel(root, items_path), "completed_items": completed},
        )

    state = load_yaml_artifact(goal_state)
    state = state if isinstance(state, dict) else {}
    state_status = state.get("status")
    if state_status in {"complete", "completed"}:
        return decision(
            workflow="epic",
            status="complete",
            next_action="CS_ROADMAP_GOAL_COMPLETE",
            reason="epic goal state is complete",
            warnings=warnings,
            evidence={"goal_state": rel(root, goal_state)},
        )
    if state_status == "handoff":
        return decision(
            workflow="epic",
            status="user_gate",
            next_action="CS_ROADMAP_GOAL_HANDOFF",
            reason=str(state.get("handoff_reason") or "epic goal driver requested handoff"),
            warnings=warnings,
            evidence={
                "goal_state": rel(root, goal_state),
                "handoff_next": state.get("handoff_next"),
            },
        )
    driver_kind = state.get("driver_kind")
    driver_id = state.get("driver_id")
    if driver_kind in {"paseo", "native"} and driver_id:
        return decision(
            workflow="epic",
            status="report_driver",
            next_action="report-visible-driver",
            reason="visible epic goal driver is already recorded",
            warnings=warnings,
            evidence={"goal_state": rel(root, goal_state), "driver_kind": driver_kind, "driver_id": driver_id},
        )
    if state_status == "ready-to-dispatch":
        return decision(
            workflow="epic",
            status="dispatch_goal",
            next_action="dispatch-epic-goal-driver-or-print-goal",
            reason="epic goal package is ready to dispatch",
            warnings=warnings,
            evidence={"goal_state": rel(root, goal_state)},
        )
    return decision(
        workflow="epic",
        status="blocked",
        next_action="inspect-epic-goal-state",
        reason="unknown epic goal-state status",
        blocking=[f"unknown goal-state status: {state.get('status')}"],
        evidence={"goal_state": rel(root, goal_state)},
    )


def epic_next(roadmap: Path) -> dict[str, Any]:
    try:
        return _epic_next(roadmap)
    except ArtifactParseError as error:
        return artifact_parse_decision("epic", roadmap, error)


def _feature_next(feature: Path, epic_child_batch: bool) -> dict[str, Any]:
    feature = feature.resolve()
    root = project_root(feature)
    if not feature.is_dir():
        return decision(
            workflow="feature",
            status="blocked",
            next_action="fix-feature-path",
            reason="feature directory is missing",
            blocking=[f"feature dir not found: {feature}"],
        )

    artifacts = feature_artifacts(feature)
    design = artifacts["design"]
    checklist = artifacts["checklist"]
    design_review = artifacts["design_review"]
    code_review = artifacts["code_review"]
    qa = artifacts["qa"]
    acceptance = artifacts["acceptance"]
    ff_note = artifacts["ff_note"]
    goal_state = artifacts["goal_state"]
    design_meta = frontmatter(design) if design else {}
    design_review_meta = frontmatter(design_review) if design_review else {}
    code_review_meta = frontmatter(code_review) if code_review else {}
    qa_meta = frontmatter(qa) if qa else {}
    acceptance_meta = frontmatter(acceptance) if acceptance else {}
    ff_note_meta = frontmatter(ff_note) if ff_note else {}
    design_status = str(design_meta.get("status") or "missing")
    design_review_status = str(design_review_meta.get("status") or "missing")
    code_review_status = str(code_review_meta.get("status") or "missing")
    qa_status = str(qa_meta.get("status") or "missing")
    acceptance_status = str(acceptance_meta.get("status") or "missing")
    checklist_steps_done = all_checklist_steps_done(checklist)
    code_review_gate_ok = review_gate_passed(code_review, code_review_meta)
    design_roadmap = str(design_meta.get("roadmap") or "").strip()
    design_roadmap_item = str(design_meta.get("roadmap_item") or "").strip()
    roadmap_metadata_incomplete = bool(design_roadmap) != bool(design_roadmap_item)
    roadmap_owner, roadmap_owner_error = roadmap_goal_owner(root, feature, design_meta)
    configured_lane_value = design_meta.get("execution_lane")
    configured_lane = str(configured_lane_value).strip().lower() if configured_lane_value is not None else None
    lane_conflict = False
    if epic_child_batch:
        execution_lane = "goal"
        execution_lane_source = "epic-child-batch"
    elif goal_state is not None:
        execution_lane = "goal"
        execution_lane_source = "feature-goal-state"
    elif roadmap_owner is not None:
        execution_lane = "goal"
        execution_lane_source = str(roadmap_owner.get("roadmap_owner_source") or "roadmap-goal-state")
    elif ff_note is not None and configured_lane not in {None, "quick"}:
        execution_lane = str(configured_lane)
        execution_lane_source = "conflict"
        lane_conflict = True
    elif ff_note is not None:
        execution_lane = "quick"
        execution_lane_source = "ff-note"
    elif configured_lane is not None:
        execution_lane = configured_lane
        execution_lane_source = "design"
    else:
        execution_lane = "standard"
        execution_lane_source = "legacy-default"
    evidence = {
        "feature_dir": rel(root, feature),
        "design": rel(root, design),
        "design_status": design_status,
        "design_roadmap": design_roadmap or None,
        "design_roadmap_item": design_roadmap_item or None,
        "execution_lane": execution_lane,
        "execution_lane_source": execution_lane_source,
        "configured_execution_lane": configured_lane,
        "checklist": rel(root, checklist),
        "checklist_steps_done": checklist_steps_done,
        "design_review": rel(root, design_review),
        "design_review_status": design_review_status,
        "code_review": rel(root, code_review),
        "code_review_status": code_review_status,
        "code_review_doc_type": code_review_meta.get("doc_type"),
        "code_review_reviewer": code_review_meta.get("reviewer"),
        "code_review_gate_passed": code_review_gate_ok,
        "qa": rel(root, qa),
        "qa_status": qa_status,
        "qa_doc_type": qa_meta.get("doc_type"),
        "acceptance": rel(root, acceptance),
        "acceptance_status": acceptance_status,
        "acceptance_doc_type": acceptance_meta.get("doc_type"),
        "ff_note": rel(root, ff_note),
        "goal_state": rel(root, goal_state),
        "roadmap_owner_error": roadmap_owner_error,
    }

    if roadmap_owner_error is not None:
        return decision(
            workflow="feature",
            status="blocked",
            next_action=(
                "fix-feature-roadmap-metadata"
                if roadmap_metadata_incomplete
                else "inspect-epic-goal-state"
            ),
            reason=roadmap_owner_error,
            blocking=[roadmap_owner_error],
            evidence=evidence,
        )
    if goal_state is not None and roadmap_owner is not None:
        return decision(
            workflow="feature",
            status="blocked",
            next_action="resolve-feature-goal-ownership",
            reason="feature and roadmap goal-state both claim this feature",
            blocking=["feature cannot be owned by both standalone Goal and Epic Goal"],
            evidence={**evidence, **roadmap_owner},
        )
    if lane_conflict:
        return decision(
            workflow="feature",
            status="blocked",
            next_action="resolve-feature-execution-lane-conflict",
            reason="ff-note conflicts with the execution lane recorded by the feature design",
            blocking=["record execution_lane: quick before resuming a reclassified feature"],
            evidence=evidence,
        )
    if execution_lane not in VALID_EXECUTION_LANES:
        return decision(
            workflow="feature",
            status="blocked",
            next_action="fix-feature-execution-lane",
            reason=f"unsupported feature execution_lane: {execution_lane}",
            blocking=["feature execution_lane must be quick, standard, or goal"],
            evidence=evidence,
        )
    if (
        execution_lane == "quick"
        and design is not None
        and not str(design_meta.get("execution_lane_reason") or "").strip()
    ):
        return decision(
            workflow="feature",
            status="blocked",
            next_action="fix-feature-execution-lane",
            reason="reclassified Quick design lacks an execution_lane_reason",
            blocking=["record the owner signal and risk recheck before resuming Quick"],
            evidence=evidence,
        )
    if execution_lane == "quick":
        return quick_feature_next(
            ff_note=ff_note,
            ff_note_meta=ff_note_meta,
            code_review=code_review,
            code_review_meta=code_review_meta,
            code_review_gate_passed=code_review_gate_ok,
            qa=qa,
            qa_meta=qa_meta,
            acceptance=acceptance,
            acceptance_meta=acceptance_meta,
            evidence=evidence,
        )
    if design is None:
        return decision(
            workflow="feature",
            status="continue",
            next_action="cs-feat design",
            reason="feature design is missing",
            missing_artifacts=[f"{feature_slug_from_dir(feature)}-design.md"],
            evidence=evidence,
        )
    if design_status == "approved" and design_review_status != "passed":
        return decision(
            workflow="feature",
            status="blocked",
            next_action="fix-feature-design-review-state",
            reason="approved design lacks a passed design-review",
            blocking=[f"approved design has design-review status: {design_review_status}"],
            evidence=evidence,
        )
    if design_review_status in {"changes-requested", "blocked"}:
        return decision(
            workflow="feature",
            status="continue",
            next_action="cs-feat design",
            reason=f"design-review is {design_review_status}",
            evidence=evidence,
        )
    if design_status == "draft" and design_review_status != "passed":
        return decision(
            workflow="feature",
            status="continue",
            next_action="cs-feat design-review",
            reason="draft design still needs a passed design-review",
            missing_artifacts=[] if design_review else [f"{feature_slug_from_dir(feature)}-design-review.md"],
            evidence=evidence,
        )
    if design_review_status == "passed" and epic_child_batch:
        roadmap_slug = design_meta.get("roadmap")
        roadmap_item = design_meta.get("roadmap_item")
        if not roadmap_slug or not roadmap_item:
            return decision(
                workflow="feature",
                status="blocked",
                next_action="fix-feature-roadmap-metadata",
                reason="epic child batch feature lacks roadmap frontmatter",
                blocking=["feature design must include roadmap and roadmap_item in epic_child_batch"],
                evidence=evidence,
            )
        roadmap = root / ".codestable" / "roadmap" / str(roadmap_slug)
        return decision(
            workflow="feature",
            status="continue",
            next_action="return-to-cs-epic-batch-loop",
            reason="epic child design is reviewed; cs-epic must decide the next batch action",
            evidence={
                **evidence,
                "roadmap": rel(root, roadmap),
                "roadmap_item": roadmap_item,
                "epic_command": tool_command(
                    "codestable-workflow-next.py",
                    "epic",
                    "--roadmap",
                    rel(root, roadmap),
                    "--json",
                ),
            },
        )
    if roadmap_owner is not None:
        return decision(
            workflow="feature",
            status="continue",
            next_action="return-to-cs-epic",
            reason="feature is owned by an existing roadmap goal-state",
            evidence={**evidence, **roadmap_owner},
        )
    if design_review_status == "passed" and design_status != "approved":
        return decision(
            workflow="feature",
            status="user_gate",
            next_action="feature-design-confirmation",
            reason="design-review passed and the single feature design awaits user approval",
            evidence=evidence,
        )
    if design_status == "approved" and execution_lane == "goal" and goal_state is None:
        return decision(
            workflow="feature",
            status="goal_package",
            next_action="cs-feat goal-package",
            reason="approved feature design is missing a goal package",
            missing_artifacts=["goal-state.yaml"],
            evidence=evidence,
        )

    if design_status == "approved" and execution_lane == "standard" and goal_state is None:
        return standard_feature_next(
            checklist_steps_done=checklist_steps_done,
            code_review=code_review,
            code_review_meta=code_review_meta,
            code_review_gate_passed=code_review_gate_ok,
            qa=qa,
            qa_meta=qa_meta,
            acceptance=acceptance,
            acceptance_meta=acceptance_meta,
            evidence=evidence,
        )

    state = load_yaml_artifact(goal_state) if goal_state else {}
    state = state if isinstance(state, dict) else {}
    stage = state.get("stage")
    status = state.get("status")
    if (stage, status) == ("complete", "passed"):
        return decision(
            workflow="feature",
            status="complete",
            next_action="CS_FEATURE_GOAL_COMPLETE",
            reason="feature goal-state stage=complete status=passed",
            evidence=evidence,
        )
    if (stage, status) == ("handoff", "blocked"):
        return decision(
            workflow="feature",
            status="user_gate",
            next_action="CS_FEATURE_GOAL_HANDOFF",
            reason=str(state.get("handoff_reason") or "feature goal driver requested handoff"),
            evidence={**evidence, "handoff_next": state.get("handoff_next")},
        )
    driver_kind = state.get("driver_kind")
    driver_id = state.get("driver_id")
    if driver_kind in {"paseo", "native"} and driver_id:
        return decision(
            workflow="feature",
            status="report_driver",
            next_action="report-visible-driver",
            reason="visible feature goal driver is already recorded",
            evidence={**evidence, "driver_kind": driver_kind, "driver_id": driver_id},
        )
    routes = {
        ("implementation", "ready-to-dispatch"): ("dispatch_goal", "dispatch-feature-goal-driver-or-print-goal"),
        ("implementation", "running"): ("continue", "cs-feat implementation"),
        ("review", "ready"): ("continue", "cs-code-review"),
        ("review", "fixing"): ("continue", "cs-feat implementation review-fix"),
        ("qa", "ready"): ("continue", "cs-feat qa"),
        ("qa", "fixing"): ("continue", "cs-feat implementation qa-fix"),
        ("acceptance", "ready"): ("continue", "cs-feat acceptance"),
    }
    if (stage, status) in routes:
        next_status, next_action = routes[(stage, status)]
        return decision(
            workflow="feature",
            status=next_status,
            next_action=next_action,
            reason=f"feature goal-state stage={stage} status={status}",
            evidence=evidence,
        )
    return decision(
        workflow="feature",
        status="blocked",
        next_action="inspect-feature-goal-state",
        reason="unknown feature goal-state stage/status",
        blocking=[f"unknown goal-state stage/status: {stage}/{status}"],
        evidence=evidence,
    )


def feature_next(feature: Path, epic_child_batch: bool) -> dict[str, Any]:
    try:
        return _feature_next(feature, epic_child_batch)
    except ArtifactParseError as error:
        return artifact_parse_decision("feature", feature, error)


def print_human(result: dict[str, Any]) -> None:
    print(f"{result['workflow']} next: {result['status']} -> {result['next_action']}")
    print(result["reason"])
    for item in result.get("blocking", []):
        print(f"blocking: {item}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    subparsers = parser.add_subparsers(dest="command", required=True)

    epic_parser = subparsers.add_parser("epic", help="Resolve next action for an epic roadmap")
    epic_parser.add_argument("--roadmap", required=True, help="Roadmap directory, e.g. .codestable/roadmap/foo")
    epic_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)

    feature_parser = subparsers.add_parser("feature", help="Resolve next action for a feature")
    feature_parser.add_argument("--feature", required=True, help="Feature directory, e.g. .codestable/features/YYYY-MM-DD-foo")
    feature_parser.add_argument("--epic-child-batch", action="store_true", help="Use cs-epic child design batch semantics")
    feature_parser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS)

    args = parser.parse_args()
    if args.command == "epic":
        result = epic_next(Path(args.roadmap))
    else:
        result = feature_next(Path(args.feature), args.epic_child_batch)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_human(result)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
