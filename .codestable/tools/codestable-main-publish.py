#!/usr/bin/env python3
"""Create an auditable owner-intent window for publishing protected main.

This tool does not merge by itself. It creates a short-lived intent file that
the branch guard can recognize while an owner-authorized main publish is in
progress.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

from codestable_common import current_branch, git_status, run_git


INTENT_FILENAME = "codestable-main-publish-intent.json"


def git_common_dir(root: Path) -> Path:
    result = run_git(root, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if result.returncode == 0 and result.stdout.strip():
        return Path(result.stdout.strip()).resolve()
    return root / ".git"


def intent_path(root: Path) -> Path:
    return git_common_dir(root) / INTENT_FILENAME


def git_head(root: Path, ref: str) -> str:
    result = run_git(root, "rev-parse", "--verify", ref)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"missing git ref: {ref}")
    return result.stdout.strip()


def detect_default_remote(root: Path, branch: str) -> str:
    """Default publish remote = the upstream remote of *branch* (fork-friendly),
    falling back to 'origin'. Avoids forcing fork users (whose origin is an
    upstream mirror) to remember --remote on every publish."""
    if branch:
        result = run_git(root, "rev-parse", "--abbrev-ref", f"{branch}@{{upstream}}")
        if result.returncode == 0 and "/" in result.stdout.strip():
            return result.stdout.strip().split("/", 1)[0]
    return "origin"


def ensure_clean_target(root: Path, target_branch: str, remote: str) -> None:
    branch = current_branch(root)
    if branch != target_branch:
        raise RuntimeError(f"main publish must start from {target_branch}; current branch is {branch or 'unknown'}")
    dirty = git_status(root)
    if dirty:
        paths = ", ".join(item.path for item in dirty[:10])
        raise RuntimeError(f"working tree must be clean before main publish: {paths}")

    fetch = run_git(root, "fetch", remote, target_branch)
    if fetch.returncode != 0:
        raise RuntimeError((fetch.stderr.strip() or f"failed to fetch {remote}/{target_branch}") + f"; 若发布到 fork,用 --remote <你的 fork remote>(当前 remote={remote})")
    local_head = git_head(root, "HEAD")
    remote_head = git_head(root, f"refs/remotes/{remote}/{target_branch}")
    if local_head != remote_head:
        raise RuntimeError(f"{target_branch} must match {remote}/{target_branch} before publish: {local_head} != {remote_head}; 若发布到 fork(origin 常是上游镜像),用 --remote <你的 fork remote>")


def resolve_publish_refs(root: Path, remote: str, branches: list[str]) -> list[str]:
    refs: list[str] = []
    for branch in branches:
        value = branch.strip()
        if not value:
            continue
        if value.startswith(f"{remote}/"):
            name = value.split("/", 1)[1]
            ref = value
        elif value.startswith("refs/"):
            name = value
            ref = value
        else:
            name = value
            ref = f"{remote}/{value}"
        fetch = run_git(root, "fetch", remote, name)
        if fetch.returncode != 0:
            raise RuntimeError(fetch.stderr.strip() or f"failed to fetch {remote} {name}")
        git_head(root, ref)
        refs.append(ref)
    return refs


def load_intent(root: Path) -> dict[str, Any] | None:
    path = intent_path(root)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def intent_status(root: Path) -> dict[str, Any]:
    payload = load_intent(root)
    path = intent_path(root)
    if not payload:
        return {"active": False, "path": path.as_posix()}
    now = time.time()
    try:
        expires_at = float(payload.get("expires_at", 0))
    except (TypeError, ValueError):
        expires_at = 0
    return {
        "active": expires_at > now,
        "path": path.as_posix(),
        "target_branch": payload.get("target_branch"),
        "remote": payload.get("remote"),
        "branches": payload.get("branches", []),
        "owner_intent": payload.get("owner_intent"),
        "expires_at": payload.get("expires_at"),
        "seconds_remaining": max(0, int(expires_at - now)),
    }


def begin(root: Path, target_branch: str, remote: str, branches: list[str], owner_intent: str, ttl_minutes: int) -> dict[str, Any]:
    if not owner_intent.strip():
        raise RuntimeError("--owner-intent is required")
    if ttl_minutes <= 0 or ttl_minutes > 240:
        raise RuntimeError("--ttl-minutes must be between 1 and 240")
    ensure_clean_target(root, target_branch, remote)
    refs = resolve_publish_refs(root, remote, branches)

    now = time.time()
    payload = {
        "version": 1,
        "root": root.resolve().as_posix(),
        "target_branch": target_branch,
        "remote": remote,
        "branches": refs,
        "owner_intent": owner_intent.strip(),
        "created_at": now,
        "expires_at": now + ttl_minutes * 60,
    }
    path = intent_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    path.chmod(0o600)
    return {"ok": True, "path": path.as_posix(), **intent_status(root)}


def end(root: Path) -> dict[str, Any]:
    path = intent_path(root)
    existed = path.exists()
    if existed:
        path.unlink()
    return {"ok": True, "removed": existed, "path": path.as_posix()}


def emit(payload: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--json", action="store_true")
    subparsers = parser.add_subparsers(dest="command", required=True)

    begin_parser = subparsers.add_parser("begin", help="Create a short-lived publish intent")
    begin_parser.add_argument("--target-branch", default="main")
    begin_parser.add_argument("--remote", default=None, help="Publish remote (default: current branch upstream remote, else origin)")
    begin_parser.add_argument("--branch", action="append", default=[], help="Remote branch intended for merge")
    begin_parser.add_argument("--owner-intent", required=True)
    begin_parser.add_argument("--ttl-minutes", type=int, default=30)

    subparsers.add_parser("status", help="Show current publish intent")
    subparsers.add_parser("end", help="Remove current publish intent")

    args = parser.parse_args()
    root = Path(args.root).expanduser().resolve()
    try:
        if args.command == "begin":
            remote = args.remote or detect_default_remote(root, args.target_branch)
            payload = begin(root, args.target_branch, remote, args.branch, args.owner_intent, args.ttl_minutes)
        elif args.command == "status":
            payload = {"ok": True, **intent_status(root)}
        elif args.command == "end":
            payload = end(root)
        else:
            raise RuntimeError(f"unknown command: {args.command}")
    except RuntimeError as exc:
        payload = {"ok": False, "error": str(exc)}
        emit(payload, args.json)
        return 1

    emit(payload, args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
