from __future__ import annotations

import json
import hashlib
import os
import subprocess
import sys
from pathlib import Path

import pytest


GOAL_CONSISTENCY_GATE = (
    Path(__file__).resolve().parents[1]
    / "plugins/codestable/skills/cs-onboard/tools/codestable-goal-consistency-gate.py"
)
TOOLS_DIR = GOAL_CONSISTENCY_GATE.parent
FEATURE_SLUG = "invoice-export"
FEATURE_IDENTITY = "2026-07-15-invoice-export"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_feature_artifacts(root: Path) -> Path:
    feature_dir = root / f".codestable/features/{FEATURE_IDENTITY}"
    write(
        feature_dir / f"{FEATURE_SLUG}-checklist.yaml",
        f"feature: {FEATURE_IDENTITY}\nsteps:\n  - id: implement\n    status: done\n"
        "checks:\n  - id: tests\n    status: passed\n",
    )
    for suffix, doc_type, status in (
        ("design", "feature-design", "approved"),
        ("review", "feature-review", "passed"),
        ("qa", "feature-qa", "passed"),
        ("acceptance", "feature-acceptance", "passed"),
        ("evidence-pack", "feature-evidence-pack", "generated"),
    ):
        write(
            feature_dir / f"{FEATURE_SLUG}-{suffix}.md",
            f"---\ndoc_type: {doc_type}\nfeature: {FEATURE_IDENTITY}\nstatus: {status}\n"
            f"---\n# {suffix}\n",
        )
    prefix = f".codestable/features/{FEATURE_IDENTITY}/{FEATURE_SLUG}"
    checklist = feature_dir / f"{FEATURE_SLUG}-checklist.yaml"
    design = feature_dir / f"{FEATURE_SLUG}-design.md"
    evidence_pack = feature_dir / f"{FEATURE_SLUG}-evidence-pack.md"
    gate_results = feature_dir / f"{FEATURE_SLUG}-gate-results.json"
    dod_results = feature_dir / f"{FEATURE_SLUG}-dod-results.json"
    dod_contract_results = feature_dir / f"{FEATURE_SLUG}-dod-contract-results.json"
    result_payloads = {
        gate_results: {
            "gate_id": "scope-gate",
            "feature": FEATURE_IDENTITY,
            "stage": "implementation.before_review",
            "status": "passed",
            "inputs": {"feature_dir": f".codestable/features/{FEATURE_IDENTITY}"},
            "input_digests": {},
        },
        dod_results: {
            "gate_id": "dod-runner",
            "feature": FEATURE_IDENTITY,
            "stage": "implementation.before_review",
            "status": "passed",
            "inputs": {"checklist": f"{prefix}-checklist.yaml"},
            "input_digests": {"checklist": digest(checklist)},
        },
        dod_contract_results: {
            "gate_id": "dod-contract-gate",
            "feature": FEATURE_IDENTITY,
            "stage": "feature_design.before_approve",
            "status": "passed",
            "inputs": {"design": f"{prefix}-design.md"},
            "input_digests": {"design": digest(design)},
        },
    }
    for path, payload in result_payloads.items():
        write(path, json.dumps(payload) + "\n")
    evidence_results = feature_dir / f"{FEATURE_SLUG}-evidence-pack-results.json"
    write(
        evidence_results,
        json.dumps(
            {
                "gate_id": "evidence-pack",
                "feature": FEATURE_IDENTITY,
                "stage": "implementation.before_review",
                "status": "passed",
                "inputs": {
                    "design": f"{prefix}-design.md",
                    "checklist": f"{prefix}-checklist.yaml",
                    "out": f"{prefix}-evidence-pack.md",
                    "dod_results": f"{prefix}-dod-results.json",
                    "gate_results": f"{prefix}-gate-results.json",
                },
                "input_digests": {
                    "design": digest(design),
                    "checklist": digest(checklist),
                    "out": digest(evidence_pack),
                    "dod_results": digest(dod_results),
                    "gate_results": digest(gate_results),
                },
            }
        )
        + "\n",
    )
    return feature_dir


