import pytest

from taskhub import storage
from taskhub.search import search_tasks
from taskhub.services import tasks


@pytest.fixture()
def conn():
    c = storage.connect(":memory:")
    storage.migrate(c)
    return c


def test_search_matches_title_and_notes(conn):
    tasks.create_task(conn, "write docs", notes="release checklist")
    tasks.create_task(conn, "triage bug", notes="customer report")
    assert [t["title"] for t in search_tasks(conn, "release")] == ["write docs"]
    assert [t["title"] for t in search_tasks(conn, "bug")] == ["triage bug"]


def test_search_can_filter_by_note_tags(conn):
    tasks.create_task(conn, "ship", notes="#release #web")
    tasks.create_task(conn, "clean", notes="#ops")
    assert [t["title"] for t in search_tasks(conn, "sh", tags=["release"])] == ["ship"]
