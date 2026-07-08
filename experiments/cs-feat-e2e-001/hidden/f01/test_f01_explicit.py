import csv
import os
import subprocess
import sys

from taskhub import storage
from taskhub.services import projects
from taskhub.services import tasks


def run_cli(tmp_path, *args):
    repo_root = os.getcwd()
    env = dict(
        os.environ,
        TASKHUB_DB=str(tmp_path / "taskhub.db"),
        PYTHONPATH=repo_root + os.pathsep + os.environ.get("PYTHONPATH", ""),
    )
    return subprocess.run(
        [sys.executable, "-m", "taskhub.cli", *args],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )


def test_export_cli_writes_requested_columns(tmp_path):
    db_path = tmp_path / "taskhub.db"
    conn = storage.connect(db_path)
    storage.migrate(conn)
    project = projects.create_project(conn, "ops", members=["ana"])
    task = tasks.create_task(
        conn,
        "ship report",
        project_id=project["id"],
        assignee="ana",
        due_date="2030-01-02",
    )
    out_path = tmp_path / "tasks.csv"

    run_cli(tmp_path, "export", str(out_path))

    rows = list(csv.DictReader(out_path.open(newline="", encoding="utf-8")))
    assert rows == [{
        "id": str(task["id"]),
        "title": "ship report",
        "status": "todo",
        "assignee": "ana",
        "dueDate": "2030-01-02",
    }]
