from __future__ import annotations

from pathlib import Path

from codestable_common import git_output, git_status, is_secret_like_path, redact_text


MAX_UNTRACKED_FILE_BYTES = 64 * 1024
DEFAULT_VALIDATION_TAIL_LINES = 20
TRANSPORTS = ("portable", "workspace")
DOCUMENT_SUFFIXES = {".md", ".yaml", ".yml"}


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
        if path.is_file() and path.suffix.lower() in DOCUMENT_SUFFIXES
    )


def normalize_include_paths(root: Path, values: list[str]) -> list[Path]:
    root = root.resolve()
    normalized: list[Path] = []
    for value in values:
        candidate = Path(value)
        resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
        try:
            relative = resolved.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"include path escapes repository: {value}") from exc
        if relative == Path("."):
            raise ValueError(f"include path must not select repository root: {value}")
        if relative not in normalized:
            normalized.append(relative)
    return normalized


def path_is_selected(path: str | Path, include_paths: list[Path]) -> bool:
    candidate = Path(path)
    return any(candidate == allowed or allowed in candidate.parents for allowed in include_paths)


def validation_tail(value: str, max_lines: int) -> tuple[int, list[str]]:
    lines = value.strip().splitlines()
    return len(lines), lines[-max_lines:]


def selected_documents(root: Path, unit_dir: Path, include_paths: list[Path]) -> list[Path]:
    selected = [
        path
        for path in unit_documents(root, unit_dir)
        if path_is_selected(path.relative_to(root), include_paths)
    ]
    for relative in include_paths:
        path = root / relative
        if path.is_file() and path.suffix.lower() in DOCUMENT_SUFFIXES and path not in selected:
            selected.append(path)
    return sorted(selected)


def packet_preamble(
    brief: dict[str, str],
    root: Path,
    unit_dir: Path,
    stage: str,
    title: str,
) -> list[str]:
    return [
        f"# CodeStable {brief['title']} {title}",
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
    ]


def build_workspace_packet(
    root: Path,
    unit_dir: Path,
    validations: list[str],
    stage: str,
    include_paths: list[Path],
    brief: dict[str, str],
    risk_prompts: tuple[str, ...],
) -> str:
    changed_paths = [
        item.path
        for item in git_status(root)
        if path_is_selected(item.path, include_paths) and not is_secret_like_path(item.path)
    ]
    input_locators = list(include_paths)
    for doc in selected_documents(root, unit_dir, include_paths):
        relative = doc.relative_to(root)
        if relative not in input_locators:
            input_locators.append(relative)
    lines = packet_preamble(brief, root, unit_dir, stage, "Workspace Packet")
    lines.extend(["", "## Selected Input Locators", ""])
    lines.extend(f"- `{path.as_posix()}`" for path in input_locators)
    lines.extend(["", "## Selected Changed Paths", ""])
    lines.extend(f"- `{path}`" for path in changed_paths)
    if not changed_paths:
        lines.append("- none")
    lines.extend(["", "## Validation References", ""])
    if validations:
        for index, validation in enumerate(validations, start=1):
            count, tail = validation_tail(validation, 1)
            summary = redact_text(tail[-1] if tail else "").replace("`", "'")
            lines.append(f"- validation {index}: {count} lines; tail: {summary}")
    else:
        lines.append("- none supplied by owner")
    lines.extend(["", "## Reviewer Risk Prompts"])
    lines.extend(f"- Check {prompt}." for prompt in risk_prompts)
    lines.append("")
    return "\n".join(lines)


def build_scoped_portable_packet(
    root: Path,
    unit_dir: Path,
    validations: list[str],
    stage: str,
    include_paths: list[Path],
    validation_tail_lines: int,
    brief: dict[str, str],
    risk_prompts: tuple[str, ...],
) -> str:
    changed = [item for item in git_status(root) if path_is_selected(item.path, include_paths)]
    safe_paths = [item.path for item in changed if not is_secret_like_path(item.path)]
    omitted_paths = [item.path for item in changed if is_secret_like_path(item.path)]
    safe_untracked = [item.path for item in changed if item.status == "??" and item.path in safe_paths]
    lines = packet_preamble(brief, root, unit_dir, stage, "Scoped Portable Packet")
    lines.extend(["", "## Selected Unit Documents"])
    docs = selected_documents(root, unit_dir, include_paths)
    if not docs:
        lines.append("No selected unit documents found.")
    for doc in docs:
        rel = doc.relative_to(root).as_posix()
        lines.extend([f"### `{rel}`", "", "```", read_safe(doc, rel).rstrip(), "```", ""])

    lines.extend(["## Selected Git Diff Stat", "", "```", "### unstaged"])
    lines.append(git_output(root, "diff", "--stat", "--", *safe_paths) if safe_paths else "No unstaged diff.")
    lines.extend(["", "### staged"])
    lines.append(git_output(root, "diff", "--cached", "--stat", "--", *safe_paths) if safe_paths else "No staged diff.")
    lines.extend(["```", "", "## Selected Focused Diff", ""])
    if safe_paths:
        unstaged_diff = redact_text(git_output(root, "diff", "--", *safe_paths))
        staged_diff = redact_text(git_output(root, "diff", "--cached", "--", *safe_paths))
        lines.extend(["### Unstaged", "", "```diff", unstaged_diff or "No unstaged diff.", "```"])
        lines.extend(["", "### Staged", "", "```diff", staged_diff or "No staged diff.", "```"])
        if safe_untracked:
            lines.extend(["", "### Untracked Files", ""])
            for path in safe_untracked:
                lines.extend([f"#### `{path}`", "", "```", read_safe(root / path, path).rstrip(), "```", ""])
    else:
        lines.append("No selected safe changed paths to diff.")
    if omitted_paths:
        lines.extend(["", "Omitted secret-like paths:", *[f"- `{path}`" for path in omitted_paths]])

    lines.extend(["", "## Validation Commands And Results"])
    if validations:
        for index, validation in enumerate(validations, start=1):
            count, tail = validation_tail(validation, validation_tail_lines)
            lines.extend(
                [
                    f"### Validation {index} ({count} lines; showing last {len(tail)})",
                    "",
                    "```text",
                    redact_text("\n".join(tail)),
                    "```",
                ]
            )
    else:
        lines.append("No validation commands/results supplied by owner.")
    lines.extend(["", "## Reviewer Risk Prompts"])
    lines.extend(f"- Check {prompt}." for prompt in risk_prompts)
    lines.append("")
    return "\n".join(lines)