def write_final_audit_candidate(
    tmp_path: Path,
    *,
    commit_ref: str = "approval-report.md#goal-commits",
    commit_decision: str = "approved",
    include_item: bool = True,
    include_feature: bool = True,
    duplicate_feature: bool = False,
    item_status: str = "done",
) -> Path:
    roadmap = tmp_path / "repo/.codestable/roadmap/billing-system"
    item_rows = (
        f"items:\n  - slug: {FEATURE_SLUG}\n    status: {item_status}\n"
        f"    feature: {FEATURE_IDENTITY}\n"
        if include_item
        else "items: []\n"
    )
    write(roadmap / "billing-system-items.yaml", "roadmap: billing-system\n" + item_rows)
    feature_row = (
        f"  - slug: {FEATURE_SLUG}\n"
        f"    roadmap_item: {FEATURE_SLUG}\n"
        "    status: accepted\n"
        f"    feature_dir: .codestable/features/{FEATURE_IDENTITY}\n"
        f"    design: .codestable/features/{FEATURE_IDENTITY}/{FEATURE_SLUG}-design.md\n"
        f"    checklist: .codestable/features/{FEATURE_IDENTITY}/{FEATURE_SLUG}-checklist.yaml\n"
        f"    review: .codestable/features/{FEATURE_IDENTITY}/{FEATURE_SLUG}-review.md\n"
        f"    qa: .codestable/features/{FEATURE_IDENTITY}/{FEATURE_SLUG}-qa.md\n"
        f"    acceptance: .codestable/features/{FEATURE_IDENTITY}/{FEATURE_SLUG}-acceptance.md\n"
    )
    feature_count = 2 if duplicate_feature else 1
    feature_state = (
        f"current_feature_index: {feature_count}\nfeatures:\n"
        + feature_row
        + (feature_row if duplicate_feature else "")
        if include_feature
        else "current_feature_index: 0\nfeatures: []\n"
    )
    write(
        roadmap / "goal-state.yaml",
        "roadmap: billing-system\n"
        "status: ready-to-dispatch\n"
        "acceptance_authorization: approved\n"
        'acceptance_authorization_ref: "approval-report.md#goal-acceptance"\n'
        "commit_authorization: approved\n"
        f'commit_authorization_ref: "{commit_ref}"\n'
        + feature_state,
    )
    write(
        roadmap / "approval-report.md",
        "---\ndoc_type: approval-report\nstatus: approved\napprovals:\n"
        "  goal-acceptance: approved\n"
        f"  goal-commits: {commit_decision}\n"
        "---\n# Approval\n",
    )
    if include_feature:
        write_feature_artifacts(roadmap.parents[2])
    return roadmap


def run_gate(roadmap: Path) -> tuple[subprocess.CompletedProcess[str], dict]:
    completed = subprocess.run(
        [sys.executable, GOAL_CONSISTENCY_GATE.as_posix(), "--roadmap", roadmap.as_posix()],
        cwd=roadmap.parents[2],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": os.environ.get("PATH", "")},
        timeout=10,
    )
    return completed, json.loads(completed.stdout)


def test_final_consistency_gate_checks_authorizations_before_audit_report(tmp_path: Path) -> None:
    roadmap = write_final_audit_candidate(tmp_path)

    completed, result = run_gate(roadmap)

    assert completed.returncode == 0
    assert result["status"] == "passed"
    authorizations = result["evidence"][0]["authorizations"]
    assert authorizations["acceptance_authorization"]["status"] == "approved"
    assert authorizations["commit_authorization"]["status"] == "approved"
    assert not (roadmap / "goal-audit.md").exists()


@pytest.mark.parametrize(
    ("commit_ref", "reason"),
    [
        ("approval-report.md#goal-acceptance", "must be approval-report.md#goal-commits"),
        ("../approval-report.md#goal-commits", "escapes the workflow unit"),
    ],
)
def test_final_consistency_gate_rejects_invalid_commit_reference(
    tmp_path: Path,
    commit_ref: str,
    reason: str,
) -> None:
    roadmap = write_final_audit_candidate(tmp_path, commit_ref=commit_ref)

    completed, result = run_gate(roadmap)

    assert completed.returncode == 1
    assert result["status"] == "failed"
    assert any(reason in item for item in result["blocking"])


