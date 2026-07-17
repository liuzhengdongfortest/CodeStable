from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "plugins/codestable/skills/cs-onboard/tools"
PACKET_CLI = TOOLS_DIR / "build-review-packet.py"
sys.path.insert(0, str(TOOLS_DIR))


def load_tool():
    spec = importlib.util.spec_from_file_location("build_review_packet", PACKET_CLI)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


packet_tool = load_tool()


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def init_repo(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "Test User")
    unit = repo / ".codestable/features/demo"
    write(
        unit / "demo-design.md",
        "---\ndoc_type: feature-design\nstatus: approved\n---\n# Demo\n",
    )
    write(repo / "src/app.py", "def value():\n    return 1\n")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "init")
    return repo, unit


def test_legacy_packet_matches_golden_without_new_flags(tmp_path: Path) -> None:
    repo, unit = init_repo(tmp_path)
    packet = packet_tool.build_packet(
        repo,
        unit.relative_to(repo).as_posix(),
        ["pytest -> passed"],
    )
    expected = (ROOT / "tests/fixtures/review_packet_legacy.md").read_text(encoding="utf-8")
    expected = expected.replace("{ROOT}", repo.resolve().as_posix())

    assert packet == expected


def test_cli_without_new_flags_writes_legacy_golden(tmp_path: Path) -> None:
    repo, unit = init_repo(tmp_path)
    output = tmp_path / "legacy.md"
    result = subprocess.run(
        [
            sys.executable,
            str(PACKET_CLI),
            "--root",
            str(repo),
            "--unit",
            unit.relative_to(repo).as_posix(),
            "--output",
            str(output),
            "--validation",
            "pytest -> passed",
        ],
        cwd=repo,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    expected = (ROOT / "tests/fixtures/review_packet_legacy.md").read_text(encoding="utf-8")
    expected = expected.replace("{ROOT}", repo.resolve().as_posix())

    assert result.returncode == 0, result.stderr
    assert result.stdout == f"{output.as_posix()}\n"
    assert result.stderr == ""
    assert output.read_text(encoding="utf-8") == expected


def test_workspace_transport_contains_only_locators_and_no_fenced_body(tmp_path: Path) -> None:
    repo, unit = init_repo(tmp_path)
    write(repo / "src/app.py", "def value():\n    return 2  # ALLOWED-BODY\n")
    write(repo / "notes/unrelated.md", "UNRELATED-SENTINEL\n")

    packet = packet_tool.build_packet(
        repo,
        unit.relative_to(repo).as_posix(),
        ["line one\nline two"],
        transport="workspace",
        include_paths=[unit.relative_to(repo).as_posix(), "src/app.py"],
    )

    assert ".codestable/features/demo/demo-design.md" in packet
    assert "src/app.py" in packet
    assert "# Demo" not in packet
    assert "ALLOWED-BODY" not in packet
    assert "UNRELATED-SENTINEL" not in packet
    assert "```" not in packet


def test_scoped_portable_excludes_unlisted_content_and_tails_validation(tmp_path: Path) -> None:
    repo, unit = init_repo(tmp_path)
    write(repo / "requirements/spec.md", "# EXTERNAL-SPEC\n")
    git(repo, "add", "requirements/spec.md")
    git(repo, "commit", "-m", "add spec")
    write(repo / "src/app.py", "def value():\n    return 2  # ALLOWED-BODY\n")
    write(repo / "notes/unrelated.md", "UNRELATED-SENTINEL\n")
    write(repo / ".env", "API_TOKEN=super-secret-value\n")
    validation = "\n".join(f"validation-line-{index}" for index in range(1, 51))

    packet = packet_tool.build_packet(
        repo,
        unit.relative_to(repo).as_posix(),
        [validation],
        transport="portable",
        include_paths=[
            unit.relative_to(repo).as_posix(),
            "requirements/spec.md",
            "src/app.py",
            ".env",
        ],
        validation_tail_lines=20,
    )

    assert "# Demo" in packet
    assert "# EXTERNAL-SPEC" in packet
    assert "ALLOWED-BODY" in packet
    assert "UNRELATED-SENTINEL" not in packet
    assert "super-secret-value" not in packet
    assert "50 lines; showing last 20" in packet
    assert "validation-line-1\n" not in packet
    assert "validation-line-31" in packet
    assert "validation-line-50" in packet


def test_include_path_cannot_escape_repository(tmp_path: Path) -> None:
    repo, unit = init_repo(tmp_path)

    with pytest.raises(ValueError, match="include path"):
        packet_tool.build_packet(
            repo,
            unit.relative_to(repo).as_posix(),
            [],
            transport="workspace",
            include_paths=["../outside"],
        )


def test_include_path_cannot_select_repository_root_in_any_form(tmp_path: Path) -> None:
    repo, unit = init_repo(tmp_path)

    for include_path in (".", str(repo), "src/.."):
        with pytest.raises(ValueError, match="repository root"):
            packet_tool.build_packet(
                repo,
                unit.relative_to(repo).as_posix(),
                [],
                transport="workspace",
                include_paths=[include_path],
            )


def test_cli_output_dash_writes_packet_to_stdout_without_dash_file(tmp_path: Path) -> None:
    repo, unit = init_repo(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            str(PACKET_CLI),
            "--root",
            str(repo),
            "--unit",
            unit.relative_to(repo).as_posix(),
            "--transport",
            "workspace",
            "--include-path",
            unit.relative_to(repo).as_posix(),
            "--output",
            "-",
        ],
        cwd=repo,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("# CodeStable Implementation Review Workspace Packet\n")
    assert result.stderr == ""
    assert not (repo / "-").exists()
