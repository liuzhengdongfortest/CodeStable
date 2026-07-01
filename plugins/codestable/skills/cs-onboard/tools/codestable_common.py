#!/usr/bin/env python3
"""Shared helpers for CodeStable repository state tools."""

from __future__ import annotations

import json
import re
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


IMPLEMENTATION_PREFIXES = (
    "app/",
    "backend/",
    "client/",
    "frontend/",
    "lib/",
    "packages/",
    "scripts/",
    "server/",
    "src/",
    "supabase/migrations/",
    "test/",
    "tests/",
)

IMPLEMENTATION_SUFFIXES = (
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".css",
    ".go",
    ".h",
    ".hpp",
    ".html",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".scss",
    ".sh",
    ".sql",
    ".svelte",
    ".swift",
    ".ts",
    ".tsx",
    ".vue",
)

UNIT_ROOTS = ("features", "issues", "refactors")
IMPLEMENTATION_UNIT_ROOTS = frozenset(UNIT_ROOTS)
SUBAGENT_REVIEWERS = {"subagent", "subagent+ocr"}
KNOWN_SKILL_DIRS = {
    "browser-bridge",
    "codestable-maintainer",
    "cs",
    "cs-audit",
    "cs-brainstorm",
    "cs-code-review",
    "cs-doc-api",
    "cs-doc-tutorial",
    "cs-docs-neat",
    "cs-domain",
    "cs-feat",
    "cs-feat-accept",
    "cs-feat-design",
    "cs-feat-design-review",
    "cs-feat-ff",
    "cs-feat-impl",
    "cs-feat-qa",
    "cs-goal",
    "cs-issue",
    "cs-issue-analyze",
    "cs-issue-fix",
    "cs-issue-report",
    "cs-keep",
    "cs-note",
    "cs-onboard",
    "cs-refactor",
    "cs-refactor-ff",
    "cs-req",
    "cs-roadmap",
    "cs-roadmap-impl-goal",
    "cs-roadmap-review",
}


@dataclass(frozen=True)
class ChangedFile:
    status: str
    path: str


@dataclass(frozen=True)
class Finding:
    severity: str
    message: str
    path: str | None = None


@dataclass(frozen=True)
class BacklogItem:
    kind: str
    path: str
    line: int
    text: str


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def git_output(root: Path, *args: str) -> str:
    result = run_git(root, *args)
    if result.returncode != 0:
        return result.stderr.strip()
    return result.stdout.strip()


def git_status(root: Path, *extra_args: str) -> list[ChangedFile]:
    result = run_git(root, "status", "--porcelain", "-uall", *extra_args)
    if result.returncode != 0:
        return []

    changed: list[ChangedFile] = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        status = line[:2]
        raw_path = line[3:]
        if " -> " in raw_path:
            raw_path = raw_path.split(" -> ", 1)[1]
        changed.append(ChangedFile(status=status, path=raw_path.strip('"')))
    return changed


def staged_files(root: Path) -> list[ChangedFile]:
    result = run_git(root, "diff", "--cached", "--name-status")
    if result.returncode != 0:
        return []
    changed: list[ChangedFile] = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        status, _, path = line.partition("\t")
        if "\t" in path:
            path = path.rsplit("\t", 1)[-1]
        changed.append(ChangedFile(status=status, path=path))
    return changed


def current_branch(root: Path) -> str | None:
    result = run_git(root, "branch", "--show-current")
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def ref_exists(root: Path, ref: str) -> bool:
    return run_git(root, "rev-parse", "--verify", "--quiet", ref).returncode == 0


def ref_head(root: Path, ref: str) -> str | None:
    result = run_git(root, "rev-parse", "--verify", ref)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def default_branch(root: Path) -> str | None:
    origin_head = run_git(root, "symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD")
    if origin_head.returncode == 0:
        value = origin_head.stdout.strip()
        if value.startswith("origin/"):
            return value.split("/", 1)[1]
    for candidate in ("main", "master"):
        if ref_exists(root, candidate) or ref_exists(root, f"refs/heads/{candidate}"):
            return candidate
    return current_branch(root)


