#!/usr/bin/env python3
"""Prepare a CodeStable execution worktree for owner-approved merge."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

from codestable_common import (
    Finding,
    branch_head,
    changed_paths_between,
    current_branch,
    default_branch,
    git_status,
    inbox_record_path,
    is_implementation_unit,
    is_linked_worktree,
    missing_review_findings,
    resolve_unit,
    scan_backlog,
    unit_dir_for,
    unit_needs_review,
    unit_slug,
    utc_now_iso,
    write_inbox_record,
)


def result(ok: bool, findings: list[Finding], **meta: object) -> dict[str, object]:
    return {"ok": ok, "findings": [asdict(finding) for finding in findings], **meta}


def existing_record_created_at(root: Path, branch: str | None, unit_dir: Path) -> str:
    path = inbox_record_path(root, branch, unit_dir)
    if path.exists():
        try:
            value = json.loads(path.read_text(encoding="utf-8")).get("created_at")
        except json.JSONDecodeError:
            value = None
        if isinstance(value, str) and value:
            return value
    return utc_now_iso()


def unit_backlog_findings(root: Path, unit_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    for item in scan_backlog(root):
        if unit_dir_for(item.path) == unit_dir:
            findings.append(
                Finding(
                    severity="P1",
                    message=f"Unit has unresolved CodeStable backlog item: {item.text}",
                    path=f"{item.path}:{item.line}",
                )
            )
    return findings


def finish_artifact_paths(unit_dir: Path) -> dict[str, Path]:
    slug = unit_slug(unit_dir)
    return {
        "learning_report": unit_dir / f"{slug}-learning-report.md",
        "context_check": unit_dir / f"{slug}-learning-context-check.json",
        "merge_readiness": unit_dir / f"{slug}-merge-readiness.json",
    }


def dirty_tree_findings(root: Path, generated_paths: dict[str, Path]) -> list[Finding]:
    allowed = {path.as_posix() for path in generated_paths.values()}
    findings: list[Finding] = []
    for item in git_status(root):
        if item.path in allowed:
            if item.status != "??" and item.status[:1] != " ":
                findings.append(
                    Finding(
                        severity="P1",
                        message="Finish artifact is staged; commit or unstage it before refreshing finish readiness.",
                        path=item.path,
                    )
                )
            continue
        findings.append(
            Finding(
                severity="P1",
                message="Finish gate requires a clean working tree before generating learner report.",
                path=item.path,
            )
        )
    return findings


def learner_report_text(
    root: Path,
    unit_dir: Path,
    branch: str,
    base_ref: str,
    head: str,
    changed_files: list[str],
    validations: list[str],
    follow_ups: list[str],
) -> str:
    slug = unit_slug(unit_dir)
    changed = changed_files or ["None"]
    follow_up_items = follow_ups or ["None"]
    return "\n".join(
        [
            "---",
            "doc_type: learner-report",
            f"unit: {unit_dir.as_posix()}",
            f"branch: {branch}",
            f"base_ref: {base_ref}",
            f"covered_head: {head}",
            f"covered_diff: {base_ref}...{head}",
            "status: ready-to-merge",
            "---",
            "",
            f"# {slug} 学习报告",
            "",
            "> 这份报告记录当前 execution worktree 在合并前必须保留的上下文和验证证据。",
            "",
            "## 决策简报",
            "",
            "### 目标",
            f"- 准备将 `{branch}` 合并回 `{base_ref}`。",
            "",
            "### 已决定",
            "- 本 worktree 已进入 finish gate，学习报告覆盖当前 HEAD。",
            "",
            "### 已排除",
            "- 不自动 merge、rebase、删除 branch 或删除 worktree。",
            "",
            "## 工作上下文",
            "",
            "### 风险",
            "- 合并前如果出现新 commit，必须重新生成学习报告。",
            "",
            "### 相关文件",
            *[f"- {path}" for path in changed],
            "",
            "### 剩余事项",
            *[f"- {item}" for item in follow_up_items],
            "",
            "## 证据附录",
            "",
            "### 验证证据",
            *[f"- {item}" for item in validations],
            "",
            "## 1. 为什么做",
            "- 记录 worktree finish 前的合并上下文，避免分支完成后被遗忘。",
            "",
            "## 2. 改了什么",
            *[f"- {path}" for path in changed],
            "",
            "## 3. 没改什么",
            "- 未自动合并到 base branch。",
            "- 未自动清理 worktree。",
            "",
            "## 4. 关键决策",
            f"- `covered_head` 固定为 `{head}`；HEAD 变化后本报告失效。",
            "",
            "## 5. Task agent review 发现与修复",
            "- 见同 unit 的 implementation review 记录；finish gate 只验证 evidence 是否存在。",
            "",
            "## 6. 验证证据",
            *[f"- {item}" for item in validations],
            "",
            "## 7. 合并前注意事项",
            f"- 合并前确认 `{branch}` 当前 HEAD 仍为 `{head}`。",
            "",
            "## 8. 后续 follow-up",
            *[f"- {item}" for item in follow_up_items],
            "",
        ]
    )


def run_context_check(script_dir: Path, report_path: Path) -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, (script_dir / "check-context-sufficiency.py").as_posix(), "--file", report_path.as_posix(), "--strict", "--json"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        payload = {
            "ok": False,
            "findings": [
                {
                    "severity": "P1",
                    "code": "context_check_failed",
                    "message": completed.stderr.strip() or completed.stdout.strip() or "context check failed",
                }
            ],
        }
    payload["returncode"] = completed.returncode
    return payload


def finish(root: Path, unit_value: str, validations: list[str]) -> dict[str, object]:
    root = root.resolve()
    unit_dir = resolve_unit(root, unit_value)
    branch = current_branch(root)
    base_ref = default_branch(root) or "main"
    head = branch_head(root, "HEAD")
    findings: list[Finding] = []

    if not is_linked_worktree(root):
        findings.append(Finding(severity="P1", message="Finish gate must run in a linked execution worktree."))
    if branch == base_ref:
        findings.append(Finding(severity="P1", message="Finish gate cannot mark the default branch ready to merge."))
    if not branch:
        findings.append(Finding(severity="P1", message="Finish gate requires a named branch."))
    if not head:
        findings.append(Finding(severity="P1", message="Could not resolve current HEAD."))
    if not validations:
        findings.append(Finding(severity="P1", message="Finish gate requires at least one validation evidence item."))

    generated_paths = finish_artifact_paths(unit_dir)
    findings.extend(dirty_tree_findings(root, generated_paths))

    if is_implementation_unit(unit_dir) and unit_needs_review(root, unit_dir):
        findings.extend(missing_review_findings(root, [unit_dir]))
    findings.extend(unit_backlog_findings(root, unit_dir))

    report_path = root / generated_paths["learning_report"]
    context_check_path = root / generated_paths["context_check"]
    merge_readiness_path = root / generated_paths["merge_readiness"]

    if findings:
        return result(
            False,
            findings,
            action="finish-worktree",
            unit=unit_dir.as_posix(),
            branch=branch,
            base_ref=base_ref,
            covered_head=head,
        )

    assert branch and head
    changed_files = changed_paths_between(root, base_ref, "HEAD")
    report_path.write_text(
        learner_report_text(root, unit_dir, branch, base_ref, head, changed_files, validations, []),
        encoding="utf-8",
    )
    context_check = run_context_check(Path(__file__).resolve().parent, report_path)
    context_check_path.write_text(json.dumps(context_check, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not context_check.get("ok"):
        findings.append(Finding(severity="P1", message="Learner report failed strict context sufficiency check.", path=context_check_path.relative_to(root).as_posix()))
        return result(False, findings, action="finish-worktree", unit=unit_dir.as_posix(), branch=branch, base_ref=base_ref, covered_head=head)

    now = utc_now_iso()
    created_at = existing_record_created_at(root, branch, unit_dir)
    record = {
        "schema_version": 1,
        "branch": branch,
        "worktree": root.as_posix(),
        "unit": unit_dir.as_posix(),
        "status": "ready-to-merge",
        "base_ref": base_ref,
        "covered_head": head,
        "covered_diff": f"{base_ref}...{head}",
        "learning_report": report_path.relative_to(root).as_posix(),
        "learning_report_abs": report_path.as_posix(),
        "context_check": context_check_path.relative_to(root).as_posix(),
        "context_check_abs": context_check_path.as_posix(),
        "merge_readiness": merge_readiness_path.relative_to(root).as_posix(),
        "merge_readiness_abs": merge_readiness_path.as_posix(),
        "created_at": created_at,
        "last_seen_at": now,
        "snoozed_until": None,
        "next_action": f"merge {branch} into {base_ref} after owner approval",
    }
    merge_readiness_path.write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    inbox_path = write_inbox_record(root, record)

    return result(
        True,
        [],
        action="finish-worktree",
        status="ready-to-merge",
        unit=unit_dir.as_posix(),
        branch=branch,
        base_ref=base_ref,
        covered_head=head,
        learning_report=report_path.relative_to(root).as_posix(),
        context_check=context_check_path.relative_to(root).as_posix(),
        merge_readiness=merge_readiness_path.relative_to(root).as_posix(),
        inbox_record=inbox_path.as_posix(),
        next_action=record["next_action"],
    )


def emit(payload: dict[str, object], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    status = "passed" if payload["ok"] else "failed"
    print(f"CodeStable finish worktree {status}.")
    if payload.get("next_action"):
        print(f"Next action: {payload['next_action']}")
    for finding in payload["findings"]:
        path = f" ({finding['path']})" if finding.get("path") else ""
        print(f"- {finding['severity']}: {finding['message']}{path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--unit", required=True, help="CodeStable unit path or slug")
    parser.add_argument("--validation", action="append", default=[], help="Validation evidence; repeat as needed")
    parser.add_argument("--json", action="store_true", help="Print machine-readable output")
    args = parser.parse_args()

    try:
        payload = finish(Path(args.root), args.unit, [item for item in args.validation if item.strip()])
    except ValueError as exc:
        payload = result(False, [Finding(severity="P1", message=str(exc))], action="finish-worktree")
    emit(payload, args.json)
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
