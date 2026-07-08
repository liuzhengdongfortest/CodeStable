import json
import threading
from datetime import datetime
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


def test_api_returns_parseable_iso_completed_at(tmp_path):
    db_path = tmp_path / "taskhub.db"
    conn = storage.connect(db_path)
    storage.migrate(conn)
    task = tasks.create_task(conn, "close via api")
    tasks.transition(conn, task["id"], "in_progress")

    server = make_server(str(db_path), 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = "http://127.0.0.1:%s" % server.server_address[1]

    try:
        status, payload = post_json(base, "/tasks/%s/transition" % task["id"], {"status": "done"})
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()

    assert status == 200
    assert payload["status"] == "done"
    completed_at = payload["completedAt"]
    assert completed_at
    parsed = datetime.fromisoformat(completed_at)
    assert parsed.second is not None
