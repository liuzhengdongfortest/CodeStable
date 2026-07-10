from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parents[1] / "plugins/codestable/skills/cs-onboard/tools"
sys.path.insert(0, str(TOOLS_DIR))


def load_tool():
    spec = importlib.util.spec_from_file_location("codestable_workflow_next", TOOLS_DIR / "codestable-workflow-next.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


workflow_next = load_tool()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".codestable").mkdir()
    return repo


def write_roadmap(repo: Path, status: str = "active") -> Path:
    roadmap = repo / ".codestable/roadmap/billing-system"
    write(
        roadmap / "billing-system-roadmap.md",
        f"---\ndoc_type: roadmap\nslug: billing-system\nstatus: {status}\n---\n# Roadmap\n",
    )
    write(roadmap / "billing-system-roadmap-review.md", "---\ndoc_type: roadmap-review\nstatus: passed\n---\n# Review\n")
    write(
        roadmap / "billing-system-items.yaml",
        "roadmap: billing-system\n"
        "items:\n"
        "  - slug: api-seed\n"
        "    status: planned\n"
        "    feature: null\n"
        "  - slug: ui-seed\n"
        "    status: planned\n"
        "    feature: null\n",
    )
    return roadmap


def write_feature(repo: Path, slug: str, *, design_status: str = "draft", review_status: str = "passed") -> Path:
    feature = repo / ".codestable/features" / f"2026-07-02-{slug}"
    write(
        feature / f"{slug}-design.md",
        f"---\ndoc_type: feature-design\nfeature: 2026-07-02-{slug}\n"
        f"roadmap: billing-system\nroadmap_item: {slug}\nstatus: {design_status}\n---\n# Design\n",
    )
    write(feature / f"{slug}-checklist.yaml", "steps:\n  - id: step-1\n    status: pending\n")
    write(
        feature / f"{slug}-design-review.md",
        f"---\ndoc_type: feature-design-review\nstatus: {review_status}\n---\n# Review\n",
    )
    return feature


def write_goal_state(
    directory: Path,
    *,
    status: str,
    stage: str | None = None,
    driver_kind: str = "none",
    driver_id: str = "",
    handoff_reason: str = "",
    handoff_next: str = "",
) -> None:
    lines = [f"status: {status}"]
    if stage is not None:
        lines.append(f"stage: {stage}")
    lines.extend(
        [
            f"driver_kind: {driver_kind}",
            f'driver_id: "{driver_id}"',
            f'handoff_reason: "{handoff_reason}"',
            f'handoff_next: "{handoff_next}"',
        ]
    )
    write(directory / "goal-state.yaml", "\n".join(lines) + "\n")


