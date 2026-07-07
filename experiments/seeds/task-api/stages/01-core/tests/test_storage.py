from taskhub import storage


def make_conn():
    conn = storage.connect(":memory:")
    storage.migrate(conn)
    return conn


def test_migrate_creates_tasks_table():
    conn = make_conn()
    names = [r["name"] for r in storage.rows(
        conn, "SELECT name FROM sqlite_master WHERE type='table'")]
    assert "tasks" in names


def test_rows_returns_dicts():
    conn = make_conn()
    conn.execute("INSERT INTO tasks (title, created_at) VALUES ('a', 't')")
    out = storage.rows(conn, "SELECT * FROM tasks")
    assert isinstance(out[0], dict)
    assert out[0]["title"] == "a"
