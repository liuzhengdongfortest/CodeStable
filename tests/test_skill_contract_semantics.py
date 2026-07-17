from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "plugins/codestable/skills"

ACTIVE_SKILLS = {
    "cs",
    "cs-audit",
    "cs-brainstorm",
    "cs-code-review",
    "cs-docs",
    "cs-docs-neat",
    "cs-domain",
    "cs-epic",
    "cs-feat",
    "cs-feedback",
    "cs-goal",
    "cs-issue",
    "cs-keep",
    "cs-note",
    "cs-onboard",
    "cs-refactor",
    "cs-req",
}

COMPATIBILITY_SKILLS = {
    "cs-doc-api",
    "cs-doc-tutorial",
    "cs-feat-accept",
    "cs-feat-design",
    "cs-feat-design-review",
    "cs-feat-ff",
    "cs-feat-impl",
    "cs-feat-qa",
    "cs-issue-analyze",
    "cs-issue-fix",
    "cs-issue-report",
    "cs-refactor-ff",
    "cs-roadmap",
    "cs-roadmap-impl-goal",
    "cs-roadmap-review",
}

HASKELL_BLOCK_RE = re.compile(r"```haskell\n(.*?)\n```", re.DOTALL)
EQUATION_RE = re.compile(
    r"(?m)^(?!(?:data|type|newtype)\b)([a-z][A-Za-z0-9_']*)\b[^=\n]*="
)
SIGNATURE_RE = re.compile(
    r"(?m)^([a-z][A-Za-z0-9_']*(?:\s*,\s*[a-z][A-Za-z0-9_']*)*)\s*::"
)
SKILL_POINTER_RE = re.compile(r"(?<![a-z0-9-])cs-[a-z0-9-]+")


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def skill(relative: str) -> str:
    return read(f"plugins/codestable/skills/{relative}")


def assert_order(text: str, *phrases: str) -> None:
    positions = [text.index(phrase) for phrase in phrases]
    assert positions == sorted(positions)


def test_every_shipped_cs_skill_has_an_explicit_role() -> None:
    discovered = {
        path.parent.name
        for path in SKILLS.glob("*/SKILL.md")
    }
    assert ACTIVE_SKILLS.isdisjoint(COMPATIBILITY_SKILLS)
    assert discovered == ACTIVE_SKILLS | COMPATIBILITY_SKILLS


def test_every_cs_skill_pointer_resolves_to_a_shipped_entry() -> None:
    shipped = ACTIVE_SKILLS | COMPATIBILITY_SKILLS
    unresolved: list[tuple[str, str]] = []
    for path in SKILLS.rglob("*.md"):
        for pointer in SKILL_POINTER_RE.findall(path.read_text(encoding="utf-8")):
            if pointer not in shipped:
                unresolved.append((path.relative_to(ROOT).as_posix(), pointer))
    assert unresolved == []


def test_every_haskell_decision_equation_has_a_typed_boundary() -> None:
    missing: list[tuple[str, str]] = []
    for path in SKILLS.rglob("*.md"):
        blocks = HASKELL_BLOCK_RE.findall(path.read_text(encoding="utf-8"))
        if not blocks:
            continue
        contract = "\n".join(blocks)
        equations = set(EQUATION_RE.findall(contract))
        signatures = {
            name.strip()
            for declaration in SIGNATURE_RE.findall(contract)
            for name in declaration.split(",")
        }
        for name in sorted(equations - signatures):
            missing.append((path.relative_to(ROOT).as_posix(), name))
    assert missing == []


def test_brainstorm_hands_feature_control_to_the_main_entry() -> None:
    brainstorm = skill("cs-brainstorm/SKILL.md")
    template = skill("cs-brainstorm/reference.md")
    overview = skill("cs-onboard/references/system-overview.md")

    assert 'route (Feature Clear) = Handoff PendingExit "cs-feat"' in brainstorm
    assert 'route (Feature Ready) = Handoff ConfirmedExit "cs-feat"' in brainstorm
    assert '"cs-feat --stage design"' not in brainstorm
    assert "由主入口选择 lane" in template
    for lane in ("featureWorkflow Quick", "featureWorkflow Standard", "featureWorkflow GoalLane"):
        assert lane in overview
    assert "workflow Feature  =" not in overview


