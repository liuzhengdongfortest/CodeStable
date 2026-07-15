---
name: cs-epic
description: "Epic 主入口。用于大需求或系统级能力的端到端拆解与长程执行：planning、review、子 feature design（批量）、goal 包。不要用于单个功能(cs-feat)、bug 修复(cs-issue)、行为等价重构(cs-refactor)、对外文档(cs-docs)。"
argument-hint: "[--stage planning|review|goal-package] <epic>"
contracts:
  - grep: "restoreEpicStage"
  - grep: "DispatchGoalDriver"
  - grep: "epic_child_batch: true"
  - grep: "codestable-workflow-next.py epic"
  - grep: "统一确认所有 design"
  - grep: "独立 Task agent reviewer"
  - grep: "final_answer_allowed: false"
  - not-grep: "git push"
  - not-grep: "read all references"
---

# cs-epic

## 启动必读

动作前先跑 CodeStable preflight：读 `.codestable/attention.md`（缺失先 `cs-onboard`）；不要用 `AGENTS.md`/`CLAUDE.md` 等外部入口代替它；细则见 `.codestable/reference/execution-conventions.md`。

`cs-epic` 是大需求端到端入口。用户文档统一叫 epic；为兼容历史产物，第一版内部目录、frontmatter 和工具仍使用 `roadmap`。用户确认 roadmap 和所有子 feature design 后，默认生成 goal 包并尝试通过可见 Task agent goal driver 长程执行；派发失败则打印 `/goal` 指令让用户粘贴执行。

旧技能 `cs-roadmap`、`cs-roadmap-review`、`cs-roadmap-impl-goal` 长期保留为兼容入口，只传入 `requested_stage`。
## 入口意图

本次调用参数：$ARGUMENTS

意图来源按优先级：调用参数 flag > 兼容入口预设 > 用户话术。参数为空或未被替换（仍是字面 `$ARGUMENTS`）时跳过该来源；调用参数用 `--stage planning|review|goal-package` 表示阶段意图，其余文本作为大需求描述。旧裸 token（如 `review`）只作为历史提示词兼容识别；新文档和新调用一律用 `--stage`。

无参数默认行为：没有 stage / epic 描述时，扫描 `.codestable/roadmap/`、子 feature design 和 goal 包状态，用状态机恢复；若没有可恢复 epic 且用户原话也没有大需求目标，先问用户要规划哪个 epic。

入口意图不覆盖仓库事实。已有 roadmap review 未通过时先修规划；已有 feature design 未确认时不生成 goal 包。
## Spec

