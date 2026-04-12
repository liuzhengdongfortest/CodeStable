#!/usr/bin/env python3
"""
search-yaml.py — Generic YAML-frontmatter search tool for markdown document directories.

Works on any directory of .md files that use YAML frontmatter (--- ... ---).
Designed for AI agent use: fast, structured output, no required external dependencies.

Filter syntax (--filter flag, repeatable, AND logic):
  key=value     Exact match on a scalar field (case-insensitive)
  key~=value    Substring match on a string field, or element-in for list fields

Usage examples:
  # Search easysdd/learnings (compound docs)
  python tools/search-yaml.py --dir easysdd/learnings --filter track=pitfall
  python tools/search-yaml.py --dir easysdd/learnings --filter tags~=prisma --filter severity=high
  python tools/search-yaml.py --dir easysdd/learnings --filter component~=database --full

  # Full-text search in body + frontmatter values
  python tools/search-yaml.py --dir easysdd/learnings --query "shadow database"

  # JSON output for AI agent consumption
  python tools/search-yaml.py --dir easysdd/learnings --filter track=knowledge --json

  # Works on any yaml-frontmatter markdown directory
  python tools/search-yaml.py --dir docs/decisions --filter status=accepted
  python tools/search-yaml.py --dir content/posts --filter tags~=python --query "asyncio"
"""

import argparse
import json
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Frontmatter parsing  (PyYAML used when available, builtin fallback otherwise)
# ---------------------------------------------------------------------------

def _parse_yaml_scalar(val: str):
    val = val.strip()
    if val.startswith("[") and val.endswith("]"):
        inner = val[1:-1]
        return [item.strip().strip("'\"") for item in inner.split(",") if item.strip()]
    lower = val.lower()
    if lower in ("true", "yes"):
        return True
    if lower in ("false", "no"):
        return False
    if lower in ("null", "~", ""):
        return None
    return val


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """
    Split a markdown document into (frontmatter_dict, body_text).
    Returns ({}, full_text) when no frontmatter is present.
    """
    if not text.startswith("---"):
        return {}, text

    end = text.find("\n---", 3)
    if end == -1:
        return {}, text

    fm_text = text[3:end].strip()
    body = text[end + 4:].strip()

    try:
        import yaml  # type: ignore
        meta = yaml.safe_load(fm_text)
        return (meta or {}), body
    except Exception:
        pass

    # Minimal fallback: handles scalar values and inline lists
    meta: dict = {}
    for line in fm_text.splitlines():
        if not line.strip() or line.startswith("#") or ":" not in line:
            continue
        key, _, raw = line.partition(":")
        meta[key.strip()] = _parse_yaml_scalar(raw)

    return meta, body


# ---------------------------------------------------------------------------
# Document loading
# ---------------------------------------------------------------------------

def load_documents(directory: Path) -> list[dict]:
    docs = []
    for md_file in sorted(directory.rglob("*.md")):
        try:
            text = md_file.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"[warn] Cannot read {md_file.name}: {exc}", file=sys.stderr)
            continue
        meta, body = parse_frontmatter(text)
        docs.append({
            "file": str(md_file.relative_to(directory)),
            "path": str(md_file),
            "meta": meta,
            "body": body,
        })
    return docs


# ---------------------------------------------------------------------------
# Filter parsing and evaluation
# ---------------------------------------------------------------------------

class Filter:
    """Parsed representation of a single --filter expression."""

    def __init__(self, raw: str):
        if "~=" in raw:
            key, _, value = raw.partition("~=")
            self.key = key.strip()
            self.value = value.strip()
            self.operator = "contains"
        elif "=" in raw:
            key, _, value = raw.partition("=")
            self.key = key.strip()
            self.value = value.strip()
            self.operator = "exact"
        else:
            raise argparse.ArgumentTypeError(
                f"Invalid filter expression {raw!r}. "
                "Use 'key=value' for exact match or 'key~=value' for substring/list-contains match."
            )

    def matches(self, meta: dict) -> bool:
        field_val = meta.get(self.key)
        if field_val is None:
            return False

        if self.operator == "exact":
            return str(field_val).lower() == self.value.lower()

        # contains: substring for strings, element-in for lists
        if isinstance(field_val, list):
            return any(self.value.lower() == str(item).lower() for item in field_val)
        return self.value.lower() in str(field_val).lower()

    def __repr__(self):
        op = "~=" if self.operator == "contains" else "="
        return f"Filter({self.key}{op}{self.value})"


def parse_filter(raw: str) -> Filter:
    """argparse type converter for --filter."""
    return Filter(raw)


def doc_matches(doc: dict, filters: list[Filter], query: str | None) -> bool:
    meta = doc["meta"]

    for f in filters:
        if not f.matches(meta):
            return False

    if query:
        needle = query.lower()
        haystack = doc["body"].lower() + " " + " ".join(str(v) for v in meta.values()).lower()
        if needle not in haystack:
            return False

    return True


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def _meta_summary(meta: dict) -> str:
    """One-line summary of frontmatter fields, skipping slug/date for brevity."""
    skip = {"slug"}
    parts = []
    for k, v in meta.items():
        if k in skip:
            continue
        if isinstance(v, list):
            parts.append(f"{k}=[{', '.join(str(i) for i in v)}]")
        else:
            parts.append(f"{k}={v}")
    return "  ".join(parts)


def format_summary(doc: dict) -> str:
    return f"### {doc['file']}\n{_meta_summary(doc['meta'])}"


def format_full(doc: dict) -> str:
    return format_summary(doc) + "\n\n" + doc["body"]


def print_text(results: list[dict], full: bool) -> None:
    print(f"Found {len(results)} document(s).\n")
    sep = "\n" + "─" * 60 + "\n"
    chunks = [format_full(d) if full else format_summary(d) for d in results]
    print(sep.join(chunks))


def print_json(results: list[dict], full: bool) -> None:
    output = []
    for doc in results:
        body = doc["body"]
        if not full and len(body) > 400:
            body = body[:400] + "…"
        output.append({"file": doc["file"], "meta": doc["meta"], "body": body})
    print(json.dumps(output, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generic YAML-frontmatter search across a directory of markdown files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--dir", metavar="DIR", required=True,
        help="Directory of .md files to search.",
    )
    parser.add_argument(
        "--filter", "-f", metavar="EXPR", dest="filters",
        type=parse_filter, action="append", default=[],
        help=(
            "Frontmatter filter expression. Repeatable (AND logic). "
            "key=value for exact match; key~=value for substring (strings) or element-in (lists)."
        ),
    )
    parser.add_argument(
        "--query", "-q", metavar="TEXT",
        help="Full-text search in document body and frontmatter values.",
    )
    parser.add_argument(
        "--full", action="store_true",
        help="Print full document body instead of just the frontmatter summary.",
    )
    parser.add_argument(
        "--json", dest="as_json", action="store_true",
        help="Output results as a JSON array.",
    )

    args = parser.parse_args()

    directory = Path(args.dir)
    if not directory.exists():
        print(f"[error] Directory not found: {directory}", file=sys.stderr)
        sys.exit(1)
    if not directory.is_dir():
        print(f"[error] Not a directory: {directory}", file=sys.stderr)
        sys.exit(1)

    docs = load_documents(directory)

    if not docs:
        print(f"No .md files found in {directory}")
        return

    results = [d for d in docs if doc_matches(d, args.filters, args.query)]

    if not results:
        print("No matching documents found.")
        return

    if args.as_json:
        print_json(results, full=args.full)
    else:
        print_text(results, full=args.full)


if __name__ == "__main__":
    main()
