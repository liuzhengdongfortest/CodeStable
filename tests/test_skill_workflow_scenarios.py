from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "plugins/codestable/skills"


AFFECTED_SKILLS = {
    "cs",
    "cs-feat",
    "cs-feat-design",
    "cs-feat-design-review",
    "cs-feat-impl",
    "cs-feat-qa",
    "cs-feat-accept",
    "cs-feat-ff",
    "cs-issue",
    "cs-issue-report",
    "cs-issue-analyze",
    "cs-issue-fix",
    "cs-refactor",
    "cs-refactor-ff",
    "cs-docs",
    "cs-doc-tutorial",
    "cs-doc-api",
    "cs-docs-neat",
    "cs-epic",
    "cs-feedback",
    "cs-roadmap",
    "cs-roadmap-review",
    "cs-roadmap-impl-goal",
    "cs-code-review",
    "cs-brainstorm",
    "cs-req",
    "cs-onboard",
}


SCENARIO_COVERAGE = {
    "router": {"cs", "cs-brainstorm", "cs-req", "cs-onboard"},
    "feature-long-range": {
        "cs-feat",
        "cs-feat-design",
        "cs-feat-design-review",
        "cs-feat-impl",
        "cs-feat-qa",
        "cs-feat-accept",
        "cs-feat-ff",
        "cs-code-review",
    },
    "epic-long-range": {
        "cs-epic",
        "cs-roadmap",
        "cs-roadmap-review",
        "cs-roadmap-impl-goal",
        "cs-feat",
        "cs-code-review",
    },
    "issue": {"cs-issue", "cs-issue-report", "cs-issue-analyze", "cs-issue-fix", "cs-code-review"},
    "refactor": {"cs-refactor", "cs-refactor-ff", "cs-code-review"},
    "docs": {"cs-docs", "cs-doc-tutorial", "cs-doc-api", "cs-docs-neat"},
    "feedback": {"cs-feedback"},
    "goal-driver": {"cs-onboard", "cs-feat", "cs-epic"},
}


COMPATIBILITY_ENTRIES = {
    "cs-feat-design": ("cs-feat", "requested_stage", "design"),
    "cs-feat-design-review": ("cs-feat", "requested_stage", "design-review"),
    "cs-feat-impl": ("cs-feat", "requested_stage", "implementation"),
    "cs-feat-qa": ("cs-feat", "requested_stage", "qa"),
    "cs-feat-accept": ("cs-feat", "requested_stage", "acceptance"),
    "cs-feat-ff": ("cs-feat", "requested_mode", "fastforward"),
    "cs-issue-report": ("cs-issue", "requested_stage", "report"),
    "cs-issue-analyze": ("cs-issue", "requested_stage", "analyze"),
    "cs-issue-fix": ("cs-issue", "requested_stage", "fix"),
    "cs-refactor-ff": ("cs-refactor", "requested_mode", "fastforward"),
    "cs-doc-tutorial": ("cs-docs", "requested_mode", "tutorial"),
    "cs-doc-api": ("cs-docs", "requested_mode", "api"),
    "cs-roadmap": ("cs-epic", "requested_stage", "planning"),
    "cs-roadmap-review": ("cs-epic", "requested_stage", "review"),
    "cs-roadmap-impl-goal": ("cs-epic", "requested_stage", "goal-package"),
}


@dataclass(frozen=True)
class Action:
    name: str
    target: str


def skill_text(skill: str, rel_path: str = "SKILL.md") -> str:
    return (SKILLS / skill / rel_path).read_text(encoding="utf-8")


def assert_doc_contains(skill: str, rel_path: str, *phrases: str) -> None:
    text = skill_text(skill, rel_path)
    missing = [phrase for phrase in phrases if phrase not in text]
    assert missing == [], f"{skill}/{rel_path} missing {missing}"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def init_isolated_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "isolated-repo"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "Workflow Test")
    git(repo, "config", "user.email", "workflow-test@example.invalid")
    write(repo / ".codestable/attention.md", "# Attention\n\n- Report language: zh.\n")
    write(repo / ".codestable/reference/execution-conventions.md", skill_text("cs-onboard", "references/execution-conventions.md"))
    write(repo / ".codestable/reference/agent-conventions.md", skill_text("cs-onboard", "references/agent-conventions.md"))
    write(repo / "src/app.py", "def hello():\n    return 'hello'\n")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "baseline")
    return repo


def frontmatter(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    block = text.split("---", 2)[1]
    result = {}
    for line in block.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip().strip('"')
    return result


def top_level_yaml(path: Path) -> dict[str, str]:
    result = {}
    if not path.exists():
        return result
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(" ") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip()] = value.strip().strip('"')
    return result


def replace_status(path: Path, status: str) -> None:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"(?m)^status: .+$", f"status: {status}", text, count=1)
    path.write_text(text, encoding="utf-8")


def feature_dir(repo: Path, slug: str) -> Path:
    return repo / ".codestable/features" / f"2026-07-02-{slug}"


def write_feature_design(
    repo: Path,
    slug: str,
    status: str = "draft",
    roadmap: str | None = None,
    execution_lane: str = "standard",
) -> Path:
    directory = feature_dir(repo, slug)
    roadmap_fields = ""
    if roadmap:
        roadmap_fields = f"roadmap: {roadmap}\nroadmap_item: {slug}\n"
    write(
        directory / f"{slug}-design.md",
        f"---\ndoc_type: feature-design\nfeature: 2026-07-02-{slug}\n{roadmap_fields}"
        f"execution_lane: {execution_lane}\nstatus: {status}\n---\n# Design\n",
    )
    write(
        directory / f"{slug}-checklist.yaml",
        f"feature: 2026-07-02-{slug}\nsteps:\n  - id: step-1\n    status: pending\nchecks:\n  - id: check-1\n    status: pending\n",
    )
    return directory


def write_feature_design_review(repo: Path, slug: str, status: str = "passed") -> None:
    directory = feature_dir(repo, slug)
    write(
        directory / f"{slug}-design-review.md",
        f"---\ndoc_type: feature-design-review\nfeature: 2026-07-02-{slug}\nstatus: {status}\n---\n# Design Review\n",
    )


def write_feature_goal_state(repo: Path, slug: str, stage: str, status: str, driver: str = "none") -> None:
    directory = feature_dir(repo, slug)
    driver_id = f"{driver}-123" if driver != "none" else ""
    write(
        directory / "goal-state.yaml",
        f"feature: {slug}\nstatus: {status}\nbaseline_ref: baseline\nstage: {stage}\ndriver_kind: {driver}\ndriver_id: \"{driver_id}\"\n",
    )
    write(directory / "goal-plan.md", "# Goal Plan\n")
    write(directory / "goal-protocol.md", "# Goal Protocol\n")


def normalized_review_state(path: Path) -> str:
    meta = frontmatter(path)
    state = meta.get("review_state")
    valid = {"passed", "changes-requested", "awaiting-reviewer", "needs-owner-approval", "reviewer-failed", "blocked"}
    if state:
        return state if state in valid else "invalid"
    status = meta.get("status")
    if status == "passed":
        return "passed"
    if status in {"changes-requested", "blocking"}:
        return "changes-requested"
    if status == "blocked":
        return "legacy-blocked"
    return "missing" if status is None else "invalid"


