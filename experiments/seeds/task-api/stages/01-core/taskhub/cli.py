"""cli entrypoint: python -m taskhub.cli <cmd>"""

import argparse
import os

from taskhub import storage
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

    p_list = sub.add_parser("list")
    p_list.add_argument("--status")

    args = p.parse_args(argv)
    conn = get_conn()

    if args.cmd == "add":
        t = tasks.create_task(conn, args.title, args.notes)
        print(f"#{t['id']} {t['title']}")
    elif args.cmd == "list":
        for t in tasks.list_tasks(conn, status=args.status):
            print(f"#{t['id']} [{t['status']}] {t['title']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
