#!/usr/bin/env python3
"""Shared CodeStable runtime asset checks and sync helpers."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


MANIFEST_PATH = ".codestable/runtime-manifest.json"
MANAGED_PATHS = [
    ".codestable/gates",
    ".codestable/reference",
    ".codestable/.gitignore",
    MANIFEST_PATH,
]
PRESERVED_LEGACY_RUNTIME_PATHS = {
    ".codestable/reference/worktree-conventions.md",
    ".codestable/reference/branch-guard-hooks.md",
    ".codestable/hooks/hooks.codex.json",
}
REPO_RUNTIME_CAPABILITIES: dict[str, list[str]] = {
    "base": [
        ".codestable/attention.md",
        ".codestable/reference/execution-conventions.md",
        ".codestable/reference/shared-conventions.md",
        ".codestable/reference/agent-conventions.md",
        ".codestable/reference/tools.md",
        MANIFEST_PATH,
    ],
    "goal-gates": [
        ".codestable/gates/roadmap-goal-gates.yaml",
    ],
}
SKILL_TOOL_CAPABILITIES: dict[str, list[str]] = {
    "runtime-assets": [
        "gates",
        "references",
        "codestable.gitignore",
    ],
    "base": [
        "tools/validate-yaml.py",
        "tools/search-yaml.py",
        "tools/codestable-doctor.py",
        "tools/build-review-packet.py",
    ],
    "workflow-next": [
        "tools/codestable-workflow-next.py",
    ],
    "goal-gates": [
        "tools/codestable-scope-gate.py",
        "tools/codestable-dod-contract-gate.py",
        "tools/codestable-dod-runner.py",
        "tools/codestable-evidence-pack.py",
        "tools/codestable-goal-consistency-gate.py",
    ],
}


def discover_plugin_version(source_skill_dir: Path | None) -> str | None:
    if source_skill_dir is None:
        return None
    current = source_skill_dir.resolve()
    for directory in [current, *current.parents]:
        version_file = directory / "VERSION"
        if version_file.is_file():
            version = version_file.read_text(encoding="utf-8").strip()
            if version:
                return version
        for rel in (".codex-plugin/plugin.json", ".claude-plugin/plugin.json"):
            plugin_json = directory / rel
            if plugin_json.is_file():
                try:
                    data = json.loads(plugin_json.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    continue
                version = data.get("version") if isinstance(data, dict) else None
                if isinstance(version, str) and version:
                    return version
    return None


def read_manifest(root: Path) -> dict[str, Any] | None:
    path = root / MANIFEST_PATH
    if path.is_symlink() or not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def git_dirty_managed_paths(root: Path) -> list[str]:
    if subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0:
        return []
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", *MANAGED_PATHS],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    dirty: list[str] = []
    for line in result.stdout.splitlines():
        if line:
            path = line[3:].strip('"')
            if path in PRESERVED_LEGACY_RUNTIME_PATHS:
                continue
            dirty.append(path)
    return dirty


def runtime_asset_pairs(root: Path, source_skill_dir: Path) -> list[tuple[Path, Path]]:
    return [
        (source_skill_dir / "gates", root / ".codestable/gates"),
        (source_skill_dir / "references", root / ".codestable/reference"),
    ]


def source_skill_path_available(source_skill_dir: Path | None, relative: str) -> bool:
    if source_skill_dir is None:
        return False
    path = source_skill_dir / relative
    if relative in {"gates", "references"}:
        return path.is_dir()
    return path.is_file()


def ignored_runtime_asset(root: Path, path: Path, relative: Path) -> bool:
    root_relative = path.relative_to(root).as_posix()
    return (
        root_relative in PRESERVED_LEGACY_RUNTIME_PATHS
        or "__pycache__" in relative.parts
        or path.suffix == ".pyc"
    )


def runtime_copy_ignored_names(
    root: Path,
    source_root: Path,
    target_root: Path,
    directory: str,
    names: list[str],
) -> set[str]:
    relative_directory = Path(directory).relative_to(source_root)
    ignored: set[str] = set()
    for name in names:
        relative = relative_directory / name
        target = target_root / relative
        if ignored_runtime_asset(root, target, relative):
            ignored.add(name)
    return ignored


def runtime_target_only_paths(root: Path, source_skill_dir: Path) -> list[str]:
    if (root / ".codestable").is_symlink():
        return [".codestable"]
    target_only: list[str] = []
    for source_root, target_root in runtime_asset_pairs(root, source_skill_dir):
        if not source_root.is_dir():
            continue
        if target_root.is_symlink():
            target_only.append(target_root.relative_to(root).as_posix())
            continue
        if not target_root.is_dir():
            continue
        source_files = {
            path.relative_to(source_root)
            for path in source_root.rglob("*")
            if path.is_file()
            and not ignored_runtime_asset(
                root,
                target_root / path.relative_to(source_root),
                path.relative_to(source_root),
            )
        }
        for target in target_root.rglob("*"):
            relative = target.relative_to(target_root)
            if ignored_runtime_asset(root, target, relative):
                continue
            if target.is_symlink() or (target.is_file() and relative not in source_files):
                target_only.append(target.relative_to(root).as_posix())
    return sorted(set(target_only))


def runtime_drift_paths(root: Path, source_skill_dir: Path | None) -> list[str]:
    if source_skill_dir is None:
        return []
    drifted = runtime_target_only_paths(root, source_skill_dir)
    for source_root, target_root in runtime_asset_pairs(root, source_skill_dir):
        if not source_root.is_dir() or target_root.is_symlink():
            continue
        for source in source_root.rglob("*"):
            relative = source.relative_to(source_root)
            if (
                not source.is_file()
                or ignored_runtime_asset(root, target_root / relative, relative)
            ):
                continue
            target = target_root / relative
            if target.is_symlink() or not target.is_file() or source.read_bytes() != target.read_bytes():
                drifted.append(target.relative_to(root).as_posix())
    gitignore = source_skill_dir / "codestable.gitignore"
    target_gitignore = root / ".codestable/.gitignore"
    if gitignore.is_file() and (
        target_gitignore.is_symlink()
        or not target_gitignore.is_file()
        or gitignore.read_bytes() != target_gitignore.read_bytes()
    ):
        drifted.append(target_gitignore.relative_to(root).as_posix())
    manifest = root / MANIFEST_PATH
    if manifest.is_symlink():
        drifted.append(MANIFEST_PATH)
    return sorted(set(drifted))


def remove_target_only_runtime_assets(root: Path, source_skill_dir: Path) -> list[str]:
    if (root / ".codestable").is_symlink():
        return []
    removed = runtime_target_only_paths(root, source_skill_dir)
    for relative in removed:
        target = root / relative
        if target.is_symlink() or target.is_file():
            target.unlink()
    for _, target_root in runtime_asset_pairs(root, source_skill_dir):
        if not target_root.is_dir():
            continue
        directories = sorted(
            (path for path in target_root.rglob("*") if path.is_dir() and not path.is_symlink()),
            key=lambda path: len(path.parts),
            reverse=True,
        )
        for directory in directories:
            try:
                directory.rmdir()
            except OSError:
                pass
    return removed


def runtime_health(root: Path, source_skill_dir: Path | None = None, plugin_version: str | None = None) -> dict[str, Any]:
    root = root.resolve()
    runtime_root_is_symlink = (root / ".codestable").is_symlink()
    expected_version = plugin_version or discover_plugin_version(source_skill_dir)
    manifest = read_manifest(root)
    capabilities: dict[str, Any] = {}
    missing_all: list[str] = []
    source_skill_dir = source_skill_dir.resolve() if source_skill_dir else None
    for name in sorted(set(REPO_RUNTIME_CAPABILITIES) | set(SKILL_TOOL_CAPABILITIES)):
        repo_paths = REPO_RUNTIME_CAPABILITIES.get(name, [])
        skill_paths = SKILL_TOOL_CAPABILITIES.get(name, [])
        missing_repo = [path for path in repo_paths if not (root / path).exists()]
        missing_skill = [
            path
            for path in skill_paths
            if not source_skill_path_available(source_skill_dir, path)
        ]
        capabilities[name] = {
            "ok": not missing_repo and not missing_skill,
            "required_paths": repo_paths + skill_paths,
            "repo_paths": repo_paths,
            "skill_tool_paths": skill_paths,
            "missing": missing_repo + missing_skill,
            "missing_repo": missing_repo,
            "missing_skill_tools": missing_skill,
        }
        missing_all.extend(missing_repo + missing_skill)

    installed_version = manifest.get("plugin_version") if manifest else None
    drifted_paths = [".codestable"] if runtime_root_is_symlink else runtime_drift_paths(root, source_skill_dir)
    if runtime_root_is_symlink:
        status = "unsafe-runtime-root"
        hint = "Replace the .codestable symlink with a real repository directory before runtime sync."
    elif not (root / ".codestable").exists():
        status = "not-onboarded"
        hint = "Run `cs-onboard` to create the CodeStable skeleton."
    elif ".codestable/attention.md" in missing_all:
        status = "onboard-incomplete"
        hint = "Run `cs-onboard` to complete the skeleton; runtime sync does not create attention.md."
    elif missing_all:
        status = "runtime-incomplete"
        hint = "Run runtime sync or `cs-onboard --mode refresh-runtime` to refresh repo-local assets; missing skill tools require reinstalling/updating CodeStable."
    elif expected_version is None:
        status = "version-unavailable"
        hint = "Reinstall or update cs-onboard; the installed skill package is missing CodeStable version metadata."
    elif installed_version != expected_version:
        status = "version-mismatch"
        hint = "Run runtime sync to refresh .codestable runtime assets for the installed CodeStable plugin."
    elif drifted_paths:
        status = "runtime-drift"
        hint = "Run runtime sync to refresh package-owned assets that differ from or no longer exist in the installed skill templates."
    else:
        status = "ok"
        hint = "runtime assets ok"

    return {
        "status": status,
        "ok": status == "ok",
        "hint": hint,
        "manifest": manifest,
        "installed_plugin_version": installed_version,
        "expected_plugin_version": expected_version,
        "capabilities": capabilities,
        "missing": missing_all,
        "drifted_paths": drifted_paths,
        "tool_runtime": "skill-global",
    }


def write_manifest(root: Path, plugin_version: str) -> None:
    path = root / MANIFEST_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        path.unlink()
    data = {
        "schema_version": 1,
        "plugin": "codestable",
        "plugin_version": plugin_version,
        "runtime_version": plugin_version,
        "tool_runtime": "skill-global",
        "managed_paths": MANAGED_PATHS,
        "updated_by": "codestable-runtime-sync",
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sync_runtime(root: Path, source_skill_dir: Path, plugin_version: str | None = None, force: bool = False) -> dict[str, Any]:
    root = root.resolve()
    source_skill_dir = source_skill_dir.resolve()
    version = plugin_version or discover_plugin_version(source_skill_dir)
    if (root / ".codestable").is_symlink():
        return {
            "ok": False,
            "status": "unsafe-runtime-root",
            "removed_paths": [],
            "hint": "Replace the .codestable symlink with a real repository directory before runtime sync.",
        }
    if not (root / ".codestable/attention.md").is_file():
        return {
            "ok": False,
            "status": "onboard-incomplete",
            "hint": "Run `cs-onboard` first; runtime sync does not create attention.md.",
        }
    missing_source_assets = [
        path
        for path in SKILL_TOOL_CAPABILITIES["runtime-assets"]
        if not source_skill_path_available(source_skill_dir, path)
    ]
    if missing_source_assets:
        return {
            "ok": False,
            "status": "runtime-incomplete",
            "removed_paths": [],
            "missing_source_assets": missing_source_assets,
            "hint": "Reinstall or update cs-onboard; the installed skill package is missing runtime source assets.",
        }
    dirty = git_dirty_managed_paths(root)
    if dirty and not force:
        return {
            "ok": False,
            "status": "managed-paths-dirty",
            "dirty_paths": dirty,
            "hint": "Commit, stash, or explicitly allow overwriting managed runtime assets before sync.",
        }
    if version is None:
        return {
            "ok": False,
            "status": "version-unavailable",
            "hint": "Reinstall or update cs-onboard; the installed skill package is missing CodeStable version metadata.",
        }

    removed_paths = remove_target_only_runtime_assets(root, source_skill_dir)
    copies = [
        ("gates", ".codestable/gates"),
        ("references", ".codestable/reference"),
    ]
    for source_rel, target_rel in copies:
        source = source_skill_dir / source_rel
        target = root / target_rel
        if source.is_dir():
            shutil.copytree(
                source,
                target,
                dirs_exist_ok=True,
                ignore=lambda directory, names: runtime_copy_ignored_names(
                    root, source, target, directory, names
                ),
            )
    gitignore = source_skill_dir / "codestable.gitignore"
    if gitignore.is_file():
        target_gitignore = root / ".codestable/.gitignore"
        if target_gitignore.is_symlink():
            target_gitignore.unlink()
        shutil.copy2(gitignore, target_gitignore)
    write_manifest(root, version)
    health = runtime_health(root, source_skill_dir=source_skill_dir, plugin_version=version)
    return {
        "ok": health["ok"],
        "status": health["status"],
        "plugin_version": version,
        "removed_paths": removed_paths,
        "health": health,
    }
