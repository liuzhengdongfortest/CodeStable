#!/usr/bin/env python3
import sys
from pathlib import Path


OLD = '    needle = (query or "").lower()\n'
NEW = '    needle = query or ""\n'


def main():
    if len(sys.argv) != 2:
        print("usage: python3 inject.py <repo_path>", file=sys.stderr)
        return 1
    path = Path(sys.argv[1]) / "taskhub" / "search.py"
    text = path.read_text(encoding="utf-8")
    if OLD not in text:
        print("g01 injection failed: expected search match string not found", file=sys.stderr)
        return 1
    path.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")
    print("g01 injected: search matching is now case-sensitive")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
