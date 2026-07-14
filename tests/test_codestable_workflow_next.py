from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


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


def write_feature(
    repo: Path,
    slug: str,
    *,
    design_status: str = "draft",
    review_status: str = "passed",
    execution_lane: str | None = None,
    execution_lane_reason: str | None = None,
    include_roadmap: bool = False,
) -> Path:
    feature = repo / ".codestable/features" / f"2026-07-02-{slug}"
    roadmap_fields = f"roadmap: billing-system\nroadmap_item: {slug}\n" if include_roadmap else ""
    lane_field = f"execution_lane: {execution_lane}\n" if execution_lane else ""
    lane_reason_field = f"execution_lane_reason: {execution_lane_reason}\n" if execution_lane_reason else ""
    write(
        feature / f"{slug}-design.md",
        f"---\ndoc_type: feature-design\nfeature: 2026-07-02-{slug}\n"
        f"{roadmap_fields}{lane_field}{lane_reason_field}"
        f"status: {design_status}\n---\n# Design\n",
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


def write_code_review(
    feature: Path,
    slug: str,
    *,
    status: str = "passed",
    reviewer: str | None = "subagent",
    doc_type: str = "feature-review",
) -> None:
    reviewer_field = f"reviewer: {reviewer}\n" if reviewer is not None else ""
    write(
        feature / f"{slug}-review.md",
        f"---\ndoc_type: {doc_type}\nstatus: {status}\n{reviewer_field}---\n# Review\n",
    )


def write_ff_note(feature: Path, slug: str) -> None:
    write(
        feature / f"{slug}-ff-note.md",
        f"---\ndoc_type: feature-ff-note\nfeature: {slug}\ndate: 2026-07-13\n---\n# Fastforward Note\n",
    )


def write_roadmap_goal_state(roadmap: Path, *, feature_slug: str = "api-seed") -> None:
    write(
        roadmap / "goal-state.yaml",
        "roadmap: billing-system\n"
        "status: ready-to-dispatch\n"
        "driver_kind: paseo\n"
        'driver_id: "epic-run-123"\n'
        "current_feature_index: 0\n"
        "features:\n"
        f"  - slug: {feature_slug}\n"
        f"    roadmap_item: {feature_slug}\n"
        f"    feature_dir: .codestable/features/2026-07-02-{feature_slug}\n"
        "    status: implementing\n",
    )


def write_reverse_owner_state(
    repo: Path,
    roadmap_slug: str,
    *,
    state_roadmap: str | None = None,
    rows: list[tuple[str | None, str]],
) -> Path:
    lines = [
        f"roadmap: {state_roadmap or roadmap_slug}",
        "status: ready-to-dispatch",
        "features:",
    ]
    for item, feature_dir in rows:
        lines.append(f"  - slug: {item}" if item else "  - status: implementing")
        if item:
            lines.append(f"    roadmap_item: {item}")
        lines.append(f"    feature_dir: {feature_dir}")
        if item:
            lines.append("    status: implementing")
    goal_state = repo / ".codestable/roadmap" / roadmap_slug / "goal-state.yaml"
    write(goal_state, "\n".join(lines) + "\n")
    return goal_state


def run_cli_json(repo: Path, workflow: str, path: Path) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    completed = subprocess.run(
        [
            sys.executable,
            (TOOLS_DIR / "codestable-workflow-next.py").as_posix(),
            workflow,
            f"--{workflow if workflow == 'feature' else 'roadmap'}",
            path.as_posix(),
            "--json",
        ],
        cwd=repo,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={"PYTHONDONTWRITEBYTECODE": "1"},
        timeout=10,
    )
    return completed, json.loads(completed.stdout)


def test_epic_continues_when_only_first_child_design_review_passed(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    roadmap = write_roadmap(repo)
    write_feature(repo, "api-seed", include_roadmap=True)

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
    write_feature(repo, "api-seed", include_roadmap=True)
    write_feature(repo, "ui-seed", include_roadmap=True)

    result = workflow_next.epic_next(roadmap)

    assert result["status"] == "user_gate"
    assert result["next_action"] == "all-feature-designs-confirmation"
    assert result["must_continue"] is False
    assert result["final_answer_allowed"] is True
    assert {item["item"] for item in result["evidence"]["unapproved_items"]} == {"api-seed", "ui-seed"}


def test_epic_goal_package_after_batch_approval(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    roadmap = write_roadmap(repo)
    write_feature(repo, "api-seed", design_status="approved", include_roadmap=True)
    write_feature(repo, "ui-seed", design_status="approved", include_roadmap=True)

    result = workflow_next.epic_next(roadmap)

    assert result["status"] == "goal_package"
    assert result["next_action"] == "cs-epic goal-package"
    assert result["must_continue"] is True
    assert result["final_answer_allowed"] is False


def test_feature_epic_child_batch_returns_to_epic_loop(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    write_roadmap(repo)
    feature = write_feature(repo, "api-seed", include_roadmap=True)

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


def test_feature_legacy_epic_child_with_roadmap_goal_state_returns_to_epic(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    roadmap = write_roadmap(repo)
    write_roadmap_goal_state(roadmap)
    feature = write_feature(repo, "api-seed", design_status="approved", include_roadmap=True)
    write(feature / "api-seed-checklist.yaml", "steps:\n  - id: step-1\n    status: done\n")
    write_code_review(feature, "api-seed")
    write(
        feature / "api-seed-acceptance.md",
        "---\ndoc_type: feature-acceptance\nstatus: passed\n---\n# Acceptance\n",
    )

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    assert result["status"] == "continue"
    assert result["next_action"] == "return-to-cs-epic"
    assert result["evidence"]["roadmap_item"] == "api-seed"
    assert result["evidence"]["roadmap_goal_state"].endswith("billing-system/goal-state.yaml")


@pytest.mark.parametrize("artifacts_complete", [False, True])
def test_feature_legacy_epic_child_without_roadmap_frontmatter_is_reverse_owned(
    tmp_path: Path,
    artifacts_complete: bool,
) -> None:
    repo = init_repo(tmp_path)
    roadmap = write_roadmap(repo)
    write_roadmap_goal_state(roadmap)
    feature = write_feature(repo, "api-seed", design_status="approved", include_roadmap=False)
    if artifacts_complete:
        write(feature / "api-seed-checklist.yaml", "steps:\n  - id: step-1\n    status: done\n")
        write_code_review(feature, "api-seed")
        write(
            feature / "api-seed-acceptance.md",
            "---\ndoc_type: feature-acceptance\nstatus: passed\n---\n# Acceptance\n",
        )

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    assert result["status"] == "continue"
    assert result["next_action"] == "return-to-cs-epic"
    assert result["evidence"]["execution_lane"] == "goal"
    assert result["evidence"]["execution_lane_source"] == "roadmap-goal-state"
    assert result["next_action"] != "CS_FEATURE_STANDARD_COMPLETE"


@pytest.mark.parametrize(
    ("design_status", "artifacts_complete"),
    [("draft", False), ("approved", True)],
)
def test_feature_pre_goal_package_metadata_less_child_with_items_pointer_returns_to_epic(
    tmp_path: Path,
    design_status: str,
    artifacts_complete: bool,
) -> None:
    repo = init_repo(tmp_path)
    roadmap = write_roadmap(repo)
    write(
        roadmap / "billing-system-items.yaml",
        "roadmap: billing-system\n"
        "items:\n"
        "  - slug: api-seed\n"
        "    status: planned\n"
        "    feature: .codestable/features/2026-07-02-api-seed\n",
    )
    feature = write_feature(repo, "api-seed", design_status=design_status, include_roadmap=False)
    if artifacts_complete:
        write(feature / "api-seed-checklist.yaml", "steps:\n  - id: step-1\n    status: done\n")
        write_code_review(feature, "api-seed")
        write(
            feature / "api-seed-acceptance.md",
            "---\ndoc_type: feature-acceptance\nstatus: passed\n---\n# Acceptance\n",
        )

    result = workflow_next.feature_next(feature, epic_child_batch=False)
    epic_result = workflow_next.epic_next(roadmap)

    assert result["status"] == "continue"
    assert result["next_action"] == "return-to-cs-epic"
    assert result["evidence"]["execution_lane"] == "goal"
    assert result["evidence"]["execution_lane_source"] == "roadmap-items"
    assert result["evidence"]["roadmap_items"].endswith("billing-system-items.yaml")
    assert result["next_action"] not in {"feature-design-confirmation", "CS_FEATURE_STANDARD_COMPLETE"}
    assert epic_result["next_action"] == (
        "all-feature-designs-confirmation" if design_status == "draft" else "cs-epic goal-package"
    )


@pytest.mark.parametrize(
    ("design_status", "artifacts_complete"),
    [("draft", False), ("approved", True)],
)
def test_feature_pre_goal_package_metadata_less_child_with_items_glob_returns_to_epic(
    tmp_path: Path,
    design_status: str,
    artifacts_complete: bool,
) -> None:
    repo = init_repo(tmp_path)
    write_roadmap(repo)
    feature = write_feature(repo, "api-seed", design_status=design_status, include_roadmap=False)
    if artifacts_complete:
        write(feature / "api-seed-checklist.yaml", "steps:\n  - id: step-1\n    status: done\n")
        write_code_review(feature, "api-seed")
        write(
            feature / "api-seed-acceptance.md",
            "---\ndoc_type: feature-acceptance\nstatus: passed\n---\n# Acceptance\n",
        )

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    assert result["status"] == "continue"
    assert result["next_action"] == "return-to-cs-epic"
    assert result["evidence"]["execution_lane_source"] == "roadmap-items"
    assert result["next_action"] not in {"feature-design-confirmation", "CS_FEATURE_STANDARD_COMPLETE"}


@pytest.mark.parametrize("same_items_file", [False, True])
def test_reverse_items_owner_multiple_claims_fail_closed(
    tmp_path: Path,
    same_items_file: bool,
) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(repo, "api-seed", design_status="approved", include_roadmap=False)
    feature_dir = ".codestable/features/2026-07-02-api-seed"
    first = repo / ".codestable/roadmap/first-roadmap/first-roadmap-items.yaml"
    if same_items_file:
        write(
            first,
            "roadmap: first-roadmap\nitems:\n"
            f"  - slug: api-seed\n    feature: {feature_dir}\n"
            f"  - slug: api-seed-copy\n    feature: {feature_dir}\n",
        )
        expected_paths = [first.relative_to(repo).as_posix()]
    else:
        second = repo / ".codestable/roadmap/second-roadmap/second-roadmap-items.yaml"
        write(first, f"roadmap: first-roadmap\nitems:\n  - slug: api-seed\n    feature: {feature_dir}\n")
        write(second, f"roadmap: second-roadmap\nitems:\n  - slug: api-seed\n    feature: {feature_dir}\n")
        expected_paths = [first.relative_to(repo).as_posix(), second.relative_to(repo).as_posix()]

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    assert result["status"] == "blocked"
    assert result["next_action"] == "inspect-epic-goal-state"
    assert "multiple roadmap items claim" in result["reason"]
    assert all(path in result["blocking"][0] for path in expected_paths)


@pytest.mark.parametrize("contents", ["items: [unterminated\n", "- api-seed\n"])
def test_reverse_items_owner_invalid_artifact_fails_closed(
    tmp_path: Path,
    contents: str,
) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(repo, "api-seed", design_status="approved", include_roadmap=False)
    items_path = repo / ".codestable/roadmap/broken-roadmap/broken-roadmap-items.yaml"
    write(items_path, contents)

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    expected_path = items_path.relative_to(repo).as_posix()
    assert result["status"] == "blocked"
    assert result["next_action"] == "inspect-epic-goal-state"
    assert expected_path in result["blocking"][0]
    assert expected_path in result["evidence"]["roadmap_owner_error"]


@pytest.mark.parametrize(
    "contents",
    [
        "roadmap: broken-roadmap\nitems:\n  slug: api-seed\n  feature: null\n",
        "roadmap: broken-roadmap\nitems:\n  - slug: api-seed\n    feature: []\n",
    ],
)
def test_reverse_items_owner_invalid_yaml_shape_returns_structured_block(
    tmp_path: Path,
    contents: str,
) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(repo, "api-seed", design_status="approved", include_roadmap=False)
    items_path = repo / ".codestable/roadmap/broken-roadmap/broken-roadmap-items.yaml"
    write(items_path, contents)

    completed, payload = run_cli_json(repo, "feature", feature)

    expected_path = items_path.relative_to(repo).as_posix()
    assert completed.returncode == 1
    assert completed.stderr == ""
    assert payload["status"] == "blocked"
    assert expected_path in payload["blocking"][0]


@pytest.mark.parametrize(
    "contents",
    [
        "roadmap: billing-system\nitems:\n  slug: api-seed\n  feature: null\n",
        "roadmap: billing-system\nitems:\n  - slug: api-seed\n    feature: []\n",
    ],
)
def test_epic_invalid_items_yaml_shape_returns_structured_block(
    tmp_path: Path,
    contents: str,
) -> None:
    repo = init_repo(tmp_path)
    roadmap = write_roadmap(repo)
    items_path = roadmap / "billing-system-items.yaml"
    write(items_path, contents)

    completed, payload = run_cli_json(repo, "epic", roadmap)

    expected_path = items_path.relative_to(repo).as_posix()
    assert completed.returncode == 1
    assert completed.stderr == ""
    assert payload["status"] == "blocked"
    assert payload["next_action"] == "fix-epic-artifact-yaml"
    assert expected_path in payload["blocking"][0]


@pytest.mark.parametrize("quick", [False, True])
def test_reverse_items_owner_ignores_unrelated_valid_items(tmp_path: Path, quick: bool) -> None:
    repo = init_repo(tmp_path)
    if quick:
        feature = repo / ".codestable/features/2026-07-13-small-export"
        write_ff_note(feature, "small-export")
    else:
        feature = write_feature(repo, "api-seed", design_status="approved", include_roadmap=False)
    write(
        repo / ".codestable/roadmap/other-roadmap/other-roadmap-items.yaml",
        "roadmap: other-roadmap\n"
        "items:\n"
        "  - slug: other-feature\n"
        "    feature: .codestable/features/2026-07-02-other-feature\n",
    )

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    assert result["status"] == "continue"
    assert result["next_action"] == ("cs-code-review" if quick else "cs-feat implementation")
    assert result["evidence"]["execution_lane"] == ("quick" if quick else "standard")


@pytest.mark.parametrize("quick", [False, True])
def test_reverse_items_owner_ignores_slug_suffix_collision(tmp_path: Path, quick: bool) -> None:
    repo = init_repo(tmp_path)
    if quick:
        item_slug = "export"
        feature = repo / ".codestable/features/2026-07-13-small-export"
        write_ff_note(feature, "small-export")
        write_code_review(feature, "small-export")
    else:
        item_slug = "auth"
        feature = write_feature(repo, "user-auth", design_status="approved", include_roadmap=False)
    write(
        repo / ".codestable/roadmap/platform/platform-items.yaml",
        "roadmap: platform\n"
        "items:\n"
        f"  - slug: {item_slug}\n"
        "    feature: null\n",
    )

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    assert result["status"] == ("complete" if quick else "continue")
    assert result["next_action"] == ("CS_FEATURE_QUICK_COMPLETE" if quick else "cs-feat implementation")
    assert result["evidence"]["execution_lane"] == ("quick" if quick else "standard")


def test_reverse_items_owner_multiple_exact_slug_directories_fail_closed(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    roadmap = write_roadmap(repo)
    feature = write_feature(repo, "api-seed", design_status="approved", include_roadmap=False)
    write(repo / ".codestable/features/2026-07-01-api-seed/placeholder.txt", "")
    write(
        roadmap / "billing-system-items.yaml",
        "roadmap: billing-system\nitems:\n  - slug: api-seed\n    feature: null\n",
    )

    result = workflow_next.feature_next(feature, epic_child_batch=False)
    epic_result = workflow_next.epic_next(roadmap)

    assert result["status"] == "blocked"
    assert result["next_action"] == "inspect-epic-goal-state"
    assert "multiple feature directories match roadmap item api-seed" in result["reason"]
    assert epic_result["status"] == "blocked"
    assert epic_result["next_action"] == "fix-roadmap-items"
    assert "multiple feature directories match roadmap item api-seed" in epic_result["reason"]


def test_reverse_items_owner_does_not_fallback_from_explicit_missing_pointer(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    roadmap = write_roadmap(repo)
    feature = write_feature(repo, "api-seed", design_status="approved", include_roadmap=False)
    write(
        roadmap / "billing-system-items.yaml",
        "roadmap: billing-system\n"
        "items:\n"
        "  - slug: api-seed\n"
        "    feature: .codestable/features/2026-07-02-missing-feature\n",
    )

    result = workflow_next.feature_next(feature, epic_child_batch=False)
    epic_result = workflow_next.epic_next(roadmap)

    assert result["status"] == "continue"
    assert result["next_action"] == "cs-feat implementation"
    assert result["evidence"]["execution_lane"] == "standard"
    assert epic_result["status"] == "continue"
    assert epic_result["next_action"] == "cs-feat design/design-review"
    assert epic_result["evidence"]["next_item"]["feature_dir"] is None


def test_reverse_items_owner_invalid_pointer_returns_structured_block(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    items_path = repo / ".codestable/roadmap/platform/platform-items.yaml"
    write(
        items_path,
        "roadmap: platform\n"
        "items:\n"
        "  - slug: api-seed\n"
        '    feature: ".codestable/features/2026\\0-07-02-api-seed"\n',
    )
    feature = write_feature(repo, "api-seed", design_status="approved", include_roadmap=False)
    write(feature / "api-seed-checklist.yaml", "steps:\n  - id: step-1\n    status: done\n")
    write_code_review(feature, "api-seed")
    write(
        feature / "api-seed-acceptance.md",
        "---\ndoc_type: feature-acceptance\nstatus: passed\n---\n# Acceptance\n",
    )

    completed, payload = run_cli_json(repo, "feature", feature)

    expected_path = items_path.relative_to(repo).as_posix()
    assert completed.returncode == 1
    assert completed.stderr == ""
    assert payload["status"] == "blocked"
    assert expected_path in payload["blocking"][0]
    assert payload["next_action"] != "CS_FEATURE_STANDARD_COMPLETE"


def test_reverse_owner_ignores_unrelated_valid_goal_state(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(repo, "api-seed", design_status="approved", include_roadmap=False)
    write_reverse_owner_state(
        repo,
        "other-roadmap",
        rows=[("other-feature", ".codestable/features/2026-07-02-other-feature")],
    )

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    assert result["status"] == "continue"
    assert result["next_action"] == "cs-feat implementation"
    assert result["evidence"]["execution_lane"] == "standard"


@pytest.mark.parametrize("quick", [False, True])
def test_reverse_owner_ignores_unrelated_identity_mismatch(tmp_path: Path, quick: bool) -> None:
    repo = init_repo(tmp_path)
    if quick:
        feature = repo / ".codestable/features/2026-07-13-small-export"
        write_ff_note(feature, "small-export")
    else:
        feature = write_feature(repo, "api-seed", design_status="approved", include_roadmap=False)
    write_reverse_owner_state(
        repo,
        "renamed-roadmap",
        state_roadmap="old-roadmap",
        rows=[("other-feature", ".codestable/features/2026-07-02-other-feature")],
    )

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    assert result["status"] == "continue"
    assert result["next_action"] == ("cs-code-review" if quick else "cs-feat implementation")


def test_reverse_owner_identity_mismatch_claiming_feature_fails_closed(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(repo, "api-seed", design_status="approved", include_roadmap=False)
    goal_state = write_reverse_owner_state(
        repo,
        "renamed-roadmap",
        state_roadmap="old-roadmap",
        rows=[("api-seed", ".codestable/features/2026-07-02-api-seed")],
    )

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    expected_path = goal_state.relative_to(repo).as_posix()
    assert result["status"] == "blocked"
    assert result["next_action"] == "inspect-epic-goal-state"
    assert expected_path in result["blocking"][0]
    assert expected_path in result["evidence"]["roadmap_owner_error"]


def test_reverse_owner_unparseable_goal_state_fails_closed(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(repo, "api-seed", design_status="approved", include_roadmap=False)
    goal_state = repo / ".codestable/roadmap/broken-roadmap/goal-state.yaml"
    write(goal_state, "roadmap: broken-roadmap\nfeatures: [unterminated\n")

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    expected_path = goal_state.relative_to(repo).as_posix()
    assert result["status"] == "blocked"
    assert expected_path in result["blocking"][0]
    assert expected_path in result["evidence"]["roadmap_owner_error"]


@pytest.mark.parametrize("same_state", [False, True])
def test_reverse_owner_multiple_claims_fail_closed(tmp_path: Path, same_state: bool) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(repo, "api-seed", design_status="approved", include_roadmap=False)
    feature_dir = ".codestable/features/2026-07-02-api-seed"
    first = write_reverse_owner_state(repo, "first-roadmap", rows=[("api-seed", feature_dir)])
    if same_state:
        write_reverse_owner_state(
            repo,
            "first-roadmap",
            rows=[("api-seed", feature_dir), ("api-seed-copy", feature_dir)],
        )
        expected_paths = [first.relative_to(repo).as_posix()]
    else:
        second = write_reverse_owner_state(repo, "second-roadmap", rows=[("api-seed", feature_dir)])
        expected_paths = [first.relative_to(repo).as_posix(), second.relative_to(repo).as_posix()]

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    assert result["status"] == "blocked"
    assert "multiple roadmap goal-states claim" in result["reason"]
    assert all(path in result["blocking"][0] for path in expected_paths)


def test_reverse_owner_matching_row_without_item_fails_closed(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(repo, "api-seed", design_status="approved", include_roadmap=False)
    goal_state = write_reverse_owner_state(
        repo,
        "broken-roadmap",
        rows=[(None, ".codestable/features/2026-07-02-api-seed")],
    )

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    expected_path = goal_state.relative_to(repo).as_posix()
    assert result["status"] == "blocked"
    assert expected_path in result["blocking"][0]
    assert expected_path in result["evidence"]["roadmap_owner_error"]


@pytest.mark.parametrize("forward", [False, True])
def test_goal_state_invalid_feature_dir_returns_structured_block(
    tmp_path: Path,
    forward: bool,
) -> None:
    repo = init_repo(tmp_path)
    roadmap = write_roadmap(repo)
    goal_state = roadmap / "goal-state.yaml"
    write(
        goal_state,
        "roadmap: billing-system\n"
        "status: ready-to-dispatch\n"
        "features:\n"
        "  - slug: api-seed\n"
        "    roadmap_item: api-seed\n"
        '    feature_dir: ".codestable/features/2026\\0-07-02-api-seed"\n'
        "    status: implementing\n",
    )
    feature = write_feature(
        repo,
        "api-seed",
        design_status="approved",
        include_roadmap=forward,
    )

    completed, payload = run_cli_json(repo, "feature", feature)

    expected_path = goal_state.relative_to(repo).as_posix()
    assert completed.returncode == 1
    assert completed.stderr == ""
    assert payload["status"] == "blocked"
    assert expected_path in payload["blocking"][0]


@pytest.mark.parametrize(
    "features_yaml",
    [
        "features:\n  slug: api-seed\n  feature_dir: .codestable/features/2026-07-02-api-seed\n",
        "features:\n  - api-seed\n",
    ],
)
def test_reverse_goal_owner_invalid_features_shape_fails_closed(
    tmp_path: Path,
    features_yaml: str,
) -> None:
    repo = init_repo(tmp_path)
    roadmap = write_roadmap(repo)
    goal_state = roadmap / "goal-state.yaml"
    write(goal_state, "roadmap: billing-system\nstatus: ready-to-dispatch\n" + features_yaml)
    feature = write_feature(repo, "api-seed", design_status="approved", include_roadmap=False)
    write(feature / "api-seed-checklist.yaml", "steps:\n  - id: step-1\n    status: done\n")
    write_code_review(feature, "api-seed")
    write(
        feature / "api-seed-acceptance.md",
        "---\ndoc_type: feature-acceptance\nstatus: passed\n---\n# Acceptance\n",
    )

    completed, payload = run_cli_json(repo, "feature", feature)

    expected_path = goal_state.relative_to(repo).as_posix()
    assert completed.returncode == 1
    assert completed.stderr == ""
    assert payload["status"] == "blocked"
    assert expected_path in payload["blocking"][0]
    assert payload["next_action"] != "CS_FEATURE_STANDARD_COMPLETE"


def test_forward_metadata_missing_state_detects_external_reverse_claim(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(repo, "api-seed", design_status="approved", include_roadmap=True)
    write(feature / "api-seed-checklist.yaml", "steps:\n  - id: step-1\n    status: done\n")
    write_code_review(feature, "api-seed")
    write(
        feature / "api-seed-acceptance.md",
        "---\ndoc_type: feature-acceptance\nstatus: passed\n---\n# Acceptance\n",
    )
    external = write_reverse_owner_state(
        repo,
        "external-roadmap",
        rows=[("api-seed", ".codestable/features/2026-07-02-api-seed")],
    )

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    expected = [
        ".codestable/roadmap/billing-system/goal-state.yaml",
        external.relative_to(repo).as_posix(),
    ]
    assert result["status"] == "blocked"
    assert result["next_action"] == "inspect-epic-goal-state"
    assert result["next_action"] != "CS_FEATURE_STANDARD_COMPLETE"
    assert all(path in result["blocking"][0] for path in expected)


def test_forward_owner_detects_second_external_claim(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    roadmap = write_roadmap(repo)
    write_roadmap_goal_state(roadmap)
    feature = write_feature(repo, "api-seed", design_status="approved", include_roadmap=True)
    external = write_reverse_owner_state(
        repo,
        "external-roadmap",
        rows=[("api-seed", ".codestable/features/2026-07-02-api-seed")],
    )

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    assert result["status"] == "blocked"
    assert result["next_action"] == "inspect-epic-goal-state"
    assert external.relative_to(repo).as_posix() in result["blocking"][0]


@pytest.mark.parametrize(
    ("design_status", "artifacts_complete"),
    [("draft", False), ("approved", True)],
)
def test_feature_pre_goal_package_roadmap_child_returns_to_epic(
    tmp_path: Path,
    design_status: str,
    artifacts_complete: bool,
) -> None:
    repo = init_repo(tmp_path)
    write_roadmap(repo)
    feature = write_feature(repo, "api-seed", design_status=design_status, include_roadmap=True)
    if artifacts_complete:
        write(feature / "api-seed-checklist.yaml", "steps:\n  - id: step-1\n    status: done\n")
        write_code_review(feature, "api-seed")
        write(
            feature / "api-seed-acceptance.md",
            "---\ndoc_type: feature-acceptance\nstatus: passed\n---\n# Acceptance\n",
        )

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    assert result["status"] == "continue"
    assert result["next_action"] == "return-to-cs-epic"
    assert result["evidence"]["roadmap_owner_source"] == "roadmap-items"
    assert result["evidence"]["roadmap_items"].endswith("billing-system-items.yaml")
    assert result["next_action"] not in {"feature-design-confirmation", "CS_FEATURE_STANDARD_COMPLETE"}


@pytest.mark.parametrize(
    ("metadata_field", "metadata_value"),
    [("roadmap", "billing-system"), ("roadmap_item", "api-seed")],
)
def test_feature_incomplete_roadmap_metadata_fails_closed(
    tmp_path: Path,
    metadata_field: str,
    metadata_value: str,
) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(repo, "api-seed", design_status="approved", include_roadmap=False)
    write(
        feature / "api-seed-design.md",
        "---\ndoc_type: feature-design\nfeature: 2026-07-02-api-seed\n"
        f"{metadata_field}: {metadata_value}\nstatus: approved\n---\n# Design\n",
    )

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    assert result["status"] == "blocked"
    assert result["next_action"] == "fix-feature-roadmap-metadata"
    assert "roadmap and roadmap_item together" in result["reason"]


def test_feature_invalid_roadmap_slug_returns_structured_block(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(repo, "api-seed", design_status="approved", include_roadmap=False)
    write(
        feature / "api-seed-design.md",
        "---\n"
        "doc_type: feature-design\n"
        "feature: 2026-07-02-api-seed\n"
        'roadmap: "billing\\0x"\n'
        "roadmap_item: api-seed\n"
        "status: approved\n"
        "---\n# Design\n",
    )

    completed, payload = run_cli_json(repo, "feature", feature)

    assert completed.returncode == 1
    assert completed.stderr == ""
    assert payload["status"] == "blocked"
    assert payload["next_action"] == "inspect-epic-goal-state"
    assert "invalid roadmap owner path" in payload["reason"]


def test_feature_pre_goal_package_roadmap_without_matching_item_fails_closed(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    roadmap = write_roadmap(repo)
    write(
        roadmap / "billing-system-items.yaml",
        "roadmap: billing-system\nitems:\n  - slug: ui-seed\n    status: planned\n",
    )
    feature = write_feature(repo, "api-seed", design_status="approved", include_roadmap=True)

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    items_path = ".codestable/roadmap/billing-system/billing-system-items.yaml"
    assert result["status"] == "blocked"
    assert result["next_action"] == "inspect-epic-goal-state"
    assert items_path in result["blocking"][0]
    assert "do not uniquely own" in result["reason"]


def test_feature_pre_goal_package_roadmap_item_pointer_must_match_feature(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    roadmap = write_roadmap(repo)
    write(
        roadmap / "billing-system-items.yaml",
        "roadmap: billing-system\n"
        "items:\n"
        "  - slug: api-seed\n"
        "    status: planned\n"
        "    feature: .codestable/features/2026-07-02-other-feature\n",
    )
    feature = write_feature(repo, "api-seed", design_status="approved", include_roadmap=True)

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    items_path = ".codestable/roadmap/billing-system/billing-system-items.yaml"
    assert result["status"] == "blocked"
    assert result["next_action"] == "inspect-epic-goal-state"
    assert "feature pointer does not match" in result["reason"]
    assert items_path in result["blocking"][0]


@pytest.mark.parametrize(
    "contents",
    [
        "roadmap: billing-system\nitems:\n  slug: api-seed\n  feature: null\n",
        "roadmap: billing-system\nitems:\n  - slug: api-seed\n    feature: []\n",
    ],
)
def test_forward_items_owner_invalid_yaml_shape_returns_structured_block(
    tmp_path: Path,
    contents: str,
) -> None:
    repo = init_repo(tmp_path)
    roadmap = write_roadmap(repo)
    items_path = roadmap / "billing-system-items.yaml"
    write(items_path, contents)
    feature = write_feature(repo, "api-seed", design_status="approved", include_roadmap=True)

    completed, payload = run_cli_json(repo, "feature", feature)

    expected_path = items_path.relative_to(repo).as_posix()
    assert completed.returncode == 1
    assert completed.stderr == ""
    assert payload["status"] == "blocked"
    assert payload["next_action"] == "inspect-epic-goal-state"
    assert expected_path in payload["blocking"][0]


@pytest.mark.parametrize("same_items_file", [False, True])
def test_forward_items_owner_detects_second_items_claim(
    tmp_path: Path,
    same_items_file: bool,
) -> None:
    repo = init_repo(tmp_path)
    roadmap = write_roadmap(repo)
    feature_dir = ".codestable/features/2026-07-02-api-seed"
    primary_items = roadmap / "billing-system-items.yaml"
    if same_items_file:
        write(
            primary_items,
            "roadmap: billing-system\nitems:\n"
            f"  - slug: api-seed\n    feature: {feature_dir}\n"
            f"  - slug: other-item\n    feature: {feature_dir}\n",
        )
        expected_paths = [primary_items.relative_to(repo).as_posix()]
    else:
        secondary_items = repo / ".codestable/roadmap/secondary/secondary-items.yaml"
        write(
            primary_items,
            f"roadmap: billing-system\nitems:\n  - slug: api-seed\n    feature: {feature_dir}\n",
        )
        write(
            secondary_items,
            f"roadmap: secondary\nitems:\n  - slug: other-item\n    feature: {feature_dir}\n",
        )
        expected_paths = [
            primary_items.relative_to(repo).as_posix(),
            secondary_items.relative_to(repo).as_posix(),
        ]
    feature = write_feature(repo, "api-seed", design_status="approved", include_roadmap=True)

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    assert result["status"] == "blocked"
    assert result["next_action"] == "inspect-epic-goal-state"
    assert "multiple roadmap items claim" in result["reason"]
    assert all(path in result["blocking"][0] for path in expected_paths)


@pytest.mark.parametrize("same_items_file", [False, True])
def test_forward_goal_owner_detects_second_items_claim(
    tmp_path: Path,
    same_items_file: bool,
) -> None:
    repo = init_repo(tmp_path)
    roadmap = write_roadmap(repo)
    write_roadmap_goal_state(roadmap)
    feature_dir = ".codestable/features/2026-07-02-api-seed"
    primary_items = roadmap / "billing-system-items.yaml"
    primary = (
        "roadmap: billing-system\nitems:\n"
        "  - slug: api-seed\n    feature: null\n"
    )
    if same_items_file:
        write(primary_items, primary + f"  - slug: other-item\n    feature: {feature_dir}\n")
        expected_paths = [primary_items.relative_to(repo).as_posix()]
    else:
        secondary_items = repo / ".codestable/roadmap/secondary/secondary-items.yaml"
        write(primary_items, primary)
        write(
            secondary_items,
            f"roadmap: secondary\nitems:\n  - slug: other-item\n    feature: {feature_dir}\n",
        )
        expected_paths = [
            primary_items.relative_to(repo).as_posix(),
            secondary_items.relative_to(repo).as_posix(),
        ]
    feature = write_feature(repo, "api-seed", design_status="approved", include_roadmap=True)

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    assert result["status"] == "blocked"
    assert result["next_action"] == "inspect-epic-goal-state"
    assert "multiple roadmap items claim" in result["reason"]
    assert all(path in result["blocking"][0] for path in expected_paths)


def test_forward_goal_owner_detects_second_claim_in_same_goal_state(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    roadmap = write_roadmap(repo)
    feature_dir = ".codestable/features/2026-07-02-api-seed"
    goal_state = roadmap / "goal-state.yaml"
    write(
        goal_state,
        "roadmap: billing-system\n"
        "status: ready-to-dispatch\n"
        "features:\n"
        "  - slug: api-seed\n"
        "    roadmap_item: api-seed\n"
        f"    feature_dir: {feature_dir}\n"
        "    status: implementing\n"
        "  - slug: duplicate-claim\n"
        "    roadmap_item: duplicate-claim\n"
        f"    feature_dir: {feature_dir}\n"
        "    status: pending\n",
    )
    feature = write_feature(repo, "api-seed", design_status="approved", include_roadmap=True)

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    expected_path = goal_state.relative_to(repo).as_posix()
    assert result["status"] == "blocked"
    assert result["next_action"] == "inspect-epic-goal-state"
    assert "multiple roadmap goal-states claim" in result["reason"]
    assert expected_path in result["blocking"][0]


def test_feature_epic_child_batch_never_completes_as_standard(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    write_roadmap(repo)
    feature = write_feature(repo, "api-seed", design_status="approved", include_roadmap=True)
    write(feature / "api-seed-checklist.yaml", "steps:\n  - id: step-1\n    status: done\n")
    write_code_review(feature, "api-seed")
    write(
        feature / "api-seed-acceptance.md",
        "---\ndoc_type: feature-acceptance\nstatus: passed\n---\n# Acceptance\n",
    )

    result = workflow_next.feature_next(feature, epic_child_batch=True)

    assert result["status"] == "continue"
    assert result["next_action"] == "return-to-cs-epic-batch-loop"
    assert result["evidence"]["execution_lane"] == "goal"
    assert result["evidence"]["execution_lane_source"] == "epic-child-batch"
    assert result["next_action"] != "CS_FEATURE_STANDARD_COMPLETE"


def test_feature_draft_owned_by_roadmap_goal_returns_to_epic(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    roadmap = write_roadmap(repo)
    write_roadmap_goal_state(roadmap)
    feature = write_feature(
        repo,
        "api-seed",
        design_status="draft",
        review_status="passed",
        include_roadmap=True,
    )

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    assert result["status"] == "continue"
    assert result["next_action"] == "return-to-cs-epic"
    assert result["next_action"] != "feature-design-confirmation"
    assert result["evidence"]["execution_lane_source"] == "roadmap-goal-state"


def test_feature_parent_goal_state_with_mismatched_owner_fails_closed(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    roadmap = write_roadmap(repo)
    write_roadmap_goal_state(roadmap, feature_slug="ui-seed")
    feature = write_feature(repo, "api-seed", design_status="approved", include_roadmap=True)

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    assert result["status"] == "blocked"
    assert result["next_action"] == "inspect-epic-goal-state"
    assert "standard" not in result["next_action"]


def test_feature_quick_ff_note_recovers_review_then_completion(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    feature = repo / ".codestable/features/2026-07-13-small-export"
    write_ff_note(feature, "small-export")

    review = workflow_next.feature_next(feature, epic_child_batch=False)
    assert review["status"] == "continue"
    assert review["next_action"] == "cs-code-review"
    assert review["evidence"]["execution_lane"] == "quick"

    write_code_review(feature, "small-export")
    complete = workflow_next.feature_next(feature, epic_child_batch=False)
    assert complete["status"] == "complete"
    assert complete["next_action"] == "CS_FEATURE_QUICK_COMPLETE"


def test_feature_quick_ff_note_routes_review_fix(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    feature = repo / ".codestable/features/2026-07-13-small-export"
    write_ff_note(feature, "small-export")
    write_code_review(feature, "small-export", status="changes-requested")

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    assert result["status"] == "continue"
    assert result["next_action"] == "cs-feat --mode quick"
    assert "review-fix" in result["reason"]


@pytest.mark.parametrize(
    ("artifact", "status"),
    [("qa", "failed"), ("qa", "blocked"), ("acceptance", "failed"), ("acceptance", "blocked")],
)
def test_feature_quick_rejects_existing_failed_quality_evidence(
    tmp_path: Path,
    artifact: str,
    status: str,
) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(
        repo,
        "api-seed",
        design_status="approved",
        execution_lane="quick",
        execution_lane_reason="owner-requested-after-risk-recheck",
    )
    write_ff_note(feature, "api-seed")
    write_code_review(feature, "api-seed")
    doc_type = "feature-qa" if artifact == "qa" else "feature-acceptance"
    write(
        feature / f"api-seed-{artifact}.md",
        f"---\ndoc_type: {doc_type}\nstatus: {status}\n---\n# Evidence\n",
    )

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    artifact_path = f".codestable/features/2026-07-02-api-seed/api-seed-{artifact}.md"
    assert result["status"] == "blocked"
    assert result["next_action"] == "resolve-quick-quality-conflict"
    assert artifact_path in result["blocking"][0]
    assert result["next_action"] != "CS_FEATURE_QUICK_COMPLETE"


def test_feature_quick_allows_existing_passed_quality_evidence(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(
        repo,
        "api-seed",
        design_status="approved",
        execution_lane="quick",
        execution_lane_reason="owner-requested-after-risk-recheck",
    )
    write_ff_note(feature, "api-seed")
    write_code_review(feature, "api-seed")
    write(feature / "api-seed-qa.md", "---\ndoc_type: feature-qa\nstatus: passed\n---\n# QA\n")
    write(
        feature / "api-seed-acceptance.md",
        "---\ndoc_type: feature-acceptance\nstatus: passed\n---\n# Acceptance\n",
    )

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    assert result["status"] == "complete"
    assert result["next_action"] == "CS_FEATURE_QUICK_COMPLETE"


def test_feature_reclassified_quick_design_resumes_fastforward(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(
        repo,
        "api-seed",
        design_status="approved",
        execution_lane="quick",
        execution_lane_reason="owner-requested-after-risk-recheck",
    )

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    assert result["status"] == "continue"
    assert result["next_action"] == "cs-feat --mode quick"
    assert result["evidence"]["execution_lane_source"] == "design"


def test_feature_reclassified_quick_design_requires_persisted_reason(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(repo, "api-seed", design_status="approved", execution_lane="quick")

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    assert result["status"] == "blocked"
    assert result["next_action"] == "fix-feature-execution-lane"
    assert "execution_lane_reason" in result["reason"]


def test_feature_ff_note_conflicting_with_recorded_standard_lane_fails_closed(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(repo, "api-seed", design_status="approved", execution_lane="standard")
    write_ff_note(feature, "api-seed")

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    assert result["status"] == "blocked"
    assert result["next_action"] == "resolve-feature-execution-lane-conflict"


def test_feature_goal_state_overrides_reclassified_quick_lane(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(repo, "api-seed", design_status="approved", execution_lane="quick")
    write_ff_note(feature, "api-seed")
    write_goal_state(feature, stage="implementation", status="ready-to-dispatch")

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    assert result["status"] == "dispatch_goal"
    assert result["evidence"]["execution_lane"] == "goal"
    assert result["evidence"]["execution_lane_source"] == "feature-goal-state"


def test_feature_standard_lane_recovers_without_goal_package_or_standalone_qa(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(repo, "api-seed", design_status="approved", execution_lane="standard")

    implementation = workflow_next.feature_next(feature, epic_child_batch=False)
    assert implementation["status"] == "continue"
    assert implementation["next_action"] == "cs-feat implementation"
    assert implementation["evidence"]["execution_lane"] == "standard"

    write(feature / "api-seed-checklist.yaml", "steps:\n  - id: step-1\n    status: done\n")
    review = workflow_next.feature_next(feature, epic_child_batch=False)
    assert review["status"] == "continue"
    assert review["next_action"] == "cs-code-review"

    write_code_review(feature, "api-seed")
    acceptance = workflow_next.feature_next(feature, epic_child_batch=False)
    assert acceptance["status"] == "continue"
    assert acceptance["next_action"] == "cs-feat --stage accept"

    write(
        feature / "api-seed-acceptance.md",
        "---\ndoc_type: feature-acceptance\nstatus: passed\n---\n# Acceptance\n",
    )
    complete = workflow_next.feature_next(feature, epic_child_batch=False)
    assert complete["status"] == "complete"
    assert complete["next_action"] == "CS_FEATURE_STANDARD_COMPLETE"


def test_feature_standard_lane_routes_review_fix_without_goal_state(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(repo, "api-seed", design_status="approved")
    write(feature / "api-seed-checklist.yaml", "steps:\n  - id: step-1\n    status: done\n")
    write(
        feature / "api-seed-review.md",
        "---\ndoc_type: feature-review\nstatus: changes-requested\n---\n# Review\n",
    )

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    assert result["status"] == "continue"
    assert result["next_action"] == "cs-feat implementation review-fix"
    assert result["evidence"]["execution_lane"] == "standard"


@pytest.mark.parametrize("qa_status", ["failed", "blocked"])
def test_feature_standard_lane_routes_failed_qa_to_qa_fix(tmp_path: Path, qa_status: str) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(repo, "api-seed", design_status="approved", execution_lane="standard")
    write(feature / "api-seed-checklist.yaml", "steps:\n  - id: step-1\n    status: done\n")
    write_code_review(feature, "api-seed")
    write(
        feature / "api-seed-qa.md",
        f"---\ndoc_type: feature-qa\nstatus: {qa_status}\n---\n# QA\n",
    )

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    assert result["status"] == "continue"
    assert result["next_action"] == "cs-feat --stage impl qa-fix"


def test_feature_standard_lane_resumes_nonterminal_qa(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(repo, "api-seed", design_status="approved", execution_lane="standard")
    write(feature / "api-seed-checklist.yaml", "steps:\n  - id: step-1\n    status: done\n")
    write_code_review(feature, "api-seed")
    write(feature / "api-seed-qa.md", "---\ndoc_type: feature-qa\nstatus: pending\n---\n# QA\n")

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    assert result["status"] == "continue"
    assert result["next_action"] == "cs-feat --stage qa"


@pytest.mark.parametrize(
    ("doc_type", "reviewer"),
    [
        ("feature-review", None),
        ("feature-review", "self"),
        ("feature-review", "ocr"),
        ("wrong-review", "subagent"),
    ],
)
def test_feature_standard_lane_rejects_untrusted_passed_review(
    tmp_path: Path,
    doc_type: str,
    reviewer: str | None,
) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(repo, "api-seed", design_status="approved", execution_lane="standard")
    write(feature / "api-seed-checklist.yaml", "steps:\n  - id: step-1\n    status: done\n")
    write_code_review(feature, "api-seed", doc_type=doc_type, reviewer=reviewer)

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    assert result["status"] == "blocked"
    assert result["next_action"] == "fix-feature-code-review-evidence"


def test_feature_standard_lane_rejects_reviewer_marker_outside_frontmatter(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(repo, "api-seed", design_status="approved", execution_lane="standard")
    write(feature / "api-seed-checklist.yaml", "steps:\n  - id: step-1\n    status: done\n")
    write(
        feature / "api-seed-review.md",
        "---\ndoc_type: feature-review\nstatus: passed\nreviewer: self\n---\n"
        "# Review\n\nreviewer: subagent\n",
    )

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    assert result["status"] == "blocked"
    assert result["next_action"] == "fix-feature-code-review-evidence"


def test_feature_standard_lane_honors_explicit_self_review_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(repo, "api-seed", design_status="approved", execution_lane="standard")
    write(feature / "api-seed-checklist.yaml", "steps:\n  - id: step-1\n    status: done\n")
    write_code_review(feature, "api-seed", reviewer="self")
    monkeypatch.setenv("CODESTABLE_ALLOW_SELF_REVIEW_FALLBACK", "1")

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    assert result["status"] == "continue"
    assert result["next_action"] == "cs-feat --stage accept"


def test_feature_execution_lane_is_normalized(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(repo, "api-seed", design_status="approved", execution_lane='" Standard "')

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    assert result["status"] == "continue"
    assert result["evidence"]["execution_lane"] == "standard"


def test_feature_standard_lane_rejects_wrong_acceptance_doc_type(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(repo, "api-seed", design_status="approved", execution_lane="standard")
    write(feature / "api-seed-checklist.yaml", "steps:\n  - id: step-1\n    status: done\n")
    write_code_review(feature, "api-seed")
    write(
        feature / "api-seed-acceptance.md",
        "---\ndoc_type: wrong-acceptance\nstatus: passed\n---\n# Acceptance\n",
    )

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    assert result["status"] == "blocked"
    assert result["next_action"] == "fix-feature-acceptance-evidence"


def test_feature_standard_lane_parses_checklist_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(repo, "api-seed", design_status="approved", execution_lane="standard")
    calls = 0
    original = workflow_next.all_checklist_steps_done

    def counted(checklist: Path | None) -> bool:
        nonlocal calls
        calls += 1
        return original(checklist)

    monkeypatch.setattr(workflow_next, "all_checklist_steps_done", counted)
    workflow_next.feature_next(feature, epic_child_batch=False)

    assert calls == 1


def test_feature_goal_lane_still_requires_goal_package(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(repo, "api-seed", design_status="approved", execution_lane="goal")

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    assert result["status"] == "goal_package"
    assert result["next_action"] == "cs-feat goal-package"
    assert result["evidence"]["execution_lane"] == "goal"


def test_feature_existing_goal_state_overrides_recorded_standard_lane(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(repo, "api-seed", design_status="approved", execution_lane="standard")
    write_goal_state(feature, stage="implementation", status="ready-to-dispatch")

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    assert result["status"] == "dispatch_goal"
    assert result["evidence"]["execution_lane"] == "goal"


def test_feature_unknown_execution_lane_fails_closed(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(repo, "api-seed", execution_lane="turbo")

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    assert result["status"] == "blocked"
    assert result["next_action"] == "fix-feature-execution-lane"


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
    write_feature(repo, "api-seed", design_status="approved", include_roadmap=True)
    write_feature(repo, "ui-seed", design_status="approved", include_roadmap=True)
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
    write_feature(repo, "api-seed", design_status="approved", include_roadmap=True)
    write_feature(repo, "ui-seed", design_status="approved", include_roadmap=True)
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


@pytest.mark.parametrize(
    "artifact",
    ["design", "checklist", "review", "qa", "acceptance", "ff-note", "goal-state"],
)
def test_feature_corrupt_artifact_returns_structured_json_block(tmp_path: Path, artifact: str) -> None:
    repo = init_repo(tmp_path)
    feature = write_feature(repo, "api-seed", design_status="approved", execution_lane="standard")
    corrupt = "---\ndoc_type: [unterminated\n---\n# Corrupt\n"
    if artifact == "design":
        target = feature / "api-seed-design.md"
        write(target, corrupt)
    elif artifact == "checklist":
        target = feature / "api-seed-checklist.yaml"
        write(target, "steps: [unterminated\n")
    elif artifact == "goal-state":
        target = feature / "goal-state.yaml"
        write(target, "stage: [unterminated\n")
    else:
        target = feature / f"api-seed-{artifact}.md"
        write(target, corrupt)

    result = workflow_next.feature_next(feature, epic_child_batch=False)

    expected_path = target.relative_to(repo).as_posix()
    assert result["status"] == "blocked"
    assert result["next_action"] == "fix-feature-artifact-yaml"
    assert expected_path in result["blocking"][0]
    assert expected_path in result["evidence"]["invalid_artifact"]

    completed, payload = run_cli_json(repo, "feature", feature)
    assert completed.returncode == 1
    assert "Traceback" not in completed.stderr
    assert payload["status"] == "blocked"
    assert expected_path in str(payload["reason"])


def test_epic_corrupt_goal_state_returns_structured_json_block(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    roadmap = write_roadmap(repo)
    write_feature(repo, "api-seed", design_status="approved", include_roadmap=True)
    write_feature(repo, "ui-seed", design_status="approved", include_roadmap=True)
    target = roadmap / "goal-state.yaml"
    write(target, "status: [unterminated\n")

    result = workflow_next.epic_next(roadmap)

    expected_path = target.relative_to(repo).as_posix()
    assert result["status"] == "blocked"
    assert result["next_action"] == "fix-epic-artifact-yaml"
    assert expected_path in result["blocking"][0]

    completed, payload = run_cli_json(repo, "epic", roadmap)
    assert completed.returncode == 1
    assert "Traceback" not in completed.stderr
    assert payload["status"] == "blocked"
    assert expected_path in str(payload["reason"])


def test_cli_accepts_json_before_or_after_subcommand(tmp_path: Path) -> None:
    repo = init_repo(tmp_path)
    roadmap = write_roadmap(repo)
    write_feature(repo, "api-seed", include_roadmap=True)

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