def test_epic_continues_when_only_first_child_design_review_passed(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    roadmap = write_roadmap(repo)
    write_feature(repo, "api-seed")

    result = workflow_next.epic_next(roadmap)

    assert result["ok"] is True
    assert result["status"] == "continue"
    assert result["next_action"] == "cs-feat design/design-review"
    assert result["must_continue"] is True
    assert result["final_answer_allowed"] is False
    assert result["evidence"]["next_item"]["item"] == "ui-seed"


def test_epic_user_gate_only_after_all_child_design_reviews_passed(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    roadmap = write_roadmap(repo)
    write_feature(repo, "api-seed")
    write_feature(repo, "ui-seed")

    result = workflow_next.epic_next(roadmap)

    assert result["status"] == "user_gate"
    assert result["next_action"] == "all-feature-designs-confirmation"
    assert result["must_continue"] is False
    assert result["final_answer_allowed"] is True
    assert {item["item"] for item in result["evidence"]["unapproved_items"]} == {"api-seed", "ui-seed"}


def test_epic_goal_package_after_batch_approval(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    roadmap = write_roadmap(repo)
    write_feature(repo, "api-seed", design_status="approved")
    write_feature(repo, "ui-seed", design_status="approved")

    result = workflow_next.epic_next(roadmap)

    assert result["status"] == "goal_package"
    assert result["next_action"] == "cs-epic goal-package"
    assert result["must_continue"] is True
    assert result["final_answer_allowed"] is False


def test_feature_epic_child_batch_returns_to_epic_loop(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(repo, "api-seed")

    result = workflow_next.feature_next(feature, epic_child_batch=True)

    assert result["status"] == "continue"
    assert result["next_action"] == "return-to-cs-epic-batch-loop"
    assert result["must_continue"] is True
    assert result["final_answer_allowed"] is False
    assert result["evidence"]["roadmap_item"] == "api-seed"
    assert result["evidence"]["epic_command"] == (
        f"python3 {(TOOLS_DIR / 'codestable-workflow-next.py').as_posix()} "
        "epic --roadmap .codestable/roadmap/billing-system --json"
    )


def test_feature_single_mode_stops_at_design_confirmation(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(repo, "api-seed")

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    assert result["status"] == "user_gate"
    assert result["next_action"] == "feature-design-confirmation"
    assert result["must_continue"] is False
    assert result["final_answer_allowed"] is True


def test_feature_review_failure_returns_to_design(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)

    for review_status in ("changes-requested", "blocked"):
        feature = write_feature(repo, review_status, review_status=review_status)

        result = workflow_next.feature_next(feature, epic_child_batch=False)

        assert result["status"] == "continue"
        assert result["next_action"] == "cs-feat design"
        assert result["reason"] == f"design-review is {review_status}"


def test_feature_approved_design_requires_passed_review_before_goal_state(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)

    for review_status in ("missing", "changes-requested", "blocked"):
        slug = f"invalid-{review_status}"
        feature = write_feature(
            repo,
            slug,
            design_status="approved",
            review_status="passed" if review_status == "missing" else review_status,
        )
        if review_status == "missing":
            (feature / f"{slug}-design-review.md").unlink()
        write_goal_state(feature, stage="complete", status="passed")

        result = workflow_next.feature_next(feature, epic_child_batch=False)

        assert result["status"] == "blocked"
        assert result["next_action"] == "fix-feature-design-review-state"
        assert result["final_answer_allowed"] is True
        assert result["blocking"] == [f"approved design has design-review status: {review_status}"]


def test_feature_goal_runtime_distinguishes_dispatch_and_active_driver(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(repo, "api-seed", design_status="approved")
    write_goal_state(feature, stage="implementation", status="ready-to-dispatch")

    dispatch = workflow_next.feature_next(feature, epic_child_batch=False)
    assert dispatch["status"] == "dispatch_goal"
    assert dispatch["next_action"] == "dispatch-feature-goal-driver-or-print-goal"
    assert dispatch["final_answer_allowed"] is False

    write_goal_state(
        feature,
        stage="implementation",
        status="running",
        driver_kind="paseo",
        driver_id="feature-run-123",
    )
    active = workflow_next.feature_next(feature, epic_child_batch=False)
    assert active["status"] == "report_driver"
    assert active["evidence"]["driver_id"] == "feature-run-123"


def test_feature_terminal_goal_states_override_stale_driver(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(repo, "api-seed", design_status="approved")
    write_goal_state(
        feature,
        stage="complete",
        status="passed",
        driver_kind="paseo",
        driver_id="feature-run-123",
    )

    complete = workflow_next.feature_next(feature, epic_child_batch=False)
    assert complete["status"] == "complete"
    assert complete["next_action"] == "CS_FEATURE_GOAL_COMPLETE"

    write_goal_state(
        feature,
        stage="handoff",
        status="blocked",
        driver_kind="paseo",
        driver_id="feature-run-123",
        handoff_reason="missing production credential",
        handoff_next="provide credential",
    )
    handoff = workflow_next.feature_next(feature, epic_child_batch=False)
    assert handoff["status"] == "user_gate"
    assert handoff["next_action"] == "CS_FEATURE_GOAL_HANDOFF"
    assert handoff["reason"] == "missing production credential"
    assert handoff["evidence"]["handoff_next"] == "provide credential"


def test_epic_goal_runtime_distinguishes_dispatch_and_active_driver(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    roadmap = write_roadmap(repo)
    write_feature(repo, "api-seed", design_status="approved")
    write_feature(repo, "ui-seed", design_status="approved")
    write_goal_state(roadmap, status="ready-to-dispatch")

    dispatch = workflow_next.epic_next(roadmap)
    assert dispatch["status"] == "dispatch_goal"
    assert dispatch["next_action"] == "dispatch-epic-goal-driver-or-print-goal"
    assert dispatch["final_answer_allowed"] is False

    write_goal_state(
        roadmap,
        status="ready-to-dispatch",
        driver_kind="paseo",
        driver_id="epic-run-123",
    )
    active = workflow_next.epic_next(roadmap)
    assert active["status"] == "report_driver"
    assert active["evidence"]["driver_id"] == "epic-run-123"


def test_epic_active_roadmap_requires_review_artifact_before_goal_state(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    roadmap = write_roadmap(repo)
    (roadmap / "billing-system-roadmap-review.md").unlink()
    write_goal_state(roadmap, status="complete")

    result = workflow_next.epic_next(roadmap)

    assert result["status"] == "blocked"
    assert result["next_action"] == "fix-roadmap-review-state"
    assert result["final_answer_allowed"] is True
    assert result["blocking"] == ["active roadmap has no roadmap review artifact"]


def test_epic_terminal_goal_states_override_stale_driver(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    roadmap = write_roadmap(repo)
    write_feature(repo, "api-seed", design_status="approved")
    write_feature(repo, "ui-seed", design_status="approved")
    write_goal_state(
        roadmap,
        status="complete",
        driver_kind="paseo",
        driver_id="epic-run-123",
    )

    complete = workflow_next.epic_next(roadmap)
    assert complete["status"] == "complete"
    assert complete["next_action"] == "CS_ROADMAP_GOAL_COMPLETE"

    write_goal_state(
        roadmap,
        status="handoff",
        driver_kind="paseo",
        driver_id="epic-run-123",
        handoff_reason="migration environment unavailable",
        handoff_next="provision migration environment",
    )
    handoff = workflow_next.epic_next(roadmap)
    assert handoff["status"] == "user_gate"
    assert handoff["next_action"] == "CS_ROADMAP_GOAL_HANDOFF"
    assert handoff["reason"] == "migration environment unavailable"
    assert handoff["evidence"]["handoff_next"] == "provision migration environment"


def test_cli_accepts_json_before_or_after_subcommand(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    roadmap = write_roadmap(repo)
    write_feature(repo, "api-seed")

    for command in (
        [
            sys.executable,
            (TOOLS_DIR / "codestable-workflow-next.py").as_posix(),
            "--json",
            "epic",
            "--roadmap",
            roadmap.as_posix(),
        ],
        [
            sys.executable,
            (TOOLS_DIR / "codestable-workflow-next.py").as_posix(),
            "epic",
            "--roadmap",
            roadmap.as_posix(),
            "--json",
        ],
    ):
        completed = subprocess.run(
            command,
            cwd=repo,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={"PYTHONDONTWRITEBYTECODE": "1"},
        )

        result = json.loads(completed.stdout)
        assert result["status"] == "continue"
        assert result["final_answer_allowed"] is False
