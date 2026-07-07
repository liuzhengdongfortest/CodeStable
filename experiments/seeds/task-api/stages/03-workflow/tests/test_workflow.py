import pytest

from taskhub import storage
from taskhub.services import tasks


@pytest.fixture()
def conn():
    c = storage.connect(":memory:")
    storage.migrate(c)
    return c


def test_todo_to_in_progress_to_done(conn):
    t = tasks.create_task(conn, "ship")
    t = tasks.transition(conn, t["id"], "in_progress")
    assert t["status"] == "in_progress"
    t = tasks.transition(conn, t["id"], "done")
    assert t["status"] == "done"


def test_blocked_round_trip(conn):
    t = tasks.create_task(conn, "debug")
    t = tasks.transition(conn, t["id"], "in_progress")
    t = tasks.transition(conn, t["id"], "blocked")
    assert t["status"] == "blocked"
    t = tasks.transition(conn, t["id"], "in_progress")
    assert t["status"] == "in_progress"


def test_todo_cannot_jump_to_done(conn):
    t = tasks.create_task(conn, "skip")
    with pytest.raises(ValueError, match="from todo to done"):
        tasks.transition(conn, t["id"], "done")


def test_done_is_terminal(conn):
    t = tasks.create_task(conn, "final")
    tasks.transition(conn, t["id"], "in_progress")
    tasks.transition(conn, t["id"], "done")
    with pytest.raises(ValueError, match="from done to in_progress"):
        tasks.transition(conn, t["id"], "in_progress")


def test_done_sets_completed_at(conn):
    t = tasks.create_task(conn, "close")
    t = tasks.transition(conn, t["id"], "in_progress")
    assert t["completed_at"] is None
    t = tasks.transition(conn, t["id"], "done")
    assert t["completed_at"]
