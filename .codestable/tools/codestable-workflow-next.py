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


NON_BLOCKING_STATUSES = {"continue", "user_gate", "goal_package", "dispatch_goal", "report_driver", "complete"}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def frontmatter(path: Path) -> dict[str, Any]:
    if not path.exists() or path.suffix != ".md":
        return {}
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    parsed = load_yaml_text(text[3:end].strip())
    return parsed if isinstance(parsed, dict) else {}


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


def find_roadmap_file(roadmap: Path) -> Path | None:
    return first_existing(roadmap / f"{roadmap.name}-roadmap.md") or single_glob(roadmap, "*-roadmap.md")


def find_items_file(roadmap: Path) -> Path | None:
    return first_existing(roadmap / f"{roadmap.name}-items.yaml") or single_glob(roadmap, "*-items.yaml")


def find_roadmap_review(roadmap: Path) -> Path | None:
    return first_existing(roadmap / f"{roadmap.name}-roadmap-review.md") or single_glob(roadmap, "*-roadmap-review.md")


def load_items(items_path: Path | None) -> list[dict[str, Any]]:
    if items_path is None or not items_path.exists():
        return []
    data = load_yaml(items_path)
    if not isinstance(data, dict):
        return []
    rows = data.get("items") or data.get("features") or []
    return [row for row in as_list(rows) if isinstance(row, dict)]


def find_feature_dir(root: Path, roadmap_slug: str, item: dict[str, Any]) -> Path | None:
    feature_value = item.get("feature")
    if feature_value not in {None, "", "null"}:
        feature_path = Path(str(feature_value))
        if not feature_path.is_absolute():
            if feature_path.parts and feature_path.parts[0] == ".codestable":
                feature_path = root / feature_path
            else:
                feature_path = root / ".codestable" / "features" / feature_path
        if feature_path.exists():
            return feature_path

    item_slug = str(item.get("slug") or "")
    features_root = root / ".codestable" / "features"
    if not features_root.exists():
        return None
    for design in sorted(features_root.glob("*/**/*-design.md")):
        meta = frontmatter(design)
        if meta.get("roadmap") == roadmap_slug and meta.get("roadmap_item") == item_slug:
            return design.parent
    matches = sorted(features_root.glob(f"*-{item_slug}"))
    return matches[0] if matches else None


def feature_artifacts(feature: Path, item_slug: str | None = None) -> dict[str, Path | None]:
    slug = item_slug or feature_slug_from_dir(feature)
    design = first_existing(feature / f"{slug}-design.md") or single_glob(feature, "*-design.md")
    checklist = first_existing(feature / f"{slug}-checklist.yaml") or single_glob(feature, "*-checklist.yaml")
    design_review = first_existing(feature / f"{slug}-design-review.md") or single_glob(feature, "*-design-review.md")
    goal_state = feature / "goal-state.yaml"
    return {
        "design": design,
        "checklist": checklist,
        "design_review": design_review,
        "goal_state": goal_state if goal_state.exists() else None,
    }


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


def epic_next(roadmap: Path) -> dict[str, Any]:
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

    review_status = status_of(review_file)
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

    roadmap_status = status_of(roadmap_file)
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
        feature = find_feature_dir(root, roadmap.name, item)
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

    state = load_yaml(goal_state)
    state = state if isinstance(state, dict) else {}
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
    if state.get("status") == "ready-to-dispatch":
        return decision(
            workflow="epic",
            status="dispatch_goal",
            next_action="dispatch-epic-goal-driver-or-print-goal",
            reason="epic goal package is ready to dispatch",
            warnings=warnings,
            evidence={"goal_state": rel(root, goal_state)},
        )
    if state.get("status") in {"complete", "completed"}:
        return decision(
            workflow="epic",
            status="complete",
            next_action="CS_ROADMAP_GOAL_COMPLETE",
            reason="epic goal state is complete",
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


def feature_next(feature: Path, epic_child_batch: bool) -> dict[str, Any]:
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
    review = artifacts["design_review"]
    goal_state = artifacts["goal_state"]
    design_status = status_of(design)
    review_status = status_of(review)
    evidence = {
        "feature_dir": rel(root, feature),
        "design": rel(root, design),
        "design_status": design_status,
        "design_review": rel(root, review),
        "design_review_status": review_status,
        "goal_state": rel(root, goal_state),
    }

    if design is None:
        return decision(
            workflow="feature",
            status="continue",
            next_action="cs-feat design",
            reason="feature design is missing",
            missing_artifacts=[f"{feature_slug_from_dir(feature)}-design.md"],
            evidence=evidence,
        )
    if design_status == "draft" and review_status != "passed":
        return decision(
            workflow="feature",
            status="continue",
            next_action="cs-feat design-review",
            reason="draft design still needs a passed design-review",
            missing_artifacts=[] if review else [f"{feature_slug_from_dir(feature)}-design-review.md"],
            evidence=evidence,
        )
    if review_status in {"changes-requested", "blocked"}:
        return decision(
            workflow="feature",
            status="continue",
            next_action="cs-feat design",
            reason=f"design-review is {review_status}",
            evidence=evidence,
        )
    if review_status == "passed" and design_status != "approved":
        if epic_child_batch:
            meta = frontmatter(design)
            roadmap_slug = meta.get("roadmap")
            if not roadmap_slug:
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
                    "roadmap_item": meta.get("roadmap_item"),
                    "epic_command": f"python3 .codestable/tools/codestable-workflow-next.py epic --roadmap {rel(root, roadmap)} --json",
                },
            )
        return decision(
            workflow="feature",
            status="user_gate",
            next_action="feature-design-confirmation",
            reason="design-review passed and the single feature design awaits user approval",
            evidence=evidence,
        )
    if design_status == "approved" and goal_state is None:
        return decision(
            workflow="feature",
            status="goal_package",
            next_action="cs-feat goal-package",
            reason="approved feature design is missing a goal package",
            missing_artifacts=["goal-state.yaml"],
            evidence=evidence,
        )

    state = load_yaml(goal_state) if goal_state else {}
    state = state if isinstance(state, dict) else {}
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
    stage = state.get("stage")
    status = state.get("status")
    routes = {
        ("implementation", "ready-to-dispatch"): ("dispatch_goal", "dispatch-feature-goal-driver-or-print-goal"),
        ("implementation", "running"): ("continue", "cs-feat implementation"),
        ("review", "ready"): ("continue", "cs-code-review"),
        ("review", "fixing"): ("continue", "cs-feat implementation review-fix"),
        ("qa", "ready"): ("continue", "cs-feat qa"),
        ("qa", "fixing"): ("continue", "cs-feat implementation qa-fix"),
        ("acceptance", "ready"): ("continue", "cs-feat acceptance"),
        ("complete", "passed"): ("complete", "CS_FEATURE_GOAL_COMPLETE"),
        ("handoff", "blocked"): ("user_gate", "CS_FEATURE_GOAL_HANDOFF"),
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
