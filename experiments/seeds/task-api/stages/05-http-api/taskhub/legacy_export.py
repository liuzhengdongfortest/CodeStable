# DEPRECATED: kept for the old CSV pipeline, remove after Q3 migration

import csv


def export_tasks_csv(conn, path):
    rows = conn.execute("SELECT * FROM tasks ORDER BY id").fetchall()
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id",
            "title",
            "status",
            "project_id",
            "assignee",
            "due_date",
            "priority",
        ])
        for row in rows:
            writer.writerow([
                "%s" % row["id"],
                "%s" % row["title"],
                "%s" % row["status"],
                "%s" % (row["project_id"] or ""),
                "%s" % (row["assignee"] or ""),
                "%s" % (row["due_date"] or ""),
                "%s" % row["priority"],
            ])