# Compact scenario model only. Production conformance is asserted by
# test_codestable_workflow_next.py against codestable-workflow-next.py directly.
def feature_next(repo: Path, slug: str) -> Action:
    directory = feature_dir(repo, slug)
    design = directory / f"{slug}-design.md"
    review = directory / f"{slug}-design-review.md"
    goal_state = directory / "goal-state.yaml"
    if not design.exists():
        return Action("load-reference", "cs-feat/references/design/protocol.md")

    design_meta = frontmatter(design)
    design_status = design_meta.get("status")
    execution_lane = design_meta.get("execution_lane", "standard")
    review_state = normalized_review_state(review)
    if design_status == "approved" and review_state != "passed":
        return Action("blocked", "invalid-approved-design-review")
    if review_state == "changes-requested":
        return Action("load-reference", "cs-feat/references/design/protocol.md")
    if review_state == "awaiting-reviewer":
        return Action("awaiting", "feature-design-reviewer")
    if review_state == "needs-owner-approval":
        return Action("user-checkpoint", "feature-design-review-fallback")
    if review_state in {"invalid", "legacy-blocked", "reviewer-failed", "blocked"}:
        return Action("blocked", "feature-design-review-block")
    if design_status == "draft" and review_state != "passed":
        return Action("load-reference", "cs-feat/references/design-review/protocol.md")
    if review_state == "passed" and design_status != "approved":
        return Action("user-checkpoint", "feature-design-confirmation")
    if design_status == "approved" and not goal_state.exists():
        if execution_lane == "goal":
            return Action("load-reference", "cs-feat/references/goal/protocol.md")
        return Action("load-reference", "cs-feat/references/implementation/protocol.md")

    state = top_level_yaml(goal_state)
    stage = state.get("stage")
    status = state.get("status")
    if (stage, status) == ("complete", "passed"):
        return Action("complete", "CS_FEATURE_GOAL_COMPLETE")
    if (stage, status) == ("handoff", "blocked"):
        return Action("user-checkpoint", "CS_FEATURE_GOAL_HANDOFF")
    if state.get("driver_kind") in {"host-agent", "paseo", "native"} and state.get("driver_id"):
        return Action("report-visible-driver", state["driver_id"])
    if (stage, status) == ("implementation", "ready-to-dispatch"):
        return Action("dispatch-goal-driver", "feature")
    if (stage, status) == ("implementation", "running"):
        return Action("load-reference", "cs-feat/references/implementation/protocol.md")
    if (stage, status) == ("review", "ready"):
        return Action("load-skill", "cs-code-review")
    if (stage, status) == ("review", "fixing"):
        return Action("load-reference", "cs-feat/references/implementation/protocol.md#review-fix")
    if (stage, status) == ("qa", "ready"):
        return Action("load-reference", "cs-feat/references/qa/protocol.md")
    if (stage, status) == ("qa", "fixing"):
        return Action("load-reference", "cs-feat/references/implementation/protocol.md#qa-fix")
    if (stage, status) == ("acceptance", "ready"):
        return Action("load-reference", "cs-feat/references/acceptance/protocol.md")
    return Action("blocked", "unknown-feature-state")


def roadmap_dir(repo: Path, slug: str) -> Path:
    return repo / ".codestable/roadmap" / slug


def write_roadmap(repo: Path, slug: str, status: str = "draft") -> Path:
    directory = roadmap_dir(repo, slug)
    write(directory / f"{slug}-roadmap.md", f"---\ndoc_type: roadmap\nslug: {slug}\nstatus: {status}\n---\n# Roadmap\n")
    write(
        directory / f"{slug}-items.yaml",
        f"roadmap: {slug}\nitems:\n  - slug: api-seed\n    status: planned\n    feature: null\n  - slug: ui-seed\n    status: planned\n    feature: null\n",
    )
    return directory


def write_roadmap_review(repo: Path, slug: str, status: str = "passed") -> None:
    directory = roadmap_dir(repo, slug)
    write(directory / f"{slug}-roadmap-review.md", f"---\ndoc_type: roadmap-review\nstatus: {status}\n---\n# Review\n")


def roadmap_item_slugs(repo: Path, slug: str) -> list[str]:
    items = roadmap_dir(repo, slug) / f"{slug}-items.yaml"
    return re.findall(r"(?m)^\s*-\s+slug:\s+([A-Za-z0-9_-]+)\s*$", items.read_text(encoding="utf-8"))


def write_epic_goal_state(repo: Path, slug: str, status: str, driver: str = "none") -> None:
    directory = roadmap_dir(repo, slug)
    driver_id = f"{driver}-roadmap-123" if driver != "none" else ""
    write(
        directory / "goal-state.yaml",
        f"roadmap: {slug}\nstatus: {status}\nbaseline_ref: baseline\ndriver_kind: {driver}\ndriver_id: \"{driver_id}\"\ncurrent_feature_index: 0\nfeatures:\n  - slug: api-seed\n    status: pending\n",
    )
    write(directory / "goal-plan.md", "# Goal Plan\n")
    write(directory / "goal-protocol.md", "# Goal Protocol\n")


def epic_next(repo: Path, slug: str) -> Action:
    directory = roadmap_dir(repo, slug)
    roadmap = directory / f"{slug}-roadmap.md"
    review = directory / f"{slug}-roadmap-review.md"
    goal_state = directory / "goal-state.yaml"
    if not roadmap.exists():
        return Action("load-reference", "cs-epic/references/planning/protocol.md")
    roadmap_status = frontmatter(roadmap).get("status")
    review_state = normalized_review_state(review)
    if roadmap_status == "active" and review_state == "missing":
        return Action("blocked", "invalid-active-roadmap-review")
    if review_state == "changes-requested":
        return Action("load-reference", "cs-epic/references/planning/protocol.md")
    if review_state == "awaiting-reviewer":
        return Action("awaiting", "roadmap-reviewer")
    if review_state == "needs-owner-approval":
        return Action("user-checkpoint", "roadmap-review-fallback")
    if review_state in {"invalid", "legacy-blocked", "reviewer-failed", "blocked"}:
        return Action("blocked", "roadmap-review-block")
    if review_state != "passed":
        return Action("load-reference", "cs-epic/references/review/protocol.md")
    if roadmap_status != "active":
        return Action("user-checkpoint", "epic-roadmap-confirmation")

    child_designs = sorted((repo / ".codestable/features").glob("*/**/*-design.md"))
    roadmap_child_designs = [path for path in child_designs if frontmatter(path).get("roadmap") == slug]
    child_items = {
        frontmatter(path).get("roadmap_item") or path.name.removesuffix("-design.md") for path in roadmap_child_designs
    }
    if any(item_slug not in child_items for item_slug in roadmap_item_slugs(repo, slug)):
        return Action("load-skill", "cs-feat design/design-review")
    if not roadmap_child_designs:
        return Action("load-skill", "cs-feat design/design-review")
    child_review_statuses = []
    child_design_statuses = []
    for design in roadmap_child_designs:
        child_slug = design.name.removesuffix("-design.md")
        child_review = design.parent / f"{child_slug}-design-review.md"
        child_review_statuses.append(frontmatter(child_review).get("status"))
        child_design_statuses.append(frontmatter(design).get("status"))
    if any(status != "passed" for status in child_review_statuses):
        return Action("load-skill", "cs-feat design/design-review")
    if any(status != "approved" for status in child_design_statuses):
        return Action("user-checkpoint", "all-feature-designs-confirmation")
    if not goal_state.exists():
        return Action("load-reference", "cs-epic/references/goal/protocol.md")

    state = top_level_yaml(goal_state)
    if state.get("status") in {"complete", "completed"}:
        return Action("complete", "CS_ROADMAP_GOAL_COMPLETE")
    if state.get("status") == "handoff":
        return Action("user-checkpoint", "CS_ROADMAP_GOAL_HANDOFF")
    if state.get("driver_kind") in {"host-agent", "paseo", "native"} and state.get("driver_id"):
        return Action("report-visible-driver", state["driver_id"])
    if state.get("status") == "ready-to-dispatch":
        return Action("dispatch-goal-driver", "epic")
    return Action("blocked", "unknown-epic-state")


def issue_dir(repo: Path, slug: str) -> Path:
    return repo / ".codestable/issues" / f"2026-07-02-{slug}"


def write_issue_doc(repo: Path, slug: str, name: str, status: str = "draft") -> None:
    write(
        issue_dir(repo, slug) / f"{slug}-{name}.md",
        f"---\ndoc_type: issue-{name}\nissue: 2026-07-02-{slug}\nstatus: {status}\n---\n# {name}\n",
    )


