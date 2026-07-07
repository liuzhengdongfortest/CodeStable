"""task crud."""

from datetime import datetime

from taskhub import models, storage


def create_task(conn, title, notes=""):
    title = (title or "").strip()
    if not title:
        raise ValueError("title is required")
    if len(title) > 200:
        raise ValueError("title too long (max 200)")
    now = datetime.now().isoformat(timespec="seconds")
    cur = conn.execute(
        "INSERT INTO tasks (title, notes, created_at) VALUES (?, ?, ?)",
        (title, notes, now),
    )
    conn.commit()
    return get_task(conn, cur.lastrowid)


def get_task(conn, task_id):
    found = storage.rows(conn, "SELECT * FROM tasks WHERE id = ?", (task_id,))
    if not found:
        raise KeyError(f"task {task_id} not found")
    return found[0]


def list_tasks(conn, status=None):
    if status is not None:
        if status not in models.VALID_STATUSES:
            raise ValueError(f"unknown status {status!r}")
        return storage.rows(
            conn, "SELECT * FROM tasks WHERE status = ? ORDER BY id", (status,)
        )
    return storage.rows(conn, "SELECT * FROM tasks ORDER BY id")


def update_notes(conn, task_id, notes):
    get_task(conn, task_id)
    conn.execute("UPDATE tasks SET notes = ? WHERE id = ?", (notes, task_id))
    conn.commit()
    return get_task(conn, task_id)
