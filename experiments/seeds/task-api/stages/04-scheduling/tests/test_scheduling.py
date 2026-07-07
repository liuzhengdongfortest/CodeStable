from datetime import datetime, timedelta

import pytest

from taskhub import storage
from taskhub.services import tasks


@pytest.fixture()
def conn():
    c = storage.connect(":memory:")
    storage.migrate(c)
    return c


def test_create_rejects_bad_priority(conn):
    with pytest.raises(ValueError, match="priority"):
        tasks.create_task(conn, "bad", priority=9)


def test_create_accepts_due_date_and_priority(conn):
    t = tasks.create_task(conn, "pay bill", due_date="2030-01-02", priority=1)
    assert t["due_date"] == "2030-01-02"
    assert t["priority"] == 1


def test_smart_order_uses_priority_then_due_then_id(conn):
    tasks.create_task(conn, "normal soon", due_date="2030-01-01", priority=2)
    tasks.create_task(conn, "high later", due_date="2030-02-01", priority=1)
    tasks.create_task(conn, "high sooner", due_date="2030-01-15", priority=1)
    tasks.create_task(conn, "high no due", priority=1)
    assert [t["title"] for t in tasks.list_tasks(conn, order="smart")] == [
        "high sooner",
        "high later",
        "high no due",
        "normal soon",
    ]


def test_set_due_updates_due_date(conn):
    t = tasks.create_task(conn, "schedule later")
    t = tasks.set_due(conn, t["id"], "2030-04-05")
    assert t["due_date"] == "2030-04-05"


def test_is_overdue_true_for_past_due_date(conn):
    due = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    assert tasks.is_overdue({"due_date": due}) is True


def test_is_overdue_false_for_future_due_date(conn):
    due = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    assert tasks.is_overdue({"due_date": due}) is False


def test_is_overdue_false_without_due_date(conn):
    assert tasks.is_overdue({"due_date": None}) is False
