"""cli entrypoint: python -m taskhub.cli <cmd>"""

import argparse
import os

from taskhub import http_api, storage
from taskhub.search import search_tasks
from taskhub.services import tasks

DEFAULT_DB = os.environ.get("TASKHUB_DB", "taskhub.db")


def get_conn(db_path=None):
    conn = storage.connect(db_path or DEFAULT_DB)
    storage.migrate(conn)
    return conn


def main(argv=None):
    p = argparse.ArgumentParser(prog="taskhub")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add")
    p_add.add_argument("title")
    p_add.add_argument("--notes", default="")
    p_add.add_argument("--due-date")
    p_add.add_argument("--priority", type=int, default=2)

    p_list = sub.add_parser("list")
    p_list.add_argument("--status")
    p_list.add_argument("--order", choices=("id", "smart"), default="id")

    p_search = sub.add_parser("search")
    p_search.add_argument("query")
    p_search.add_argument("--tag", action="append", dest="tags")

    p_serve = sub.add_parser("serve")
    p_serve.add_argument("--port", type=int, default=8000)

    args = p.parse_args(argv)

    if args.cmd == "serve":
        server = http_api.make_server(DEFAULT_DB, args.port)
        print(f"serving taskhub on http://127.0.0.1:{args.port}")
        server.serve_forever()
        return 0

    conn = get_conn()

    if args.cmd == "add":
        t = tasks.create_task(
            conn,
            args.title,
            args.notes,
            due_date=args.due_date,
            priority=args.priority,
        )
        print(f"#{t['id']} {t['title']}")
    elif args.cmd == "list":
        for t in tasks.list_tasks(conn, status=args.status, order=args.order):
            print(f"#{t['id']} [{t['status']}] {t['title']}")
    elif args.cmd == "search":
        for t in search_tasks(conn, args.query, tags=args.tags):
            print(f"#{t['id']} [{t['status']}] {t['title']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
