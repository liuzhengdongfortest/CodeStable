import pytest

from taskhub import storage
from taskhub.services import tasks


@pytest.fixture()
def conn():
    c = storage.connect(":memory:")
    storage.migrate(c)
    return c


def test_create_and_get(conn):
    t = tasks.create_task(conn, "write report", notes="q2")
    assert t["id"] == 1
    assert t["status"] == "todo"
    assert tasks.get_task(conn, 1)["notes"] == "q2"


def test_create_rejects_empty_title(conn):
    with pytest.raises(ValueError):
        tasks.create_task(conn, "   ")


def test_create_rejects_long_title(conn):
    with pytest.raises(ValueError):
        tasks.create_task(conn, "x" * 201)


def test_list_filters_by_status(conn):
    tasks.create_task(conn, "a")
    tasks.create_task(conn, "b")
    conn.execute("UPDATE tasks SET status='done' WHERE id=1")
    conn.commit()
    assert [t["id"] for t in tasks.list_tasks(conn, status="done")] == [1]
    with pytest.raises(ValueError):
        tasks.list_tasks(conn, status="bogus")


def test_get_missing_raises(conn):
    with pytest.raises(KeyError):
        tasks.get_task(conn, 99)