def issue_next(repo: Path, slug: str) -> Action:
    directory = issue_dir(repo, slug)
    report = directory / f"{slug}-report.md"
    if not report.exists():
        return Action("load-reference", "cs-issue/references/report/protocol.md")
    if frontmatter(report).get("status") != "confirmed":
        return Action("user-checkpoint", "issue-report-confirmation")
    analysis = directory / f"{slug}-analysis.md"
    if not analysis.exists():
        return Action("load-reference", "cs-issue/references/analyze/protocol.md")
    if frontmatter(analysis).get("status") != "confirmed":
        return Action("user-checkpoint", "issue-fix-plan-confirmation")
    if not (directory / f"{slug}-fix-note.md").exists():
        return Action("load-reference", "cs-issue/references/fix/protocol.md")
    review_status = frontmatter(directory / f"{slug}-review.md").get("status")
    if not review_status:
        return Action("load-skill", "cs-code-review")
    if review_status in {"changes-requested", "blocked"}:
        return Action("load-reference", "cs-issue/references/fix/protocol.md#review-fix")
    if review_status == "passed":
        approval = directory / "approval-report.md"
        approval_status = frontmatter(approval).get("status")
        if not approval_status:
            return Action("load-reference", "cs-issue/references/fix/protocol.md#completion-checkpoint")
        if approval_status == "pending":
            return Action("user-checkpoint", "issue-fix-completion")
        if approval_status == "approved":
            return Action("complete", "issue-reviewed")
        return Action("blocked", "issue-fix-completion-rejected")
    return Action("blocked", "unknown-issue-state")


def refactor_dir(repo: Path, slug: str) -> Path:
    return repo / ".codestable/refactors" / f"2026-07-02-{slug}"


def write_refactor_doc(repo: Path, slug: str, name: str, status: str = "draft") -> None:
    write(
        refactor_dir(repo, slug) / f"{slug}-{name}.md",
        f"---\ndoc_type: refactor-{name}\nrefactor: 2026-07-02-{slug}\nstatus: {status}\n---\n# {name}\n",
    )


def refactor_next(repo: Path, slug: str, mode: str | None = None, small_scope: bool = False) -> Action:
    if mode == "fastforward" and small_scope:
        return Action("load-reference", "cs-refactor/references/fastforward/protocol.md")
    directory = refactor_dir(repo, slug)
    scan = directory / f"{slug}-scan.md"
    design = directory / f"{slug}-refactor-design.md"
    apply_notes = directory / f"{slug}-apply-notes.md"
    if not scan.exists():
        return Action("load-reference", "cs-refactor/references/standard/protocol.md#scan")
    if "selected: true" not in scan.read_text(encoding="utf-8"):
        return Action("user-checkpoint", "refactor-scan-selection")
    if not design.exists():
        return Action("load-reference", "cs-refactor/references/standard/protocol.md#design")
    if frontmatter(design).get("status") != "approved":
        return Action("user-checkpoint", "refactor-design-confirmation")
    if not apply_notes.exists():
        return Action("load-reference", "cs-refactor/references/standard/protocol.md#apply")
    apply_state = apply_notes.read_text(encoding="utf-8")
    if "step_state: applied-awaiting-human" in apply_state:
        return Action("user-checkpoint", "refactor-human-validation")
    if "step_state: verified" not in apply_state:
        return Action("load-reference", "cs-refactor/references/standard/protocol.md#apply")
    review_status = frontmatter(directory / f"{slug}-review.md").get("status")
    if review_status != "passed":
        return Action("load-skill", "cs-code-review")
    return Action("complete", "refactor-reviewed")


def docs_next(repo: Path, request: str, mode: str | None = None) -> Action:
    if "sync" in request or "neat" in request or "memory" in request:
        return Action("load-skill", "cs-docs-neat")
    if mode == "api" or "api" in request:
        return Action("load-reference", "cs-docs/references/api/protocol.md")
    guide = repo / "docs/dev/widget-guide.md"
    if guide.exists() and frontmatter(guide).get("status") == "current" and "small edit" in request:
        return Action("focused-edit", "docs/dev/widget-guide.md")
    return Action("load-reference", "cs-docs/references/tutorial/protocol.md")


def code_review_next(repo: Path, feature_slug: str | None = None, range_arg: str | None = None) -> Action:
    if range_arg:
        diff = subprocess.run(["git", "diff", range_arg], cwd=repo, text=True, stdout=subprocess.PIPE, check=True).stdout
        return Action("ad-hoc-range-review", range_arg) if diff else Action("blocked", "empty-range")
    if feature_slug:
        directory = feature_dir(repo, feature_slug)
        review = directory / f"{feature_slug}-review.md"
        if frontmatter(review).get("status") == "passed":
            diff = git(repo, "diff", "--stat").stdout
            if not diff:
                design = directory / f"{feature_slug}-design.md"
                lane = frontmatter(design).get("execution_lane", "standard")
                downstream = "cs-feat QA" if lane == "goal" else "cs-feat acceptance-inline"
                return Action("downstream", downstream)
        diff = git(repo, "diff", "--stat").stdout
        if diff:
            return Action("run-review", f".codestable/features/2026-07-02-{feature_slug}")
    return Action("blocked", "no-review-scope")


def goal_driver_decision(
    *,
    host_agent: bool = False,
    visible: bool = False,
    nested_reviewer: bool = False,
) -> Action:
    if host_agent and visible and nested_reviewer:
        return Action("dispatch", "host-agent")
    return Action("fallback", "fenced-/goal")


def test_scenario_matrix_covers_every_refactored_skill() -> None:
    covered = set().union(*SCENARIO_COVERAGE.values())
    assert AFFECTED_SKILLS - covered == set()


def test_router_classifies_intake_before_selecting_a_target() -> None:
    assert_doc_contains(
        "cs",
        "SKILL.md",
        "入口模式先于路由目标",
        "data Ambiguity = MissingActionIntent | RouteChoice [SkillName]",
        "data IntakeMode = Execute | Advise | Explain | Ambiguous Ambiguity",
        "Completed Recommendation",
        "Completed Overview",
        "NeedsHuman ActionIntentMissing",
        "HumanCheckpoint ClarifyRoute",
        "preflight 只记录缺失状态",
    )


def test_router_execute_mode_continues_in_the_current_run() -> None:
    assert_doc_contains(
        "cs",
        "SKILL.md",
        "RoutedTo target",
        "当前 run 继续",
        "原始诉求原样传递",
        "一个请求同一时刻只转交一个主入口",
    )


def test_router_keeps_route_brief_small_and_mode_specific() -> None:
    text = skill_text("cs")
    _, separator, body = text.partition("\n---\n")
    assert separator
    assert "Dispatch: continuing-current-run | recommendation-only" in text
    assert "route brief 只用于 Execute / Advise" in text
    assert "L0-L4" not in body
    assert "Route Level Quick Reference" not in body


def test_router_priority_and_recovery_boundaries_are_explicit() -> None:
    assert_doc_contains(
        "cs",
        "SKILL.md",
        "专用 workflow 优先于 `cs-goal`",
        "已知优化目标",
        "主动扫描未知问题",
        "capability / requirement",
        "canonical 决策",
        "复用经验",
        "features/issues/roadmap/goals/refactors/audits/brainstorms/feedback",
        "`cs-onboard` 是串行前置 gate",
        "目标 skill 无法加载",
    )


def test_shared_dispatch_conventions_distinguish_exit_confirmation() -> None:
    text = skill_text("cs-onboard", "references/execution-conventions.md")
    for phrase in (
        "## Skill 间同轮转交",
        "已确认出口",
        "待确认出口",
        "不要求重新调用命令",
        "转交本身不授权",
        "data PendingHandoff = PendingHandoff Skill Context",
        "| AwaitOwner PendingHandoff",
        "resumeHandoff :: PendingHandoff -> OwnerDecision -> TargetAvailability -> HandoffOutcome",
        "ApproveExit TargetAvailable   = LoadAndContinue target ctx",
        "DeclineExit _                 = Stay ctx",
        "缺输入或能力用 `NeedsHuman`",
        "只需等待的外部工作用 `Awaiting`",
        "才用 `HumanCheckpoint`",
    ):
        assert phrase in text
    assert "OneCheckpoint Skill" not in text
    decline = "resumeHandoff (PendingHandoff _ ctx)      DeclineExit _"
    unavailable = "resumeHandoff (PendingHandoff target _)   ApproveExit TargetUnavailable"
    approved = "resumeHandoff (PendingHandoff target ctx) ApproveExit TargetAvailable"
    assert text.index(decline) < text.index(unavailable) < text.index(approved)


