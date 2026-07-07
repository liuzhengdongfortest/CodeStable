#!/usr/bin/env python3
import sys
from pathlib import Path


OLD = """                if path.startswith("/tasks/") and path.endswith("/transition"):
                    task_id = int(path.split("/")[2])
                    body = self._read_json()
                    task = tasks.transition(self._conn(), task_id, body.get("status"))
                    self._send(200, _task_to_json(task))
                    return
"""

NEW = """                if path.startswith("/tasks/") and path.endswith("/transition"):
                    task_id = int(path.split("/")[2])
                    body = self._read_json()
                    conn = self._conn()
                    try:
                        task = tasks.transition(conn, task_id, body.get("status"))
                    except ValueError:
                        conn.execute(
                            "UPDATE tasks SET status = ? WHERE id = ?",
                            (body.get("status"), task_id),
                        )
                        conn.commit()
                        task = tasks.get_task(conn, task_id)
                    self._send(200, _task_to_json(task))
                    return
"""


def main():
    if len(sys.argv) != 2:
        print("usage: python3 inject.py <repo_path>", file=sys.stderr)
        return 1
    path = Path(sys.argv[1]) / "taskhub" / "http_api.py"
    text = path.read_text(encoding="utf-8")
    if OLD not in text:
        print("g02 injection failed: expected transition handler string not found", file=sys.stderr)
        return 1
    path.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")
    print("g02 injected: API transition now accepts illegal status moves")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
