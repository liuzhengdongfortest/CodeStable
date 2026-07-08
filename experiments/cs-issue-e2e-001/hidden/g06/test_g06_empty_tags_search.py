from taskhub import storage
from taskhub.search import search_tasks
from taskhub.services import tasks


def test_empty_tag_filter_behaves_like_no_tag_filter():
    conn = storage.connect(":memory:")
    storage.migrate(conn)
    tasks.create_task(conn, "deploy prod", notes="#release")
    tasks.create_task(conn, "deploy docs", notes="")
    tasks.create_task(conn, "plan sprint", notes="#release")

    no_tags = search_tasks(conn, "deploy", tags=None)
    empty_tags = search_tasks(conn, "deploy", tags=[])

    assert [t["title"] for t in empty_tags] == [t["title"] for t in no_tags]
    assert [t["title"] for t in empty_tags] == ["deploy prod", "deploy docs"]
