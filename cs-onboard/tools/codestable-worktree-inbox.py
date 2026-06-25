#!/usr/bin/env python3
"""Report CodeStable worktrees that are ready to merge or need owner action."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from codestable_common import (
    branch_head,
    changed_paths_between,
    default_branch,
    inbox_dir,
    inbox_record_id,
    is_ancestor,
    iter_inbox_records,
    utc_now_iso,
    worktree_map,
    write_inbox_record,
)


def parse_time(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def is_snoozed(record: dict[str, object], status: str) -> bool:
    if status != "ready-to-merge":
        return False
    until = parse_time(record.get("snoozed_until"))
    return until is not None and until > datetime.now(timezone.utc)


def finish_artifact_paths(record: dict[str, object]) -> set[str]:
    return {
        str(record.get(key) or "")
        for key in ("learning_report", "context_check", "merge_readiness")
        if record.get(key)
    }


def only_finish_artifacts_changed(root: Path, record: dict[str, object], covered_head: str, current_head: str) -> bool:
    if not is_ancestor(root, covered_head, current_head):
        return False
    changed = set(changed_paths_between(root, covered_head, current_head))
    return bool(changed) and changed <= finish_artifact_paths(record)


def reminder_severity(status: str, created_at: object) -> str | None:
    if status == "stale-report":
        return "P1"
    if status == "blocked":
        return "P1"
    if status == "merged":
        return "P3"
    if status != "ready-to-merge":
        return None
    created = parse_time(created_at)
    if created is None:
        return "P2"
    age_seconds = (datetime.now(timezone.utc) - created).total_seconds()
    return "P1" if age_seconds >= 3 * 24 * 60 * 60 else "P2"


def classify_record(root: Path, record: dict[str, object], worktrees: dict[str, dict[str, object]]) -> dict[str, object]:
    branch = str(record.get("branch") or "")
    base_ref = str(record.get("base_ref") or default_branch(root) or "main")
    covered_head = str(record.get("covered_head") or "")
    worktree = str(record.get("worktree") or "")
    original_status = str(record.get("status") or "active")
    current_head = branch_head(root, branch) if branch else None
    base_head = branch_head(root, base_ref) or base_ref
    worktree_abs = Path(worktree).resolve().as_posix() if worktree else ""
    worktree_exists = worktree_abs in worktrees or (bool(worktree) and Path(worktree).exists())

    reasons: list[str] = []
    if original_status == "abandoned":
        status = "abandoned"
    elif not covered_head:
        status = "blocked"
        reasons.append("covered_head is missing")
    elif not branch or current_head is None:
        if base_head and is_ancestor(root, covered_head, base_ref):
            status = "merged"
        else:
            status = "blocked"
            reasons.append("branch is missing")
    elif current_head != covered_head and not only_finish_artifacts_changed(root, record, covered_head, current_head):
        status = "stale-report"
        reasons.append("branch HEAD differs from learner report covered_head")
    elif base_head and is_ancestor(root, current_head, base_ref):
        status = "merged"
    elif current_head != covered_head:
        status = "ready-to-merge"
        reasons.append("branch HEAD differs from covered_head only by finish artifacts")
    elif original_status in {"ready-to-merge", "blocked", "active", "stale-report"}:
        status = original_status if original_status != "stale-report" else "ready-to-merge"
    else:
        status = original_status

    if status == "ready-to-merge" and not worktree_exists:
        reasons.append("referenced worktree is missing")

    snoozed = is_snoozed(record, status)
    severity = None if snoozed else reminder_severity(status, record.get("created_at"))
    if snoozed:
        reasons.append(f"snoozed until {record.get('snoozed_until')}")
    return {
        **record,
        "id": inbox_record_id(branch, str(record.get("unit") or "")),
        "status": status,
        "severity": severity,
        "snoozed": snoozed,
        "current_head": current_head,
        "base_head": base_head,
        "worktree_exists": worktree_exists,
        "reasons": reasons,
    }


def inbox(root: Path) -> dict[str, object]:
    root = root.resolve()
    worktrees = worktree_map(root)
    items = [classify_record(root, record, worktrees) for record in iter_inbox_records(root)]
    active_items = [item for item in items if not item.get("snoozed")]
    p1 = [item for item in active_items if item.get("severity") == "P1"]
    ready = [item for item in active_items if item.get("status") == "ready-to-merge"]
    stale = [item for item in items if item.get("status") == "stale-report"]
    merged = [item for item in items if item.get("status") == "merged"]
    snoozed = [item for item in items if item.get("snoozed")]
    return {
        "ok": not p1,
        "inbox_dir": inbox_dir(root).as_posix(),
        "items": items,
        "ready_to_merge": ready,
        "stale_reports": stale,
        "merged": merged,
        "snoozed": snoozed,
        "p1_count": len(p1),
        "next_action": next_action(items),
    }


def next_action(items: list[dict[str, object]]) -> str:
    active_items = [item for item in items if not item.get("snoozed")]
    if any(item.get("status") == "stale-report" for item in active_items):
        return "Refresh stale learner reports before merging those worktrees."
    if any(item.get("severity") == "P1" for item in active_items):
        return "Resolve P1 worktree inbox records before merge."
    if any(item.get("status") == "ready-to-merge" for item in active_items):
        return "Merge, snooze, or abandon ready-to-merge worktrees."
    if any(item.get("status") == "merged" for item in active_items):
        return "Clean up merged worktrees or archive inbox records."
    return "No worktree merge reminder is active."


def find_record(root: Path, record_id: str) -> dict[str, object]:
    for record in iter_inbox_records(root):
        if inbox_record_id(str(record.get("branch") or ""), str(record.get("unit") or "")) == record_id:
            return record
        if str(record.get("branch") or "") == record_id:
            return record
    raise ValueError(f"inbox record not found: {record_id}")


def snooze(root: Path, record_id: str, until: str) -> dict[str, object]:
    if parse_time(until) is None:
        raise ValueError(f"invalid --until timestamp: {until}")
    record = find_record(root, record_id)
    record["snoozed_until"] = until
    record["last_seen_at"] = utc_now_iso()
    path = write_inbox_record(root, record)
    return {"ok": True, "action": "snooze", "record": record, "path": path.as_posix()}


def abandon(root: Path, record_id: str, reason: str) -> dict[str, object]:
    record = find_record(root, record_id)
    record["status"] = "abandoned"
    record["abandon_reason"] = reason
    record["last_seen_at"] = utc_now_iso()
    path = write_inbox_record(root, record)
    return {"ok": True, "action": "abandon", "record": record, "path": path.as_posix()}


def emit(payload: dict[str, object], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(f"CodeStable worktree inbox: {payload.get('next_action', payload.get('action'))}")
    for item in payload.get("items", []):
        severity = item.get("severity") or "info"
        print(f"- {severity} {item.get('status')} {item.get('branch')} {item.get('next_action', '')}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--json", action="store_true", help="Print machine-readable output")
    parser.add_argument("--snooze", help="Record id or branch to snooze")
    parser.add_argument("--until", help="Snooze until timestamp")
    parser.add_argument("--abandon", help="Record id or branch to abandon")
    parser.add_argument("--reason", help="Abandon reason")
    args = parser.parse_args()

    root = Path(args.root)
    try:
        if args.snooze:
            if not args.until:
                raise ValueError("--snooze requires --until")
            payload = snooze(root, args.snooze, args.until)
        elif args.abandon:
            if not args.reason:
                raise ValueError("--abandon requires --reason")
            payload = abandon(root, args.abandon, args.reason)
        else:
            payload = inbox(root)
    except ValueError as exc:
        payload = {"ok": False, "action": "error", "findings": [{"severity": "P1", "message": str(exc)}]}

    emit(payload, args.json)
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