def test_brainstorm_secondary_routes_keep_one_confirmation_gate() -> None:
    text = skill_text("cs-brainstorm")
    for phrase in (
        "data Readiness = Fuzzy | Clear | Ready",
        'route (Feature Clear) = Handoff PendingExit "cs-feat"',
        'route (Feature Ready) = Handoff ConfirmedExit "cs-feat"',
        'route (Epic Clear)    = Handoff PendingExit "cs-epic"',
        'route (Epic Ready)    = Handoff ConfirmedExit "cs-epic"',
        "`Ready` 只来自 owner 明确表示现在进入下一阶段",
        "用户确认后在当前 run 加载 `cs-feat`",
        "直接在当前 run 加载 `cs-epic`",
    ):
        assert phrase in text
    assert re.search(r"(?m)^confirmed\b", text) is None
    assert "route Clear" not in text
    assert "停下来等用户触发 design" not in text
    assert "准备好了就触发 `cs-epic`" not in text


def test_review_outcomes_do_not_treat_waiting_or_missing_input_as_approval() -> None:
    text = skill_text("cs-code-review")
    protocol = skill_text("cs-code-review", "references/independent-review/protocol.md")
    for phrase in (
        "| Awaiting ReviewWait",
        "| NeedsHuman ReviewBlocker",
        "not s.specFinalized                                -> NeedsHuman SpecNotFinalized",
        "not s.diffAttributed                               -> NeedsHuman DiffNotAttributable",
        "anyStartedLanePending s                            -> Awaiting LaneStillPending",
        "HumanCheckpoint SelfReviewDowngrade",
    ):
        assert phrase in text
    for forbidden in (
        "HumanCheckpoint SpecNotFinalized",
        "HumanCheckpoint DiffNotAttributable",
        "HumanCheckpoint LaneStillPending",
    ):
        assert forbidden not in text
    guard_order = (
        "not s.specFinalized",
        "not s.diffAttributed",
        "anyLaneFailed s",
        "anyStartedLanePending s",
        "focusedClosureEligible s && hasBlocking s",
        "focusedClosureEligible s                           -> FocusedClosure Passed",
        "laneAMissing s",
        "hasBlocking s                                      -> ReviewWritten ChangesRequested",
    )
    assert [text.index(guard) for guard in guard_order] == sorted(
        text.index(guard) for guard in guard_order
    )
    for phrase in (
        "mergeGate (Launch _ _) _ = MergeAwaiting LaneStillPending",
        "mergeGate Await _ = MergeAwaiting LaneStillPending",
        "mergeGate (NeedOwnerApproval reason) _ = MergeNeedsOwnerApproval reason",
        "pending laneB                       = MergeAwaiting LaneStillPending",
    ):
        assert phrase in protocol
    assert "Blocked LaneStillPending" not in protocol


def test_issue_fast_path_confirmation_is_persisted_and_resumable() -> None:
    skill = skill_text("cs-issue")
    report = skill_text("cs-issue", "references/report/protocol.md")

    for phrase in (
        "data IssuePath = PathUndecided | StandardPath | FastPathPending | FastPathApproved | FastPathRejected",
        "issuePath    : IssuePath",
        "fastPathApproval approval == Pending  = FastPathPending",
        "issuePathField report == Just StandardPath = StandardPath",
        "isNothing (issuePathField report) && reportStatus report == ArtifactConfirmed = StandardPath",
        "s.reportStatus /= ArtifactConfirmed                -> RoutedTo (IssueStage Report)",
        "s.issuePath == FastPathApproved                     -> RoutedTo (IssueStage FastPath)",
        "s.analysisStatus /= ArtifactConfirmed",
        's.issuePath == PathUndecided                        -> NeedsHuman "confirmed report lacks path decision"',
        "approval-report.md       # 仅需 owner 决策时",
        "s.fixCompletionApproval == ApprovalMissing",
        "s.fixCompletionApproval == ApprovalApproved",
    ):
        assert phrase in skill
    for phrase in (
        "advance Standard _ (Just ApproveCheckpoint) = PersistAndRoute StandardPath AnalyzeNext",
        "advance FastPath _ (Just ApproveCheckpoint) = PersistAndRoute FastPathApproved FixNext",
        "advance FastPath _ (Just RejectCheckpoint)  = PersistAndRoute FastPathRejected AnalyzeNext",
        "PersistDraftAndCheckpoint ConfirmReport",
        "PersistDraftAndCheckpoint ConfirmFixPlan",
        "fast-track 不得绕过五问",
        "记录 fast-path 已批准再进入 fix",
        "issue_path: undecided # undecided | standard | fast-track",
    ):
        assert phrase in report
    assert "ConfirmFastPath" not in skill
    guard_order = (
        "s.hasFixNote && s.reviewStatus == Missing",
        "not s.hasFixNote && s.reviewStatus /= Missing",
        "s.reportStatus /= ArtifactConfirmed",
        "s.codeStatus == Changed && not s.hasFixNote",
        "s.issuePath == PathUndecided",
        "s.issuePath == FastPathPending",
        "s.issuePath == FastPathApproved && not",
        "s.issuePath == FastPathApproved                     -> RoutedTo (IssueStage FastPath)",
        "s.issuePath in [StandardPath, FastPathRejected] && s.analysisStatus /= ArtifactConfirmed",
    )
    assert [skill.index(guard) for guard in guard_order] == sorted(
        skill.index(guard) for guard in guard_order
    )


def test_req_review_checkpoint_precedes_persistence() -> None:
    text = skill_text("cs-req")
    checkpoint = "HumanCheckpoint (ReviewDraft (buildReqDraft s r))"
    persist = "Review draft ApproveDraft)     -> Drafted (persistReqAndRefreshIndex s draft)"

    assert "data ReqInput" in text
    assert "| Review ReqDraft DraftDecision" in text
    assert checkpoint in text
    assert persist in text
    assert text.index(checkpoint) < text.index(persist)
    assert "writeReqThenReview" not in text
    assert 's.capabilityLive == Unknown -> NeedsHuman "capability evidence missing"' in text
    assert "HumanCheckpoint CapabilityUnproven" not in text


def test_docs_checkpoint_domain_matches_stage_protocols() -> None:
    skill = skill_text("cs-docs")
    tutorial = skill_text("cs-docs", "references/tutorial/protocol.md")
    api = skill_text("cs-docs", "references/api/protocol.md")
    reasons = {
        "ReviewDraft",
        "ReviewManifest",
        "ConfirmOverwrite",
        "ConfirmContractWording",
        "ReviewEntry",
        "ReviewSamples",
        "ReviewAllDrafts",
    }

    assert all(reason in skill for reason in reasons)
    assert 'targetAmbiguous state       = NeedsHuman "which reader?"' in tutorial
    assert "Just reason <- approvalGate state" in tutorial
    assert "Just reason <- approvalGate s" in api
    assert "ConfirmNewDoc" not in skill
    assert "ConfirmReaderAndScope" not in skill
    assert tutorial.index("targetAmbiguous state") < tutorial.index("Just reason <- approvalGate state")


def test_goal_owner_stop_has_resume_and_terminal_branches() -> None:
    skill = skill_text("cs-goal")
    reference = skill_text("cs-goal", "reference.md")
    for phrase in (
        "data OwnerStopState",
        "| PendingStop CheckpointReason",
        "| ResolvedStop GoalOwnerDecision",
        "data GoalOwnerDecision = ResumeWith GoalDelta | KeepBlocked",
        "| Blocked GoalSummary",
        "ResolvedStop (ResumeWith delta)",
        "ResolvedStop KeepBlocked",
        's.status == Blocked                           -> NeedsHuman "blocked goal lacks owner-stop state"',
    ):
        assert phrase in skill
    for phrase in (
        "schema_version: 2",
        "status: none # none | pending | resolved",
        "status: pending",
        "选择不继续时",
        "读取 schema v1 时",
    ):
        assert phrase in reference
    terminal_order = (
        "s.status == Complete && s.acceptancePassed",
        "s.ownerStop is PendingStop reason",
        "ownerStopTriggered(s)",
        "s.status == Active && not s.acceptancePassed",
    )
    assert [skill.index(guard) for guard in terminal_order] == sorted(
        skill.index(guard) for guard in terminal_order
    )


