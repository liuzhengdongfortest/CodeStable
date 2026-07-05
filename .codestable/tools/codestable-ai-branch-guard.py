#!/usr/bin/env python3
"""Guard AI agents from mutating protected checkouts.

The primary protection target is an agent command hook such as Claude Code
PreToolUse. Git has no pre-checkout/pre-switch hook, so branch switching must be
blocked before the shell command runs. Git hooks installed by this script are a
commit-time fallback only.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import stat
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from codestable_common import (
    current_branch,
    git_status,
    is_implementation_path,
    is_linked_worktree,
    run_git,
    staged_files,
)


PROTECTED_BRANCHES = ("main", "master")
EDIT_TOOL_NAMES = {
    "Edit",
    "MultiEdit",
    "NotebookEdit",
    "Write",
    "apply_patch",
    "functions.apply_patch",
    "str_replace_editor",
}
GIT_OPTIONS_WITH_VALUE = {
    "-C",
    "-c",
    "--config-env",
    "--exec-path",
    "--git-dir",
    "--namespace",
    "--super-prefix",
    "--work-tree",
}
PROTECTED_WRITE_COMMANDS = {"add", "commit", "merge", "rebase", "cherry-pick", "revert", "apply", "am", "reset", "stash", "rm", "mv", "push"}
HOOK_MARKER = "# CodeStable AI branch guard"
PUBLISH_INTENT_FILENAME = "codestable-main-publish-intent.json"


@dataclass(frozen=True)
class GuardResult:
    ok: bool
    message: str
    reason: str
    branch: str | None
    linked_worktree: bool
    paths: tuple[str, ...] = ()


def protected_set(value: str | None) -> set[str]:
    if not value:
        return set(PROTECTED_BRANCHES)
    return {item.strip() for item in value.split(",") if item.strip()}


def resolve_root(value: str | None) -> Path:
    if value:
        return Path(value).expanduser().resolve()
    for env_name in ("CODEX_PROJECT_DIR", "CLAUDE_PROJECT_DIR", "PWD"):
        env_value = os.environ.get(env_name)
        if env_value:
            candidate = Path(env_value).expanduser().resolve()
            if (candidate / ".git").exists() or run_git(candidate, "rev-parse", "--is-inside-work-tree").returncode == 0:
                return candidate
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip()).resolve()
    return Path.cwd().resolve()


def payload_tool_input(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("tool_input") or payload.get("input") or {}
    return value if isinstance(value, dict) else {}


def payload_command(payload: dict[str, Any]) -> str | None:
    tool_input = payload_tool_input(payload)
    for key in ("command", "cmd"):
        value = tool_input.get(key) or payload.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def normalize_path(root: Path, value: str) -> str | None:
    if not value or "\n" in value:
        return None
    path = Path(value).expanduser()
    try:
        if path.is_absolute():
            path = path.resolve().relative_to(root)
    except ValueError:
        return None
    raw = path.as_posix().strip()
    if not raw or raw.startswith("../"):
        return None
    return raw


def collect_paths(value: Any, root: Path) -> list[str]:
    paths: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"file_path", "path", "filename"} and isinstance(child, (str, os.PathLike)):
                normalized = normalize_path(root, os.fspath(child))
                if normalized:
                    paths.append(normalized)
            else:
                paths.extend(collect_paths(child, root))
    elif isinstance(value, list):
        for child in value:
            paths.extend(collect_paths(child, root))
    return paths


def payload_paths(payload: dict[str, Any], root: Path) -> list[str]:
    return sorted(set(collect_paths(payload_tool_input(payload), root)))


def shell_tokens(command: str) -> list[str]:
    try:
        return shlex.split(command)
    except ValueError:
        return command.split()


def git_invocations(command: str) -> list[tuple[str, list[str]]]:
    invocations: list[tuple[str, list[str]]] = []
    tokens = shell_tokens(command)
    for index, token in enumerate(tokens):
        if token != "git":
            continue
        cursor = index + 1
        while cursor < len(tokens) and tokens[cursor].startswith("-"):
            option = tokens[cursor]
            if option in GIT_OPTIONS_WITH_VALUE and cursor + 1 < len(tokens):
                cursor += 2
            else:
                cursor += 1
        if cursor < len(tokens):
            invocations.append((tokens[cursor], tokens[cursor + 1 :]))
    return invocations


def implementation_args(args: list[str]) -> list[str]:
    paths = [arg for arg in args if not arg.startswith("-") and arg not in {".", "--"}]
    return [path for path in paths if is_implementation_path(path)]


def dirty_implementation_paths(root: Path) -> list[str]:
    return sorted(item.path for item in git_status(root) if is_implementation_path(item.path))


def staged_implementation_paths(root: Path) -> list[str]:
    return sorted(item.path for item in staged_files(root) if is_implementation_path(item.path))


def git_common_dir(root: Path) -> Path:
    result = run_git(root, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip()).resolve()
    return root / ".git"


def publish_intent_path(root: Path) -> Path:
    return git_common_dir(root) / PUBLISH_INTENT_FILENAME


def merge_in_progress(root: Path) -> bool:
    result = run_git(root, "rev-parse", "--git-path", "MERGE_HEAD")
    path = (root / result.stdout.strip()).resolve() if result.returncode == 0 and result.stdout.strip() else root / ".git/MERGE_HEAD"
    return path.exists()


def active_publish_intent(root: Path, protected: set[str]) -> dict[str, Any] | None:
    path = publish_intent_path(root)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    branch = current_branch(root)
    if branch not in protected:
        return None
    if payload.get("target_branch") != branch:
        return None
    root_value = payload.get("root")
    if not isinstance(root_value, str) or not root_value.strip():
        return None
    if Path(root_value).expanduser().resolve() != root.resolve():
        return None
    try:
        expires_at = float(payload.get("expires_at", 0))
    except (TypeError, ValueError):
        return None
    if expires_at <= time.time():
        return None
    if not str(payload.get("owner_intent", "")).strip():
        return None
    return payload


def publish_intent_allows_command(root: Path, subcommand: str, args: list[str], intent: dict[str, Any] | None) -> bool:
    if not intent:
        return False
    if subcommand == "merge":
        return True
    if subcommand == "push":
        return not any(
            arg == "-f" or arg.startswith(("--force", "--force-with-lease", "--force-if-includes"))
            for arg in args
        )
    return subcommand in {"add", "commit"} and merge_in_progress(root)


def command_write_block(root: Path, command: str, intent: dict[str, Any] | None = None) -> tuple[str, tuple[str, ...]] | None:
    for subcommand, args in git_invocations(command):
        if subcommand not in PROTECTED_WRITE_COMMANDS:
            continue

        if publish_intent_allows_command(root, subcommand, args, intent):
            continue

        if subcommand == "add":
            impl = implementation_args(args)
            if "." in args or "--all" in args or "-A" in args:
                impl = dirty_implementation_paths(root)
            if impl:
                return ("git_add_implementation_on_protected_branch", tuple(impl))
            continue

        if subcommand == "commit":
            impl = staged_implementation_paths(root)
            if impl:
                return ("git_commit_implementation_on_protected_branch", tuple(impl))
            continue

        return (f"git_{subcommand}_on_protected_branch", ())

    return None


def branch_switch_block(command: str) -> bool:
    return any(subcommand in {"switch", "checkout"} for subcommand, _args in git_invocations(command))


def worktree_of(path: Path) -> Path | None:
    """Return the git worktree toplevel that owns *path* (file or dir), or None.

    Used so the guard judges the branch of the file/command being acted on,
    not the branch of the --root passed by the PreToolUse hook (which is the
    session project dir and does not follow EnterWorktree)."""
    target = path if path.is_dir() else path.parent
    # The path may not exist yet (e.g. a Write to a new file/dir); walk up to the
    # nearest existing ancestor so run_git has a valid cwd.
    while not target.exists() and target != target.parent:
        target = target.parent
    if not target.exists():
        return None
    result = run_git(target, "rev-parse", "--show-toplevel")
    if result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip()).resolve()
    return None


def collect_raw_paths(value: Any) -> list[str]:
    """Collect raw (un-normalized, possibly absolute) edit target paths."""
    out: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"file_path", "path", "filename"} and isinstance(child, (str, os.PathLike)):
                out.append(os.fspath(child))
            else:
                out.extend(collect_raw_paths(child))
    elif isinstance(value, list):
        for child in value:
            out.extend(collect_raw_paths(child))
    return out


def edit_impl_paths_on_protected(payload: dict[str, Any], root: Path, protected: set[str]) -> tuple[str, ...]:
    """Implementation files being edited that truly live on a protected branch.

    A file whose own worktree is on a typed branch (feat/fix/...) is allowed,
    even if it sits physically under the main checkout (e.g. .claude/worktrees/)."""
    impl: list[str] = []
    for raw in collect_raw_paths(payload_tool_input(payload)):
        if not raw or "\n" in raw:
            continue
        ap = Path(raw).expanduser()
        if not ap.is_absolute():
            ap = root / ap
        try:
            ap = ap.resolve()
        except OSError:
            continue
        wt = worktree_of(ap)
        if wt is not None:
            wb = current_branch(wt)
            if wb is not None and wb not in protected:
                continue  # file belongs to a typed-branch worktree -> allow
        base = wt or root
        try:
            rel = ap.relative_to(base).as_posix()
        except ValueError:
            rel = ap.name
        if is_implementation_path(rel):
            impl.append(rel)
    return tuple(sorted(set(impl)))


def guard_payload(payload: dict[str, Any], root: Path, protected: set[str]) -> GuardResult:
    command = payload_command(payload)
    tool_name = str(payload.get("tool_name") or payload.get("name") or "")

    # A Bash command runs in its cwd's worktree; judge by that real worktree so a
    # command issued from a linked worktree is not mistaken for the main checkout.
    eff_root = root
    cwd_value = payload_tool_input(payload).get("cwd") or payload.get("cwd")
    if command and isinstance(cwd_value, str) and cwd_value.strip():
        wt = worktree_of(Path(cwd_value).expanduser())
        if wt is not None:
            eff_root = wt

    branch = current_branch(eff_root)
    linked = is_linked_worktree(eff_root)

    if command and branch_switch_block(command):
        return GuardResult(
            False,
            "AI agents must not run git switch/checkout in an existing checkout. Create or use a linked git worktree instead.",
            "branch_switch_command",
            branch,
            linked,
        )

    on_protected = branch in protected
    intent = active_publish_intent(eff_root, protected)
    if command and on_protected:
        blocked = command_write_block(eff_root, command, intent)
        if blocked:
            reason, paths = blocked
            return GuardResult(
                False,
                "AI agents must not perform protected-branch development. Use a linked execution worktree on a typed branch (feat/fix/refactor/...).",
                reason,
                branch,
                linked,
                paths,
            )

    if on_protected and tool_name in EDIT_TOOL_NAMES:
        impl_paths = edit_impl_paths_on_protected(payload, root, protected)
        if impl_paths and not (intent and merge_in_progress(eff_root)):
            return GuardResult(
                False,
                "AI agents must not edit implementation files on main/master. Use a linked execution worktree on a typed branch (feat/fix/refactor/...).",
                "implementation_edit_on_protected_branch",
                branch,
                linked,
                impl_paths,
            )

    return GuardResult(True, "allowed", "allowed", branch, linked)


def guard_git_hook(root: Path, hook_name: str, protected: set[str]) -> GuardResult:
    branch = current_branch(root)
    linked = is_linked_worktree(root)
    if branch not in protected:
        return GuardResult(True, "allowed", "allowed", branch, linked)

    intent = active_publish_intent(root, protected)
    if hook_name == "pre-commit":
        if intent and merge_in_progress(root):
            return GuardResult(True, "allowed by owner-intent main publish", "owner_intent_main_publish", branch, linked)
        impl = tuple(staged_implementation_paths(root))
        if impl:
            return GuardResult(
                False,
                "Protected branch commit contains implementation changes. Move the work to a linked execution worktree.",
                "pre_commit_implementation_on_protected_branch",
                branch,
                linked,
                impl,
            )
        return GuardResult(True, "allowed", "allowed", branch, linked)

    return GuardResult(True, "allowed", "allowed", branch, linked)


def hook_path(root: Path, hook_name: str) -> Path:
    result = run_git(root, "rev-parse", "--git-path", f"hooks/{hook_name}")
    if result.returncode == 0 and result.stdout.strip():
        return (root / result.stdout.strip()).resolve()
    return root / ".git" / "hooks" / hook_name


def install_git_hooks(root: Path, force: bool) -> list[Path]:
    installed: list[Path] = []
    script = root / ".codestable" / "tools" / "codestable-ai-branch-guard.py"
    fallback = Path(__file__).resolve()
    for hook_name in ("pre-commit",):
        path = hook_path(root, hook_name)
        if path.exists() and HOOK_MARKER not in path.read_text(encoding="utf-8", errors="ignore") and not force:
            raise RuntimeError(f"refusing to overwrite existing hook without --force: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "#!/usr/bin/env sh\n"
            f"{HOOK_MARKER}\n"
            "ROOT=\"$(git rev-parse --show-toplevel 2>/dev/null)\" || exit 0\n"
            "SCRIPT=\"$ROOT/.codestable/tools/codestable-ai-branch-guard.py\"\n"
            "if [ ! -f \"$SCRIPT\" ]; then\n"
            f"  SCRIPT=\"{fallback.as_posix()}\"\n"
            "fi\n"
            "if [ ! -f \"$SCRIPT\" ]; then\n"
            "  echo \"CodeStable AI branch guard unavailable; allowing Git hook.\" >&2\n"
            "  exit 0\n"
            "fi\n"
            f"exec python3 \"$SCRIPT\" --root \"$ROOT\" --git-hook {hook_name}\n",
            encoding="utf-8",
        )
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        installed.append(path)
    return installed


def emit_result(result: GuardResult, as_json: bool) -> None:
    payload = {
        "ok": result.ok,
        "message": result.message,
        "reason": result.reason,
        "branch": result.branch,
        "linked_worktree": result.linked_worktree,
        "paths": list(result.paths),
    }
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    stream = sys.stdout if result.ok else sys.stderr
    print(result.message, file=stream)
    if result.paths:
        print("Paths: " + ", ".join(result.paths), file=stream)


def load_payload(stdin_text: str, command: str | None) -> dict[str, Any]:
    if command:
        return {"tool_name": "Bash", "tool_input": {"command": command}}
    if stdin_text.strip():
        return json.loads(stdin_text)
    return {}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", help="Repository root")
    parser.add_argument("--protected-branches", default="main,master")
    parser.add_argument("--command", help="Check a shell command without reading hook JSON")
    parser.add_argument("--git-hook", choices=["pre-commit", "pre-merge-commit", "pre-rebase", "pre-push"])
    parser.add_argument("--install-git-hooks", action="store_true", help="Install local Git hook fallbacks")
    parser.add_argument("--force", action="store_true", help="Overwrite existing Git hooks when installing")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = resolve_root(args.root)
    protected = protected_set(args.protected_branches)

    if args.install_git_hooks:
        try:
            installed = install_git_hooks(root, args.force)
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        if args.json:
            print(json.dumps({"ok": True, "installed": [path.as_posix() for path in installed]}, indent=2))
        else:
            for path in installed:
                print(f"installed {path}")
        return 0

    if args.git_hook:
        result = guard_git_hook(root, args.git_hook, protected)
        emit_result(result, args.json)
        return 0 if result.ok else 2

    try:
        payload = load_payload(sys.stdin.read(), args.command)
    except json.JSONDecodeError as exc:
        print(f"invalid hook JSON: {exc}", file=sys.stderr)
        return 1

    result = guard_payload(payload, root, protected)
    emit_result(result, args.json)
    return 0 if result.ok else 2


if __name__ == "__main__":
    sys.exit(main())