```haskell
csEpic :: EpicInput -> EpicOutcome
csEpic = workflow
data EpicInput
  = Start EpicRequest | Resume RepoFacts | ResumePlanningInput PlanningResume
  | ConfirmRoadmapInput | ConfirmAllChildDesignInput
  | ApproveLocalReviewInput | AuthorizeGoalAcceptanceInput ApprovalRef | RejectGoalAcceptanceInput
  | AuthorizeGoalCommitsInput ApprovalRef | RejectGoalCommitsInput
data EpicRequest = EpicRequest
  { requestedStage : Maybe EntryStage    -- planning | review | goal-package
  , userGoal       : Maybe Text
  , repoFacts      : RepoFacts           -- 优先于 args / 聊天历史
  }
data EntryStage = PlanningEntry | ReviewEntry | GoalPackageEntry
data Stage = Planning | Review | ChildDesignBatch | GoalPackage
data RoadmapReviewState
  = ReviewMissing | ReviewPassed | ReviewChangesRequested
  | ReviewAwaiting AgentRef | ReviewNeedsOwnerApproval Reason
  | ReviewerFailed Reason | ReviewBlocked Reason
data EpicGoalRunState                     -- 从 goal-state.yaml status/driver 字段恢复
  = GoalMissing
  | GoalReadyToDispatch ApprovalRef ApprovalRef -- acceptance ref + commit ref
  | GoalAuthorizationMissing GoalAuthorizationKind
  | GoalDriverActive DriverInfo           -- driver_kind + driver_id；仅非终态生效
  | GoalComplete ApprovalRef ApprovalRef  -- 两项授权有效时优先于残留 driver 元数据
  | GoalHandoffBlocked Reason             -- status: handoff；优先于残留 driver 元数据
  | GoalUnknown Text
data GoalAuthorizationKind = AcceptanceAuthorization | CommitAuthorization
data EpicState = EpicState                -- 从 .codestable/roadmap/{slug}/ 与子 features/ 恢复
  { roadmapStatus       : Missing | Draft | Confirmed  -- frontmatter status: active 归一为 Confirmed
  , roadmapReviewState  : RoadmapReviewState           -- 从 roadmap-review review_state 恢复
  , childrenDesign      : AllPassed | Pending          -- 未 dropped child 均有 design+checklist+passed review
  , allDesignApproved   : Bool
  , goalRunState        : EpicGoalRunState
  , pendingCheckpoint   : Maybe CheckpointReason
  }
data EpicOutcome
  = RoutedTo Stage
  | Awaiting WaitReason
  | HumanCheckpoint CheckpointReason
  | DispatchGoalDriver Command            -- 先尝试可见 Task agent；失败才降级为 GoalHandoff
  | GoalHandoff Command
  | Completed EpicSummary
  | NeedsHuman Reason
  | Blocked Reason
data WaitReason = RoadmapReviewerRunning AgentRef | GoalDriverRunning DriverInfo | WorkflowWait Text
data CheckpointReason
  = ConfirmRoadmap | ConfirmAllChildDesign | ConfirmGoalAcceptanceAuthorization | ConfirmGoalCommitAuthorization | ApproveReviewFallback Reason
data CheckpointResume
  = PersistRoadmapConfirmed | PersistAllDesignsApproved | DelegatePlanningResume PlanningResume
  | PersistGoalAcceptanceAuthorization ApprovalRef | PersistGoalAcceptanceRejection | PersistGoalCommitAuthorization ApprovalRef | PersistGoalCommitRejection | RerunReview OwnerApproval | RejectResume Reason

resumeCheckpoint :: EpicInput -> CheckpointResume
resumeCheckpoint ConfirmRoadmapInput                = PersistRoadmapConfirmed
resumeCheckpoint ConfirmAllChildDesignInput         = PersistAllDesignsApproved
resumeCheckpoint (ResumePlanningInput resume)         = DelegatePlanningResume resume
resumeCheckpoint (AuthorizeGoalAcceptanceInput ref)  = PersistGoalAcceptanceAuthorization ref
resumeCheckpoint RejectGoalAcceptanceInput           = PersistGoalAcceptanceRejection
resumeCheckpoint (AuthorizeGoalCommitsInput ref)      = PersistGoalCommitAuthorization ref
resumeCheckpoint RejectGoalCommitsInput               = PersistGoalCommitRejection
resumeCheckpoint ApproveLocalReviewInput             = RerunReview ApproveLocalOnly
resumeCheckpoint _                                  = RejectResume InvalidCheckpointResume

resumeMatches :: EpicInput -> CheckpointReason -> Bool
resumeMatches ConfirmRoadmapInput ConfirmRoadmap = True
resumeMatches ConfirmAllChildDesignInput ConfirmAllChildDesign = True
resumeMatches input ConfirmGoalAcceptanceAuthorization = input is AuthorizeGoalAcceptanceInput _ || input == RejectGoalAcceptanceInput
resumeMatches input ConfirmGoalCommitAuthorization = input is AuthorizeGoalCommitsInput _ || input == RejectGoalCommitsInput
resumeMatches ApproveLocalReviewInput (ApproveReviewFallback _) = True
resumeMatches _ _ = False

applyCheckpointResume :: EpicInput -> EpicState -> Either Reason EpicState
applyCheckpointResume (Start _) s = Right s
applyCheckpointResume (Resume _) s = Right s
applyCheckpointResume (ResumePlanningInput r) s = persistPlanningResume s <$> resumePlanning (planningState s) r
applyCheckpointResume input s
  | Just reason <- s.pendingCheckpoint, resumeMatches input reason = Right (persistCheckpointResume (resumeCheckpoint input) s)
  | otherwise = Left InvalidCheckpointResume
```

