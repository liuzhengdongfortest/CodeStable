import pytest
import os
import subprocess
import sys

from taskhub import storage
from taskhub.services import tasks


def run_cli(tmp_path, *args, check=True):
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
        check=check,
    )


@pytest.fixture()
def conn(tmp_path):
    c = storage.connect(tmp_path / "taskhub.db")
    storage.migrate(c)
    return c


def test_archive_leaves_non_done_tasks_active(tmp_path, conn):
    task = tasks.create_task(conn, "not done")

    before = run_cli(tmp_path, "list").stdout
    run_cli(tmp_path, "archive", str(task["id"]), check=False)
    after_default = run_cli(tmp_path, "list").stdout
    after_all = run_cli(tmp_path, "list", "--all").stdout

    assert "not done" in before
    assert "not done" in after_default
    assert "not done" in after_all


def test_archived_task_is_hidden_by_default_but_visible_with_all(tmp_path, conn):
    task = tasks.create_task(conn, "release archive", notes="find me")
    tasks.transition(conn, task["id"], "in_progress")
    tasks.transition(conn, task["id"], "done")

    run_cli(tmp_path, "archive", str(task["id"]))

    assert "release archive" not in run_cli(tmp_path, "list").stdout
    assert "release archive" in run_cli(tmp_path, "list", "--all").stdout


def test_archived_task_cannot_transition(tmp_path, conn):
    task = tasks.create_task(conn, "closed")
    tasks.transition(conn, task["id"], "in_progress")
    tasks.transition(conn, task["id"], "done")
    run_cli(tmp_path, "archive", str(task["id"]))

    try:
        tasks.transition(conn, task["id"], "in_progress")
    except Exception:
        pass
    default_list = run_cli(tmp_path, "list").stdout
    all_list = run_cli(tmp_path, "list", "--all").stdout

    assert "closed" not in default_list
    assert "[done] closed" in all_list
