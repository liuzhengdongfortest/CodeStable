#!/usr/bin/env python3
"""Deterministic helpers for CodeStable spec routing, deltas, and drift checks."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

from codestable_common import git_status, resolve_unit, unit_slug

try:
    import yaml  # type: ignore

    HAS_YAML = True
except ImportError:
    HAS_YAML = False


SPEC_DIRS = (
    ".codestable/requirements",
    ".codestable/architecture",
    ".codestable/roadmap",
    ".codestable/decisions",
)
REHABILITATION_STATES = {
    "current-trusted",
    "current-unreviewed",
    "drift-suspected",
    "historical",
    "superseded",
    "orphaned",
}
LOCAL_SKIP_TERMS = (
    "frontend-only display tweak",
    "small ui",
    "ui tweak",
    "typo",
    "internal crawler retry",
    "local refactor",
)


def parse_scalar(value: str) -> object:
    raw = value.strip()
    if raw.startswith("[") and raw.endswith("]"):
        return [item.strip().strip("'\"") for item in raw[1:-1].split(",") if item.strip()]
    lower = raw.lower()
    if lower in {"true", "yes"}:
        return True
    if lower in {"false", "no"}:
        return False
    if lower in {"null", "~", ""}:
        return None
    return raw.strip("'\"")


def parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    raw = text[3:end].strip()
    body = text[end + 4 :].strip()
    if HAS_YAML:
        try:
            parsed = yaml.safe_load(raw)
            if isinstance(parsed, dict):
                return parsed, body
        except yaml.YAMLError:
            pass
    meta: dict[str, object] = {}
    current_key: str | None = None
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        stripped = line.strip()
        if stripped.startswith("- ") and current_key:
            if not isinstance(meta.get(current_key), list):
                meta[current_key] = []
            meta[current_key].append(stripped[2:].strip().strip("'\""))  # type: ignore[union-attr]
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        current_key = key.strip()
        meta[current_key] = parse_scalar(value)
    return meta, body


def as_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)] if str(value).strip() else []


def slug_from_path(path: Path, meta: dict[str, object]) -> str:
    slug = meta.get("slug")
    if slug:
        return str(slug)
    return path.stem


def load_specs(root: Path) -> list[dict[str, object]]:
    specs: list[dict[str, object]] = []
    for directory in SPEC_DIRS:
        parent = root / directory
        if not parent.exists():
            continue
        for path in sorted(parent.rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            meta, body = parse_frontmatter(text)
            rel = path.relative_to(root).as_posix()
            specs.append(
                {
                    "path": rel,
                    "slug": slug_from_path(path, meta),
                    "kind": Path(directory).name,
                    "meta": meta,
                    "body": body,
                    "applies_when": as_list(meta.get("applies_when")),
                    "excludes_when": as_list(meta.get("excludes_when")),
                    "owner_review_state": str(meta.get("owner_review_state") or "current-unreviewed"),
                }
            )
    return specs


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", value.lower()).strip()


def phrase_matches(query: str, phrase: str) -> bool:
    normalized_query = normalize(query)
    normalized_phrase = normalize(phrase)
    if not normalized_phrase:
        return False
    if normalized_phrase in normalized_query:
        return True
    words = normalized_phrase.split()
    return bool(words) and all(word in normalized_query for word in words)


def phrase_overlap(query: str, phrase: str) -> bool:
    normalized_query = normalize(query)
    query_words = set(normalized_query.split())
    phrase_words = {word for word in normalize(phrase).split() if len(word) > 3}
    return bool(query_words & phrase_words)


def route_specs(root: Path, query: str) -> dict[str, object]:
    specs = load_specs(root)
    selected: list[dict[str, object]] = []
    excluded: list[dict[str, object]] = []
    for spec in specs:
        excluded_hits = [phrase for phrase in spec["excludes_when"] if phrase_matches(query, phrase)]  # type: ignore[index]
        if excluded_hits:
            excluded.append(
                {
                    "path": spec["path"],
                    "slug": spec["slug"],
                    "reason": f"excluded by {', '.join(excluded_hits)}",
                }
            )
            continue
        applies_hits = [phrase for phrase in spec["applies_when"] if phrase_matches(query, phrase)]  # type: ignore[index]
        partial_hits = [
            phrase
            for phrase in spec["applies_when"]  # type: ignore[index]
            if phrase not in applies_hits and phrase_overlap(query, phrase)
        ]
        slug_hit = phrase_matches(query, str(spec["slug"]).replace("-", " "))
        if applies_hits or partial_hits or slug_hit:
            score = len(applies_hits) * 10 + len(partial_hits) * 3 + (5 if slug_hit else 0)
            selected.append(
                {
                    "path": spec["path"],
                    "slug": spec["slug"],
                    "kind": spec["kind"],
                    "score": score,
                    "matched": applies_hits + [f"partial:{hit}" for hit in partial_hits] + (["slug"] if slug_hit else []),
                    "owner_review_state": spec["owner_review_state"],
                }
            )
    selected.sort(key=lambda item: (-int(item["score"]), str(item["path"])))
    local_skip = any(phrase_matches(query, term) for term in LOCAL_SKIP_TERMS)
    ambiguous = len(selected) > 1
    no_match = not selected
    needs_review = any(item.get("owner_review_state") in {"unreviewed", "current-unreviewed", "drift-suspected"} for item in selected)
    return {
        "ok": True,
        "query": query,
        "selected_specs": selected,
        "excluded_specs": excluded,
        "clarification_required": ambiguous or needs_review or (no_match and not local_skip),
        "allowed_to_skip_requirement_delta": local_skip,
        "next_action": next_action_for_route(selected, ambiguous, needs_review, local_skip),
    }


def next_action_for_route(selected: list[dict[str, object]], ambiguous: bool, needs_review: bool, local_skip: bool) -> str:
    if local_skip:
        return "Record a lightweight skip; do not create a requirement delta."
    if not selected:
        return "Ask owner which long-lived spec, if any, is canonical for this work."
    if ambiguous:
        return "Ask owner to choose the canonical spec before writing design or deltas."
    if needs_review:
        return "Clarify owner review state before mutating long-lived specs."
    return "Use the selected spec and continue with design or delta generation."


def content_write(path: Path, content: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def record_clarification(root: Path, file_value: str, question: str, answer: str, anchor: str | None) -> dict[str, object]:
    path = root / file_value
    if not path.exists():
        raise ValueError(f"spec file not found: {file_value}")
    text = path.read_text(encoding="utf-8")
    section = "\n\n## Clarifications\n" if "\n## Clarifications" not in text else ""
    entry = (
        f"\n- date: {date.today().isoformat()}\n"
        f"  question: {question}\n"
        f"  answer: {answer}\n"
        f"  anchor: {anchor or 'general'}\n"
    )
    changed = False
    if question not in text or answer not in text:
        text = text.rstrip() + section + entry
        changed = content_write(path, text.rstrip() + "\n")
    return {"ok": True, "file": file_value, "changed": changed}


def delta_path_for(root: Path, unit_value: str) -> Path:
    unit = resolve_unit(root, unit_value)
    return root / unit / f"{unit_slug(unit)}-req-delta.md"


def create_delta(
    root: Path,
    unit_value: str,
    requirement: str,
    added: list[str],
    modified: list[str],
    removed: list[str],
    scenarios: list[str],
    owner_decision: str,
) -> dict[str, object]:
    path = delta_path_for(root, unit_value)
    def list_items(values: list[str]) -> list[str]:
        return [f"- {item}" for item in values] if values else ["- None"]

    lines = [
        "---",
        "doc_type: requirement-delta",
        f"requirement: {requirement}",
        f"owner_decision: {owner_decision}",
        "---",
        "",
        "# Requirement Delta",
        "",
        "## ADDED Requirements",
        *list_items(added),
        "",
        "## MODIFIED Requirements",
        *list_items(modified),
        "",
        "## REMOVED Requirements",
        *list_items(removed),
        "",
        "## Scenarios",
        *list_items(scenarios),
        "",
        "## Owner Decision",
        f"- {owner_decision}",
        "",
    ]
    changed = content_write(path, "\n".join(lines))
    return {"ok": True, "path": path.relative_to(root).as_posix(), "changed": changed, "owner_decision": owner_decision}


def delta_is_approved(path: Path) -> bool:
    if not path.exists():
        return False
    meta, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
    return str(meta.get("owner_decision") or meta.get("status") or "").lower() == "approved"


def apply_delta(root: Path, delta_value: str, target_value: str) -> dict[str, object]:
    delta_path = root / delta_value
    target = root / target_value
    if not delta_is_approved(delta_path):
        return {"ok": False, "findings": [{"severity": "P1", "code": "delta_not_approved", "path": delta_value}]}
    if not target.exists():
        raise ValueError(f"target requirement not found: {target_value}")
    marker = f"Applied delta: {delta_value}"
    text = target.read_text(encoding="utf-8")
    changed = False
    if marker not in text:
        if "\n## Change Log" not in text:
            text = text.rstrip() + "\n\n## Change Log\n"
        text = text.rstrip() + f"\n\n- {date.today().isoformat()}: {marker}\n"
        changed = content_write(target, text)
    return {"ok": True, "target": target_value, "delta": delta_value, "changed": changed}


def classify_spec(spec: dict[str, object]) -> str:
    state = str(spec.get("owner_review_state") or "").lower()
    status = str(spec.get("meta", {}).get("status") if isinstance(spec.get("meta"), dict) else "").lower()
    if state in REHABILITATION_STATES:
        return state
    if state in {"current", "clarified"} and status == "current":
        return "current-trusted"
    if status in {"historical", "superseded", "orphaned"}:
        return status
    if state == "drift-suspected":
        return "drift-suspected"
    return "current-unreviewed"


def inventory(root: Path) -> dict[str, object]:
    items = []
    counts: dict[str, int] = {}
    for spec in load_specs(root):
        classification = classify_spec(spec)
        counts[classification] = counts.get(classification, 0) + 1
        items.append(
            {
                "path": spec["path"],
                "slug": spec["slug"],
                "kind": spec["kind"],
                "classification": classification,
                "owner_review_state": spec["owner_review_state"],
            }
        )
    return {"ok": True, "items": items, "counts": counts}


def render_inventory_markdown(payload: dict[str, object]) -> str:
    counts = payload.get("counts") if isinstance(payload.get("counts"), dict) else {}
    items = payload.get("items") if isinstance(payload.get("items"), list) else []
    lines = [
        "---",
        "doc_type: spec-governance-inventory",
        "generated_by: codestable-spec-governance.py",
        "---",
        "",
        "# Spec Governance Inventory",
        "",
        "## Summary",
        "",
    ]
    for state in sorted(REHABILITATION_STATES):
        lines.append(f"- {state}: {counts.get(state, 0)}")
    lines.extend(["", "## Items", ""])
    if not items:
        lines.append("- None")
    for item in items:
        if not isinstance(item, dict):
            continue
        lines.append(
            "- "
            f"`{item.get('path')}` - "
            f"slug: `{item.get('slug')}` - "
            f"classification: `{item.get('classification')}` - "
            f"owner_review_state: `{item.get('owner_review_state')}`"
        )
    lines.extend(["", "## Owner Follow-Up", ""])
    follow_up = [
        item
        for item in items
        if isinstance(item, dict) and item.get("classification") in {"current-unreviewed", "drift-suspected"}
    ]
    if not follow_up:
        lines.append("- None")
    for item in follow_up:
        lines.append(
            "- "
            f"`{item.get('path')}` needs owner adjudication before direct long-lived spec mutation."
        )
    lines.append("")
    return "\n".join(lines)


def write_inventory(root: Path, output_value: str) -> dict[str, object]:
    payload = inventory(root)
    output = Path(output_value)
    if not output.is_absolute():
        output = root / output
    changed = content_write(output, render_inventory_markdown(payload))
    try:
        display_path = output.relative_to(root).as_posix()
    except ValueError:
        display_path = output.as_posix()
    return {**payload, "path": display_path, "changed": changed}


def approved_deltas(root: Path, unit: Path) -> list[Path]:
    return [path for path in (root / unit).glob("*-req-delta.md") if delta_is_approved(path)]


def design_text(root: Path, unit: Path) -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in sorted((root / unit).glob("*-design.md")))


def analyze(root: Path, unit_value: str | None) -> dict[str, object]:
    findings: list[dict[str, object]] = []
    unit = resolve_unit(root, unit_value) if unit_value else None
    approved = approved_deltas(root, unit) if unit else []
    if unit:
        text = design_text(root, unit).lower()
        boundary_changed = any(
            marker in text
            for marker in (
                "capability_boundary: changed",
                "capability boundary: changed",
                "新增用户可感能力",
                "changes user-visible capability",
            )
        )
        if boundary_changed and not approved:
            findings.append(
                {
                    "severity": "P1",
                    "code": "missing_approved_req_delta",
                    "path": unit.as_posix(),
                    "message": "Capability-boundary change requires an approved requirement delta.",
                }
            )
    dirty_requirement_paths = [
        item.path
        for item in git_status(root)
        if item.path.startswith(".codestable/requirements/") and item.path.endswith(".md")
    ]
    if dirty_requirement_paths and not approved:
        for path in dirty_requirement_paths:
            findings.append(
                {
                    "severity": "P1",
                    "code": "forbidden_requirement_rewrite",
                    "path": path,
                    "message": "Requirement docs changed without an approved delta, clarification, archive marker, or compaction review.",
                }
            )
    for item in inventory(root)["items"]:  # type: ignore[index]
        if item["classification"] == "drift-suspected":
            findings.append(
                {
                    "severity": "P2",
                    "code": "drift_suspected",
                    "path": item["path"],
                    "message": "Spec is marked drift-suspected and needs owner adjudication before acceptance.",
                }
            )
    return {
        "ok": not any(finding["severity"] == "P1" for finding in findings),
        "unit": unit.as_posix() if unit else None,
        "findings": findings,
    }


def emit(payload: dict[str, object], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print("OK:", payload.get("ok"))
    for finding in payload.get("findings", []):
        print(f"- {finding.get('severity')}: {finding.get('message')} ({finding.get('path')})")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--json", action="store_true")
    subparsers = parser.add_subparsers(dest="command", required=True)

    route_parser = subparsers.add_parser("route")
    route_parser.add_argument("--query", required=True)

    clarify_parser = subparsers.add_parser("clarify")
    clarify_parser.add_argument("--file", required=True)
    clarify_parser.add_argument("--question", required=True)
    clarify_parser.add_argument("--answer", required=True)
    clarify_parser.add_argument("--anchor")

    delta_parser = subparsers.add_parser("create-delta")
    delta_parser.add_argument("--unit", required=True)
    delta_parser.add_argument("--requirement", required=True)
    delta_parser.add_argument("--added", action="append", default=[])
    delta_parser.add_argument("--modified", action="append", default=[])
    delta_parser.add_argument("--removed", action="append", default=[])
    delta_parser.add_argument("--scenario", action="append", default=[])
    delta_parser.add_argument("--owner-decision", default="pending", choices=["pending", "approved", "rejected"])

    apply_parser = subparsers.add_parser("apply-delta")
    apply_parser.add_argument("--delta", required=True)
    apply_parser.add_argument("--target", required=True)

    inventory_parser = subparsers.add_parser("inventory")
    inventory_parser.add_argument("--output", help="Optional Markdown inventory artifact path")

    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("--unit")

    args = parser.parse_args()
    root = Path(args.root).resolve()
    try:
        if args.command == "route":
            payload = route_specs(root, args.query)
        elif args.command == "clarify":
            payload = record_clarification(root, args.file, args.question, args.answer, args.anchor)
        elif args.command == "create-delta":
            payload = create_delta(
                root,
                args.unit,
                args.requirement,
                args.added,
                args.modified,
                args.removed,
                args.scenario,
                args.owner_decision,
            )
        elif args.command == "apply-delta":
            payload = apply_delta(root, args.delta, args.target)
        elif args.command == "inventory":
            payload = write_inventory(root, args.output) if args.output else inventory(root)
        elif args.command == "analyze":
            payload = analyze(root, args.unit)
        else:
            payload = {"ok": False, "findings": [{"severity": "P1", "message": "unknown command"}]}
    except ValueError as exc:
        payload = {"ok": False, "findings": [{"severity": "P1", "message": str(exc)}]}
    emit(payload, args.json)
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
