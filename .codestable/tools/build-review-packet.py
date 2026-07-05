#!/usr/bin/env python3
"""Build a redacted packet for staged Task agent review."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from codestable_common import (
    git_status,
    git_output,
    is_secret_like_path,
    redact_text,
    resolve_unit,
)


STAGE_BRIEFS = {
    "implementation": {
        "title": "Implementation Review",
        "mission": (
            "Review the implementation as an independent Task agent. Verify the code directly from "
            "the packet instead of trusting the implementer summary."
        ),
        "focus": (
            "scope drift, hidden behavior changes, missing tests, maintainability, edge cases, "
            "security, and production safety"
        ),
    },
    "spec": {
        "title": "Spec Compliance Review",
        "mission": (
            "Check whether the implementation built exactly what the approved requirement, report, "
            "analysis, design, or checklist requested."
        ),
        "focus": (
            "missing requested behavior, extra unrequested behavior, changed acceptance criteria, "
            "scope drift, and mismatches between unit docs and code"
        ),
    },
    "quality": {
        "title": "Code Quality Review",
        "mission": (
            "Check whether the code is clean, tested, maintainable, secure, and robust under real "
            "project conditions."
        ),
        "focus": (
            "maintainability, readability, coupling, security, edge cases, test gaps, performance, "
            "idempotency, crash-resume behavior, and deterministic boundaries"
        ),
    },
    "verification": {
        "title": "Verification Evidence Review",
        "mission": (
            "Check fresh validation evidence. Do not accept remembered claims, unstated commands, "
            "or summaries without command output or directly inspectable evidence."
        ),
        "focus": (
            "test/build/type/lint output, CLI smoke evidence, browser/runtime evidence when relevant, "
            "failed or skipped commands, and whether evidence matches the acceptance criteria"
        ),
    },
}

RISK_PROMPTS = (
    "database and migration safety",
    "concurrency and race conditions",
    "idempotency and rerun behavior",
    "crash-resume persistence",
    "provider cost and production writes",
    "deterministic LLM boundary for IDs, paths, enums, and foreign keys",
)
MAX_UNTRACKED_FILE_BYTES = 64 * 1024


def read_safe(path: Path, display_path: str | None = None) -> str:
    if not path.exists() or not path.is_file():
        return ""
    if is_secret_like_path(display_path or path.as_posix()):
        return "[REDACTED secret-like file omitted]\n"
    if path.stat().st_size > MAX_UNTRACKED_FILE_BYTES:
        return "[large file omitted]\n"
    try:
        return redact_text(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        return "[binary or non-utf8 file omitted]\n"


def unit_documents(root: Path, unit_dir: Path) -> list[Path]:
    unit_root = root / unit_dir
    if not unit_root.exists():
        return []
    return sorted(
        path
        for path in unit_root.iterdir()
        if path.is_file() and path.suffix.lower() in {".md", ".yaml", ".yml"}
    )


def stage_brief(stage: str) -> dict[str, str]:
    if stage not in STAGE_BRIEFS:
        raise ValueError(f"unknown review stage: {stage}")
    return STAGE_BRIEFS[stage]


def normalize_validations(validations: list[str]) -> list[str]:
    return [item.strip() for item in validations if item.strip()]


def build_packet(root: Path, unit_value: str, validations: list[str], stage: str = "implementation") -> str:
    brief = stage_brief(stage)
    validations = normalize_validations(validations)
    if stage == "verification" and not validations:
        raise ValueError("verification stage requires at least one --validation or --validation-file entry")

    root = root.resolve()
    unit_dir = resolve_unit(root, unit_value)
    changed = git_status(root)
    changed_paths = [item.path for item in changed]
    untracked_paths = [item.path for item in changed if item.status == "??"]
    safe_diff_paths = [path for path in changed_paths if not is_secret_like_path(path)]
    omitted_paths = [path for path in changed_paths if is_secret_like_path(path)]

    lines: list[str] = [
        f"# CodeStable {brief['title']} Packet",
        "",
        f"- root: `{root.as_posix()}`",
        f"- unit: `{unit_dir.as_posix()}`",
        f"- stage: `{stage}`",
        "",
        "## Reviewer Mission",
        "",
        brief["mission"],
        "",
        "## Stage Focus",
        "",
        brief["focus"],
        "",
        "## Reviewer Output Contract",
        "",
        "- Lead with findings, ordered by severity.",
        "- Include severity (`P0`/`P1`/`P2`/`P3`) and confidence for each finding.",
        "- Reference concrete files, code, docs, or validation evidence when possible.",
        "- If there are no blocking findings, say so explicitly and list residual risks or test gaps.",
        "",
        "## Unit Documents",
    ]

    docs = unit_documents(root, unit_dir)
    if not docs:
        lines.append("No unit documents found.")
    for doc in docs:
        rel = doc.relative_to(root).as_posix()
        lines.extend([f"### `{rel}`", "", "```", read_safe(doc, rel).rstrip(), "```", ""])

    lines.extend(["## Git Diff Stat", "", "```"])
    unstaged_stat = git_output(root, "diff", "--stat")
    staged_stat = git_output(root, "diff", "--cached", "--stat")
    lines.append("### unstaged")
    lines.append(unstaged_stat or "No unstaged diff.")
    lines.append("")
    lines.append("### staged")
    lines.append(staged_stat or "No staged diff.")
    lines.extend(["```", "", "## Focused Diff", ""])
    if safe_diff_paths:
        unstaged_diff = redact_text(git_output(root, "diff", "--", *safe_diff_paths))
        staged_diff = redact_text(git_output(root, "diff", "--cached", "--", *safe_diff_paths))
        lines.extend(["### Unstaged", "", "```diff", unstaged_diff or "No unstaged diff.", "```"])
        lines.extend(["", "### Staged", "", "```diff", staged_diff or "No staged diff.", "```"])
        safe_untracked = [path for path in untracked_paths if not is_secret_like_path(path)]
        if safe_untracked:
            lines.extend(["", "### Untracked Files", ""])
            for path in safe_untracked:
                lines.extend([f"#### `{path}`", "", "```", read_safe(root / path, path).rstrip(), "```", ""])
    else:
        lines.append("No safe changed paths to diff.")
    if omitted_paths:
        lines.extend(["", "Omitted secret-like paths:", *[f"- `{path}`" for path in omitted_paths]])

    lines.extend(["", "## Validation Commands And Results"])
    if validations:
        lines.extend(f"- {redact_text(item)}" for item in validations)
    else:
        lines.append("No validation commands/results supplied by owner.")

    lines.extend(["", "## Reviewer Risk Prompts"])
    lines.extend(f"- Check {prompt}." for prompt in RISK_PROMPTS)
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--unit", required=True, help="CodeStable unit path or slug")
    parser.add_argument("--output", required=True, help="Output Markdown file")
    parser.add_argument(
        "--stage",
        choices=sorted(STAGE_BRIEFS),
        default="implementation",
        help="Review stage to shape reviewer instructions",
    )
    parser.add_argument(
        "--validation",
        action="append",
        default=[],
        help="Validation command/result line to include; repeat as needed",
    )
    parser.add_argument(
        "--validation-file",
        action="append",
        default=[],
        help="Text file containing validation command/results to include; repeat as needed",
    )
    args = parser.parse_args()

    try:
        validations = list(args.validation)
        for validation_file in args.validation_file:
            validations.append(Path(validation_file).read_text(encoding="utf-8"))
        packet = build_packet(Path(args.root), args.unit, validations, args.stage)
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