def test_final_consistency_gate_rejects_named_commit_rejection(tmp_path: Path) -> None:
    roadmap = write_final_audit_candidate(tmp_path, commit_decision="rejected")

    completed, result = run_gate(roadmap)

    assert completed.returncode == 1
    assert result["status"] == "failed"
    assert "approval decision goal-commits was rejected" in result["blocking"]


@pytest.mark.parametrize(
    "artifact",
    ["items", "state", "approval", "checklist"],
)
def test_final_consistency_gate_reports_invalid_yaml_without_traceback(
    tmp_path: Path,
    artifact: str,
) -> None:
    roadmap = write_final_audit_candidate(tmp_path)
    paths = {
        "items": roadmap / "billing-system-items.yaml",
        "state": roadmap / "goal-state.yaml",
        "approval": roadmap / "approval-report.md",
        "checklist": roadmap.parents[2]
        / ".codestable/features/2026-07-15-invoice-export/invoice-export-checklist.yaml",
    }
    target = paths[artifact]
    if artifact == "approval":
        write(target, "---\napprovals: [unterminated\n---\n# Approval\n")
    else:
        write(target, "items: [unterminated\n")

    completed, result = run_gate(roadmap)

    assert completed.returncode == 1
    assert "Traceback" not in completed.stderr
    assert result["status"] == "failed"
    assert any(f"invalid YAML artifact: {target}" in item for item in result["blocking"])


def test_final_consistency_gate_rejects_non_mapping_checklist(tmp_path: Path) -> None:
    roadmap = write_final_audit_candidate(tmp_path)
    checklist = (
        roadmap.parents[2]
        / ".codestable/features/2026-07-15-invoice-export/invoice-export-checklist.yaml"
    )
    write(checklist, "- step-1\n")

    completed, result = run_gate(roadmap)

    assert completed.returncode == 1
    assert "Traceback" not in completed.stderr
    assert result["status"] == "failed"
    assert f"invoice-export: checklist is not a mapping: {checklist}" in result["blocking"]


def test_final_consistency_gate_rejects_done_item_without_feature(tmp_path: Path) -> None:
    roadmap = write_final_audit_candidate(tmp_path, include_feature=False)

    completed, result = run_gate(roadmap)

    assert completed.returncode == 1
    assert result["status"] == "failed"
    assert f"roadmap item has no goal-state feature: {FEATURE_SLUG}" in result["blocking"]


def test_final_consistency_gate_rejects_empty_roadmap(tmp_path: Path) -> None:
    roadmap = write_final_audit_candidate(
        tmp_path,
        include_item=False,
        include_feature=False,
    )

    completed, result = run_gate(roadmap)

    assert completed.returncode == 1
    assert result["status"] == "failed"
    assert "roadmap items is empty" in result["blocking"]


def test_final_consistency_gate_rejects_feature_without_roadmap_item(tmp_path: Path) -> None:
    roadmap = write_final_audit_candidate(tmp_path, include_item=False)

    completed, result = run_gate(roadmap)

    assert completed.returncode == 1
    assert result["status"] == "failed"
    assert f"goal-state feature has no non-dropped roadmap item: {FEATURE_SLUG}" in result["blocking"]


def test_final_consistency_gate_rejects_mismatched_roadmap_feature_pointer(tmp_path: Path) -> None:
    roadmap = write_final_audit_candidate(tmp_path)
    items_path = roadmap / "billing-system-items.yaml"
    items = items_path.read_text(encoding="utf-8").replace(
        f"feature: {FEATURE_IDENTITY}",
        "feature: 2026-07-15-other",
    )
    write(items_path, items)

    completed, result = run_gate(roadmap)

    assert completed.returncode == 1
    assert result["status"] == "failed"
    assert any("roadmap item feature pointer does not match" in item for item in result["blocking"])


def test_final_consistency_gate_accepts_all_dropped_roadmap(tmp_path: Path) -> None:
    roadmap = write_final_audit_candidate(
        tmp_path,
        include_feature=False,
        item_status="dropped",
    )

    completed, result = run_gate(roadmap)

    assert completed.returncode == 0
    assert result["status"] == "passed"


def test_final_consistency_gate_rejects_duplicate_feature(tmp_path: Path) -> None:
    roadmap = write_final_audit_candidate(tmp_path, duplicate_feature=True)

    completed, result = run_gate(roadmap)

    assert completed.returncode == 1
    assert result["status"] == "failed"
    assert f"duplicate goal-state feature slug: {FEATURE_SLUG}" in result["blocking"]


