import pytest

from taskhub import storage
from taskhub.services import tasks


@pytest.fixture()
def conn():
    c = storage.connect(":memory:")
    storage.migrate(c)
    return c


def test_bad_due_date_is_rejected_on_create(conn):
    with pytest.raises(ValueError):
        tasks.create_task(conn, "bad import date", due_date="03/04/2030")


def test_bad_due_date_is_rejected_when_rescheduling(conn):
    task = tasks.create_task(conn, "reschedule me", due_date="2030-03-04")

    with pytest.raises(ValueError):
        tasks.set_due(conn, task["id"], "03/05/2030")

    assert tasks.get_task(conn, task["id"])["due_date"] == "2030-03-04"
