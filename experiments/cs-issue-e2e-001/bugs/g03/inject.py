#!/usr/bin/env python3
import sys
from pathlib import Path


OLD = '                        due_date=body.get("dueDate"),\n'
NEW = '                        due_date=body.get("due_date"),\n'


def main():
    if len(sys.argv) != 2:
        print("usage: python3 inject.py <repo_path>", file=sys.stderr)
        return 1
    path = Path(sys.argv[1]) / "taskhub" / "http_api.py"
    text = path.read_text(encoding="utf-8")
    if OLD not in text:
        print("g03 injection failed: expected dueDate mapping string not found", file=sys.stderr)
        return 1
    path.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")
    print("g03 injected: POST /tasks silently ignores camelCase dueDate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
