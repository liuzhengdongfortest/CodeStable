from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "cs-onboard/tools/validate-implementation-review.py"
SPEC = importlib.util.spec_from_file_location("validate_implementation_review", MODULE_PATH)
assert SPEC and SPEC.loader
gate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gate
SPEC.loader.exec_module(gate)


def run(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    run(repo, "init")
    run(repo, "config", "user.email", "test@example.com")
    run(repo, "config", "user.name", "Test User")
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    run(repo, "add", "README.md")
    run(repo, "commit", "-m", "init")
    return repo


def test_docs_only_change_passes_in_main_checkout(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    (repo / "docs").mkdir()
    (repo / "docs/note.md").write_text("note\n", encoding="utf-8")

    ok, findings, meta = gate.validate(repo)

    assert ok
    assert findings == []
    assert meta["implementation_changes"] == []


def test_code_change_requires_worktree_unless_overridden(tmp_path: Path, monkeypatch) -> None:
    repo = init_repo(tmp_path)
    (repo / "src").mkdir()
    (repo / "src/app.py").write_text("print('x')\n", encoding="utf-8")

    ok, findings, _meta = gate.validate(repo)
    assert not ok
    assert "outside a linked worktree" in findings[0].message

    monkeypatch.setenv("CODESTABLE_ALLOW_MAIN_CHECKOUT_IMPLEMENTATION", "1")
    ok, findings, _meta = gate.validate(repo)
    assert ok
    assert findings == []


def test_path_named_worktree_dir_is_not_linked_worktree(tmp_path: Path) -> None:
    repo_parent = tmp_path / ".worktree"
    repo_parent.mkdir(parents=True)
    repo = repo_parent / "plain-repo"
    repo.mkdir()
    run(repo, "init", "-b", "main")
    run(repo, "config", "user.email", "test@example.com")
    run(repo, "config", "user.name", "Test User")
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    run(repo, "add", "README.md")
    run(repo, "commit", "-m", "init")
    (repo / "src").mkdir()
    (repo / "src/app.py").write_text("print('x')\n", encoding="utf-8")

    ok, findings, meta = gate.validate(repo)

    assert not ok
    assert meta["linked_worktree"] is False
    assert "outside a linked worktree" in findings[0].message


def test_completed_feature_requires_review_evidence(tmp_path: Path, monkeypatch) -> None:
    repo = init_repo(tmp_path)
    monkeypatch.setenv("CODESTABLE_ALLOW_MAIN_CHECKOUT_IMPLEMENTATION", "1")
    unit = repo / ".codestable/features/2026-05-25-demo"
    unit.mkdir(parents=True)
    (unit / "demo-checklist.yaml").write_text(
        "steps:\n"
        "  - id: one\n"
        "    status: done\n",
        encoding="utf-8",
    )
    (repo / "src").mkdir()
    (repo / "src/app.py").write_text("print('x')\n", encoding="utf-8")

    ok, findings, _meta = gate.validate(repo)

    assert not ok
    assert findings[0].path == ".codestable/features/2026-05-25-demo/demo-review.md"


def test_review_evidence_satisfies_completed_feature(tmp_path: Path, monkeypatch) -> None:
    repo = init_repo(tmp_path)
    monkeypatch.setenv("CODESTABLE_ALLOW_MAIN_CHECKOUT_IMPLEMENTATION", "1")
    unit = repo / ".codestable/features/2026-05-25-demo"
    unit.mkdir(parents=True)
    (unit / "demo-checklist.yaml").write_text(
        "steps:\n"
        "  - id: one\n"
        "    status: done\n",
        encoding="utf-8",
    )
    (unit / "demo-review.md").write_text("reviewer: subagent\n", encoding="utf-8")

    ok, findings, _meta = gate.validate(repo)

    assert ok
    assert findings == []


def test_self_review_evidence_requires_explicit_fallback(tmp_path: Path, monkeypatch) -> None:
    repo = init_repo(tmp_path)
    monkeypatch.setenv("CODESTABLE_ALLOW_MAIN_CHECKOUT_IMPLEMENTATION", "1")
    unit = repo / ".codestable/features/2026-05-25-demo"
    unit.mkdir(parents=True)
    (unit / "demo-ff-note.md").write_text("done\n", encoding="utf-8")
    (unit / "demo-review.md").write_text("reviewer: self\n", encoding="utf-8")
    (repo / "src").mkdir()
    (repo / "src/app.py").write_text("print('x')\n", encoding="utf-8")

    ok, findings, _meta = gate.validate(repo)

    assert not ok
    assert "must use a subagent reviewer" in findings[0].message

    monkeypatch.setenv("CODESTABLE_ALLOW_SELF_REVIEW_FALLBACK", "1")
    ok, findings, _meta = gate.validate(repo)

    assert ok
    assert findings == []


def test_self_review_explanation_does_not_count_as_subagent_evidence(tmp_path: Path, monkeypatch) -> None:
    repo = init_repo(tmp_path)
    monkeypatch.setenv("CODESTABLE_ALLOW_MAIN_CHECKOUT_IMPLEMENTATION", "1")
    unit = repo / ".codestable/features/2026-05-25-demo"
    unit.mkdir(parents=True)
    (unit / "demo-ff-note.md").write_text("done\n", encoding="utf-8")
    (unit / "demo-review.md").write_text(
        "reviewer: self\nNo subagent reviewer was available.\n",
        encoding="utf-8",
    )
    (repo / "src").mkdir()
    (repo / "src/app.py").write_text("print('x')\n", encoding="utf-8")

    ok, findings, _meta = gate.validate(repo)

    assert not ok
    assert "must use a subagent reviewer" in findings[0].message


def test_issue_fix_note_requires_review_evidence(tmp_path: Path, monkeypatch) -> None:
    repo = init_repo(tmp_path)
    monkeypatch.setenv("CODESTABLE_ALLOW_MAIN_CHECKOUT_IMPLEMENTATION", "1")
    unit = repo / ".codestable/issues/2026-05-25-demo"
    unit.mkdir(parents=True)
    (unit / "demo-fix-note.md").write_text("fixed\n", encoding="utf-8")
    (repo / "src").mkdir()
    (repo / "src/app.py").write_text("print('x')\n", encoding="utf-8")

    ok, findings, _meta = gate.validate(repo)

    assert not ok
    assert findings[0].path == ".codestable/issues/2026-05-25-demo/demo-review.md"


def test_refactor_apply_notes_requires_review_evidence(tmp_path: Path, monkeypatch) -> None:
    repo = init_repo(tmp_path)
    monkeypatch.setenv("CODESTABLE_ALLOW_MAIN_CHECKOUT_IMPLEMENTATION", "1")
    unit = repo / ".codestable/refactors/2026-05-25-demo"
    unit.mkdir(parents=True)
    (unit / "demo-apply-notes.md").write_text("applied\n", encoding="utf-8")
    (repo / "src").mkdir()
    (repo / "src/app.py").write_text("print('x')\n", encoding="utf-8")

    ok, findings, _meta = gate.validate(repo)

    assert not ok
    assert findings[0].path == ".codestable/refactors/2026-05-25-demo/demo-review.md"
