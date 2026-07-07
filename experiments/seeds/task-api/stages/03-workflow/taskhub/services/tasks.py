"""task crud + assignment + workflow."""

from datetime import datetime

from taskhub import models, storage
from taskhub.services import projects


def create_task(conn, title: str, notes: str = "", project_id=None, assignee=None):
    title = (title or "").strip()
    if not title:
        raise ValueError("title is required")
    if len(title) > 200:
        raise ValueError("title too long (max 200)")
    if assignee is not None:
        if project_id is None:
            raise ValueError("assignee requires a project")
        if not projects.is_member(conn, project_id, assignee):
            raise ValueError(f"{assignee} is not a member of project {project_id}")
    now = datetime.now().isoformat(timespec="seconds")
    cur = conn.execute(
        "INSERT INTO tasks (title, notes, project_id, assignee, created_at)"
        " VALUES (?, ?, ?, ?, ?)",
        (title, notes, project_id, assignee, now),
    )
    conn.commit()
    return get_task(conn, cur.lastrowid)


def get_task(conn, task_id: int):
    found = storage.rows(conn, "SELECT * FROM tasks WHERE id = ?", (task_id,))
    if not found:
        raise KeyError(f"task {task_id} not found")
    return found[0]


def list_tasks(conn, status: str | None = None, project_id=None):
    sql = "SELECT * FROM tasks"
    where, params = [], []
    if status is not None:
        if status not in models.VALID_STATUSES:
            raise ValueError(f"unknown status {status!r}")
        where.append("status = ?")
        params.append(status)
    if project_id is not None:
        where.append("project_id = ?")
        params.append(project_id)
    if where:
        sql += " WHERE " + " AND ".join(where)
    return storage.rows(conn, sql + " ORDER BY id", tuple(params))


def assign_task(conn, task_id: int, username: str):
    t = get_task(conn, task_id)
    if t["project_id"] is None:
        raise ValueError("task has no project; add it to a project first")
    if not projects.is_member(conn, t["project_id"], username):
        raise ValueError(f"{username} is not a member of project {t['project_id']}")
    conn.execute("UPDATE tasks SET assignee = ? WHERE id = ?", (username, task_id))
    conn.commit()
    return get_task(conn, task_id)


def update_notes(conn, task_id: int, notes: str):
    get_task(conn, task_id)
    conn.execute("UPDATE tasks SET notes = ? WHERE id = ?", (notes, task_id))
    conn.commit()
    return get_task(conn, task_id)


def transition(conn, task_id: int, new_status: str):
    if new_status not in models.VALID_STATUSES:
        raise ValueError(f"unknown status {new_status!r}")
    t = get_task(conn, task_id)
    current = t["status"]
    if new_status not in models.TRANSITIONS[current]:
        raise ValueError(f"cannot transition task {task_id} from {current} to {new_status}")
    completed_at = None
    if new_status == models.STATUS_DONE:
        completed_at = datetime.now().isoformat(timespec="seconds")
    conn.execute(
        "UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?",
        (new_status, completed_at, task_id),
    )
    conn.commit()
    return get_task(conn, task_id)