def test_audit_selected_finding_dispatches_in_the_current_run() -> None:
    assert_doc_contains(
        "cs-audit",
        "SKILL.md",
        "用户选中 finding 已构成确认",
        "当前 run 加载 `cs-issue` 或 `cs-refactor`",
        "原始 finding",
        "selectedFinding",
        "RoutedTo SkillName",
    )


def test_feature_long_range_scenario_simulates_human_design_confirmation(tmp_path: Path) -> None:
    assert_doc_contains(
        "cs-feat",
        "SKILL.md",
        "design gate 停下来等用户确认",
        "Goal lane",
        "可见 Task agent goal driver 长程执行",
    )
    assert_doc_contains(
        "cs-feat",
        "references/goal/protocol.md",
        "Goal 模式接管",
        "CS_FEATURE_GOAL_COMPLETE",
        "CS_FEATURE_GOAL_HANDOFF",
        "transition Complete event",
        "transition (Handoff reason) event",
    )
    repo = init_isolated_repo(tmp_path)
    slug = "export-csv"

    assert feature_next(repo, slug) == Action("load-reference", "cs-feat/references/design/protocol.md")
    write_feature_design(repo, slug, status="draft", execution_lane="goal")
    assert feature_next(repo, slug) == Action("load-reference", "cs-feat/references/design-review/protocol.md")
    write_feature_design_review(repo, slug, status="passed")
    assert feature_next(repo, slug) == Action("user-checkpoint", "feature-design-confirmation")

    # Simulated human gate: user approved the reviewed design, so the workflow can continue.
    replace_status(feature_dir(repo, slug) / f"{slug}-design.md", "approved")
    assert feature_next(repo, slug) == Action("load-reference", "cs-feat/references/goal/protocol.md")

    write_feature_goal_state(repo, slug, "implementation", "ready-to-dispatch")
    assert feature_next(repo, slug) == Action("dispatch-goal-driver", "feature")
    write_feature_goal_state(repo, slug, "implementation", "running", driver="host-agent")
    assert feature_next(repo, slug) == Action("report-visible-driver", "host-agent-123")


def test_feature_quick_lane_is_default_for_clear_local_work_and_can_reclassify() -> None:
    assert_doc_contains(
        "cs-feat",
        "SKILL.md",
        "classifyExecutionLane",
        "Quick",
        "Standard",
        "Goal",
        "复用既有公开契约",
        "目标验证入口",
        "流程太重",
        "重新分类",
        "data QuickRunState",
        "CS_FEATURE_QUICK_COMPLETE",
        "CS_FEATURE_STANDARD_COMPLETE",
        "先把 `execution_lane: quick`",
        "已有 `goal-state.yaml` 时不得原地降级",
    )
    assert_doc_contains(
        "cs-feat",
        "references/fastforward/protocol.md",
        "默认按任务事实自动选择",
        "首次独立代码审查",
        "不生成独立 QA / acceptance 报告",
    )


def test_feature_spec_routes_roadmap_owned_children_to_epic() -> None:
    assert_doc_contains(
        "cs-feat",
        "SKILL.md",
        "roadmapOwner",
        "hasRoadmapOwner(s)",
        "parent `items.yaml`",
        "精确目录 slug",
        "features[].feature_dir",
        "RoutedTo <return-to-cs-epic>",
    )


def test_feature_review_restarts_only_for_material_changes() -> None:
    assert_doc_contains(
        "cs-feat",
        "references/design-review/protocol.md",
        "实质变化",
        "focused closure",
        "文字、编号、链接、格式",
    )
    assert_doc_contains(
        "cs-code-review",
        "SKILL.md",
        "test/docs/type/metadata/nit-only",
        "focused closure",
        "行为、公开契约、安全、数据、并发或架构",
        "完整独立复审",
    )


def test_standard_implementation_proceeds_directly_to_code_review() -> None:
    implementation = skill_text("cs-feat", "references/implementation/protocol.md")

    assert "afterAllSteps Normal               = RunCodeReview" in implementation
    assert "modeForFix OwnerRequestedChanges   = ReviewFixMode" in implementation
    assert "modeForFix QAFix                   = QAFixMode" in implementation
    assert "afterAllSteps ReviewFixMode        = RunCodeReview" in implementation
    assert "afterAllSteps QAFixMode            = RunCodeReviewThenQA" in implementation
    assert "afterAllSteps GoalMode             = RunGatesThenCodeReview" in implementation
    assert "ConfirmImplementation" not in implementation


def test_acceptance_separates_evidence_causes_and_reaches_repeated_gap_handoff() -> None:
    acceptance = skill_text("cs-feat", "references/acceptance/protocol.md")
    ordered_guards = (
        "coreEvidenceMissingDueToInput s",
        "coreEvidenceMissingDueToEnvironment s",
        "not (coreEvidencePassed s)",
        "not (finalAuditPassed s) && sameFinalAuditGapCount s >= 3",
        "not (allChecksPassed s)",
        "| not (finalAuditPassed s)                    = RepairGap FinalAudit",
    )

    positions = [acceptance.index(guard) for guard in ordered_guards]
    assert positions == sorted(positions)
    assert "NeedsHuman CoreEvidenceInput" in acceptance
    assert "NeedsHuman CoreEvidenceEnvironmentUnavailable" in acceptance
    assert "RouteImplementation QAFix" in acceptance
    assert "Handoff RepeatedFinalAuditGap" in acceptance


def test_review_focused_closure_never_masks_failed_or_pending_lanes() -> None:
    review = skill_text("cs-code-review")
    ordered_guards = (
        "anyLaneFailed s",
        "anyStartedLanePending s",
        "focusedClosureEligible s && hasBlocking s",
        "focusedClosureEligible s                           -> FocusedClosure Passed",
    )

    positions = [review.index(guard) for guard in ordered_guards]
    assert positions == sorted(positions)
    assert "anyLaneFailed s                                    -> ReviewWritten Blocked" in review
    assert "s.priorIndependentReview" in review
    assert "s.changeClass == ClosureOnly" in review


def test_refactor_human_validation_happens_after_the_step_is_applied() -> None:
    protocol = skill_text("cs-refactor", "references/standard/protocol.md")
    pending = "PendingApply` 必须先进入 `Run Apply`"
    applied = "afterStep item HumanVerification StepApplied       = PersistAndCheckpoint (HumanValidation item)"
    verified = "afterStep _ HumanVerification VerificationPassed  = Continue"

    assert pending in protocol
    assert applied in protocol
    assert verified in protocol
    assert protocol.index(applied) < protocol.index(verified)


@pytest.mark.parametrize(
    ("review_status", "expected"),
    [
        ("changes-requested", Action("load-reference", "cs-feat/references/design/protocol.md")),
        ("blocked", Action("blocked", "feature-design-review-block")),
    ],
)
def test_feature_design_review_failure_preserves_failure_kind(
    tmp_path: Path, review_status: str, expected: Action
) -> None:
    repo = init_isolated_repo(tmp_path)
    slug = "export-csv"
    write_feature_design(repo, slug, status="draft")
    write_feature_design_review(repo, slug, status=review_status)

    assert feature_next(repo, slug) == expected


def test_epic_legacy_blocked_review_fails_closed_in_compact_model(tmp_path: Path) -> None:
    repo = init_isolated_repo(tmp_path)
    slug = "billing-system"
    write_roadmap(repo, slug, status="draft")
    write_roadmap_review(repo, slug, status="blocked")

    assert epic_next(repo, slug) == Action("blocked", "roadmap-review-block")


