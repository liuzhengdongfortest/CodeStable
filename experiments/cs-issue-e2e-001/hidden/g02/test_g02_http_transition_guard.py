import json
import threading
from urllib.error import HTTPError
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


def test_api_rejects_done_to_in_progress_transition(tmp_path):
    db_path = tmp_path / "taskhub.db"
    conn = storage.connect(db_path)
    storage.migrate(conn)
    task = tasks.create_task(conn, "release")
    tasks.transition(conn, task["id"], "in_progress")
    tasks.transition(conn, task["id"], "done")

    server = make_server(str(db_path), 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = "http://127.0.0.1:%s" % server.server_address[1]

    try:
        try:
            post_json(base, "/tasks/%s/transition" % task["id"], {"status": "in_progress"})
        except HTTPError as e:
            assert e.code == 400
        else:
            raise AssertionError("illegal transition should return HTTP 400")
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()

    assert tasks.get_task(conn, task["id"])["status"] == "done"
