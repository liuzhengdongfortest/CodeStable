from taskhub import storage
from taskhub.search import search_tasks
from taskhub.services import tasks


def test_search_finds_title_when_query_case_differs():
    conn = storage.connect(":memory:")
    storage.migrate(conn)
    tasks.create_task(conn, "deploy prod", notes="rollout")

    matches = search_tasks(conn, "Deploy")

    assert [t["title"] for t in matches] == ["deploy prod"]
