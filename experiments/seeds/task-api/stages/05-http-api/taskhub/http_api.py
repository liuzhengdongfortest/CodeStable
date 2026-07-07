"""tiny JSON API built on http.server."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from urllib.parse import parse_qs, urlparse

from taskhub import storage
from taskhub.services import tasks


def _task_to_json(task):
    return {
        "id": task["id"],
        "title": task["title"],
        "notes": task["notes"],
        "status": task["status"],
        "projectId": task["project_id"],
        "assignee": task["assignee"],
        "createdAt": task["created_at"],
        "completedAt": task["completed_at"],
        "dueDate": task["due_date"],
        "priority": task["priority"],
    }


def _first(params, key):
    values = params.get(key)
    if not values:
        return None
    return values[0]


def make_handler(db_path):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            path, params = self._path_and_params()
            if path == "/health":
                self._send(200, {"ok": True})
                return
            if path == "/tasks":
                try:
                    project_id = _first(params, "projectId")
                    if project_id is not None:
                        project_id = int(project_id)
                    rows = tasks.list_tasks(
                        self._conn(),
                        status=_first(params, "status"),
                        project_id=project_id,
                    )
                    self._send(200, {"tasks": [_task_to_json(t) for t in rows]})
                except ValueError as e:
                    self._send(400, {"error": str(e)})
                return
            self._send(404, {"error": "not found"})

        def do_POST(self):
            path, _params = self._path_and_params()
            try:
                if path == "/tasks":
                    body = self._read_json()
                    task = tasks.create_task(
                        self._conn(),
                        body.get("title"),
                        notes=body.get("notes", ""),
                        project_id=body.get("projectId"),
                        assignee=body.get("assignee"),
                        due_date=body.get("dueDate"),
                        priority=body.get("priority", 2),
                    )
                    self._send(201, _task_to_json(task))
                    return
                if path.startswith("/tasks/") and path.endswith("/transition"):
                    task_id = int(path.split("/")[2])
                    body = self._read_json()
                    task = tasks.transition(self._conn(), task_id, body.get("status"))
                    self._send(200, _task_to_json(task))
                    return
            except (KeyError, IndexError, ValueError) as e:
                self._send(400, {"error": str(e)})
                return
            self._send(404, {"error": "not found"})

        def log_message(self, fmt, *args):
            pass

        def _conn(self):
            conn = storage.connect(db_path)
            storage.migrate(conn)
            return conn

        def _path_and_params(self):
            parsed = urlparse(self.path)
            return parsed.path, parse_qs(parsed.query)

        def _read_json(self):
            length = int(self.headers.get("Content-Length", "0"))
            if length == 0:
                return {}
            return json.loads(self.rfile.read(length).decode("utf-8"))

        def _send(self, status, payload):
            raw = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

    return Handler


def make_server(db_path, port):
    return ThreadingHTTPServer(("127.0.0.1", port), make_handler(db_path))


def main():
    import argparse
    import os

    p = argparse.ArgumentParser(prog="taskhub-api")
    p.add_argument("--db", default=os.environ.get("TASKHUB_DB", "taskhub.db"))
    p.add_argument("--port", type=int, default=8000)
    args = p.parse_args()
    server = make_server(args.db, args.port)
    print(f"serving taskhub on http://127.0.0.1:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
