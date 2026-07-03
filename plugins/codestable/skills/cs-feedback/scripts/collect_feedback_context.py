#!/usr/bin/env python3
"""Collect local Codex/Claude history snippets for CodeStable feedback."""

from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


CS_PATTERN = re.compile(r"(?:\b(?:cs-[a-z0-9-]+|codestable)\b|\.codestable\b|/goal\b)", re.IGNORECASE)
FAILURE_PATTERN = re.compile(
    r"(failed|failure|error|exception|traceback|timeout|timed out|permission|denied|not found|"
    r"no such file|tool call|apply_patch|file read|read failed|mcp|paseo|gh issue|git clone|early EOF)",
    re.IGNORECASE,
)
USER_CORRECTION_PATTERN = re.compile(
    r"(不对|不是|应该|你没有|你刚才|绕|错|确认后|没有用|没用|wrong|should have|"
    r"you didn't|not what|instead)",
    re.IGNORECASE,
)
SECRET_PATTERN = re.compile(
    r"(?i)(api[_-]?key|token|secret|password|authorization|bearer)\s*[:=]\s*['\"]?([A-Za-z0-9._~+/=-]{8,})"
)


@dataclass
class Event:
    provider: str
    session: str
    path: str
    timestamp: str
    kind: str
    score: int
    reasons: list[str]
    text: str
    context: list[str]


@dataclass(frozen=True)
class Candidate:
    path: str
    provider: str
    session: str
    cwd: str
    mtime: float
    score: int


def redact(text: str, limit: int = 1200) -> str:
    text = SECRET_PATTERN.sub(lambda match: f"{match.group(1)}=<redacted>", text)
    text = re.sub(r"sk-[A-Za-z0-9]{20,}", "sk-<redacted>", text)
    text = re.sub(r"gh[pousr]_[A-Za-z0-9_]{20,}", "gh_<redacted>", text)
    text = text.replace("\x00", "")
    if len(text) > limit:
        return text[:limit] + "...<truncated>"
    return text