def test_docs_manifest_and_draft_reviews_are_recoverable() -> None:
    main = skill("cs-docs/SKILL.md")
    api = skill("cs-docs/references/api/protocol.md")
    tutorial = skill("cs-docs/references/tutorial/protocol.md")
    reference = skill("cs-docs/references/api/reference.md")

    assert "ReviewManifest" in main
    assert "manifest_status: draft | approved" in reference
    assert_order(
        api,
        "manifestStatus s == ManifestMissing",
        "not (manifestConfirmed (manifestStatus s))",
        "Just reason <- approvalGate s",
    )
    assert "Checkpoint ReviewManifest" in api
    guide_stage = re.search(r"data GuideStage = ([^\n]+)", tutorial)
    assert guide_stage
    assert "Scope" not in guide_stage.group(1)
    assert "UserReview" not in guide_stage.group(1)
    assert "全局同步 / 记忆整理属于 `RoutedTo NeatHandoff`" in main


def test_feedback_and_neat_use_shared_outcome_semantics() -> None:
    feedback = skill("cs-feedback/SKILL.md")
    neat = skill("cs-docs-neat/SKILL.md")

    assert "NeedsHuman FailureKindMissing" in feedback
    assert "HumanCheckpoint (SelectSession xs)" in feedback
    assert "next _ Collected             = Completed LocalFeedback" in feedback
    assert "HumanCheckpoint ConfirmPublicPreview" in feedback
    assert "--repo codestable/CodeStable" in feedback
    assert "HumanCheckpoint ConfirmExternalMemoryEdit" in neat
    assert "允许零改动完成" in neat
    assert "不制造格式 churn" in neat
    assert "runRef    : NeatRunRef" in neat
    assert "resolutions : [NeatResolution]" in neat
    assert "ResolveLargeDocSplit NeatRunRef SplitDecision" in neat
    assert "ResolveExternalMemoryEdit NeatRunRef ExternalMemoryDecision" in neat
    assert "validResolutionSet (runRef req) (resolutions req)" in neat
    assert "all ((== current) . resolutionRunRef) rs" in neat
    assert "hasLargeDocResolution (resolutions req)" in neat
    assert "hasExternalMemoryResolution (resolutions req)" in neat
    assert "恢复取不到同一 ref 时不得消费旧 resolution" in neat
    assert "applyResolutions req facts" in neat
    assert_order(
        neat,
        "not (validResolutionSet (runRef req) (resolutions req))",
        "largeDocSplitNeeded facts",
        "externalMemoryEditNeeded facts",
        "runPipeline [SizeCheck, Enumerate, ImpactMatrix, Edit, SelfCheck, Summary]",
    )


def test_onboard_does_not_assume_sibling_skills_or_overwrite_dirty_runtime() -> None:
    onboard = skill("cs-onboard/SKILL.md")
    execution = skill("cs-onboard/references/execution-conventions.md")
    shared = skill("cs-onboard/references/shared-conventions.md")
    overview = skill("cs-onboard/references/system-overview.md")

    assert "ConfirmManagedOverwrite" in onboard
    assert "没有明确批准不得使用 `--force`" in onboard
    for resume in (
        "ApproveManagedOverwrite = Right RetrySelectedPath",
        "PreserveManagedAssets = Right StopPreservingFiles",
        "ApproveMigrationMapping = Right ApplyMigrationMapping",
        "SkipMigrationMapping = Right KeepOriginalFile",
        "ApproveGlobalInstall = Right InstallOptionalTool",
        "SkipGlobalInstall = Right ContinueWithoutOcr",
        "resumeOnboard _ _ = Left InvalidOnboardDecision",
    ):
        assert resume in onboard
    assert "HumanCheckpoint (ConfirmMigrationMapping source candidates)" in onboard
    assert "HumanCheckpoint ConfirmGlobalInstall" in onboard
    assert "按已安装 skill 名称加载 `cs-onboard`" in execution
    assert "不得假设当前 skill 能读取 sibling 目录" in execution
    assert "../cs-onboard" not in execution
    assert "allowed _              _                     = False" in shared
    assert "data CloseoutStage" in shared
    assert "workflow :: WorkflowEntry -> [Stage]" in overview
    assert "workflow :: MainEntry" not in overview
    for reference in (shared, overview, skill("cs-onboard/references/maintainer-notes.md")):
        assert "plugins/codestable/skills/" not in reference


