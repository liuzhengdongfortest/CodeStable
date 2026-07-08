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


def parse_stats(text):
    out = {}
    for line in text.splitlines():
        if not line.strip() or line.startswith("tag "):
            continue
        tag, count, rate = line.split()
        out[tag] = (int(count), float(rate.rstrip("%")))
    return out


def test_stats_cli_summarizes_tag_counts_and_completion_rate(tmp_path):
    db_path = tmp_path / "taskhub.db"
    conn = storage.connect(db_path)
    storage.migrate(conn)
    done = tasks.create_task(conn, "ship", notes="#web")
    tasks.transition(conn, done["id"], "in_progress")
    tasks.transition(conn, done["id"], "done")
    tasks.create_task(conn, "fix", notes="#web")

    stats = parse_stats(run_cli(tmp_path, "stats").stdout)

    assert stats["web"] == (2, 50.0)
