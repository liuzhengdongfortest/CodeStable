#!/usr/bin/env python3
"""Build lightweight context packets for CodeStable stage handoffs and human reports."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from codestable_common import git_status, is_secret_like_path, redact_text, resolve_unit


MAX_LIST_ITEMS = 20
AUDIENCES = ("handoff", "human-reviewer", "owner-decision", "owner-judgment", "learner", "interviewee")

AUDIENCE_TITLES = {
    "en": {
        "handoff": "CodeStable Handoff Context",
        "human-reviewer": "CodeStable Human Reviewer Context",
        "owner-decision": "CodeStable Owner Decision Brief",
        "owner-judgment": "CodeStable Owner Judgment Context",
        "learner": "CodeStable Learning Report",
        "interviewee": "CodeStable Interview Context",
    },
    "zh": {
        "handoff": "CodeStable 交接上下文",
        "human-reviewer": "CodeStable 人审上下文报告",
        "owner-decision": "CodeStable Owner 决策简报",
        "owner-judgment": "CodeStable Owner 判断上下文",
        "learner": "CodeStable 学习报告",
        "interviewee": "CodeStable 访谈上下文",
    },
}

AUDIENCE_MISSIONS = {
    "en": {
        "human-reviewer": "Review the work using only this packet and the repository state it points to.",
        "owner-decision": "Decide whether the remaining risks and work are acceptable.",
        "owner-judgment": "Make the requested judgment using the decision context, tradeoffs, and evidence in this packet.",
        "learner": "Understand what changed, why it changed, and how to verify it later.",
        "interviewee": "Prepare a concise, evidence-backed explanation of the work.",
    },
    "zh": {
        "human-reviewer": "请只基于这份报告和它指向的仓库现状做人审，不依赖隐藏聊天历史。",
        "owner-decision": "请判断剩余风险和后续事项是否可以接受，或需要继续收敛。",
        "owner-judgment": "请基于这份上下文中的判断点、取舍和证据做出选择，不依赖隐藏聊天历史。",
        "learner": "用于理解这次工作为什么发生、改了什么、以后如何验证。",
        "interviewee": "用于准备一份有证据支撑的简洁讲述，不把细节埋在聊天记录里。",
    },
}


def format_items(items: list[str], empty: str = "None recorded.") -> list[str]:
    if not items:
        return [f"- {empty}"]
    lines = [f"- {redact_text(item)}" for item in items[:MAX_LIST_ITEMS]]
    if len(items) > MAX_LIST_ITEMS:
        lines.append(f"- ... {len(items) - MAX_LIST_ITEMS} more item(s) omitted.")
    return lines


def labels(language: str) -> dict[str, str]:
    if language == "zh":
        return {
            "decision_brief": "决策简报",
            "working_context": "工作上下文",
            "evidence_appendix": "证据附录",
            "objective": "目标",
            "decided": "已决定",
            "rejected": "已排除",
            "risks": "风险",
            "files": "相关文件",
            "remaining": "剩余事项",
            "evidence": "验证证据",
            "judgment_context": "判断上下文",
            "judgment_needed": "需要判断",
            "why_now": "为什么现在问",
            "terms": "术语",
            "options": "选项与取舍",
            "default_recommendation": "默认建议",
            "effects": "回答后的影响",
            "non_automatic": "不会自动执行的动作",
            "none": "未记录。",
        }
    return {
        "decision_brief": "Decision Brief",
        "working_context": "Working Context",
        "evidence_appendix": "Evidence Appendix",
        "objective": "Objective",
        "decided": "Decided",
        "rejected": "Rejected",
        "risks": "Risks",
        "files": "Files",
        "remaining": "Remaining",
        "evidence": "Evidence",
        "judgment_context": "Judgment Context",
        "judgment_needed": "Judgment Needed",
        "why_now": "Why Now",
        "terms": "Terms",
        "options": "Options And Tradeoffs",
        "default_recommendation": "Default Recommendation",
        "effects": "What Changes After The Answer",
        "non_automatic": "Actions That Remain Non-Automatic",
        "none": "None recorded.",
    }


def changed_files(root: Path) -> list[str]:
    paths = []
    for item in git_status(root):
        if is_secret_like_path(item.path):
            paths.append(f"{item.path} [redacted secret-like path]")
        else:
            paths.append(item.path)
    return sorted(paths)


def title_for(audience: str, language: str) -> str:
    return AUDIENCE_TITLES.get(language, AUDIENCE_TITLES["en"])[audience]


def mission_for(audience: str, language: str) -> str | None:
    return AUDIENCE_MISSIONS.get(language, AUDIENCE_MISSIONS["en"]).get(audience)


def build_handoff_packet(
    root: Path,
    unit_value: str,
    decided: list[str],
    rejected: list[str],
    risks: list[str],
    files: list[str],
    remaining: list[str],
    evidence: list[str],
) -> str:
    root = root.resolve()
    unit_dir = resolve_unit(root, unit_value)
    file_items = files or changed_files(root)

    lines: list[str] = [
        "# CodeStable Handoff Context",
        "",
        f"- root: `{root.as_posix()}`",
        f"- unit: `{unit_dir.as_posix()}`",
        "",
        "## Handoff",
        "",
        "- Decided:",
        *format_items(decided),
        "- Rejected:",
        *format_items(rejected),
        "- Risks:",
        *format_items(risks),
        "- Files:",
        *format_items(file_items),
        "- Remaining:",
        *format_items(remaining),
        "- Evidence:",
        *format_items(evidence),
        "",
    ]
    return "\n".join(lines)


def build_audience_report(
    root: Path,
    unit_value: str,
    audience: str,
    language: str,
    decided: list[str],
    rejected: list[str],
    risks: list[str],
    files: list[str],
    remaining: list[str],
    evidence: list[str],
    judgment: list[str] | None = None,
    why_now: list[str] | None = None,
    terms: list[str] | None = None,
    options: list[str] | None = None,
    default_recommendation: list[str] | None = None,
    effects: list[str] | None = None,
    non_automatic: list[str] | None = None,
) -> str:
    root = root.resolve()
    unit_dir = resolve_unit(root, unit_value)
    file_items = files or changed_files(root)
    text = labels(language)
    title = title_for(audience, language)
    mission = mission_for(audience, language)

    lines: list[str] = [
        f"# {title}",
        "",
        f"- root: `{root.as_posix()}`",
        f"- unit: `{unit_dir.as_posix()}`",
        f"- audience: `{audience}`",
        f"- language: `{language}`",
    ]
    if mission:
        lines.extend(["", f"> {mission}"])
    if audience == "owner-judgment":
        lines.extend(
            [
                "",
                f"## {text['judgment_context']}",
                "",
                f"### {text['judgment_needed']}",
                *format_items(judgment or [], text["none"]),
                "",
                f"### {text['why_now']}",
                *format_items(why_now or [], text["none"]),
                "",
                f"### {text['terms']}",
                *format_items(terms or [], text["none"]),
                "",
                f"### {text['options']}",
                *format_items(options or [], text["none"]),
                "",
                f"### {text['default_recommendation']}",
                *format_items(default_recommendation or [], text["none"]),
                "",
                f"### {text['effects']}",
                *format_items(effects or [], text["none"]),
                "",
                f"### {text['non_automatic']}",
                *format_items(non_automatic or [], text["none"]),
            ]
        )
    lines.extend(
        [
            "",
            f"## {text['decision_brief']}",
            "",
            f"### {text['objective']}",
            *format_items(remaining, text["none"]),
            "",
            f"### {text['decided']}",
            *format_items(decided, text["none"]),
            "",
            f"### {text['rejected']}",
            *format_items(rejected, text["none"]),
            "",
            f"## {text['working_context']}",
            "",
            f"### {text['risks']}",
            *format_items(risks, text["none"]),
            "",
            f"### {text['files']}",
            *format_items(file_items, text["none"]),
            "",
            f"### {text['remaining']}",
            *format_items(remaining, text["none"]),
            "",
            f"## {text['evidence_appendix']}",
            "",
            f"### {text['evidence']}",
            *format_items(evidence, text["none"]),
            "",
        ]
    )
    return "\n".join(lines)


def build_packet(
    root: Path,
    unit_value: str,
    audience: str,
    decided: list[str],
    rejected: list[str],
    risks: list[str],
    files: list[str],
    remaining: list[str],
    evidence: list[str],
    language: str = "en",
    judgment: list[str] | None = None,
    why_now: list[str] | None = None,
    terms: list[str] | None = None,
    options: list[str] | None = None,
    default_recommendation: list[str] | None = None,
    effects: list[str] | None = None,
    non_automatic: list[str] | None = None,
) -> str:
    if audience not in AUDIENCES:
        raise ValueError(f"unknown context audience: {audience}")
    if language not in {"en", "zh"}:
        raise ValueError(f"unknown context language: {language}")
    if audience == "handoff" and language != "en":
        raise ValueError("handoff context supports language=en only; use a human-report audience for zh output")
    if audience == "handoff":
        return build_handoff_packet(root, unit_value, decided, rejected, risks, files, remaining, evidence)
    return build_audience_report(
        root,
        unit_value,
        audience,
        language,
        decided,
        rejected,
        risks,
        files,
        remaining,
        evidence,
        judgment,
        why_now,
        terms,
        options,
        default_recommendation,
        effects,
        non_automatic,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--unit", required=True, help="CodeStable unit path or slug")
    parser.add_argument("--audience", choices=AUDIENCES, required=True, help="Context audience")
    parser.add_argument("--language", choices=["en", "zh"], default="en", help="Output language")
    parser.add_argument("--output", required=True, help="Output Markdown file")
    parser.add_argument("--decided", action="append", default=[], help="Decision to include; repeat as needed")
    parser.add_argument("--rejected", action="append", default=[], help="Rejected option to include; repeat as needed")
    parser.add_argument("--risk", action="append", default=[], help="Risk to include; repeat as needed")
    parser.add_argument("--file", action="append", default=[], help="File to include; defaults to current changed files")
    parser.add_argument("--remaining", action="append", default=[], help="Remaining work item; repeat as needed")
    parser.add_argument("--evidence", action="append", default=[], help="Evidence line to include; repeat as needed")
    parser.add_argument("--judgment", action="append", default=[], help="Owner judgment being requested; repeat as needed")
    parser.add_argument("--why-now", action="append", default=[], help="Why the judgment is needed now; repeat as needed")
    parser.add_argument("--term", action="append", default=[], help="Term definition for owner judgment context")
    parser.add_argument("--option", action="append", default=[], help="Option and tradeoff for owner judgment context")
    parser.add_argument("--default-recommendation", action="append", default=[], help="Recommended default and reason")
    parser.add_argument("--effect", action="append", default=[], help="What changes after the owner answers")
    parser.add_argument("--non-automatic", action="append", default=[], help="Action that remains non-automatic")
    args = parser.parse_args()

    try:
        packet = build_packet(
            Path(args.root),
            args.unit,
            args.audience,
            args.decided,
            args.rejected,
            args.risk,
            args.file,
            args.remaining,
            args.evidence,
            args.language,
            args.judgment,
            args.why_now,
            args.term,
            args.option,
            args.default_recommendation,
            args.effect,
            args.non_automatic,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(packet, encoding="utf-8")
    print(output.as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())
