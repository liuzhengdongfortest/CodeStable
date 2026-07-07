# TODO: build an index; linear scan won't scale past a few thousand tasks


def search_tasks(conn, query, tags=None):
    needle = (query or "").lower()
    out = []
    rows = conn.execute("SELECT * FROM tasks ORDER BY id").fetchall()
    for row in rows:
        task = dict(row)
        haystack = "%s\n%s" % (task["title"], task["notes"] or "")
        if needle in haystack.lower():
            if tags:
                notes = task["notes"] or ""
                if not all("#%s" % tag in notes for tag in tags):
                    continue
            out.append(task)
    return out