@pytest.mark.parametrize(
    ("stage", "status", "expected"),
    [
        ("implementation", "running", Action("load-reference", "cs-feat/references/implementation/protocol.md")),
        ("review", "ready", Action("load-skill", "cs-code-review")),
        ("review", "fixing", Action("load-reference", "cs-feat/references/implementation/protocol.md#review-fix")),
        ("qa", "ready", Action("load-reference", "cs-feat/references/qa/protocol.md")),
        ("qa", "fixing", Action("load-reference", "cs-feat/references/implementation/protocol.md#qa-fix")),
        ("acceptance", "ready", Action("load-reference", "cs-feat/references/acceptance/protocol.md")),
        ("complete", "passed", Action("complete", "CS_FEATURE_GOAL_COMPLETE")),
        ("handoff", "blocked", Action("user-checkpoint", "CS_FEATURE_GOAL_HANDOFF")),
    ],
)
def test_feature_goal_state_machine_routes_each_long_range_stage(tmp_path: Path, stage: str, status: str, expected: Action) -> None:
    repo = init_isolated_repo(tmp_path)
    slug = "export-csv"
    write_feature_design(repo, slug, status="approved")
    write_feature_design_review(repo, slug, status="passed")
    write_feature_goal_state(repo, slug, stage, status)

    assert feature_next(repo, slug) == expected


def test_epic_long_range_scenario_simulates_both_human_confirmations(tmp_path: Path) -> None:
    assert_doc_contains(
        "cs-epic",
        "SKILL.md",
        "roadmap review passed 但用户未确认",
        "用户统一确认所有 design",
        "可见 Task agent goal driver",
    )
    assert_doc_contains("cs-epic", "references/goal/protocol.md", "两次确认门禁", "CS_ROADMAP_GOAL_COMPLETE")
    repo = init_isolated_repo(tmp_path)
    slug = "billing-system"

    assert epic_next(repo, slug) == Action("load-reference", "cs-epic/references/planning/protocol.md")
    write_roadmap(repo, slug, status="draft")
    assert epic_next(repo, slug) == Action("load-reference", "cs-epic/references/review/protocol.md")
    write_roadmap_review(repo, slug, status="passed")
    assert epic_next(repo, slug) == Action("user-checkpoint", "epic-roadmap-confirmation")

    # Simulated human gate 1: roadmap is approved by the user.
    replace_status(roadmap_dir(repo, slug) / f"{slug}-roadmap.md", "active")
    assert epic_next(repo, slug) == Action("load-skill", "cs-feat design/design-review")

    for child in ["api-seed", "ui-seed"]:
        write_feature_design(repo, child, status="draft", roadmap=slug)
        write_feature_design_review(repo, child, status="passed")
    assert epic_next(repo, slug) == Action("user-checkpoint", "all-feature-designs-confirmation")

    # Simulated human gate 2: all child designs are approved as a batch.
    for child in ["api-seed", "ui-seed"]:
        replace_status(feature_dir(repo, child) / f"{child}-design.md", "approved")
    assert epic_next(repo, slug) == Action("load-reference", "cs-epic/references/goal/protocol.md")

    write_epic_goal_state(repo, slug, "ready-to-dispatch")
    assert epic_next(repo, slug) == Action("dispatch-goal-driver", "epic")
    write_epic_goal_state(repo, slug, "running", driver="host-agent")
    assert epic_next(repo, slug) == Action("report-visible-driver", "host-agent-roadmap-123")


def test_epic_child_design_batch_continues_after_one_child_review_passed(tmp_path: Path) -> None:
    assert_doc_contains(
        "cs-epic",
        "SKILL.md",
        "Child design batch loop",
        "codestable-workflow-next.py epic",
        "完成某一个 child 的 design + design-review `passed` 只是内部进度",
        "不得 final answer",
        "本轮必须继续调用 `cs-feat`",
        "取下一个 planned / in-progress 且缺 design、checklist",
    )
    # batch loop 纪律唯一权威在 SKILL.md；goal protocol 只保留 workflow-next hook 引用
    assert_doc_contains(
        "cs-epic",
        "references/goal/protocol.md",
        "codestable-workflow-next.py epic",
    )

    repo = init_isolated_repo(tmp_path)
    slug = "billing-system"
    write_roadmap(repo, slug, status="active")
    write_roadmap_review(repo, slug, status="passed")

    write_feature_design(repo, "api-seed", status="draft", roadmap=slug)
    write_feature_design_review(repo, "api-seed", status="passed")

    assert epic_next(repo, slug) == Action("load-skill", "cs-feat design/design-review")


def test_epic_goal_qa_blocked_hands_off_without_entering_review_fix() -> None:
    feature_loop = skill_text("cs-epic", "references/goal/support/protocol-feature-loop.md")

    assert "advance QA (Failed _)                                   = Remediate Implementation Review" in feature_loop
    assert "advance stage (Awaiting ref)                            = WaitFor stage ref" in feature_loop
    assert "advance stage (NeedsHuman reason)                       = RequestHuman stage reason" in feature_loop
    assert "advance stage (Blocked reason)                          = HandoffStage stage reason" in feature_loop
    assert "advance QA _" not in feature_loop


def test_epic_goal_audit_hands_off_unapproved_h_only_evidence_immediately() -> None:
    audit = skill_text("cs-epic", "references/goal/support/protocol-audit.md")
    goal = skill_text("cs-epic", "references/goal/support/protocol.md")
    gates = skill_text("cs-epic", "references/goal/support/protocol-gates.md")

    assert "not (noUnapprovedHOnlyCoreCheck a)   = AuditHandoff UnapprovedHOnlyCoreCheck" in audit
    assert "sameAuditFailureCount a >= 3         = AuditHandoff RepeatedFailure" in audit
    assert "AuditRepeatedFailure" not in audit
    assert "unapprovedHOnlyCoreCheck s       = Just UnapprovedHOnlyCoreCheck" in goal
    assert "recover QA             = FixQAThenReview" in gates
    assert "| FixQA |" not in gates


def test_roadmap_item_enters_in_progress_when_design_starts() -> None:
    planning = skill_text("cs-epic", "references/planning/reference.md")
    shared = skill_text("cs-onboard", "references/shared-conventions.md")

    assert "roadmap item 生命周期以项目 `.codestable/reference/shared-conventions.md`" in planning
    assert "不复制 transition" in planning
    assert "data ItemEvent" not in planning
    assert "data ItemEvent = StartDesign | AcceptFeature | OwnerDrops Reason" in shared
    assert "transition Planned StartDesign" in shared
    assert "StartFeature" not in shared


def test_workflow_runtime_details_are_centralized_in_preflight() -> None:
    assert_doc_contains(
        "cs-onboard",
        "SKILL.md",
        "--mode refresh-runtime",
        "可重复执行",
        "不重新审计 / 迁移文档",
        "selectOnboardPath RefreshRuntime Installed _  = Refresh",
        ".codestable/runtime-manifest.json",
        "codestable-runtime-sync.py",
        "不移动用户文件",
    )
    assert_doc_contains(
        "cs-onboard",
        "references/execution-conventions.md",
        "Runtime 资产恢复",
        "runtime capability",
        ".codestable/runtime-manifest.json",
        "recoverRuntime RuntimeIncomplete  = SyncRuntime",
        "recoverRuntime ManagedPathsDirty  = Stop ManagedRuntimeDirty",
        "--check --json",
        "去掉 `--check`",
        "`workflow-next`",
        "managed-paths-dirty",
        "不自动覆盖",
        ".codestable/reference/agent-conventions.md",
    )
    assert_doc_contains(
        "cs-feat",
        "SKILL.md",
        "codestable-workflow-next.py feature",
    )
    assert_doc_contains(
        "cs-epic",
        "SKILL.md",
        "codestable-workflow-next.py epic",
        "若 preflight 刚完成 runtime 同步，从仓库事实恢复 batch loop",
    )
    assert_doc_contains(
        "cs-epic",
        "references/goal/protocol.md",
        "codestable-workflow-next.py epic",
    )


def test_goal_driver_selection_requires_visibility_and_nested_reviewer() -> None:
    assert_doc_contains(
        "cs-onboard",
        "references/agent-conventions.md",
        "visibleHostDriver e && canSpawnReviewer e",
        'PrintGoal "/goal"',
    )

    assert goal_driver_decision(host_agent=True, visible=True, nested_reviewer=True) == Action("dispatch", "host-agent")
    assert goal_driver_decision(host_agent=True, visible=True, nested_reviewer=False) == Action("fallback", "fenced-/goal")
    assert goal_driver_decision(host_agent=True, visible=False, nested_reviewer=True) == Action("fallback", "fenced-/goal")
    assert goal_driver_decision() == Action("fallback", "fenced-/goal")


