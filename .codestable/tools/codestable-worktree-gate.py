#!/usr/bin/env python3
"""Gate CodeStable implementation worktree lifecycle actions."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

from codestable_common import (
    Finding,
    baseline_path,
    bucket_paths,
    changed_paths_between,
    current_branch,
    default_branch,
    has_human_approved_override,
    has_secret_like_untracked,
    is_implementation_path,
    is_implementation_unit,
    is_linked_worktree,
    missing_review_findings,
    read_baseline,
    ref_head,
    resolve_unit,
    review_file_for,
    staged_files,
    unit_needs_review,
    unit_slug,
    write_baseline,
)


def result(ok: bool, action: str, findings: list[Finding], **meta: object) -> dict[str, object]:
    return {
        "ok": ok,
        "action": action,
        "findings": [asdict(finding) for finding in findings],
        **meta,
    }


def start_gate(root: Path, unit_value: str) -> dict[str, object]:
    root = root.resolve()
    unit_dir = resolve_unit(root, unit_value)
    findings: list[Finding] = []
    linked = is_linked_worktree(root)
    has_override = has_human_approved_override(root, unit_dir)
    implementation_unit = is_implementation_unit(unit_dir)

    if implementation_unit and not linked and not has_override:
        findings.append(
            Finding(
                severity="P1",
                message=(
                    "Implementation unit must start in a linked execution worktree. "
                    "Add worktree-override.md with reason, scope, and approval for an explicit exception."
                ),
                path=unit_dir.as_posix(),
            )
        )

    baseline = None
    if not findings:
        baseline = write_baseline(root, unit_dir)

    return result(
        not findings,
        "start",
        findings,
        unit=unit_dir.as_posix(),
        implementation_unit=implementation_unit,
        linked_worktree=linked,
        override=has_override,
        baseline=baseline,
        baseline_path=baseline_path(root, unit_dir).as_posix(),
    )


def commit_gate(root: Path, unit_value: str) -> dict[str, object]:
    root = root.resolve()
    unit_dir = resolve_unit(root, unit_value)
    findings: list[Finding] = []
    warnings: list[Finding] = []
    branch = current_branch(root)
    default = default_branch(root)
    staged = staged_files(root)
    staged_paths = [item.path for item in staged]
    staged_implementation = [path for path in staged_paths if is_implementation_path(path)]
    baseline = read_baseline(root, unit_dir)

    if branch == default and staged_implementation:
        findings.append(
            Finding(
                severity="P1",
                message="Staged implementation changes are present on the default branch.",
                path=", ".join(staged_implementation),
            )
        )

    post_baseline_implementation: list[str] = []
    if baseline and baseline.get("default_head") and baseline.get("default_branch"):
        default_ref = str(baseline["default_branch"])
        head = ref_head(root, default_ref)
        if head and head != baseline["default_head"]:
            post_baseline_implementation = [
                path
                for path in changed_paths_between(root, str(baseline["default_head"]), default_ref)
                if is_implementation_path(path)
            ]
            if post_baseline_implementation:
                findings.append(
                    Finding(
                        severity="P1",
                        message="Default branch contains implementation changes after the recorded worktree baseline.",
                        path=", ".join(post_baseline_implementation),
                    )
                )

    if unit_needs_review(root, unit_dir):
        findings.extend(missing_review_findings(root, [unit_dir]))

    buckets = bucket_paths(staged_paths)
    if len([bucket for bucket, paths in buckets.items() if paths]) > 1:
        warnings.append(
            Finding(
                severity="P2",
                message="Staged files span multiple commit buckets; split commits intentionally.",
            )
        )

    return result(
        not findings,
        "commit",
        findings,
        warnings=[asdict(warning) for warning in warnings],
        unit=unit_dir.as_posix(),
        current_branch=branch,
        default_branch=default,
        staged_files=staged_paths,
        dirty_buckets=buckets,
        baseline=baseline,
        post_baseline_implementation=post_baseline_implementation,
        required_review=review_file_for(unit_dir).as_posix() if unit_needs_review(root, unit_dir) else None,
    )


def quarantine_gate(root: Path, unit_value: str, apply: bool) -> dict[str, object]:
    root = root.resolve()
    unit_dir = resolve_unit(root, unit_value)
    slug = unit_slug(unit_dir)
    findings: list[Finding] = []
    secret_untracked = has_secret_like_untracked(root)
    target_branch = f"chore/quarantine-{slug}"
    target_worktree = root / ".worktree" / f"quarantine-{slug}"

    if secret_untracked:
        findings.append(
            Finding(
                severity="P1",
                message="Quarantine refuses to run while untracked secret-like files are present.",
                path=", ".join(secret_untracked),
            )
        )

    has_override = has_human_approved_override(root, unit_dir)
    if apply and not has_override:
        findings.append(
            Finding(
                severity="P1",
                message="Quarantine --apply requires worktree-override.md with reason, scope, and approval.",
                path=unit_dir.as_posix(),
            )
        )

    applied = False
    if apply and not findings:
        target_worktree.parent.mkdir(parents=True, exist_ok=True)
        command = ["git", "worktree", "add", "-b", target_branch, target_worktree.as_posix(), "HEAD"]
        completed = subprocess.run(
            command,
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0:
            findings.append(
                Finding(
                    severity="P1",
                    message=f"Failed to create quarantine worktree: {completed.stderr.strip()}",
                )
            )
        else:
            applied = True

    return result(
        not findings,
        "quarantine",
        findings,
        unit=unit_dir.as_posix(),
        dry_run=not apply,
        applied=applied,
        plan={
            "target_branch": target_branch,
            "target_worktree": target_worktree.as_posix(),
            "mutation_requires_apply": True,
            "moves_files": False,
            "note": "Phase 1 creates a safe execution worktree; moving dirty files remains a manual owner action.",
        },
    )


def emit(payload: dict[str, object], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    status = "passed" if payload["ok"] else "failed"
    print(f"CodeStable worktree gate {payload['action']} {status}.")
    for finding in payload["findings"]:
        path = f" ({finding['path']})" if finding.get("path") else ""
        print(f"- {finding['severity']}: {finding['message']}{path}")


def error_payload(action: str, message: str) -> dict[str, object]:
    return result(False, action, [Finding(severity="P1", message=message)])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--json", action="store_true", help="Print machine-readable output")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("start", "commit", "quarantine"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--unit", required=True, help="CodeStable unit path or slug")
        if name == "quarantine":
            sub.add_argument("--apply", action="store_true", help="Create the quarantine worktree")

    args = parser.parse_args()
    root = Path(args.root)
    try:
        if args.command == "start":
            payload = start_gate(root, args.unit)
        elif args.command == "commit":
            payload = commit_gate(root, args.unit)
        else:
            payload = quarantine_gate(root, args.unit, args.apply)
    except ValueError as exc:
        payload = error_payload(args.command, str(exc))

    emit(payload, args.json)
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