def test_artifact_conventions_separate_persistence_from_read_depth() -> None:
    conventions = skill("cs-onboard/references/artifact-conventions.md")

    for artifact_class in (
        "human document",
        "workflow receipt",
        "ephemeral transport",
    ):
        assert artifact_class in conventions
    assert "持久化判断" in conventions
    assert "读取深度判断" in conventions
    assert "consumer projection" in conventions
    assert "drill-down" in conventions
    assert "可从仓库事实重建" in conventions


def test_review_packet_transport_is_scoped_without_changing_the_default_reviewer() -> None:
    tools = skill("cs-onboard/references/tools.md")
    agents = skill("cs-onboard/references/agent-conventions.md")
    review = skill("cs-code-review/references/independent-review/protocol.md")

    assert "同 workspace reviewer 已能按 prompt locator 回源" in tools
    assert "--transport workspace" in tools
    assert "--transport portable" in tools
    assert "--include-path" in tools
    assert "legacy compatibility" in tools
    assert "不得指向仓库根" in tools
    assert "同 workspace reviewer 直接接收 canonical locator" in agents
    assert "不先构建或内联 review packet" in review
    assert "legacy unscoped portable" in review


def test_code_review_report_is_verdict_sensitive_and_keeps_recovery_anchors() -> None:
    main = skill("cs-code-review/SKILL.md")
    template = skill("cs-code-review/references/report-template.md")

    assert "compact-passed" in main
    assert "detailed variant" in main
    assert "不要求为了 review 新建 implementation report" in main
    for field in (
        "reviewer:",
        "lane_a_state:",
        "lane_a_ref:",
        "lane_a_reason:",
        "lane_b_state:",
        "lane_b_ref:",
        "lane_b_reason:",
    ):
        assert field in template
    assert "## compact-passed variant" in template
    assert "Reviewed scope:" in template
    assert "## detailed variant" in template
    assert "failed / blocked / changes-requested" in template


def test_feature_qa_owns_behavioral_verification_not_code_review() -> None:
    qa = skill("cs-feat/references/qa/protocol.md")
    behavioral = skill("cs-feat/references/qa/behavioral-verification.md")
    default_inputs = qa[qa.index("## 输入"):qa.index("## 启动检查")]

    assert "references/qa/behavioral-verification.md" in qa
    assert "review 报告第 5 节" in default_inputs
    assert "review 报告第 6 节" in default_inputs
    assert "`git status --short`" in default_inputs
    assert "实现完成汇报" not in default_inputs
    assert "`git diff`" not in default_inputs
    assert "实现源码" not in default_inputs
    assert "behavioralEvidencePassed q" in qa
    assert "cleanlinessPassed q" not in qa
    assert "## 6. Cleanliness" not in qa

    for evidence in ("功能", "integration", "E2E", "browser", "API", "CLI", "manual"):
        assert evidence in behavioral
    assert "typecheck / lint / build" in behavioral
    assert "不能单独证明功能行为" in behavioral
    assert "代码风格、TODO/FIXME、unused import" in behavioral
    assert "只在失败或 blocked 的诊断分支" in behavioral