```haskell
restoreEpicStage :: EpicState -> EpicRequest -> EpicOutcome
restoreEpicStage(s, request)
  | ambiguousTarget(s, request)                             -> NeedsHuman "which epic?"
  | noRecoverableEpic s && isNothing request.userGoal      -> NeedsHuman "which epic?"
  | s.roadmapStatus == Missing                              -> RoutedTo Planning      -- 大需求未拆解
  | s.roadmapReviewState == ReviewChangesRequested          -> RoutedTo Planning
  | s.roadmapReviewState is ReviewAwaiting agent            -> Awaiting (RoadmapReviewerRunning agent)
  | s.roadmapReviewState is ReviewNeedsOwnerApproval reason -> HumanCheckpoint (ApproveReviewFallback reason)
  | s.roadmapReviewState is ReviewerFailed reason           -> Blocked reason
  | s.roadmapReviewState is ReviewBlocked reason            -> Blocked reason
  | s.roadmapStatus == Draft && s.roadmapReviewState == ReviewMissing -> RoutedTo Review
  | s.roadmapReviewState == ReviewPassed && s.roadmapStatus /= Confirmed
      -> HumanCheckpoint ConfirmRoadmap        -- roadmap review passed 但用户未确认：停下让用户确认 epic 规划
  | s.roadmapStatus == Confirmed && s.roadmapReviewState /= ReviewPassed
      -> Blocked "confirmed roadmap lacks passed review"
  | s.roadmapStatus == Confirmed && s.childrenDesign == Pending
      -> RoutedTo ChildDesignBatch             -- 逐项进 cs-feat（epic_child_batch: true）；design 保持 `draft`，不逐个让用户确认
                                               -- 仍有子 feature 未完成 design-review 就继续下一个，不停用户
  | s.childrenDesign == AllPassed && not s.allDesignApproved
      -> HumanCheckpoint ConfirmAllChildDesign -- 停下让用户统一确认所有 design，确认后逐份标 approved
  | s.allDesignApproved && s.goalRunState == GoalMissing     -> RoutedTo GoalPackage
  | s.goalRunState is GoalComplete _ _                       -> Completed EpicSummary
  | s.goalRunState is GoalHandoffBlocked reason              -> GoalHandoff (handoffCommand reason)
  | s.goalRunState is GoalDriverActive driver                -> Awaiting (GoalDriverRunning driver)
  | s.goalRunState == GoalAuthorizationMissing AcceptanceAuthorization -> HumanCheckpoint ConfirmGoalAcceptanceAuthorization
  | s.goalRunState == GoalAuthorizationMissing CommitAuthorization     -> HumanCheckpoint ConfirmGoalCommitAuthorization
  | s.goalRunState is GoalReadyToDispatch _ _                -> DispatchGoalDriver "/goal"
  | s.goalRunState is GoalUnknown raw                        -> Blocked ("unknown goal-state: " <> raw)
  | otherwise                                                -> Blocked InvalidEpicState
```

`restoreEpicStage` 是唯一路由真相：扫 roadmap 与子 features 恢复 `EpicState`；`DelegatePlanningResume` 先交 planning protocol 的 `resumePlanning` 精确匹配 pending checkpoint 并持久化，再恢复本状态机。任一 goal authorization rejected 归一为 handoff，其他非 handoff 状态按缺失项归一为 acceptance/commit `GoalAuthorizationMissing`，两份可验证 `ApprovalRef` 都存在才 ready。子 design 是连续 batch loop，在统一确认前不得 final answer；stage protocol 见后文。

`cs-epic` 不在主线程直接执行长程 goal；只能通过可见 Task agent goal driver 派发。没有可见 driver 或派发失败时，回退为用户手动粘贴 `/goal`。

## Workflow

主执行主线（每次调用按序走；planning/review/goal 的厚规则见对应 protocol，本节只定顺序与边界）：