def is_linked_worktree(root: Path) -> bool:
    superproject = run_git(root, "rev-parse", "--show-superproject-working-tree")
    in_submodule = superproject.returncode == 0 and bool(superproject.stdout.strip())

    git_dir = run_git(root, "rev-parse", "--path-format=absolute", "--git-dir")
    common_dir = run_git(root, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if git_dir.returncode == 0 and common_dir.returncode == 0:
        git_dir_path = Path(git_dir.stdout.strip()).resolve()
        common_dir_path = Path(common_dir.stdout.strip()).resolve()
        if git_dir_path != common_dir_path and not in_submodule:
            return True

    return False


def is_implementation_path(path: str) -> bool:
    if path.startswith(".codestable/"):
        return False
    return path.startswith(IMPLEMENTATION_PREFIXES) or path.endswith(IMPLEMENTATION_SUFFIXES)


def path_bucket(path: str) -> str:
    if path.startswith(".codestable/"):
        return "codestable"
    first = Path(path).parts[0] if Path(path).parts else ""
    if first in KNOWN_SKILL_DIRS:
        return "installed_skill"
    if path.startswith("supabase/migrations/"):
        return "migrations"
    if path.startswith("docs/database/"):
        return "database_docs"
    if path.startswith(("data/input/", "data/output/")):
        return "data"
    if path.endswith((".log", ".jsonl")) or "/logs/" in path or path.startswith("logs/"):
        return "logs"
    if path.startswith(("docs/", "doc/")) or path.endswith(".md"):
        return "docs"
    if path.startswith("tests/") or path.startswith("test/"):
        return "tests"
    if is_implementation_path(path):
        return "code"
    return "unknown"


def is_secret_like_path(path: str) -> bool:
    lower = path.lower()
    name = Path(lower).name
    return name.startswith(".env") or "secret" in lower or "token" in lower or "credential" in lower


SECRET_QUOTED_VALUE_RE = re.compile(
    r"(?i)(token|api[_-]?key|secret|password|credential)(\s*[:=]\s*)(['\"])([^'\"\n]+)(['\"])"
)
SECRET_VALUE_RE = re.compile(
    r"(?i)(token|api[_-]?key|secret|password|credential)(\s*[:=]\s*)([^\s'\"`]+)"
)


def redact_text(text: str) -> str:
    text = SECRET_QUOTED_VALUE_RE.sub(r"\1\2\3[REDACTED]\5", text)
    text = SECRET_VALUE_RE.sub(r"\1\2[REDACTED]", text)
    text = re.sub(r"(?i)(bearer\s+)[a-z0-9._~+/=-]{12,}", r"\1[REDACTED]", text)
    text = re.sub(r"eyJ[a-zA-Z0-9_-]{12,}\.[a-zA-Z0-9_-]{12,}\.[a-zA-Z0-9_-]{12,}", "[REDACTED_JWT]", text)
    return text


def bucket_paths(paths: list[str]) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = {}
    for path in paths:
        buckets.setdefault(path_bucket(path), []).append(path)
    return {bucket: sorted(values) for bucket, values in sorted(buckets.items())}


def unit_dir_for(path: str) -> Path | None:
    parts = Path(path).parts
    if len(parts) < 3 or parts[0] != ".codestable" or parts[1] not in UNIT_ROOTS:
        return None
    return Path(*parts[:3])


def unit_slug(unit_dir: Path) -> str:
    return unit_dir.name.split("-", 3)[-1]


def review_file_for(unit_dir: Path) -> Path:
    return unit_dir / f"{unit_slug(unit_dir)}-review.md"


def all_checklist_steps_done(path: Path) -> bool:
    if not path.exists():
        return False

    in_steps = False
    saw_step = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if stripped == "steps:":
            in_steps = True
            continue
        if in_steps and stripped and not raw_line.startswith((" ", "-")):
            break
        if not in_steps:
            continue
        if stripped.startswith("- "):
            saw_step = True
        if stripped.startswith("status:"):
            _, _, value = stripped.partition(":")
            if value.strip() != "done":
                return False
    return saw_step


def unit_needs_review(root: Path, unit_dir: Path) -> bool:
    unit_root = root / unit_dir
    if not unit_root.exists():
        return False
    unit_type = unit_dir.parts[1]

    if unit_type == "features":
        return any(unit_root.glob("*-ff-note.md")) or any(
            all_checklist_steps_done(path) for path in unit_root.glob("*-checklist.yaml")
        )

    if unit_type == "issues":
        return any(unit_root.glob("*-fix-note.md"))

    if unit_type == "refactors":
        return any(unit_root.glob("*-apply-notes.md")) or any(
            all_checklist_steps_done(path) for path in unit_root.glob("*-checklist.yaml")
        )

    return False


def find_touched_units(changed: list[ChangedFile]) -> set[Path]:
    units: set[Path] = set()
    for item in changed:
        unit_dir = unit_dir_for(item.path)
        if unit_dir is not None:
            units.add(unit_dir)
    return units


def iter_units(root: Path) -> list[Path]:
    units: list[Path] = []
    codestable = root / ".codestable"
    for unit_root in UNIT_ROOTS:
        parent = codestable / unit_root
        if not parent.exists():
            continue
        units.extend(path.relative_to(root) for path in parent.iterdir() if path.is_dir())
    return sorted(units, key=lambda path: path.as_posix())


def review_has_subagent_evidence(path: Path) -> bool:
    if not path.exists():
        return False
    for line in path.read_text(encoding="utf-8").splitlines():
        key, sep, value = line.partition(":")
        if sep and key.strip().lower() == "reviewer" and value.strip().lower() in SUBAGENT_REVIEWERS:
            return True
    return False


def missing_review_findings(root: Path, units: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for unit_dir in units:
        if not unit_needs_review(root, unit_dir):
            continue
        review_path = review_file_for(unit_dir)
        full_review_path = root / review_path
        if not full_review_path.exists():
            findings.append(
                Finding(
                    severity="P1",
                    message="Completed CodeStable implementation unit is missing code review evidence ({slug}-review.md).",
                    path=review_path.as_posix(),
                )
            )
        elif not review_has_subagent_evidence(full_review_path):
            findings.append(
                Finding(
                    severity="P1",
                    message="CodeStable implementation review must use a Task agent reviewer.",
                    path=review_path.as_posix(),
                )
            )
    return findings


def resolve_unit(root: Path, value: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate.resolve().relative_to(root.resolve())
    if (root / candidate).exists():
        return candidate
    matches = [unit for unit in iter_units(root) if value in unit.name or value == unit_slug(unit)]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise ValueError(f"unit not found: {value}")
    raise ValueError(f"unit is ambiguous: {value}")


def is_implementation_unit(unit_dir: Path) -> bool:
    parts = unit_dir.parts
    return len(parts) >= 3 and parts[0] == ".codestable" and parts[1] in IMPLEMENTATION_UNIT_ROOTS


def override_file_for(root: Path, unit_dir: Path) -> Path:
    return root / unit_dir / "worktree-override.md"


def has_human_approved_override(root: Path, unit_dir: Path) -> bool:
    path = override_file_for(root, unit_dir)
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8").lower()
    return "reason" in text and "scope" in text and ("approved" in text or "approval" in text)


def baseline_id(unit_dir: Path) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", unit_dir.as_posix()).strip("_")


def baseline_path(root: Path, unit_dir: Path) -> Path:
    result = run_git(root, "rev-parse", "--git-path", f"codestable/worktree-gate/{baseline_id(unit_dir)}.json")
    if result.returncode == 0 and result.stdout.strip():
        return (root / result.stdout.strip()).resolve()
    return root / ".git" / "codestable" / "worktree-gate" / f"{baseline_id(unit_dir)}.json"


def write_baseline(root: Path, unit_dir: Path) -> dict[str, object]:
    branch = current_branch(root)
    default = default_branch(root)
    default_ref = default or branch or "HEAD"
    baseline = {
        "unit": unit_dir.as_posix(),
        "default_branch": default,
        "default_head": ref_head(root, default_ref),
        "current_branch": branch,
        "worktree": root.resolve().as_posix(),
        "linked_worktree": is_linked_worktree(root),
        "timestamp": int(time.time()),
    }
    path = baseline_path(root, unit_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(baseline, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return baseline


def read_baseline(root: Path, unit_dir: Path) -> dict[str, object] | None:
    path = baseline_path(root, unit_dir)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def iter_baselines(root: Path) -> list[dict[str, object]]:
    git_path = run_git(root, "rev-parse", "--git-path", "codestable/worktree-gate")
    if git_path.returncode != 0 or not git_path.stdout.strip():
        return []
    baseline_root = (root / git_path.stdout.strip()).resolve()
    if not baseline_root.exists():
        return []
    baselines: list[dict[str, object]] = []
    for path in sorted(baseline_root.glob("*.json")):
        try:
            baselines.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return baselines


def changed_paths_between(root: Path, base_ref: str, head_ref: str) -> list[str]:
    diff = run_git(root, "diff", "--name-only", f"{base_ref}..{head_ref}")
    if diff.returncode != 0:
        return []
    return [line.strip() for line in diff.stdout.splitlines() if line.strip()]


def post_baseline_implementation_changes(root: Path, baseline: dict[str, object]) -> list[str]:
    default = baseline.get("default_branch")
    default_head = baseline.get("default_head")
    if not default or not default_head:
        return []
    head = ref_head(root, str(default))
    if not head or head == default_head:
        return []
    return [
        path
        for path in changed_paths_between(root, str(default_head), str(default))
        if is_implementation_path(path)
    ]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_common_dir(root: Path) -> Path:
    result = run_git(root, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip()).resolve()
    return (root / ".git").resolve()


def inbox_dir(root: Path) -> Path:
    return git_common_dir(root) / "codestable" / "worktree-inbox"


def inbox_record_id(branch: str | None, unit_dir: Path | str | None) -> str:
    source = branch or (unit_dir.as_posix() if isinstance(unit_dir, Path) else str(unit_dir or "detached"))
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", source).strip("_") or "detached"


def inbox_record_path(root: Path, branch: str | None, unit_dir: Path | str | None) -> Path:
    return inbox_dir(root) / f"{inbox_record_id(branch, unit_dir)}.json"


def write_inbox_record(root: Path, record: dict[str, object]) -> Path:
    path = inbox_record_path(root, str(record.get("branch") or ""), str(record.get("unit") or ""))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def iter_inbox_records(root: Path) -> list[dict[str, object]]:
    directory = inbox_dir(root)
    if not directory.exists():
        return []
    records: list[dict[str, object]] = []
    for path in sorted(directory.glob("*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            record["_record_path"] = path.as_posix()
            records.append(record)
    return records


def branch_head(root: Path, branch: str) -> str | None:
    return ref_head(root, branch) or ref_head(root, f"refs/heads/{branch}")


def is_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    return run_git(root, "merge-base", "--is-ancestor", ancestor, descendant).returncode == 0


def worktree_map(root: Path) -> dict[str, dict[str, object]]:
    result = run_git(root, "worktree", "list", "--porcelain")
    if result.returncode != 0:
        return {}
    entries: dict[str, dict[str, object]] = {}
    current: dict[str, object] = {}
    for line in result.stdout.splitlines():
        if not line:
            if current.get("path"):
                entries[str(current["path"])] = current
            current = {}
            continue
        key, _, value = line.partition(" ")
        if key == "worktree":
            current["path"] = str(Path(value).resolve())
        elif key == "HEAD":
            current["head"] = value
        elif key == "branch":
            current["branch"] = value.removeprefix("refs/heads/")
        elif key == "detached":
            current["detached"] = True
    if current.get("path"):
        entries[str(current["path"])] = current
    return entries


BACKLOG_PATTERNS = (
    ("needs-human-review", re.compile(r"needs-human-review", re.IGNORECASE)),
    ("human-review", re.compile(r"human review required", re.IGNORECASE)),
    ("accepted-p2", re.compile(r"accepted.{0,40}P2|P2.{0,40}accepted", re.IGNORECASE)),
    ("deferred-p2", re.compile(r"deferred.{0,40}P2|P2.{0,40}deferred", re.IGNORECASE)),
    ("follow-up", re.compile(r"^\s*(?:[-*]\s+|\d+\.\s+)?follow[- ]ups?(?:\s*:|\b)", re.IGNORECASE)),
)
ATTENTION_CANDIDATES_HEADING_RE = re.compile(r"attention\.md.{0,40}candidates?|candidates?.{0,40}attention\.md", re.IGNORECASE)
MARKDOWN_BULLET_RE = re.compile(r"^\s*[-*]\s+(.+)")
FOLLOW_UP_SECTION_HEADING_RE = re.compile(r"^\s*#{1,6}\s+follow[- ]ups?\s*$", re.IGNORECASE)
BACKLOG_SCAN_EXCLUDED_SUFFIXES = ("-review-packet.md",)
BACKLOG_SCAN_EXCLUDED_PREFIXES = (".codestable/reference/",)
FOLLOW_UP_BLOCKING_TEXT_MARKERS = (
    "before merge",
    "before publish",
    "before release",
    "before ship",
    "before completion",
    "blocking",
    "must",
    "required",
)
RESOLVED_FOLLOW_UP_RE = re.compile(
    r"(?:subagent review )?follow[- ]up(?:s)?(?:\s+(?:fix(?:es)?|review|evidence|implementation)|$)|"
    r"follow[- ]up(?:s)?.{0,40}(?:backlog|fixed;|passed after|was added before|has been fixed)|"
    r"passed after.{0,40}follow[- ]up|"
    r"after follow[- ]up fixes|"
    r"follow[- ]up.{0,80}(?:no (?:new )?(?:remaining )?p0|no (?:new )?(?:remaining )?p1|"
    r"no (?:new )?(?:remaining )?p2|closed|fixed|resolved|已修|无 p0|无 p1|无阻塞)",
    re.IGNORECASE,
)
CANCELED_UNIT_STATUSES = {"canceled", "cancelled", "abandoned"}
STATUS_RE = re.compile(r"^\s*status:\s*['\"]?([a-z0-9_-]+)['\"]?\s*$", re.IGNORECASE)


def should_scan_backlog_file(rel_path: str) -> bool:
    return not (
        rel_path.startswith(BACKLOG_SCAN_EXCLUDED_PREFIXES)
        or rel_path.endswith(BACKLOG_SCAN_EXCLUDED_SUFFIXES)
    )


def is_blocking_follow_up_text(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in FOLLOW_UP_BLOCKING_TEXT_MARKERS)


def is_resolved_backlog_match(kind: str, text: str) -> bool:
    if kind != "follow-up":
        return False
    if is_blocking_follow_up_text(text):
        return False
    return bool(RESOLVED_FOLLOW_UP_RE.search(text))


def unit_lifecycle_status_files(root: Path, unit_dir: Path) -> list[Path]:
    unit_root = root / unit_dir
    slug = unit_slug(unit_dir)
    names = (
        f"{slug}-acceptance.md",
        f"{slug}-ff-note.md",
        f"{slug}-fix-note.md",
        f"{slug}-apply-notes.md",
    )
    return [unit_root / name for name in names if (unit_root / name).exists()]


def file_has_canceled_status(path: Path) -> bool:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return False
    for line in lines:
        match = STATUS_RE.match(line)
        if match and match.group(1).lower() in CANCELED_UNIT_STATUSES:
            return True
    return False


def unit_has_canceled_lifecycle_status(root: Path, rel_path: str) -> bool:
    unit_dir = unit_dir_for(rel_path)
    if unit_dir is None:
        return False
    return any(file_has_canceled_status(path) for path in unit_lifecycle_status_files(root, unit_dir))


def scan_backlog(root: Path) -> list[BacklogItem]:
    codestable = root / ".codestable"
    if not codestable.exists():
        return []
    items: list[BacklogItem] = []
    for path in sorted(codestable.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".md", ".yaml", ".yml", ".txt"}:
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        rel_path = path.relative_to(root).as_posix()
        if not should_scan_backlog_file(rel_path):
            continue
        if unit_has_canceled_lifecycle_status(root, rel_path):
            continue
        in_attention_candidates = False
        in_follow_up_section = False
        for line_no, line in enumerate(lines, start=1):
            stripped = line.strip()
            if ATTENTION_CANDIDATES_HEADING_RE.search(stripped):
                in_attention_candidates = True
                continue
            if FOLLOW_UP_SECTION_HEADING_RE.search(stripped):
                in_follow_up_section = True
                continue
            if in_attention_candidates:
                if stripped.startswith("#"):
                    in_attention_candidates = False
                elif not stripped:
                    continue
                else:
                    bullet = MARKDOWN_BULLET_RE.match(line)
                    if bullet:
                        items.append(
                            BacklogItem(
                                kind="attention-candidate",
                                path=rel_path,
                                line=line_no,
                                text=bullet.group(1).strip(),
                            )
                        )
                    continue
            if in_follow_up_section:
                if stripped.startswith("#"):
                    in_follow_up_section = False
                else:
                    bullet = MARKDOWN_BULLET_RE.match(line)
                    if bullet:
                        text = bullet.group(1).strip()
                        items.append(
                            BacklogItem(
                                kind="follow-up",
                                path=rel_path,
                                line=line_no,
                                text=text,
                            )
                        )
                        continue
            for kind, pattern in BACKLOG_PATTERNS:
                if pattern.search(line):
                    if is_resolved_backlog_match(kind, stripped):
                        continue
                    items.append(BacklogItem(kind=kind, path=rel_path, line=line_no, text=stripped))
                    break
    return items


def unit_for_path(path: str) -> str | None:
    unit_dir = unit_dir_for(path)
    return unit_dir.as_posix() if unit_dir is not None else None


def has_secret_like_untracked(root: Path) -> list[str]:
    secret_paths: list[str] = []
    for item in git_status(root):
        if item.status != "??":
            continue
        lower = item.path.lower()
        name = Path(lower).name
        if name.startswith(".env") or "secret" in lower or "token" in lower:
            secret_paths.append(item.path)
    return sorted(secret_paths)


def tracked_ignored_paths(root: Path) -> list[str]:
    result = run_git(root, "ls-files", "-ci", "--exclude-standard")
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]