def test_final_consistency_gate_rejects_cross_feature_evidence_replay(tmp_path: Path) -> None:
    roadmap = write_final_audit_candidate(tmp_path)
    other_review = roadmap.parents[2] / ".codestable/features/2026-07-15-other/other-review.md"
    write(
        other_review,
        "---\ndoc_type: feature-review\nfeature: 2026-07-15-other\nstatus: passed\n---\n# Review\n",
    )
    state_path = roadmap / "goal-state.yaml"
    state = state_path.read_text(encoding="utf-8").replace(
        f".codestable/features/{FEATURE_IDENTITY}/{FEATURE_SLUG}-review.md",
        ".codestable/features/2026-07-15-other/other-review.md",
    )
    write(state_path, state)

    completed, result = run_gate(roadmap)

    assert completed.returncode == 1
    assert result["status"] == "failed"
    assert any(f"{FEATURE_SLUG}: review path is not canonical" in item for item in result["blocking"])


def test_final_consistency_gate_does_not_read_escaped_feature_artifacts(tmp_path: Path) -> None:
    roadmap = write_final_audit_candidate(tmp_path)
    state_path = roadmap / "goal-state.yaml"
    escaped = tmp_path / "outside-feature"
    write(
        escaped / f"{FEATURE_SLUG}-review.md",
        "---\napprovals: [unterminated\n---\n# Invalid external evidence\n",
    )
    state = state_path.read_text(encoding="utf-8")
    state = state.replace(
        f".codestable/features/{FEATURE_IDENTITY}",
        escaped.as_posix(),
    )
    write(state_path, state)

    completed, result = run_gate(roadmap)

    assert completed.returncode == 1
    assert "Traceback" not in completed.stderr
    assert result["status"] == "failed"
    assert any("feature_dir escapes .codestable/features" in item for item in result["blocking"])
    assert not any("invalid YAML artifact" in item for item in result["blocking"])


@pytest.mark.parametrize(
    ("old", "new", "reason"),
    [
        (
            "doc_type: feature-review",
            "doc_type: feature-qa",
            "doc_type is not feature-review",
        ),
        (
            f"feature: {FEATURE_IDENTITY}",
            "feature: 2026-07-15-other",
            f"feature identity does not match {FEATURE_IDENTITY}",
        ),
    ],
)
def test_final_consistency_gate_rejects_review_frontmatter_identity_mismatch(
    tmp_path: Path,
    old: str,
    new: str,
    reason: str,
) -> None:
    roadmap = write_final_audit_candidate(tmp_path)
    review = (
        roadmap.parents[2]
        / f".codestable/features/{FEATURE_IDENTITY}/{FEATURE_SLUG}-review.md"
    )
    write(review, review.read_text(encoding="utf-8").replace(old, new))

    completed, result = run_gate(roadmap)

    assert completed.returncode == 1
    assert result["status"] == "failed"
    assert any(reason in item for item in result["blocking"])


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("gate_id", "dod-runner", "gate_results gate_id is not scope-gate"),
        (
            "feature",
            "2026-07-15-other",
            f"gate_results feature identity does not match {FEATURE_IDENTITY}",
        ),
    ],
)
def test_final_consistency_gate_rejects_replayed_gate_result_identity(
    tmp_path: Path,
    field: str,
    value: str,
    reason: str,
) -> None:
    roadmap = write_final_audit_candidate(tmp_path)
    gate_results = (
        roadmap.parents[2]
        / f".codestable/features/{FEATURE_IDENTITY}/{FEATURE_SLUG}-gate-results.json"
    )
    data = json.loads(gate_results.read_text(encoding="utf-8"))
    data[field] = value
    write(gate_results, json.dumps(data) + "\n")

    completed, result = run_gate(roadmap)

    assert completed.returncode == 1
    assert result["status"] == "failed"
    assert any(reason in item for item in result["blocking"])


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("status", "generated", "gate_results JSON is not passed: status=generated"),
        ("stage", "other-feature", "gate_results stage is not valid for final audit"),
    ],
)
def test_final_consistency_gate_rejects_invalid_gate_result_state(
    tmp_path: Path,
    field: str,
    value: str,
    reason: str,
) -> None:
    roadmap = write_final_audit_candidate(tmp_path)
    gate_results = (
        roadmap.parents[2]
        / f".codestable/features/{FEATURE_IDENTITY}/{FEATURE_SLUG}-gate-results.json"
    )
    data = json.loads(gate_results.read_text(encoding="utf-8"))
    data[field] = value
    write(gate_results, json.dumps(data) + "\n")

    completed, result = run_gate(roadmap)

    assert completed.returncode == 1
    assert result["status"] == "failed"
    assert any(reason in item for item in result["blocking"])


