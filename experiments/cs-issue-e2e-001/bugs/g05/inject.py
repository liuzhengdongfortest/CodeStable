#!/usr/bin/env python3
import sys
from pathlib import Path


OLD = """    if new_status == models.STATUS_DONE:
        completed_at = datetime.now().isoformat(timespec="seconds")
    conn.execute(
"""

NEW = """    if new_status == models.STATUS_DONE:
        completed_at = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
    conn.execute(
"""


def main():
    if len(sys.argv) != 2:
        print("usage: python3 inject.py <repo_path>", file=sys.stderr)
        return 1
    path = Path(sys.argv[1]) / "taskhub" / "services" / "tasks.py"
    text = path.read_text(encoding="utf-8")
    if OLD not in text:
        print("g05 injection failed: expected completed_at timestamp string not found", file=sys.stderr)
        return 1
    path.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")
    print("g05 injected: completed_at is stored in a legacy non-ISO format")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
