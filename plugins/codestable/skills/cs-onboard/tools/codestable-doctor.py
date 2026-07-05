#!/usr/bin/env python3
"""Report CodeStable lifecycle state without mutating the repository."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from dataclasses import asdict
from pathlib import Path

from codestable_common import (
    Finding,
    bucket_paths,
    current_branch,
    default_branch,
    git_status,
    is_implementation_path,
    iter_units,
    missing_review_findings,
    scan_backlog,
)
from codestable_runtime import runtime_health


def ocr_health() -> dict[str, object]:
    """Static, network-free health check for the optional open-code-review (ocr) CLI."""
    exe = shutil.which("ocr")
    if not exe:
        return {
            "installed": False,
            "status": "not-installed",
            "hint": "可选增强；cs-code-review 检测不到会自动降级。需要时装：npm install -g @alibaba-group/open-code-review",
        }
    cfg_path = Path(os.path.expanduser("~/.opencodereview/config.json"))
    info: dict[str, object] = {"installed": True, "path": exe, "config_path": cfg_path.as_posix()}
    if not cfg_path.exists():
        info["status"] = "unconfigured"
        info["hint"] = (
            "ocr 已装但未配 LLM。用 provider 体系配置"
            "（ocr config set provider <name> + providers.<name>.url/api_key），"
            "勿用旧 llm.* 块；详见 cs-onboard OCR 段。"
        )
        return info
    try:
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        info["status"] = "config-error"
        info["hint"] = f"config.json 解析失败：{exc}"
        return info
    cfg = cfg if isinstance(cfg, dict) else {}
    provider = cfg.get("provider")
    providers = cfg.get("providers")
    providers = providers if isinstance(providers, dict) else {}
    has_legacy_llm = isinstance(cfg.get("llm"), dict)
    info["provider"] = provider
    info["legacy_llm_block"] = has_legacy_llm
    pcfg = providers.get(provider) if isinstance(provider, str) else None
    if not isinstance(pcfg, dict):
        info["status"] = "misconfigured"
        if has_legacy_llm:
            info["hint"] = (
                "检测到旧 `llm.*` 块但无有效 provider 配置——旧块在 ocr v1.x 不生效。"
                "改用：ocr config set provider <name>；"
                "ocr config set providers.<name>.url <base-url>；"
                "ocr config set providers.<name>.api_key <key>。"
            )
        else:
            info["hint"] = "未设置有效 provider。用 ocr config set provider <name> + providers.<name>.url/api_key 配置。"
        return info
    info["status"] = "configured"
    info["model"] = cfg.get("model") or pcfg.get("model")
    info["has_custom_url"] = bool(pcfg.get("url"))
    hint = "已配 provider；跑 `ocr llm test` 验证连通（doctor 不发网络请求）。"
    if has_legacy_llm:
        hint += " 注意 config 仍残留旧 llm.* 块，建议手动删除避免混淆。"
    info["hint"] = hint
    return info


def diagnose(root: Path) -> dict[str, object]:
    root = root.resolve()
    changed = git_status(root)
    changed_paths = [item.path for item in changed]
    implementation_changes = [path for path in changed_paths if is_implementation_path(path)]
    units = iter_units(root)
    review_findings = missing_review_findings(root, units)
    backlog = scan_backlog(root)
    runtime = runtime_health(root, source_skill_dir=Path(__file__).resolve().parents[1])
    branch = current_branch(root)
    default = default_branch(root)

    findings: list[Finding] = []
    if not runtime["ok"]:
        message = (
            "CodeStable onboarding is incomplete; run `cs-onboard`."
            if runtime["status"] in {"not-onboarded", "onboard-incomplete"}
            else "CodeStable runtime assets are incomplete or stale; run runtime sync."
        )
        findings.append(
            Finding(
                severity="P1",
                message=message,
                path=", ".join(runtime["missing"]),
            )
        )
    findings.extend(review_findings)
    if backlog:
        findings.append(
            Finding(
                severity="P2",
                message="CodeStable backlog contains human-review or follow-up items.",
            )
        )

    if any(finding.severity == "P1" for finding in findings):
        status = "blocked"
        next_action = "Resolve P1 findings before reporting the task complete."
    elif implementation_changes:
        status = "implementation-active"
        next_action = "Run the appropriate CodeStable review before reporting implementation complete."
    elif changed_paths:
        buckets = set(bucket_paths(changed_paths))
        status = "planning-safe" if buckets <= {"codestable", "docs"} else "dirty"
        next_action = "Review dirty buckets and commit only the intended scope."
    elif backlog:
        status = "attention-needed"
        next_action = "Resolve or explicitly defer the backlog items."
    else:
        status = "idle"
        next_action = "No CodeStable lifecycle action is required."

    return {
        "ok": status not in {"blocked"},
        "status": status,
        "next_action": next_action,
        "checkout": {
            "root": root.as_posix(),
            "current_branch": branch,
            "default_branch": default,
            "is_default_branch": branch == default if branch and default else None,
        },
        "changed_files": changed_paths,
        "dirty_buckets": bucket_paths(changed_paths),
        "implementation_changes": implementation_changes,
        "active_units": [unit.as_posix() for unit in units],
        "backlog": [asdict(item) for item in backlog],
        "findings": [asdict(finding) for finding in findings],
        "tooling": {"runtime": runtime, "ocr": ocr_health()},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root_pos", nargs="?", default=None, help="Repository root (positional; same as --root)")
    parser.add_argument("--root", default=".", help="Repository root to inspect")
    parser.add_argument("--json", action="store_true", help="Print machine-readable output")
    args = parser.parse_args()

    root = args.root_pos or args.root
    report = diagnose(Path(root))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"CodeStable doctor: {report['status']}")
        print(f"Next action: {report['next_action']}")
        for finding in report["findings"]:
            path = f" ({finding['path']})" if finding.get("path") else ""
            print(f"- {finding['severity']}: {finding['message']}{path}")
        ocr = report["tooling"]["ocr"]
        ocr_hint = f" — {ocr['hint']}" if ocr.get("hint") else ""
        runtime = report["tooling"]["runtime"]
        runtime_hint = f" — {runtime['hint']}" if runtime.get("hint") else ""
        print(f"Runtime assets: {runtime['status']}{runtime_hint}")
        print(f"OCR tool: {ocr['status']}{ocr_hint}")

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
