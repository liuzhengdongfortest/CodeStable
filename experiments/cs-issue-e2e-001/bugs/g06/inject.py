#!/usr/bin/env python3
import sys
from pathlib import Path


OLD = """            if tags:
                notes = task["notes"] or ""
                if not all("#%s" % tag in notes for tag in tags):
                    continue
            out.append(task)
"""

NEW = """            if tags is not None:
                notes = task["notes"] or ""
                if not all("#%s" % tag in notes for tag in tags):
                    continue
                if not tags:
                    continue
            out.append(task)
"""


def main():
    if len(sys.argv) != 2:
        print("usage: python3 inject.py <repo_path>", file=sys.stderr)
        return 1
    path = Path(sys.argv[1]) / "taskhub" / "search.py"
    text = path.read_text(encoding="utf-8")
    if OLD not in text:
        print("g06 injection failed: expected tag filtering string not found", file=sys.stderr)
        return 1
    path.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")
    print("g06 injected: search treats an empty tag filter as match-nothing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
