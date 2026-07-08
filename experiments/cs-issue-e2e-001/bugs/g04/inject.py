#!/usr/bin/env python3
import sys
from pathlib import Path


REPLACEMENTS = [
    (
        """    if due_date is not None:
        _parse_due_date(due_date)
    if assignee is not None:
""",
        """    if due_date is not None:
        due_date = str(due_date)
    if assignee is not None:
""",
    ),
    (
        """    if due_date is not None:
        _parse_due_date(due_date)
    conn.execute("UPDATE tasks SET due_date = ? WHERE id = ?", (due_date, task_id))
""",
        """    if due_date is not None:
        due_date = str(due_date)
    conn.execute("UPDATE tasks SET due_date = ? WHERE id = ?", (due_date, task_id))
""",
    ),
]


def main():
    if len(sys.argv) != 2:
        print("usage: python3 inject.py <repo_path>", file=sys.stderr)
        return 1
    path = Path(sys.argv[1]) / "taskhub" / "services" / "tasks.py"
    text = path.read_text(encoding="utf-8")
    for old, _new in REPLACEMENTS:
        if old not in text:
            print("g04 injection failed: expected due_date validation string not found", file=sys.stderr)
            return 1
    for old, new in REPLACEMENTS:
        text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")
    print("g04 injected: both task creation and set_due now accept malformed due dates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
