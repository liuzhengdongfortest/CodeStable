from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "cs-onboard/tools"
sys.path.insert(0, str(TOOLS_DIR))


def load_tool(module_name: str, filename: str):
    spec = importlib.util.spec_from_file_location(module_name, TOOLS_DIR / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


guard = load_tool("codestable_ai_branch_guard", "codestable-ai-branch-guard.py")
main_publish = load_tool("codestable_main_publish", "codestable-main-publish.py")


def run(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=check,
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


def init_repo_with_remote(tmp_path: Path) -> Path:
    remote = tmp_path / "remote.git"
    run(tmp_path, "init", "--bare", remote.as_posix())
    repo = init_repo(tmp_path)
    run(repo, "remote", "add", "origin", remote.as_posix())
    run(repo, "push", "-u", "origin", "main")
    return repo


def test_blocks_git_switch_command(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    payload = {"tool_name": "Bash", "tool_input": {"command": "git switch feat/demo"}}

    result = guard.guard_payload(payload, repo, {"main", "master"})

    assert not result.ok
    assert result.reason == "branch_switch_command"


def test_blocks_git_switch_with_global_options(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    payload = {"tool_name": "Bash", "tool_input": {"command": f"git -C {repo.as_posix()} switch feat/demo"}}

    result = guard.guard_payload(payload, repo, {"main", "master"})

    assert not result.ok
    assert result.reason == "branch_switch_command"


def test_allows_git_worktree_add_command(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "git worktree add -b feat/demo .worktree/demo HEAD"},
    }

    result = guard.guard_payload(payload, repo, {"main", "master"})

    assert result.ok


def test_blocks_implementation_edit_on_main(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    payload = {"tool_name": "Write", "tool_input": {"file_path": repo / "src/app.py"}}

    result = guard.guard_payload(payload, repo, {"main", "master"})

    assert not result.ok
    assert result.reason == "implementation_edit_on_protected_branch"
    assert result.paths == ("src/app.py",)


def test_allows_codestable_planning_edit_on_main(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    payload = {
        "tool_name": "Write",
        "tool_input": {"file_path": repo / ".codestable/features/2026-06-18-demo/demo-design.md"},
    }

    result = guard.guard_payload(payload, repo, {"main", "master"})

    assert result.ok


def test_pre_commit_blocks_staged_implementation_on_main(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    (repo / "src").mkdir()
    (repo / "src/app.py").write_text("print('x')\n", encoding="utf-8")
    run(repo, "add", "src/app.py")

    result = guard.guard_git_hook(repo, "pre-commit", {"main", "master"})

    assert not result.ok
    assert result.reason == "pre_commit_implementation_on_protected_branch"
    assert result.paths == ("src/app.py",)


def test_owner_intent_allows_protected_pre_push(tmp_path: Path) -> None:
    repo = init_repo_with_remote(tmp_path)

    blocked = guard.guard_git_hook(repo, "pre-push", {"main", "master"})
    created = main_publish.begin(repo, "main", "origin", [], "owner approved release", 5)
    allowed = guard.guard_git_hook(repo, "pre-push", {"main", "master"})

    assert created["ok"]
    assert not blocked.ok
    assert allowed.ok
    assert allowed.reason == "owner_intent_main_publish"


def test_owner_intent_allows_merge_command_but_not_switch(tmp_path: Path) -> None:
    repo = init_repo_with_remote(tmp_path)
    main_publish.begin(repo, "main", "origin", [], "owner approved release", 5)

    merge_payload = {"tool_name": "Bash", "tool_input": {"command": "git merge origin/feat/demo"}}
    switch_payload = {"tool_name": "Bash", "tool_input": {"command": "git switch feat/demo"}}

    assert guard.guard_payload(merge_payload, repo, {"main", "master"}).ok
    assert guard.guard_payload(switch_payload, repo, {"main", "master"}).reason == "branch_switch_command"


def test_owner_intent_does_not_allow_force_push(tmp_path: Path) -> None:
    repo = init_repo_with_remote(tmp_path)
    main_publish.begin(repo, "main", "origin", [], "owner approved release", 5)
    payload = {"tool_name": "Bash", "tool_input": {"command": "git push --force-with-lease origin main"}}

    result = guard.guard_payload(payload, repo, {"main", "master"})

    assert not result.ok
    assert result.reason == "git_push_on_protected_branch"


def test_owner_intent_allows_real_hooked_merge_and_push(tmp_path: Path) -> None:
    repo = init_repo_with_remote(tmp_path)
    run(repo, "switch", "-c", "feat/demo")
    (repo / "README.md").write_text("published\n", encoding="utf-8")
    run(repo, "add", "README.md")
    run(repo, "commit", "-m", "demo change")
    run(repo, "push", "-u", "origin", "feat/demo")
    run(repo, "switch", "main")
    guard.install_git_hooks(repo, force=False)

    main_publish.begin(repo, "main", "origin", ["feat/demo"], "owner approved release", 5)
    merge = run(repo, "merge", "--no-ff", "--no-edit", "origin/feat/demo", check=False)
    push = run(repo, "push", "origin", "main", check=False)
    ended = main_publish.end(repo)

    assert merge.returncode == 0, merge.stderr
    assert push.returncode == 0, push.stderr
    assert ended["removed"]


def test_allows_implementation_edit_in_linked_worktree_branch(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    worktree = tmp_path / "repo-worktree"
    run(repo, "worktree", "add", "-b", "feat/demo", worktree.as_posix())
    payload = {"tool_name": "Write", "tool_input": {"file_path": worktree / "src/app.py"}}

    result = guard.guard_payload(payload, worktree, {"main", "master"})

    assert result.ok


def test_cli_blocks_hook_json_with_status_two(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    payload = {"tool_name": "Bash", "tool_input": {"command": "git checkout main"}}

    result = subprocess.run(
        [
            sys.executable,
            (TOOLS_DIR / "codestable-ai-branch-guard.py").as_posix(),
            "--root",
            repo.as_posix(),
            "--json",
        ],
        input=json.dumps(payload),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 2
    assert json.loads(result.stdout)["reason"] == "branch_switch_command"


def test_installed_git_hook_allows_when_guard_script_is_missing(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)

    [hook] = guard.install_git_hooks(repo, force=False)[:1]
    hook_text = hook.read_text(encoding="utf-8")

    assert "CodeStable AI branch guard unavailable; allowing Git hook." in hook_text
    assert "exit 0" in hook_text


def test_codex_hook_definition_invokes_branch_guard() -> None:
    hook_path = Path(__file__).resolve().parents[1] / "cs-onboard/hooks/hooks.codex.json"
    payload = json.loads(hook_path.read_text(encoding="utf-8"))

    hook_command = payload["hooks"]["PreToolUse"][0]["hooks"][0]["command"]

    assert "codestable-ai-branch-guard.py" in hook_command
    assert "PreToolUse" in payload["hooks"]


def test_allows_worktree_edit_when_root_is_main(tmp_path: Path) -> None:
    """Regression: PreToolUse passes --root=main checkout, but the edited file
    lives in a linked worktree on a typed branch (often under main's
    .claude/worktrees/). It must be allowed, judged by the file's own worktree."""
    repo = init_repo(tmp_path)
    worktree = repo / ".claude" / "worktrees" / "feat-demo"
    worktree.parent.mkdir(parents=True, exist_ok=True)
    run(repo, "worktree", "add", "-b", "feat/demo", worktree.as_posix())
    payload = {"tool_name": "Write", "tool_input": {"file_path": worktree / "cs-onboard/tools/x.py"}}

    # root is the MAIN checkout (on main), not the worktree
    result = guard.guard_payload(payload, repo, {"main", "master"})

    assert result.ok, result.message


def test_still_blocks_main_edit_when_worktree_exists(tmp_path: Path) -> None:
    """A file on the main checkout itself is still blocked even when worktrees exist."""
    repo = init_repo(tmp_path)
    worktree = repo / ".claude" / "worktrees" / "feat-demo"
    worktree.parent.mkdir(parents=True, exist_ok=True)
    run(repo, "worktree", "add", "-b", "feat/demo", worktree.as_posix())
    payload = {"tool_name": "Write", "tool_input": {"file_path": repo / "src/app.py"}}

    result = guard.guard_payload(payload, repo, {"main", "master"})

    assert not result.ok
    assert result.reason == "implementation_edit_on_protected_branch"


def test_bash_uses_cwd_worktree_branch(tmp_path: Path) -> None:
    """A Bash git command whose cwd is a typed-branch worktree is judged by that
    worktree's branch, not by the main --root."""
    repo = init_repo(tmp_path)
    worktree = repo / ".claude" / "worktrees" / "feat-demo"
    worktree.parent.mkdir(parents=True, exist_ok=True)
    run(repo, "worktree", "add", "-b", "feat/demo", worktree.as_posix())
    (worktree / "src").mkdir(parents=True, exist_ok=True)
    (worktree / "src/app.py").write_text("x=1\n", encoding="utf-8")
    run(worktree, "add", "src/app.py")
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": "git commit -m wip", "cwd": worktree.as_posix()},
    }

    result = guard.guard_payload(payload, repo, {"main", "master"})

    assert result.ok, result.message


def test_main_publish_default_remote_follows_upstream(tmp_path: Path) -> None:
    """detect_default_remote returns the branch's upstream remote (fork-friendly)."""
    repo = init_repo_with_remote(tmp_path)
    # rename origin -> fork and re-point upstream, simulating a fork remote
    run(repo, "remote", "rename", "origin", "fork")
    run(repo, "fetch", "fork", "main")
    run(repo, "branch", "--set-upstream-to=fork/main", "main")

    assert main_publish.detect_default_remote(repo, "main") == "fork"


def test_main_publish_begin_accepts_custom_remote(tmp_path: Path) -> None:
    """begin compares against the given --remote, not a hardcoded origin."""
    repo = init_repo_with_remote(tmp_path)
    run(repo, "remote", "rename", "origin", "fork")
    created = main_publish.begin(repo, "main", "fork", [], "owner approved release", 5)

    assert created["ok"] is True
    assert created["remote"] == "fork"