def test_qa_projection_and_standard_inline_share_one_behavior_contract() -> None:
    qa = skill("cs-feat/references/qa/protocol.md")
    acceptance = skill("cs-feat/references/acceptance/protocol.md")
    review = skill("cs-code-review/SKILL.md")

    for field in ("runner_state:", "runner_reason:", "runner_id:", "round:"):
        assert field in qa
    for heading in (
        "## compact-passed variant",
        "## 1. Scope And Inputs",
        "## 2. Verification Matrix",
        "## 5. Findings",
        "## 7. Verdict",
        "## detailed variant",
    ):
        assert heading in qa
    assert "failed / blocked / pending" in qa
    assert 'persistedQAStatus QAPassed = "passed"' in qa
    assert 'persistedQAStatus QAFailed = "failed"' in qa
    assert 'persistedQAStatus QABlocked = "blocked"' in qa
    assert "terminal QA receipt 前" in qa
    assert "ReturnToCodeReview" in qa

    assert "references/qa/behavioral-verification.md" in acceptance
    assert "不额外生成 QA 报告" in acceptance
    assert "Command Results / Scenario Results / Diagnostic Context（如有）" in acceptance
    assert "references/qa/behavioral-verification.md" not in review


def test_note_routes_semantic_owners_before_size_and_frequency() -> None:
    note = skill("cs-note/SKILL.md")

    assert_order(
        note,
        "needsDecisionRecord n               = RouteToDomain",
        "lifetime n == Temporary             = RouteToWorkSpec",
        "lineCount n > 2                     = RouteToKeep",
        "frequency n /= EverySession         = RouteToKeep",
    )


def test_release_protocol_runs_all_repository_gates() -> None:
    release = read(".claude/skills/eval-cs-skill/references/release/protocol.md")

    for command in (
        "python3 -m pytest -q tests -rs",
        "check-plugin-package.py --root . --json",
        "codestable-runtime-sync.py --root . --source-skill-dir plugins/codestable/skills/cs-onboard --check --json",
        "codestable-doctor.py --root . --json",
        "git diff --check",
    ):
        assert command in release
    assert "任一 JSON gate 的 `ok` 非 true 都阻断发布" in release


def test_epic_final_audit_requires_bijective_canonical_feature_evidence() -> None:
    audit = skill("cs-epic/references/goal/support/protocol-audit.md")
    gates = skill("cs-epic/references/goal/support/protocol-gates.md")

    assert "roadmapFeatureBijection a" in audit
    assert "canonicalFeatureEvidence a" in audit
    assert "每个非 dropped item 恰好对应一个 feature" in gates
    assert "frontmatter `doc_type` / `feature` 必须匹配当前 feature" in gates


def test_requirement_index_is_owned_lazily_by_cs_req() -> None:
    req = skill("cs-req/SKILL.md")
    shared = skill("cs-onboard/references/shared-conventions.md")

    assert "缺失按空索引处理，首次落 req 时创建" in req
    assert "onboard 只建 `requirements/` 聚合根" in req
    assert "cs-req 首次落 req 时 lazy 创建" in shared


def test_goal_stop_reason_vocabulary_matches_the_goal_skill() -> None:
    goal = skill("cs-goal/SKILL.md")
    conventions = skill("cs-onboard/references/goal-conventions.md")
    reasons = {
        "AcceptanceConflict",
        "AmbiguousTerminal",
        "ScopeBoundaryChange",
        "RepeatedBlocker",
        "BudgetExhausted",
        "RiskAcceptanceNeeded",
        "ReviewAgentUnavailable",
        "AcceptanceAgentUnavailable",
    }
    for reason in reasons:
        assert reason in goal
        assert reason in conventions
    for stale in (
        "TerminalAmbiguity",
        "LongLivedContractChange",
        "BudgetLimit",
        "PrivilegedAction",
        "AgentUnavailable",
    ):
        assert re.search(rf"\b{re.escape(stale)}\b", conventions) is None