def test_task_agent_lifecycle_closes_consumed_agents_and_cleans_only_on_capacity_failure() -> None:
    assert_doc_contains(
        "cs-onboard",
        "references/agent-conventions.md",
        "## Task Agent 生命周期",
        "data CreateRecovery = RetryCreate | CreateBlocked Reason",
        "terminal s && resultConsumed s && not (permissionPending s)",
        "recoverCreate CapacityExhausted",
        "closeOldest mayClose >> RetryCreate",
        "recoverCreate reason            = CreateBlocked reason",
    )
    assert_doc_contains(
        "cs-goal",
        "SKILL.md",
        "按 Task agent 生命周期关闭该验收 agent",
        "先按 Task agent 生命周期处理容量失败重试",
    )
    assert_doc_contains(
        "cs-goal",
        "reference.md",
        "Task agent id / run id、关闭结果或关闭失败 warning",
        "Task agent 结果消费后",
    )
    assert_doc_contains(
        "cs-code-review",
        "references/independent-review/protocol.md",
        "Task agent 生命周期关闭该 reviewer",
        "只在失败后按最老已完成 agent 清理并重试一次",
    )
    assert_doc_contains("cs-feat", "references/qa/protocol.md", "Task agent 生命周期关闭该 runner")
    assert_doc_contains("cs-feat", "references/acceptance/protocol.md", "auditor 输出被消费后按 Task agent 生命周期关闭")
    assert_doc_contains("cs-epic", "references/goal/support/protocol-gates.md", "结果消费后按 Task agent 生命周期关闭")


def test_issue_scenario_progresses_through_main_entry_references(tmp_path: Path) -> None:
    assert_doc_contains("cs-issue", "SKILL.md", "report、analyze、fix、review", "仓库事实")
    repo = init_isolated_repo(tmp_path)
    slug = "login-error"

    assert issue_next(repo, slug) == Action("load-reference", "cs-issue/references/report/protocol.md")
    write_issue_doc(repo, slug, "report")
    assert issue_next(repo, slug) == Action("user-checkpoint", "issue-report-confirmation")
    replace_status(issue_dir(repo, slug) / f"{slug}-report.md", "confirmed")
    assert issue_next(repo, slug) == Action("load-reference", "cs-issue/references/analyze/protocol.md")
    write_issue_doc(repo, slug, "analysis")
    assert issue_next(repo, slug) == Action("user-checkpoint", "issue-fix-plan-confirmation")
    replace_status(issue_dir(repo, slug) / f"{slug}-analysis.md", "confirmed")
    assert issue_next(repo, slug) == Action("load-reference", "cs-issue/references/fix/protocol.md")
    write_issue_doc(repo, slug, "fix-note")
    assert issue_next(repo, slug) == Action("load-skill", "cs-code-review")
    write_issue_doc(repo, slug, "review", status="changes-requested")
    assert issue_next(repo, slug) == Action("load-reference", "cs-issue/references/fix/protocol.md#review-fix")
    replace_status(issue_dir(repo, slug) / f"{slug}-review.md", "passed")
    assert issue_next(repo, slug) == Action(
        "load-reference", "cs-issue/references/fix/protocol.md#completion-checkpoint"
    )
    write(
        issue_dir(repo, slug) / "approval-report.md",
        "---\ndoc_type: approval-report\nstatus: pending\n---\n# Approval\n",
    )
    assert issue_next(repo, slug) == Action("user-checkpoint", "issue-fix-completion")
    replace_status(issue_dir(repo, slug) / "approval-report.md", "approved")
    assert issue_next(repo, slug) == Action("complete", "issue-reviewed")


def test_refactor_scenario_respects_scan_design_and_human_validation_gates(tmp_path: Path) -> None:
    assert_doc_contains("cs-refactor", "SKILL.md", "scan → 用户勾选 → design → 用户确认 → apply → cs-code-review")
    assert_doc_contains("cs-refactor", "references/standard/protocol.md", "用户勾选", "HUMAN 验证")
    repo = init_isolated_repo(tmp_path)
    slug = "split-helper"

    assert refactor_next(repo, slug, mode="fastforward", small_scope=True) == Action(
        "load-reference", "cs-refactor/references/fastforward/protocol.md"
    )
    assert refactor_next(repo, slug) == Action("load-reference", "cs-refactor/references/standard/protocol.md#scan")
    write_refactor_doc(repo, slug, "scan")
    assert refactor_next(repo, slug) == Action("user-checkpoint", "refactor-scan-selection")
    write(refactor_dir(repo, slug) / f"{slug}-scan.md", "selected: true\n")
    assert refactor_next(repo, slug) == Action("load-reference", "cs-refactor/references/standard/protocol.md#design")
    write_refactor_doc(repo, slug, "refactor-design", status="draft")
    write(refactor_dir(repo, slug) / f"{slug}-checklist.yaml", "steps:\n  - id: visual\n    verification: HUMAN\n")
    assert refactor_next(repo, slug) == Action("user-checkpoint", "refactor-design-confirmation")
    replace_status(refactor_dir(repo, slug) / f"{slug}-refactor-design.md", "approved")
    assert refactor_next(repo, slug) == Action("load-reference", "cs-refactor/references/standard/protocol.md#apply")
    write_refactor_doc(repo, slug, "apply-notes")
    with (refactor_dir(repo, slug) / f"{slug}-apply-notes.md").open("a", encoding="utf-8") as handle:
        handle.write("step_state: applied-awaiting-human\n")
    assert refactor_next(repo, slug) == Action("user-checkpoint", "refactor-human-validation")
    apply_notes = refactor_dir(repo, slug) / f"{slug}-apply-notes.md"
    apply_notes.write_text(
        apply_notes.read_text(encoding="utf-8").replace("applied-awaiting-human", "verified"),
        encoding="utf-8",
    )
    assert refactor_next(repo, slug) == Action("load-skill", "cs-code-review")


def test_refactor_low_candidate_scan_does_not_enter_design() -> None:
    protocol = skill_text("cs-refactor", "references/standard/protocol.md")
    spec = protocol.split("```haskell", 1)[1].split("```", 1)[0]
    scan_missing = "not (scanExists s)          = Run Scan"
    low_candidates = "candidateCount s < 3 && fastforwardEligible s"
    selection_gate = "not (selectionConfirmed s)  = Checkpoint ScanSelection"

    assert scan_missing in spec
    assert low_candidates in spec
    assert selection_gate in spec
    assert spec.index(scan_missing) < spec.index(low_candidates) < spec.index(selection_gate)


def test_docs_scenario_selects_docs_entry_or_neat_hygiene(tmp_path: Path) -> None:
    assert_doc_contains("cs-docs", "SKILL.md", "不做全局同步", "转 `cs-docs-neat`")
    assert_doc_contains("cs-docs-neat", "SKILL.md", "不是 `cs-docs`", "Phase 1：机械式枚举")
    repo = init_isolated_repo(tmp_path)

    assert docs_next(repo, "write api docs", mode="api") == Action("load-reference", "cs-docs/references/api/protocol.md")
    assert docs_next(repo, "write a developer guide") == Action(
        "load-reference", "cs-docs/references/tutorial/protocol.md"
    )
    write(
        repo / "docs/dev/widget-guide.md",
        "---\ndoc_type: dev-guide\nstatus: current\n---\n# Widget Guide\n",
    )
    assert docs_next(repo, "small edit to widget guide") == Action("focused-edit", "docs/dev/widget-guide.md")
    assert docs_next(repo, "sync memory and README") == Action("load-skill", "cs-docs-neat")