def test_final_consistency_gate_rejects_result_from_alternate_checklist(tmp_path: Path) -> None:
    roadmap = write_final_audit_candidate(tmp_path)
    gate_results = (
        roadmap.parents[2]
        / f".codestable/features/{FEATURE_IDENTITY}/{FEATURE_SLUG}-dod-results.json"
    )
    data = json.loads(gate_results.read_text(encoding="utf-8"))
    data["inputs"] = {
        "checklist": f".codestable/features/{FEATURE_IDENTITY}/alternate-checklist.yaml"
    }
    write(gate_results, json.dumps(data) + "\n")

    completed, result = run_gate(roadmap)

    assert completed.returncode == 1
    assert result["status"] == "failed"
    assert any(
        "dod_results inputs do not match canonical feature artifacts" in item
        for item in result["blocking"]
    )


def test_final_consistency_gate_rejects_stale_result_after_checklist_changes(tmp_path: Path) -> None:
    roadmap = write_final_audit_candidate(tmp_path)
    checklist = (
        roadmap.parents[2]
        / f".codestable/features/{FEATURE_IDENTITY}/{FEATURE_SLUG}-checklist.yaml"
    )
    write(checklist, checklist.read_text(encoding="utf-8") + "# changed after gate\n")

    completed, result = run_gate(roadmap)

    assert completed.returncode == 1
    assert result["status"] == "failed"
    assert any(
        "dod_results input digests do not match current canonical artifacts" in item
        for item in result["blocking"]
    )


@pytest.mark.parametrize(
    ("checklist_body", "reason"),
    [
        ("steps: []\nchecks:\n  - id: tests\n    status: passed\n", "checklist steps must be a non-empty list"),
        ("steps:\n  - id: implement\n    status: done\nchecks: []\n", "checklist checks must be a non-empty list"),
        ("steps: invalid\nchecks:\n  - id: tests\n    status: passed\n", "checklist steps must be a non-empty list"),
        ("steps:\n  - invalid\nchecks:\n  - id: tests\n    status: passed\n", "checklist steps[0] is not a mapping"),
    ],
)
def test_final_consistency_gate_requires_nonempty_mapping_checklist_entries(
    tmp_path: Path,
    checklist_body: str,
    reason: str,
) -> None:
    roadmap = write_final_audit_candidate(tmp_path)
    root = roadmap.parents[2]
    feature_dir = root / f".codestable/features/{FEATURE_IDENTITY}"
    checklist = feature_dir / f"{FEATURE_SLUG}-checklist.yaml"
    write(checklist, f"feature: {FEATURE_IDENTITY}\n{checklist_body}")
    for suffix in ("dod-results", "evidence-pack-results"):
        result_path = feature_dir / f"{FEATURE_SLUG}-{suffix}.json"
        data = json.loads(result_path.read_text(encoding="utf-8"))
        data["input_digests"]["checklist"] = digest(checklist)
        write(result_path, json.dumps(data) + "\n")

    completed, result = run_gate(roadmap)

    assert completed.returncode == 1
    assert "Traceback" not in completed.stderr
    assert result["status"] == "failed"
    assert any(reason in item for item in result["blocking"])