def test_shipped_markdown_does_not_bind_to_a_specific_agent_backend() -> None:
    findings: list[tuple[str, str]] = []
    for path in SKILLS.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        for forbidden in ("cs_agent_", "Paseo subagent", "Paseo reviewer"):
            if forbidden in text:
                findings.append((path.relative_to(ROOT).as_posix(), forbidden))
    assert findings == []


def test_feature_and_acceptance_decision_domains_are_closed() -> None:
    feature = skill("cs-feat/SKILL.md")
    acceptance = skill("cs-feat/references/acceptance/protocol.md")
    design = skill("cs-feat/references/design/protocol.md")
    fastforward = skill("cs-feat/references/fastforward/protocol.md")

    assert "requestedMode  : Maybe ExecutionLane" in feature
    for stage_resume in (
        "ResumeDesign DesignDecision",
        "ResumeReview OwnerApproval",
        "ResumeAcceptance AcceptanceDecision",
        "ResumeEffect EffectDecision",
    ):
        assert stage_resume in feature
    for checkpoint in ("ConfirmAcceptance", "ConfirmEffect", "ApproveReviewFallback Reason"):
        assert checkpoint in feature
    assert "data WaitReason = DesignReviewerRunning AgentRef | AwaitGoalDriver DriverInfo" in feature
    assert "Awaiting (AwaitGoalDriver driver)" in feature
    assert "otherwise                                                   -> Blocked InvalidFeatureState" in feature
    assert "data FixKind = CompleteFeature | QAFix | OwnerRequestedChanges" in feature
    assert "ResumeGoalAcceptance ApprovalRef" in acceptance
    assert "goalAuthorizationMatches input s" in acceptance
    assert "persistedGoalAuthorization s == AuthorizationApproved ref" in acceptance
    assert 'approvalArtifactApproved s ref "goal-acceptance"' in acceptance
    assert "not (goalMode s) && input /= ResumeAcceptance ApproveAcceptance" in acceptance
    assert "data DesignInput = Start DesignEntry | ResumeDesign DesignDecision" in design
    assert "data FastForwardInput = StartQuick | ResumeEffect EffectDecision" in fastforward
    assert "ownerRejectedCheckpoint s" in feature


def test_feature_agent_gates_persist_recoverable_state() -> None:
    feature = skill("cs-feat/SKILL.md")
    agent_conventions = skill("cs-onboard/references/agent-conventions.md")
    design_review = skill("cs-feat/references/design-review/protocol.md")
    qa = skill("cs-feat/references/qa/protocol.md")
    acceptance = skill("cs-feat/references/acceptance/protocol.md")

    for field in ("review_state:", "review_reason:", "reviewer_id:"):
        assert field in design_review
    for field in ("runner_state:", "runner_reason:", "runner_id:"):
        assert field in qa
    for field in ("audit_state:", "audit_reason:", "auditor_id:"):
        assert field in acceptance
    assert "ReviewAwaiting AgentRef" in feature
    assert "ReviewNeedsOwnerApproval Reason" in feature
    assert "ReviewerFailed Reason" in feature
    assert "旧 `blocked` 无 `review_state` 时 fail-closed" in feature
    assert "data OwnerApproval = ApproveLocalOnly" in agent_conventions


def test_feature_and_epic_classify_stage_conflicts_as_needs_human() -> None:
    feature = skill("cs-feat/SKILL.md")
    epic = skill("cs-epic/SKILL.md")

    for contract in (feature, epic):
        needs_human = contract[contract.index("needsHuman ::"):contract.index("isBlocked ::") if "isBlocked ::" in contract else contract.index("blocked ::")]
        assert "stageConflictsRepoFacts s" in needs_human
    epic_blocked = epic[epic.index("isBlocked ::"):epic.index("```", epic.index("isBlocked ::"))]
    assert "stageConflictsRepoFacts s" not in epic_blocked


