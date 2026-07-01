from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


sys.dont_write_bytecode = True
TOOLS_DIR = Path(__file__).resolve().parents[1] / "plugins/codestable/skills/cs-onboard/tools"
sys.path.insert(0, str(TOOLS_DIR))


def load_tool(module_name: str, filename: str):
    spec = importlib.util.spec_from_file_location(module_name, TOOLS_DIR / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


doctor = load_tool("codestable_doctor", "codestable-doctor.py")
worktree_gate = load_tool("codestable_worktree_gate", "codestable-worktree-gate.py")


def run(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    run(repo, "init", "-b", "main")
    run(repo, "config", "user.email", "test@example.com")
    run(repo, "config", "user.name", "Test User")
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    run(repo, "add", "README.md")
    run(repo, "commit", "-m", "init")
    return repo


def make_feature_unit(repo: Path) -> Path:
    unit = repo / ".codestable/features/2026-06-03-demo"
    unit.mkdir(parents=True)
    return unit


def test_idle_repo_reports_idle_without_mutation(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    before = run(repo, "status", "--porcelain").stdout

    report = doctor.diagnose(repo)

    after = run(repo, "status", "--porcelain").stdout
    assert report["status"] == "idle"
    assert report["findings"] == []
    assert before == after == ""


def test_docs_only_dirty_state_is_planning_safe(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    (repo / "docs").mkdir()
    (repo / "docs/plan.md").write_text("plan\n", encoding="utf-8")

    report = doctor.diagnose(repo)

    assert report["status"] == "planning-safe"
    assert report["dirty_buckets"] == {"docs": ["docs/plan.md"]}
    assert report["implementation_changes"] == []


def test_dirty_implementation_on_main_is_blocked(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    (repo / "src").mkdir()
    (repo / "src/app.py").write_text("print('x')\n", encoding="utf-8")

    report = doctor.diagnose(repo)

    assert report["status"] == "blocked"
    assert report["implementation_changes"] == ["src/app.py"]
    assert "outside a linked execution worktree" in report["findings"][0]["message"]


def test_completed_unit_without_review_is_blocked(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    unit = make_feature_unit(repo)
    (unit / "demo-checklist.yaml").write_text(
        "steps:\n"
        "  - id: one\n"
        "    status: done\n",
        encoding="utf-8",
    )

    report = doctor.diagnose(repo)

    assert report["status"] == "blocked"
    assert report["findings"][0]["path"] == ".codestable/features/2026-06-03-demo/demo-review.md"


def test_backlog_terms_are_reported_with_line_numbers(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    unit = make_feature_unit(repo)
    (repo / ".codestable/attention.md").write_text("## attention.md Candidates\n- add test command\n", encoding="utf-8")
    (unit / "demo-acceptance.md").write_text(
        "status: needs-human-review\n"
        "Human review required before publish.\n"
        "Follow-up: convert risk into issue.\n"
        "accepted P2: reviewer allowed delayed cleanup.\n",
        encoding="utf-8",
    )

    report = doctor.diagnose(repo)

    kinds = {item["kind"] for item in report["backlog"]}
    assert {"attention-candidate", "needs-human-review", "human-review", "follow-up", "accepted-p2"} <= kinds
    assert all(item["line"] >= 1 for item in report["backlog"])


def test_clean_main_with_post_baseline_implementation_commit_is_blocked(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    unit = make_feature_unit(repo)
    (unit / "worktree-override.md").write_text(
        "reason: test\nscope: demo\napproval: approved\n",
        encoding="utf-8",
    )
    payload = worktree_gate.start_gate(repo, ".codestable/features/2026-06-03-demo")
    assert payload["ok"]
    assert run(repo, "status", "--porcelain").stdout == "?? .codestable/\n"

    run(repo, "add", ".codestable")
    run(repo, "commit", "-m", "add unit")
    (repo / "src").mkdir()
    (repo / "src/app.py").write_text("print('x')\n", encoding="utf-8")
    run(repo, "add", "src/app.py")
    run(repo, "commit", "-m", "implement on main")
    assert run(repo, "status", "--porcelain").stdout == ""

    report = doctor.diagnose(repo)

    assert report["status"] == "blocked"
    assert report["post_baseline_blocks"][0]["implementation_changes"] == ["src/app.py"]