@pytest.mark.parametrize(
    ("suffix", "label", "payload"),
    [
        ("evidence-pack-results", "evidence_pack_results", "[]\n"),
        ("gate-results", "gate_results", "null\n"),
        ("dod-results", "dod_results", '"passed"\n'),
        ("dod-contract-results", "dod_contract_results", "[1]\n"),
    ],
)
def test_final_consistency_gate_rejects_non_mapping_result_json(
    tmp_path: Path,
    suffix: str,
    label: str,
    payload: str,
) -> None:
    roadmap = write_final_audit_candidate(tmp_path)
    result_path = (
        roadmap.parents[2]
        / f".codestable/features/{FEATURE_IDENTITY}/{FEATURE_SLUG}-{suffix}.json"
    )
    write(result_path, payload)

    completed, result = run_gate(roadmap)

    assert completed.returncode == 1
    assert "Traceback" not in completed.stderr
    assert result["status"] == "failed"
    assert any(f"{label} JSON is not passed: status=invalid" in item for item in result["blocking"])


def test_executable_feature_gates_emit_canonical_feature_identity(tmp_path: Path) -> None:
    roadmap = write_final_audit_candidate(tmp_path)
    root = roadmap.parents[2]
    feature_dir = root / f".codestable/features/{FEATURE_IDENTITY}"
    design = feature_dir / f"{FEATURE_SLUG}-design.md"
    checklist = feature_dir / f"{FEATURE_SLUG}-checklist.yaml"
    evidence_pack = feature_dir / f"{FEATURE_SLUG}-evidence-pack.md"
    gate_results = feature_dir / f"{FEATURE_SLUG}-gate-results.json"
    dod_results = feature_dir / f"{FEATURE_SLUG}-dod-results.json"
    cases = [
        (
            "codestable-scope-gate.py",
            ["--feature-dir", feature_dir.relative_to(root).as_posix()],
            "scope-gate",
            {"feature_dir": feature_dir.relative_to(root).as_posix()},
            {},
        ),
        (
            "codestable-dod-contract-gate.py",
            ["--design", design.as_posix()],
            "dod-contract-gate",
            {"design": design.relative_to(root).as_posix()},
            {"design": design},
        ),
        (
            "codestable-dod-runner.py",
            ["--checklist", checklist.as_posix()],
            "dod-runner",
            {"checklist": checklist.relative_to(root).as_posix()},
            {"checklist": checklist},
        ),
        (
            "codestable-evidence-pack.py",
            [
                "--feature",
                FEATURE_IDENTITY,
                "--design",
                design.as_posix(),
                "--checklist",
                checklist.as_posix(),
                "--out",
                evidence_pack.as_posix(),
                "--dod-results",
                dod_results.as_posix(),
                "--gate-results",
                gate_results.as_posix(),
            ],
            "evidence-pack",
            {
                "design": design.relative_to(root).as_posix(),
                "checklist": checklist.relative_to(root).as_posix(),
                "out": evidence_pack.relative_to(root).as_posix(),
                "dod_results": dod_results.relative_to(root).as_posix(),
                "gate_results": gate_results.relative_to(root).as_posix(),
            },
            {
                "design": design,
                "checklist": checklist,
                "out": evidence_pack,
                "dod_results": dod_results,
                "gate_results": gate_results,
            },
        ),
    ]

    for filename, args, gate_id, expected_inputs, digest_paths in cases:
        completed = subprocess.run(
            [sys.executable, (TOOLS_DIR / filename).as_posix(), *args],
            cwd=root,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": os.environ.get("PATH", "")},
            timeout=10,
        )
        result = json.loads(completed.stdout)
        assert "Traceback" not in completed.stderr
        assert result["gate_id"] == gate_id
        assert result["feature"] == FEATURE_IDENTITY
        assert result["inputs"] == expected_inputs
        assert result["input_digests"] == {
            name: digest(path) for name, path in digest_paths.items()
        }


def test_scope_gate_fails_closed_when_git_status_cannot_run(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    feature_dir = root / f".codestable/features/{FEATURE_IDENTITY}"
    feature_dir.mkdir(parents=True)

    completed = subprocess.run(
        [
            sys.executable,
            (TOOLS_DIR / "codestable-scope-gate.py").as_posix(),
            "--feature-dir",
            feature_dir.relative_to(root).as_posix(),
        ],
        cwd=root,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": os.environ.get("PATH", "")},
        timeout=10,
    )
    result = json.loads(completed.stdout)

    assert completed.returncode == 1
    assert "Traceback" not in completed.stderr
    assert result["status"] == "failed"
    assert result["blocking"] == ["git status failed with exit 128"]
    assert result["evidence"][0]["git_status"]["exit_code"] == 128