def test_build_cs_skill_audits_resume_and_awaiting_paths_end_to_end() -> None:
    build_skill = read(".claude/skills/build-cs-skill/SKILL.md")
    spec_standard = read(
        ".claude/skills/build-cs-skill/references/cs-skill-spec-standard.md"
    )
    quality_gates = read(
        ".claude/skills/build-cs-skill/references/cs-skill-quality-gates.md"
    )

    assert "canonical main entry's tagged resume domain" in build_skill
    assert "canonical main entry's tagged resume union" in spec_standard
    assert "locally closed reference type does not prove end-to-end resume coverage" in quality_gates
    assert "missing ids plus ambiguous legacy `blocked` states" in quality_gates


def test_goal_status_keeps_stop_reason_in_the_owner_stop_state() -> None:
    conventions = skill("cs-onboard/references/goal-conventions.md")
    assert "data GoalStatus = Active | Complete | Blocked" in conventions
    assert "Blocked StopReason" not in conventions


def test_goal_completion_requires_linked_final_iteration_and_typed_owner_resume() -> None:
    goal = skill("cs-goal/SKILL.md")
    reference = skill("cs-goal/reference.md")
    conventions = skill("cs-onboard/references/goal-conventions.md")

    for phrase in (
        "resumeInput : Maybe GoalResume",
        "ResolveGoalStop CheckpointReason GoalOwnerDecision",
        "s.ownerStop == PendingStop reason",
        "Left InvalidGoalResume",
        "ApproveLocalReviewFallback ApprovalRef",
        'approvalArtifactApproved s ref "goal-local-review"',
        "validGoalDecision _ (ApproveLocalReviewFallback _) _ = False",
        "completionEvidenceReady :: GoalState -> Bool",
        "s.acceptanceFinalIteration == s.finalIterationReport",
        "s.finalAcceptanceReport == s.acceptanceReport",
        "recordFinalIterationAndComplete s",
        'NeedsHuman "complete goal lacks linked acceptance/final-iteration evidence"',
    ):
        assert phrase in goal
    assert "s.status == Active && s.acceptancePassed      -> Completed" not in goal
    assert "显式 pin 的配置不可用时 owner-stop，不能降级" in goal
    assert "不在 goal driver 主线程静默自审" in goal
    assert "AcceptanceAgentUnavailable -- 终端验收 Task agent 无法启动" in goal
    assert "含 `ReviewAgentUnavailable` / `AcceptanceAgentUnavailable`" in goal
    assert "只有真实未完成动作写 `Follow-Up`，已完成交付写 `Delivery Record`" in goal

    for phrase in (
        "functional_acceptance: null # final iteration 必填 ../functional-acceptance.md",
        "doc_type: goal-functional-acceptance",
        'final_iteration: "iterations/{nnn}.md"',
        "两份引用与 `state.yaml.current_iteration` 不一致时不得把 goal 标为 complete",
        "`AcceptanceAgentUnavailable` 不接受 local/self 验收",
    ):
        assert phrase in reference
    assert "&& finalIterationRecorded g" in conventions
    assert "&& acceptanceAndFinalIterationCrossReference g" in conventions
    assert "reviewAgentUnavailable g              = Just ReviewAgentUnavailable" in conventions


def test_refactor_fails_closed_on_invalid_restored_state() -> None:
    refactor = skill("cs-refactor/SKILL.md")
    assert "| Blocked Reason" in refactor
    assert "otherwise                                        -> Blocked InvalidRefactorState" in refactor


