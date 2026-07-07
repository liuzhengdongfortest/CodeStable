import json
import threading
from datetime import datetime, timedelta
from urllib.request import Request, urlopen

from taskhub import storage
from taskhub.http_api import make_server
from taskhub.services import tasks


def post_json(base, path, payload):
    req = Request(
        base + path,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=5) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def test_api_created_task_keeps_due_date_for_overdue_and_smart_order(tmp_path):
    db_path = tmp_path / "taskhub.db"
    conn = storage.connect(db_path)
    storage.migrate(conn)
    future = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    tasks.create_task(conn, "cli future", due_date=future, priority=2)

    server = make_server(str(db_path), 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = "http://127.0.0.1:%s" % server.server_address[1]
    past = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        status, payload = post_json(
            base,
            "/tasks",
            {"title": "api overdue", "dueDate": past, "priority": 1},
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()

    assert status == 201
    assert payload["dueDate"] == past
    created = tasks.get_task(conn, payload["id"])
    assert tasks.is_overdue(created) is True
    assert [t["title"] for t in tasks.list_tasks(conn, order="smart")][:2] == [
        "api overdue",
        "cli future",
    ]
