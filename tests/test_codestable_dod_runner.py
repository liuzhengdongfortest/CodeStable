from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "plugins/codestable/skills/cs-onboard/tools"
DOD_RUNNER = TOOLS_DIR / "codestable-dod-runner.py"
EVIDENCE_PACK = TOOLS_DIR / "codestable-evidence-pack.py"


def run_dod_process(
    tmp_path: Path,
    checklist_yaml: str,
    existing_json_out: str | None = None,
    python_args: tuple[str, ...] = (),
) -> tuple[subprocess.CompletedProcess[str], dict]:
    repo = tmp_path / "proj"
    (repo / ".codestable").mkdir(parents=True, exist_ok=True)  # repo_root() marker
    checklist = repo / "checklist.yaml"
    checklist.write_text(checklist_yaml, encoding="utf-8")
    out = repo / "dod-results.json"
    if existing_json_out is not None:
        out.write_text(existing_json_out, encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, *python_args, str(DOD_RUNNER), "--checklist", str(checklist), "--json-out", str(out)],
        cwd=repo,
        text=True,
        capture_output=True,
        env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": __import__("os").environ.get("PATH", "")},
    )
    return completed, json.loads(out.read_text(encoding="utf-8"))


def run_dod(tmp_path: Path, checklist_yaml: str, existing_json_out: str | None = None) -> dict:
    _, result = run_dod_process(tmp_path, checklist_yaml, existing_json_out)
    return result


def test_top_level_dod_commands_are_run(tmp_path: Path) -> None:
    """Regression: top-level `dod.commands` (the authoritative schema) must be
    executed, not skipped."""
    data = run_dod(
        tmp_path,
        """feature: x
steps:
  - action: a
    status: done
dod:
  commands:
    - id: CMD-001
      command: "true"
      core: true
    - id: CMD-002
      command: "false"
      core: true
""",
    )
    assert data["status"] == "failed"  # CMD-002 (core) exits non-zero
    assert {e["id"] for e in data["evidence"]} == {"CMD-001", "CMD-002"}


def test_step_level_dod_commands_still_supported(tmp_path: Path) -> None:
    data = run_dod(
        tmp_path,
        """feature: x
steps:
  - action: a
    status: done
    dod:
      commands:
        - id: S-1
          command: "true"
          core: true
""",
    )
    assert data["status"] == "passed"
    assert [e["id"] for e in data["evidence"]] == ["S-1"]


def test_top_level_takes_precedence_no_duplicate(tmp_path: Path) -> None:
    """When both top-level and step-level dod.commands exist, top-level is the
    single source — commands must NOT be executed twice."""
    data = run_dod(
        tmp_path,
        """feature: x
dod:
  commands:
    - id: CMD-001
      command: "true"
      core: true
    - id: CMD-002
      command: "true"
      core: true
steps:
  - action: a
    status: done
    dod:
      commands:
        - id: CMD-001
          command: "true"
          core: true
        - id: CMD-002
          command: "true"
          core: true
""",
    )
    assert data["status"] == "passed"
    ids = [e["id"] for e in data["evidence"]]
    assert ids == ["CMD-001", "CMD-002"]  # each once, no duplicate


def test_non_core_failure_is_warning_not_block(tmp_path: Path) -> None:
    data = run_dod(
        tmp_path,
        """feature: x
dod:
  commands:
    - id: NC-1
      command: "false"
      core: false
""",
    )
    assert data["status"] == "passed"
    assert any("NC-1" in w for w in data["warnings"])


def test_no_commands_is_skipped(tmp_path: Path) -> None:
    data = run_dod(
        tmp_path,
        """feature: x
steps:
  - action: a
    status: done
""",
    )
    assert data["status"] == "skipped"


def test_existing_json_out_is_hidden_from_dod_commands(tmp_path: Path) -> None:
    data = run_dod(
        tmp_path,
        """feature: x
dod:
  commands:
    - id: CMD-001
      command: "test ! -e dod-results.json"
      core: true
""",
        existing_json_out='{"status":"stale"}\n',
    )
    assert data["status"] == "passed"
    assert data["evidence"][0]["exit_code"] == 0


def test_dod_runner_rejects_invalid_yaml_without_traceback(tmp_path: Path) -> None:
    completed, data = run_dod_process(tmp_path, "dod:\n  commands:\n    - id: [\n")

    assert completed.returncode == 1
    assert "Traceback" not in completed.stderr
    assert data["status"] == "blocked"
    assert any("invalid YAML artifact" in item for item in data["blocking"])


def test_dod_runner_rejects_non_mapping_checklist_without_skipping(tmp_path: Path) -> None:
    completed, data = run_dod_process(tmp_path, "[]\n")

    assert completed.returncode == 1
    assert "Traceback" not in completed.stderr
    assert data["status"] == "blocked"
    assert any("checklist is not a mapping" in item for item in data["blocking"])


def test_dod_runner_without_pyyaml_fails_closed_for_untrusted_yaml(tmp_path: Path) -> None:
    for payload in ("[]\n", "dod:\n  commands:\n    - id: [\n"):
        completed, data = run_dod_process(tmp_path, payload, python_args=("-S",))

        assert completed.returncode == 1
        assert "Traceback" not in completed.stderr
        assert data["status"] == "blocked"
        assert any("PyYAML" in item for item in data["blocking"])


def run_evidence_pack(
    tmp_path: Path,
    result_name: str,
    payload: str,
) -> tuple[subprocess.CompletedProcess[str], dict]:
    repo = tmp_path / "evidence-proj"
    (repo / ".codestable").mkdir(parents=True, exist_ok=True)
    design = repo / "design.md"
    checklist = repo / "checklist.yaml"
    design.write_text("# Design\n", encoding="utf-8")
    checklist.write_text("steps: []\n", encoding="utf-8")
    dod_results = repo / "dod-results.json"
    gate_results = repo / "gate-results.json"
    dod_results.write_text("{}\n", encoding="utf-8")
    gate_results.write_text("{}\n", encoding="utf-8")
    target = dod_results if result_name == "dod-results" else gate_results
    target.write_text(payload, encoding="utf-8")
    json_out = repo / "evidence-results.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(EVIDENCE_PACK),
            "--feature",
            "demo",
            "--design",
            str(design),
            "--checklist",
            str(checklist),
            "--dod-results",
            str(dod_results),
            "--gate-results",
            str(gate_results),
            "--out",
            str(repo / "evidence-pack.md"),
            "--json-out",
            str(json_out),
        ],
        cwd=repo,
        text=True,
        capture_output=True,
        env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": __import__("os").environ.get("PATH", "")},
    )
    return completed, json.loads(json_out.read_text(encoding="utf-8"))


def test_evidence_pack_rejects_invalid_json_without_traceback(tmp_path: Path) -> None:
    completed, data = run_evidence_pack(tmp_path, "dod-results", "{invalid\n")

    assert completed.returncode == 1
    assert "Traceback" not in completed.stderr
    assert data["status"] == "blocked"
    assert any("invalid JSON artifact" in item for item in data["blocking"])


def test_evidence_pack_rejects_non_mapping_json_without_traceback(tmp_path: Path) -> None:
    completed, data = run_evidence_pack(tmp_path, "gate-results", "[]\n")

    assert completed.returncode == 1
    assert "Traceback" not in completed.stderr
    assert data["status"] == "blocked"
    assert any("gate results JSON is not a mapping" in item for item in data["blocking"])