def test_code_review_lane_launch_wait_and_resume_preserve_run_identity() -> None:
    review = skill("cs-code-review/SKILL.md")
    protocol = skill("cs-code-review/references/independent-review/protocol.md")
    report = skill("cs-code-review/references/report-template.md")
    conventions = skill("cs-onboard/references/agent-conventions.md")

    for phrase in (
        "data ExternalRunRef = TaskRunRef AgentRef | OcrRunRef Text",
        "| Launching LaneName",
        "data ReviewWait = LaneStillPending LaneName ExternalRunRef",
        "ResumeLane LaneName ExternalRunRef LaneResult",
        "ResumeSelfReviewDowngrade ApprovalRef",
        "restoreReviewState :: RepoFacts -> Either ReviewBlocker ReviewState",
        "invalidPersistedLaneState facts = Left InvalidReviewResume",
        "fullRereviewRequired facts = Right (resetLanesForNewRound facts)",
        "restoreReviewState req.repoFacts >>= applyReviewResume req.resumeInput",
        "pendingLaneRef lane s == Just ref",
        'approvalArtifactApproved s ref "code-review-local-only"',
        "InvalidReviewResume",
        "旧 `status: blocked` 缺 lane/ref 或非法 enum 直接 `Left InvalidReviewResume`",
    ):
        assert phrase in review
    for field in (
        "lane_a_state:",
        "lane_a_ref:",
        "lane_a_reason:",
        "lane_b_state:",
        "lane_b_ref:",
        "lane_b_reason:",
    ):
        assert field in report
    assert "not-started|ready-to-launch|pending|completed|failed|skipped|unavailable" in report
    assert "focused closure 复用同 round 的 completed；完整复审增加 round 并重置 lane" in report
    assert "MergeLaunch LaneName LaneCommand" in protocol
    assert "OcrActive Text" in protocol
    assert "mergeGate (Await ref)" in protocol
    assert "pending (RunCommitted _)" not in protocol
    assert "正常同步执行" in protocol
    assert "不得自行合成 id" in protocol
    assert "| Await AgentRef" in conventions
    assert "reviewGate _ (Active ref) _ = Await ref" in conventions
    assert "toReviewLane (Await _) = Left AgentLaneNotReturned" in conventions
    epic_review = skill("cs-epic/references/review/protocol.md")
    design_review = skill("cs-feat/references/design-review/protocol.md")
    assert "ref == awaitedRef" in epic_review
    assert "(Await _)" in epic_review
    assert "`Await ref` 必须把同一 `ref` 写入 `reviewer_id`" in design_review