```haskell
workflow :: EpicInput -> EpicOutcome
workflow = preflight >=> parseEntryIntent >=> restoreEpicState >=> applyCheckpointResume
       >=> restoreEpicStage >=> loadStageProtocol >=> executeStage >=> exitRecoverable

preflight        -- 读 .codestable/attention.md；缺失 -> route to cs-onboard；不得用 AGENTS.md/CLAUDE.md 代替
parseEntryIntent -- flag > compat-preset > utterance；repoFacts override requestedStage；空参不推断 stage
restoreEpicStage -- 扫 .codestable/roadmap/ + 子 features/ + goal 包恢复 EpicState，选 next stage（见 Spec）
loadStageProtocol -- 「Reference 加载」映射；进 stage 才加载该 stage 一个 protocol，禁止 eager 读全部 references
executeStage     -- ChildDesignBatch 走连续 batch loop（下节为唯一权威）；
                 -- 全部 child passed 后 HumanCheckpoint 统一确认所有 design，确认后逐份标 approved；
                 -- DispatchGoalDriver 先尝试可见 driver，失败才输出 GoalHandoff
exitRecoverable  -- artifact 已落盘 / next stage 明确 / checkpoint reason 明确，任一即可让下次调用从 repoFacts 恢复
```

## 文件放哪儿

```text
.codestable/roadmap/{slug}/
├── {slug}-roadmap.md
├── {slug}-items.yaml
├── {slug}-roadmap-review.md
├── goal-plan.md
├── goal-state.yaml
├── goal-protocol*.md
├── goal-audit.md
└── goal-features/
```

普通子 feature 仍放 `.codestable/features/YYYY-MM-DD-{feature-slug}/`。

## Child design batch loop

roadmap 已确认后，子 feature design 阶段是一个连续 batch loop，不是单次子任务：

```haskell
childDesignBatch :: Slug -> Loop
childDesignBatch slug = loop
  where
    loop = do
      -- 每轮开始、每个 child design-review 后、以及准备 final answer 前都先跑 hook：
      next <- run "python3 <cs-onboard skill 目录>/tools/codestable-workflow-next.py epic \
                  \--roadmap .codestable/roadmap/{slug} --json"
      case next.status of
        continue      -> step next.next_action >> loop
        goal_package  -> step next.next_action >> loop
        dispatch_goal -> step next.next_action >> loop
        user_gate | next.next_action == "all-feature-designs-confirmation"
                      -> stopAt (HumanCheckpoint ConfirmAllChildDesign)
        user_gate     -> stopAt (Blocked UnexpectedWorkflowUserGate)
        awaiting      -> stopAt (Awaiting (WorkflowWait next.next_action))
        handoff       -> stopAt (GoalHandoff next.next_action)
        blocked       -> stopAt (Blocked next.reason)
        _             -> stopAt (Blocked InvalidWorkflowNext)
      -- hook 输出 must_continue: true 或 final_answer_allowed: false 时只能来自前三个继续态；不得 final answer
      -- 每轮先扫 {slug}-items.yaml：按 DAG 取下一个 design-ready 且缺 design、checklist
      -- 或 passed design-review 的 item，调用 cs-feat（epic_child_batch: true）推进；design-ready
      -- 允许依赖 done / dropped / design-review passed，但实现前仍要求依赖严格 done
```

- 完成某一个 child 的 design + design-review `passed` 只是内部进度；不得 final answer、不得要求用户确认该 child、不得进入实现。
- 只有 items.yaml 里所有未 dropped child 都已有 design + checklist + `passed` design-review，才允许触发"所有 design 统一确认"的人工 checkpoint。
- 若下一条 child 可继续推进，本轮必须继续调用 `cs-feat`，而不是用"下一步继续处理下一个 child"作为结束汇报。
- child batch 只放宽 design admission；不得把 `dropped` 或仅 design-review passed 的依赖当成 implementation-ready。
- 若 preflight 刚完成 runtime 同步，从仓库事实恢复 batch loop，不靠对话记忆。

## Reference 加载

```haskell
stageProtocol :: Stage -> Protocol
stageProtocol Planning         = "references/planning/protocol.md"   -- 必要时 reference.md、support/codebase-design.md
stageProtocol Review           = "references/review/protocol.md"     -- gate 纪律见下
stageProtocol GoalPackage      = "references/goal/protocol.md"       -- 并复制 support/protocol*.md 和 support/goal-command-template.md
stageProtocol ChildDesignBatch = skill "cs-feat" (epic_child_batch: true)
  -- 子 feature 通过 cs-feat 主入口推进，不直接调用旧阶段技能；
  -- 内部上下文让单 feature 人工 checkpoint 推迟到 cs-epic 的批量确认

-- goal driver 派发规则见 .codestable/reference/agent-conventions.md 的 Goal driver 一节
```