def flatten(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(flatten(item) for item in value)
    if isinstance(value, dict):
        parts: list[str] = []
        for key in ("message", "text", "output", "content", "arguments", "name", "type", "role"):
            if key in value:
                parts.append(flatten(value[key]))
        if parts:
            return "\n".join(part for part in parts if part)
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def event_text(record: dict[str, Any]) -> str:
    payload = record.get("payload", record)
    return flatten(payload)


def event_kind(record: dict[str, Any]) -> str:
    payload = record.get("payload")
    if isinstance(payload, dict):
        for key in ("type", "name", "role"):
            if payload.get(key):
                return str(payload[key])
    return str(record.get("type", "unknown"))


def score_text(text: str, feedback: str) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    combined = f"{feedback}\n{text}"
    if CS_PATTERN.search(combined):
        score += 2
        reasons.append("codestable")
    if FAILURE_PATTERN.search(text):
        score += 3
        reasons.append("failure")
    if USER_CORRECTION_PATTERN.search(text):
        score += 3
        reasons.append("user-correction")
    for token in re.findall(r"[A-Za-z0-9_-]{4,}", feedback):
        if token.lower() in text.lower():
            score += 1
            if "feedback-token" not in reasons:
                reasons.append("feedback-token")
    return score, reasons


def normalize_json_records(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item if isinstance(item, dict) else {"payload": item} for item in value]
    if not isinstance(value, dict):
        return [{"payload": value}]

    collection_keys = ("messages", "events", "entries", "items", "transcript")
    records: list[dict[str, Any]] = []
    meta = {key: item for key, item in value.items() if key not in collection_keys}
    if meta:
        records.append(meta)
    for key in collection_keys:
        items = value.get(key)
        if not isinstance(items, list):
            continue
        for item in items:
            records.append(item if isinstance(item, dict) else {"payload": item})
    return records or [value]


def read_records(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".json":
        try:
            value = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
        except json.JSONDecodeError:
            return []
        return normalize_json_records(value)

    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                records.append(value)
    return records


def session_id_from(path: Path, records: list[dict[str, Any]]) -> str:
    for record in records:
        payload = record.get("payload")
        if isinstance(payload, dict):
            session_id = payload.get("session_id") or payload.get("sessionId") or payload.get("id")
            if session_id:
                return str(session_id)
        session_id = record.get("session_id") or record.get("sessionId") or record.get("sessionid") or record.get("id")
        if session_id:
            return str(session_id)
    return path.stem


def cwd_from(records: list[dict[str, Any]]) -> str:
    for record in records:
        payload = record.get("payload")
        if isinstance(payload, dict) and payload.get("cwd"):
            return str(payload["cwd"])
        if record.get("cwd"):
            return str(record["cwd"])
    return ""


def provider_from_path(path: Path) -> str:
    text = str(path)
    if ".codex" in text:
        return "codex"
    if ".claude" in text:
        return "claude"
    return "unknown"


def collect_file(path: Path, feedback: str, max_events: int, context_window: int) -> list[Event]:
    records = read_records(path)
    if not records:
        return []
    provider = provider_from_path(path)
    session = session_id_from(path, records)
    texts = [redact(event_text(record), limit=800) for record in records]
    events: list[Event] = []
    for index, record in enumerate(records):
        text = texts[index]
        score, reasons = score_text(text, feedback)
        if score < 3:
            continue
        start = max(0, index - context_window)
        end = min(len(texts), index + context_window + 1)
        timestamp = str(record.get("timestamp") or record.get("created_at") or "")
        events.append(
            Event(
                provider=provider,
                session=session,
                path=str(path),
                timestamp=timestamp,
                kind=event_kind(record),
                score=score,
                reasons=reasons,
                text=text,
                context=[texts[pos] for pos in range(start, end)],
            )
        )
    events.sort(key=lambda event: event.score, reverse=True)
    return events[:max_events]


def candidate_for(path: Path, cwd: str | None) -> Candidate:
    records = read_records(path)
    session = session_id_from(path, records)
    transcript_cwd = cwd_from(records)
    score = 0
    if cwd and transcript_cwd == cwd:
        score += 5
    elif cwd and transcript_cwd and (cwd.startswith(transcript_cwd) or transcript_cwd.startswith(cwd)):
        score += 2
    score += int(path.stat().st_mtime // 60)
    return Candidate(
        path=str(path),
        provider=provider_from_path(path),
        session=session,
        cwd=transcript_cwd,
        mtime=path.stat().st_mtime,
        score=score,
    )


def resolve_current_session(files: list[Path], cwd: str | None) -> tuple[list[Path], list[Candidate]]:
    candidates = [candidate_for(path, cwd) for path in files if path.suffix in {".jsonl", ".json"}]
    candidates.sort(key=lambda candidate: candidate.score, reverse=True)
    if not candidates:
        return [], []
    best = candidates[0]
    near = [
        candidate
        for candidate in candidates
        if candidate.score >= best.score - 2 and (not cwd or not candidate.cwd or candidate.cwd == best.cwd)
    ][:5]
    if len(near) == 1:
        return [Path(best.path)], []
    return [], near


def discover_files(
    home: Path,
    since_days: int,
    session_filter: str | None,
    cwd: str | None,
) -> tuple[list[Path], list[Candidate]]:
    roots = [
        home / ".codex/sessions",
        home / ".claude/projects",
        home / ".claude/sessions",
    ]
    if session_filter and session_filter != "current":
        candidate = Path(session_filter).expanduser()
        if candidate.is_file():
            return [candidate], []
    cutoff = time.time() - since_days * 86400
    files: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".jsonl", ".json"}:
                continue
            if path.stat().st_mtime < cutoff:
                continue
            if session_filter and session_filter != "current":
                if session_filter in path.name or session_filter in str(path):
                    files.append(path)
                    continue
                records = read_records(path)
                if session_filter not in session_id_from(path, records):
                    continue
            files.append(path)
    files = sorted(files)
    if session_filter == "current":
        return resolve_current_session(files, cwd)
    return files, []


def main_with_args_for_test(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feedback", default="", help="User's short feedback text")
    parser.add_argument("--since-days", type=int, default=3)
    parser.add_argument("--session", default=None, help="Session id substring or transcript path")
    parser.add_argument("--output", required=True)
    parser.add_argument("--history-root", default=None, help="Override home directory for tests")
    parser.add_argument("--cwd", default=None, help="Current working directory, used by --session current")
    parser.add_argument("--max-events-per-file", type=int, default=5)
    parser.add_argument("--context-window", type=int, default=2)
    args = parser.parse_args(argv)

    home = Path(args.history_root).expanduser() if args.history_root else Path.home()
    cwd = str(Path(args.cwd).expanduser()) if args.cwd else None
    files, ambiguity = discover_files(home, args.since_days, args.session, cwd)
    events: list[Event] = []
    for path in files:
        events.extend(collect_file(path, args.feedback, args.max_events_per_file, args.context_window))
    events.sort(key=lambda event: (event.score, event.timestamp), reverse=True)

    payload = {
        "feedback": args.feedback,
        "since_days": args.since_days,
        "session_filter": args.session,
        "history_root": str(home),
        "cwd": cwd,
        "searched_files": [str(path) for path in files],
        "ambiguity": {"candidates": [asdict(candidate) for candidate in ambiguity]},
        "matched_events": [asdict(event) for event in events],
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


def main() -> int:
    return main_with_args_for_test()


if __name__ == "__main__":
    raise SystemExit(main())
