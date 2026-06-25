#!/usr/bin/env python3
"""Report unresolved CodeStable human-review and follow-up backlog items."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from codestable_common import is_blocking_follow_up_text, scan_backlog, unit_for_path


BLOCKING_KINDS = {"needs-human-review", "human-review"}


def is_blocking_item(kind: str, text: str) -> bool:
    if kind in BLOCKING_KINDS:
        return True
    if kind != "follow-up":
        return False
    return is_blocking_follow_up_text(text)


def backlog(root: Path) -> dict[str, object]:
    root = root.resolve()
    items = []
    for item in scan_backlog(root):
        payload = asdict(item)
        blocking = is_blocking_item(item.kind, item.text)
        payload["unit"] = unit_for_path(item.path)
        payload["file"] = item.path
        payload["excerpt"] = item.text
        payload["blocking"] = blocking
        payload["severity"] = "P1" if blocking else "P2"
        payload["action"] = (
            "Get human decision before completion."
            if blocking
            else "Resolve, convert to an issue, or explicitly defer."
        )
        items.append(payload)
    return {
        "ok": not any(item["severity"] == "P1" for item in items),
        "items": items,
        "blocking_count": sum(1 for item in items if item["severity"] == "P1"),
        "optional_count": sum(1 for item in items if item["severity"] == "P2"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--json", action="store_true", help="Print machine-readable output")
    args = parser.parse_args()

    payload = backlog(Path(args.root))
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Blocking backlog: {payload['blocking_count']}")
        print(f"Optional backlog: {payload['optional_count']}")
        for item in payload["items"]:
            print(f"- {item['severity']} {item['kind']} {item['path']}:{item['line']} {item['text']}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