review **gate 必需独立 Task agent reviewer**：主 agent 本地审查不得定稿、不得给 `passed`；roadmap 修订后的**每一轮重审同样适用**，降级须 approval-report + 用户明确授权（细则见 protocol）。子 feature design-review 经 `cs-feat` 同受此约束。
## 人工 checkpoint

触发时机以 Spec 的 `restoreEpicStage` 为唯一权威；本节只定义停下后的行为：

```haskell
onCheckpoint :: CheckpointReason -> Action
onCheckpoint ConfirmRoadmap        = 停等用户确认 epic 规划            -- roadmap/epic planning review passed 后
onCheckpoint ConfirmAllChildDesign = 停等用户统一确认所有 design，确认后逐份标 approved
onCheckpoint ConfirmGoalAcceptanceAuthorization = 写 pending goal-acceptance decision，停等 owner 授权
onCheckpoint ConfirmGoalCommitAuthorization = 写 pending goal-commits decision，停等 owner 授权自动 scoped-commit
onCheckpoint (ApproveReviewFallback reason) = 停等 owner 决定是否批准 local-only review；记录 reason
```

所有 `onCheckpoint` 都先把完整 reason 写入 canonical `approval-report.md` pending decision，再停等输入；无法恢复出同一 pending reason 时，任何 resume 都 fail-closed。

不要在第一个或任一单独子 feature design-review passed 后停下来要求用户确认执行；那是 `cs-feat` 普通单 feature 行为，在 `cs-epic` 子流程里必须延后到所有子 feature 都完成 design-review 后统一处理。
driver 不可见、派发失败或返回 `CS_ROADMAP_GOAL_HANDOFF` 时走 `GoalHandoff`，不是 `HumanCheckpoint` / `NeedsHuman` 的第二种写法。
## Failure Behavior

```haskell
needsHuman :: Situation -> Bool
needsHuman s = noRecoverableEpic s
            || ambiguousEpicTarget s
            || stageConflictsRepoFacts s

isBlocked :: Situation -> Bool
isBlocked s = invalidArtifactState s    -- 例如 active roadmap 没有 passed review
           || unknownGoalState s
           || reviewerFailed s
```

报告：当前 roadmap 目录、阻塞原因、下一步用户动作、已写文件、是否可安全重试。可安全回退为 fenced `/goal` 的 driver 不可用不算 `NeedsHuman`，统一返回 `GoalHandoff`。

## Output Contract

```haskell
data ExitPolicy = ContinueRun | StopRecoverable

exitPolicy :: EpicOutcome -> ExitPolicy
exitPolicy (RoutedTo _)           = ContinueRun
exitPolicy (DispatchGoalDriver _) = ContinueRun
exitPolicy (Awaiting _)           = StopRecoverable
exitPolicy (HumanCheckpoint _)    = StopRecoverable
exitPolicy (GoalHandoff _)        = StopRecoverable
exitPolicy (NeedsHuman _)         = StopRecoverable
exitPolicy (Blocked _)            = StopRecoverable
exitPolicy (Completed _)          = StopRecoverable
```

退出或交接时必须报告：roadmap 目录、恢复出的 `goalRunState`、child batch 进度、本轮写入文件、下一动作或 checkpoint、已运行验证。`DispatchGoalDriver` 不得直接退化成 `/goal`：先按 agent conventions 尝试可见 driver，只有不可用或派发失败才输出 `GoalHandoff`。
## 退出条件

```haskell
mayExit :: State -> Bool
mayExit s = workflowNext(s).final_answer_allowed        -- codestable-workflow-next.py 返回 final_answer_allowed: false 时当前 run 不能退出
         && batchLoopSettled s   -- child design batch loop 只在全部 child design-review passed、遇到 blocking / pending / 授权问题、或用户明确要求停止时才可结束
         && stateRecoverable s   -- 规划、审查、子 feature design 和 goal 包状态能从仓库事实恢复
```

历史 `roadmap` 命名只作为内部兼容说明出现；用户主路径称为 epic。需要同步文档或记忆时提示 `cs-docs-neat`。
