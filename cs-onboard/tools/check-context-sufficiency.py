#!/usr/bin/env python3
"""Check whether a CodeStable context packet has enough explicit context."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from codestable_common import redact_text


HANDOFF_LABELS = ("Decided", "Rejected", "Risks", "Files", "Remaining", "Evidence")
AUDIENCE_REPORT_SECTIONS = (
    ("Decision Brief", "决策简报"),
    ("Working Context", "工作上下文"),
    ("Evidence Appendix", "证据附录"),
)
FILE_HEADINGS = ("Files", "相关文件")
EVIDENCE_HEADINGS = ("Evidence", "验证证据")
OWNER_JUDGMENT_REQUIRED_SECTIONS = {
    "missing_judgment": ("Judgment Needed", "需要判断"),
    "missing_why_now": ("Why Now", "为什么现在问"),
    "missing_terms": ("Terms", "术语"),
    "missing_options": ("Options And Tradeoffs", "选项与取舍"),
    "missing_default_recommendation": ("Default Recommendation", "默认建议"),
    "missing_effects": ("What Changes After The Answer", "回答后的影响"),
    "missing_non_automatic": ("Actions That Remain Non-Automatic", "不会自动执行的动作"),
}
EMPTY_MARKERS = {"None recorded.", "未记录。"}
BARE_SECRET_TOKEN_RE = re.compile(
    r"(?i)(?:"
    r"\bsk-(?:proj-)?[a-z0-9_-]{20,}\b|"
    r"\bgh[pousr]_[a-z0-9_]{20,}\b"
    r")"
)


def has_heading(text: str, names: tuple[str, ...]) -> bool:
    for name in names:
        if re.search(rf"^\s*#+\s+{re.escape(name)}\s*$", text, re.MULTILINE):
            return True
    return False


def has_label(text: str, label: str) -> bool:
    return bool(re.search(rf"^\s*-\s+{re.escape(label)}:\s*$", text, re.MULTILINE))


def section_items(text: str, headings: tuple[str, ...]) -> list[str]:
    escaped = "|".join(re.escape(heading) for heading in headings)
    match = re.search(rf"^\s*#+\s+(?:{escaped})\s*$", text, re.MULTILINE)
    label_mode = False
    if not match:
        match = re.search(rf"^\s*-\s+(?:{escaped}):\s*$", text, re.MULTILINE)
        label_mode = True
    if not match:
        return []
    lines = text[match.end() :].splitlines()
    items: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            break
        if label_mode and re.match(r"^-\s+[^:]+:\s*$", stripped):
            break
        if stripped.startswith("- "):
            item = stripped[2:].strip()
            if item not in EMPTY_MARKERS:
                items.append(item)
    return items


def detect_shape(text: str) -> str | None:
    if "## Handoff" in text and all(has_label(text, label) for label in HANDOFF_LABELS):
        return "handoff"
    if all(has_heading(text, section) for section in AUDIENCE_REPORT_SECTIONS):
        return "audience-report"
    return None


def packet_audience(text: str) -> str | None:
    match = re.search(r"^\s*-\s+audience:\s+`([^`]+)`\s*$", text, re.MULTILINE)
    if not match:
        return None
    return match.group(1)


def has_unredacted_secret_like_text(text: str) -> bool:
    return redact_text(text) != text or bool(BARE_SECRET_TOKEN_RE.search(text))


def check_packet(path: Path, strict: bool = False) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    findings: list[dict[str, str]] = []
    shape = detect_shape(text)

    if shape is None:
        findings.append(
            {
                "severity": "P1",
                "code": "unknown_context_shape",
                "message": "Packet is missing the required handoff labels or audience report sections.",
            }
        )

    if has_unredacted_secret_like_text(text):
        findings.append(
            {
                "severity": "P1",
                "code": "unredacted_secret_like_text",
                "message": "Packet appears to contain secret-like text that should be redacted first.",
            }
        )

    if strict:
        if not section_items(text, FILE_HEADINGS):
            findings.append(
                {
                    "severity": "P1",
                    "code": "missing_files",
                    "message": "Strict context checks require at least one concrete file reference.",
                }
            )
        if not section_items(text, EVIDENCE_HEADINGS):
            findings.append(
                {
                    "severity": "P1",
                    "code": "missing_evidence",
                    "message": "Strict context checks require at least one evidence item.",
                }
            )
        if packet_audience(text) == "owner-judgment":
            for code, headings in OWNER_JUDGMENT_REQUIRED_SECTIONS.items():
                if not section_items(text, headings):
                    findings.append(
                        {
                            "severity": "P1",
                            "code": code,
                            "message": f"Owner judgment context requires a non-empty {'/'.join(headings)} section.",
                        }
                    )

    return {
        "ok": not findings,
        "file": path.as_posix(),
        "shape": shape,
        "strict": strict,
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", required=True, help="Context packet Markdown file")
    parser.add_argument("--strict", action="store_true", help="Require concrete Files and Evidence entries")
    parser.add_argument("--json", action="store_true", help="Print machine-readable output")
    args = parser.parse_args()

    payload = check_packet(Path(args.file), args.strict)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"OK: {payload['ok']}")
        print(f"Shape: {payload['shape']}")
        for finding in payload["findings"]:
            print(f"- {finding['severity']} {finding['code']}: {finding['message']}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
