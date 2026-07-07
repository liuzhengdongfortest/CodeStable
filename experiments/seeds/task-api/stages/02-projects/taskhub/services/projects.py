"""project management: a project owns tasks and has a member list."""

import json

from taskhub import storage


def create_project(conn, name, members=None):
    name = (name or "").strip()
    if not name:
        raise ValueError("project name is required")
    cur = conn.execute(
        "INSERT INTO projects (name, members) VALUES (?, ?)",
        (name, json.dumps(sorted(set(members or [])))),
    )
    conn.commit()
    return get_project(conn, cur.lastrowid)


def get_project(conn, project_id):
    found = storage.rows(conn, "SELECT * FROM projects WHERE id = ?", (project_id,))
    if not found:
        raise KeyError(f"project {project_id} not found")
    p = found[0]
    p["members"] = json.loads(p["members"])
    return p


def add_member(conn, project_id, username):
    p = get_project(conn, project_id)
    members = sorted(set(p["members"]) | {username})
    conn.execute(
        "UPDATE projects SET members = ? WHERE id = ?",
        (json.dumps(members), project_id),
    )
    conn.commit()
    return get_project(conn, project_id)


def is_member(conn, project_id, username):
    return username in get_project(conn, project_id)["members"]
