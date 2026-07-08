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


def test_done_task_can_be_archived_and_default_list_hides_it(tmp_path):
    db_path = tmp_path / "taskhub.db"
    conn = storage.connect(db_path)
    storage.migrate(conn)
    done = tasks.create_task(conn, "finished")
    tasks.transition(conn, done["id"], "in_progress")
    tasks.transition(conn, done["id"], "done")
    tasks.create_task(conn, "open")

    run_cli(tmp_path, "archive", str(done["id"]))
    listed = run_cli(tmp_path, "list").stdout

    assert "finished" not in listed
    assert "open" in listed
