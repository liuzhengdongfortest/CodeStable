import pytest

from taskhub import storage
from taskhub.services import projects, tasks


@pytest.fixture()
def conn():
    c = storage.connect(":memory:")
    storage.migrate(c)
    return c


def test_create_project_and_members(conn):
    p = projects.create_project(conn, "site", members=["ana", "bo"])
    assert p["members"] == ["ana", "bo"]
    p = projects.add_member(conn, p["id"], "cy")
    assert "cy" in p["members"]


def test_assign_requires_membership(conn):
    p = projects.create_project(conn, "site", members=["ana"])
    t = tasks.create_task(conn, "deploy", project_id=p["id"])
    with pytest.raises(ValueError):
        tasks.assign_task(conn, t["id"], "mallory")
    t = tasks.assign_task(conn, t["id"], "ana")
    assert t["assignee"] == "ana"


def test_assign_without_project_rejected(conn):
    t = tasks.create_task(conn, "orphan")
    with pytest.raises(ValueError):
        tasks.assign_task(conn, t["id"], "ana")


def test_create_with_assignee_validates(conn):
    p = projects.create_project(conn, "site", members=["ana"])
    with pytest.raises(ValueError):
        tasks.create_task(conn, "x", project_id=p["id"], assignee="mallory")
    with pytest.raises(ValueError):
        tasks.create_task(conn, "x", assignee="ana")