def test_code_review_scenario_handles_feature_diff_and_ad_hoc_range(tmp_path: Path) -> None:
    assert_doc_contains(
        "cs-code-review",
        "SKILL.md",
        "ad-hoc range 审查允许工作区干净",
        "横切代码审查 gate",
        "references/independent-review/protocol.md",
    )
    repo = init_isolated_repo(tmp_path)
    slug = "export-csv"
    write_feature_design(repo, slug, status="approved")
    write_feature_design_review(repo, slug, status="passed")
    write(feature_dir(repo, slug) / f"{slug}-checklist.yaml", "steps:\n  - id: step-1\n    status: done\nchecks:\n  - id: check-1\n    status: pending\n")
    write(repo / "src/app.py", "def hello():\n    return 'hello export'\n")
    assert code_review_next(repo, feature_slug=slug) == Action("run-review", ".codestable/features/2026-07-02-export-csv")

    git(repo, "add", ".")
    git(repo, "commit", "-m", "feature change")
    assert code_review_next(repo, range_arg="HEAD~1..HEAD") == Action("ad-hoc-range-review", "HEAD~1..HEAD")

    write(
        feature_dir(repo, slug) / f"{slug}-review.md",
        "---\ndoc_type: feature-review\nstatus: passed\nreviewer: subagent\n---\n# Review\n",
    )
    git(repo, "add", ".")
    git(repo, "commit", "-m", "add review")
    assert code_review_next(repo, feature_slug=slug) == Action("downstream", "cs-feat acceptance-inline")


@pytest.mark.parametrize("entry,expected", sorted(COMPATIBILITY_ENTRIES.items()))
def test_compatibility_entry_scenarios_delegate_without_rerun(entry: str, expected: tuple[str, str, str]) -> None:
    main, key, value = expected
    text = skill_text(entry)

    assert f"加载 `{main}`" in text
    assert f"{key}: {value}" in text
    assert "不要要求用户重新调用" in text
    assert "不维护独立流程规则" in text
    assert "../" not in text


def test_solution_depth_prepass_is_authoritative_and_reachable() -> None:
    # 权威源:方案深度 pre-pass 单一定义(防降本默认偏置:最小闭环/fake/正则),
    # 硬约束 = 采用降级必须显式论证 + 转正条件。
    assert_doc_contains(
        "cs-onboard",
        "references/solution-depth-conventions.md",
        "方案深度 pre-pass",
        "场景适配",
        "最小闭环",
        "fake",
        "转正条件",
        "不接受",
    )
    # 有 design 的选型阶段必须触达权威源(现状缺触达路径,指针不可删)。
    assert_doc_contains("cs-feat", "references/design/protocol.md", "solution-depth-conventions", "方案深度")
    assert_doc_contains("cs-epic", "references/planning/protocol.md", "solution-depth-conventions", "方案深度")
    assert_doc_contains("cs-goal", "SKILL.md", "solution-depth-conventions", "方案深度 pre-pass")
    # 快速路径(fastforward / fix)最易"够跑就行",同样必须触达(codex review imp-3)。
    assert_doc_contains("cs-feat", "references/fastforward/protocol.md", "solution-depth-conventions")
    assert_doc_contains("cs-issue", "references/fix/protocol.md", "solution-depth-conventions")
    assert_doc_contains("cs-refactor", "references/fastforward/protocol.md", "solution-depth-conventions")
    # shared-conventions 第 7 节结构反射检查与选型层降级互补,交叉引用不可断。
    assert_doc_contains("cs-onboard", "references/shared-conventions.md", "solution-depth-conventions")


def test_readonly_task_agent_capability_is_provider_aware_and_reachable() -> None:
    # 只读 mode 的唯一权威在共享 selector；阶段协议只组合 selector，不复制规则。
    assert_doc_contains(
        "cs-onboard",
        "references/agent-conventions.md",
        "data Isolation = Heterogeneous | Independent",
        "data ReadOnlyControl = EnforcedReadOnly | VerifiedNoWrite",
        "data AgentSelection",
        "hostAgentCapabilities",
        "readOnlyControlled",
        "selectTaskAgent",
        "reviewGate :: AgentSelection -> AgentRun",
    )
    for skill, path in (
        ("cs-feat", "references/design-review/protocol.md"),
        ("cs-epic", "references/review/protocol.md"),
        ("cs-code-review", "references/independent-review/protocol.md"),
    ):
        assert_doc_contains(skill, path, "selectTaskAgent Review", "reviewGate")
        assert "runReviewer" not in skill_text(skill, path)
    # 其他只读 Task agent 启动点也须触达共享 mode 规则。
    assert_doc_contains("cs-feat", "references/qa/protocol.md", "read-only 等价 mode")
    assert_doc_contains("cs-feat", "references/acceptance/protocol.md", "read-only 等价 mode")
    assert_doc_contains("cs-goal", "SKILL.md", "read-only 等价 mode")


def test_review_selector_preserves_guard_order_and_scope() -> None:
    assert_doc_contains(
        "cs-onboard",
        "references/agent-conventions.md",
        "Heterogeneous",
        "Independent",
        "hostAgentCapabilities",
        "不依赖 backend 产品名或工具名",
        "ExplicitConfigUnavailable",
    )
    selector = skill_text("cs-onboard", "references/agent-conventions.md")
    selection_order = (
        "Just agent <- bestFit",
        "= Start agent config",
        "SelectionBlocked ExplicitConfigUnavailable",
        "SelectionNeedsOwnerApproval IndependentAgentUnavailable",
    )
    positions = [selector.index(fragment) for fragment in selection_order]
    assert positions == sorted(positions)
    review_gate_order = (
        "reviewGate _ (Finished findings)",
        "reviewGate _ (Active _)",
        "reviewGate _ (Failed _) (Just ApproveLocalOnly)",
        "reviewGate _ (Failed reason) _",
        "reviewGate (SelectionBlocked reason) NotStarted",
        "reviewGate (SelectionNeedsOwnerApproval _) NotStarted (Just ApproveLocalOnly)",
        "reviewGate (SelectionNeedsOwnerApproval reason) NotStarted",
        "reviewGate (Start agent config) NotStarted",
    )
    review_gate_positions = [selector.index(fragment) for fragment in review_gate_order]
    assert review_gate_positions == sorted(review_gate_positions)
    assert "toReviewLane (NeedOwnerApproval reason) = Left reason" in selector
    assert "data ReviewVerdict = Passed | ChangesRequested | ReviewBlocked Reason" in selector
    assert_doc_contains(
        "cs-code-review",
        "references/independent-review/protocol.md",
        "dirtyPaths scope `isSubsetOf` currentScope scope",
        "OcrSkippedByUser",
        "pending laneB",
        "pending (RunCommitted _)",
        "failed (OcrFailed _)",
        "finished (OcrFinished _)",
        "verifiedFindings (IndependentFindings findings) laneB",
        "mergeableDecision (MergeVerified findings)",
        "`ApproveLocalOnly` 是 owner 的人类授权",
        "环境变量是 runner 的机械 opt-in",
    )
    independent_review = skill_text("cs-code-review", "references/independent-review/protocol.md")
    assert "otherwise                       = Blocked IndependentReviewRequired" not in independent_review
    assert "reviewerField LocalReview" not in independent_review


def test_cs_skills_depend_on_host_agent_behavior_not_a_backend_tool_name() -> None:
    selector = skill_text("cs-onboard", "references/agent-conventions.md")
    assert "hostAgentCapabilities" in selector
    assert "Heterogeneous" in selector
    assert "Independent" in selector
    assert "异构候选不可用不阻塞独立 review" in selector

    for markdown in SKILLS.rglob("*.md"):
        text = markdown.read_text(encoding="utf-8")
        assert "cs_agent_" not in text, markdown
        assert "CS Agent Facade" not in text, markdown

def test_runtime_reference_copies_match_templates() -> None:
    # runtime 可保留 legacy-only 文件；每个 onboard 模板都必须存在同名逐字副本。
    templates = SKILLS / "cs-onboard" / "references"
    runtime = ROOT / ".codestable" / "reference"
    for src in sorted(templates.rglob("*.md")):
        relative = src.relative_to(templates)
        copy = runtime / relative
        assert copy.exists(), f"{relative}: 缺 runtime reference 副本"
        assert src.read_text(encoding="utf-8") == copy.read_text(encoding="utf-8"), (
            f"{relative}: 模板与项目副本不一致，需 sync"
        )