def test_primary_workflow_checkpoint_resumes_are_typed_matched_and_consumed() -> None:
    issue = skill("cs-issue/SKILL.md")
    refactor = skill("cs-refactor/SKILL.md")
    docs = skill("cs-docs/SKILL.md")
    audit = skill("cs-audit/SKILL.md")
    epic = skill("cs-epic/SKILL.md")
    planning = skill("cs-epic/references/planning/protocol.md")
    feature = skill("cs-feat/SKILL.md")
    qa = skill("cs-feat/references/qa/protocol.md")
    acceptance = skill("cs-feat/references/acceptance/protocol.md")

    for text, phrases in (
        (
            issue,
            (
                "checkpointResume : Maybe IssueResume",
                "ResumeIssueCheckpoint CheckpointReason CheckpointAnswer",
                "s.pendingCheckpoint == Just reason",
                "Left InvalidCheckpointResume",
            ),
        ),
        (
            refactor,
            (
                "checkpointResume : Maybe RefactorResume",
                "ResumeRefactorCheckpoint CheckpointReason CheckpointAnswer",
                "s.pendingCheckpoint == Just reason && validRefactorAnswer reason answer",
                "KeepPartialChanges, DiscardPartialChanges",
                "Left InvalidCheckpointResume",
            ),
        ),
        (
            docs,
            (
                "resumeInput   : Maybe DocsResume",
                "ResumeDocsCheckpoint CheckpointReason DocsDecision",
                "s.pendingCheckpoint == Just reason",
                "Left InvalidDocsResume",
                "s.rejectedCheckpoint == Just ConfirmOverwrite",
                "preservedExistingDocSummary s",
            ),
        ),
        (
            audit,
            (
                "resumeInput : Maybe AuditResume",
                "resumeReason :: AuditResume -> CheckpointReason",
                "s.pendingCheckpoint == Just (resumeReason resume)",
                "validAuditResume resume",
                "ArchDrift `notElem` dims",
                "Left InvalidAuditResume",
                "wholeRepoBlindScan(s)",
                "archDriftRequested(s)",
                "后续 blind-scan 与 arch-drift guards 只读该 state",
            ),
        ),
    ):
        for phrase in phrases:
            assert phrase in text

    issue_workflow = issue[issue.index("workflow :: IssueRequest"):issue.index("```", issue.index("workflow :: IssueRequest"))]
    refactor_workflow = refactor[
        refactor.index("workflow :: RefactorRequest"):refactor.index("```", refactor.index("workflow :: RefactorRequest"))
    ]
    for workflow_text, ordered in (
        (issue_workflow, ("preflight req", "restoreIssueState", "applyIssueResume", "restoreIssueStage")),
        (
            refactor_workflow,
            ("preflight req", "restoreRefactorState", "applyRefactorResume", "restoreRefactorStage"),
        ),
    ):
        positions = [workflow_text.index(fragment) for fragment in ordered]
        assert positions == sorted(positions)

    assert 'csDocs req | attentionMissing req.repoFacts = NeedsHuman "route to cs-onboard"' in docs
    assert "applyDocsResume req.resumeInput" in docs
    assert 'csAudit req | attentionMissing req = NeedsHuman "route to cs-onboard"' in audit
    assert "applyAuditResume req.resumeInput" in audit
    audit_select = audit[audit.index("selectAuditStep(s, req)"):audit.index("```", audit.index("selectAuditStep(s, req)"))]
    audit_order = ("attentionMissing req", "s.pendingCheckpoint", "hasSelectedFinding(req)")
    assert [audit_select.index(item) for item in audit_order] == sorted(
        audit_select.index(item) for item in audit_order
    )

    assert "ResumePlanningInput PlanningResume" in epic
    assert "DelegatePlanningResume PlanningResume" in epic
    assert "resumeCheckpoint (ResumePlanningInput resume)" in epic
    for phrase in (
        "pendingCheckpoint   : Maybe CheckpointReason",
        "resumeMatches input reason",
        "Left InvalidCheckpointResume",
        "resumePlanning (planningState s) r",
        "所有 `onCheckpoint` 都先把完整 reason 写入 canonical `approval-report.md` pending decision",
    ):
        assert phrase in epic
    assert "data PlanningResume" in planning
    assert "resumePlanning :: PlanningState -> PlanningResume -> Either Reason PlanningOutcome" in planning
    assert "s.pendingCheckpoint == Just SelectOneRoadmap" in planning
    assert "s.pendingCheckpoint == Just ReviewRoadmapDraft" in planning
    assert "Left InvalidPlanningResume" in planning
    for phrase in ("ResumeQARunner OwnerApproval", "ResumeAcceptanceAuditor OwnerApproval"):
        assert phrase in feature
    assert "data QAInput = StartQA | ResumeQARunner OwnerApproval" in qa
    assert "selectQARunner :: QAInput -> QARequest" in qa
    assert "case input of ResumeQARunner approval -> Just approval" in qa
    assert "ResumeAcceptanceAuditor OwnerApproval" in acceptance
    assert "selectAcceptanceAuditor :: AcceptanceInput -> Bool" in acceptance
    assert "case input of ResumeAcceptanceAuditor approval -> Just approval" in acceptance

    issue_report = skill("cs-issue/references/report/protocol.md")
    issue_analyze = skill("cs-issue/references/analyze/protocol.md")
    issue_fix = skill("cs-issue/references/fix/protocol.md")
    refactor_standard = skill("cs-refactor/references/standard/protocol.md")
    refactor_fast = skill("cs-refactor/references/fastforward/protocol.md")
    docs_tutorial = skill("cs-docs/references/tutorial/protocol.md")
    docs_api = skill("cs-docs/references/api/protocol.md")
    for reference in (issue_report, issue_analyze, issue_fix):
        assert "ResumeIssueCheckpoint" in reference
    for reference in (refactor_standard, refactor_fast):
        assert "ResumeRefactorCheckpoint" in reference
    for reference in (docs_tutorial, docs_api):
        assert "ResumeDocsCheckpoint" in reference
