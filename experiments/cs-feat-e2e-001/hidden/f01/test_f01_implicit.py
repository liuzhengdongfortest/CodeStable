import csv
import os
import subprocess
import sys

from taskhub import storage
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


def read_rows(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_export_uses_csv_escaping_and_empty_due_date(tmp_path):
    db_path = tmp_path / "taskhub.db"
    conn = storage.connect(db_path)
    storage.migrate(conn)
    title = 'deploy, "prod"\nphase 2'
    tasks.create_task(conn, title, notes='needs, "review"\nsoon')
    out_path = tmp_path / "tasks.csv"

    run_cli(tmp_path, "export", str(out_path))

    rows = read_rows(out_path)
    assert rows[0]["title"] == title
    assert rows[0]["dueDate"] == ""
    assert "None" not in out_path.read_text(encoding="utf-8")


def test_export_empty_task_list_still_writes_header(tmp_path):
    db_path = tmp_path / "taskhub.db"
    conn = storage.connect(db_path)
    storage.migrate(conn)
    out_path = tmp_path / "empty.csv"

    run_cli(tmp_path, "export", str(out_path))

    assert out_path.read_text(encoding="utf-8").splitlines() == [
        "id,title,status,assignee,dueDate"
    ]
