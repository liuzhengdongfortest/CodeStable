---
name: cs-feat
description: "Feature 主入口。用于新功能或功能改造，先按风险自动选择 Quick、Standard 或 Goal lane，再恢复并推进对应流程。不要用于单纯 bug 修复(cs-issue)、行为等价重构(cs-refactor)、对外文档(cs-docs)、大需求拆解(cs-epic)。"
argument-hint: "[--stage design|design-review|impl|qa|accept|goal-package] [--mode quick|standard|goal|fastforward] <feature>"
contracts:
  - grep: "restoreFeatureStage"
  - grep: "classifyExecutionLane"
  - grep: "DispatchGoalDriver"
  - grep: "progressive reference loading"
  - grep: "must not auto-approve design"
  - grep: "独立 Task agent reviewer"
  - grep: "design-review passed"
  - grep: "不重复读取这些全局输入"
  - not-grep: "git push"
  - not-grep: "read all references"
---

# cs-feat

## 启动必读

动作前先跑 CodeStable preflight：读 `.codestable/attention.md`（缺失先 `cs-onboard`）；不要用 `AGENTS.md`/`CLAUDE.md` 等外部入口代替它；细则见 `.codestable/reference/execution-conventions.md`。

`cs-feat` 是 feature 的唯一推荐入口。它先按任务事实选择执行 lane，再从仓库事实恢复阶段：Quick 直接实现；Standard 在当前 run 完成 design、implementation、review 和 accept-inline；Goal 才生成 goal package 并尝试通过可见 Task agent goal driver 长程执行。Standard / Goal 仍在 design gate 停下来等用户确认。真正的各阶段动作由对应 protocol 负责（见 Progressive Reference Loading）。

## 入口意图

本次调用参数：$ARGUMENTS

意图来源按优先级：调用参数 flag > 兼容入口预设 > 用户话术。参数为空或未被替换（仍是字面 `$ARGUMENTS`）时跳过该来源；`--stage <stage>` 表示阶段意图，`--mode <mode>` 表示执行模式，其余文本作为需求描述。

| 参数 | 入口意图 |
|---|---|
| `--stage design` | `requested_stage: design` |
| `--stage design-review` | `requested_stage: design-review` |
| `--stage impl` | `requested_stage: implementation` |
| `--stage qa` | `requested_stage: qa` |
| `--stage accept` | `requested_stage: acceptance` |
| `--stage goal-package` | `requested_stage: goal-package` |
| `--mode quick` / `--mode fastforward` | `requested_mode: quick`（fastforward 是兼容别名） |
| `--mode standard` | `requested_mode: standard` |
| `--mode goal` | `requested_mode: goal` |

入口意图只是偏好；**仓库事实优先**（`restoreFeatureStage`），也优先于聊天历史。

无参数默认行为：没有 flag / 需求描述时，不猜阶段；扫描 `.codestable/features/`、目标产物与当前 git diff，用状态机恢复下一步。没有可恢复 feature 且用户原话也无新功能目标时，返回 `NeedsHuman` 问处理哪个 feature。

## 风险分级

```haskell
data ExecutionLane = Quick | Standard | Goal

classifyExecutionLane :: FeatureState -> EntryIntent -> ExecutionLane
classifyExecutionLane(s, intent)
  | s.epicChildBatch || hasGoalState(s) || hasRoadmapOwner(s)          = Goal
  | hasExistingDesign(s)                                               = recordedLaneOrConfirmedReclassification(s, intent)
  | explicitlyRequestsGoal(intent)                                     = Goal
  | explicitlyRequestsStandard(intent)                                = Standard
  | explicitlyRequestsQuick(intent) && quickEligible(s, intent)       = Quick
  | explicitlyRequestsQuick(intent)                                   = Standard
  | quickEligible(s, intent)                                           = Quick
  | otherwise                                                          = Standard
```

`quickEligible` 必须同时满足：需求与验收行为明确；改动局部且挂载点已知；复用既有公开契约，不新增或改变跨系统协议；目标验证入口已知；不涉及 requirement/ADR 边界、迁移、权限/安全、并发或高风险数据语义。任一项未知就选 Standard，不按模型名称、推理档位或所谓“智商”选 lane。

Standard 用于需要新契约、跨模块决策或正式 design，但适合当前 run 完成的单 feature。Goal lane 只在用户明确要求长程自主执行、显式 `--stage goal-package` / `--mode goal`、已有 `goal-state.yaml`，或 Epic 批量上下文时选择；任务较大本身不自动等于 Goal。

用户说“这是小改动”“流程太重”“文档比代码多”或同义反馈时，必须暂停继续建产物并重新分类。满足 Quick 就立即降级；仍有风险条件时逐条说明为什么不能降级，不得沿既定流程无视反馈。

已有 design 时不允许入口参数静默越过已记录 lane。用户明确要求降级且重新核对仍满足 `quickEligible` 时，先把 `execution_lane: quick` 和降级原因写回 design，再进入 FastForward；已有 `goal-state.yaml` 时不得原地降级，必须先按 Goal 协议安全 handoff，再由 owner 决定是否重分类。

## Spec

```haskell
csFeat :: FeatureRequest -> FeatureOutcome

data FeatureRequest = FeatureRequest
  { requestedStage : Maybe Stage
  , requestedMode  : Maybe Mode          -- quick | standard | goal；fastforward -> quick
  , userGoal       : Maybe Text
  , repoFacts      : RepoFacts           -- 优先于 args / 聊天历史
  }

data Stage = Design | DesignReview | GoalPackage | Implementation | CodeReview | QA | Acceptance | FastForward

data DesignReviewStatus = ReviewMissing | ReviewPassed | ChangesRequested | ReviewBlocked

data QuickRunState = QuickImplementationPending | QuickReviewReady | QuickReviewFixing | QuickComplete

data StandardRunState
  = StandardImplementationPending
  | StandardReviewReady | StandardReviewFixing
  | StandardAcceptanceReady | StandardComplete

data GoalRunState                        -- 从 goal-state.yaml 的 stage/status/driver 字段恢复
  = GoalMissing
  | GoalReadyToDispatch                  -- implementation / ready-to-dispatch
  | GoalDriverActive DriverInfo          -- driver_kind + driver_id；仅非终态生效
  | GoalImplementationRunning            -- implementation / running
  | GoalReviewReady | GoalReviewFixing    -- review / ready|fixing
  | GoalQAReady | GoalQAFixing            -- qa / ready|fixing
  | GoalAcceptanceReady                  -- acceptance / ready
  | GoalComplete                         -- complete / passed；优先于残留 driver 元数据
  | GoalHandoffBlocked Reason            -- handoff / blocked；优先于残留 driver 元数据
  | GoalUnknown Text

data FeatureState = FeatureState          -- 从 feature 目录及 parent roadmap items / goal-state 恢复
  { featureDir         : Maybe Path
  , executionLane      : Maybe ExecutionLane
  , designStatus       : Missing | Draft | Approved
  , designReviewStatus : DesignReviewStatus
  , quickRunState      : QuickRunState
  , standardRunState   : StandardRunState
  , goalRunState       : GoalRunState
  , roadmapOwner       : Maybe EpicOwnership
  , epicChildBatch     : Bool             -- cs-epic 批量上下文，非公开参数
  }

data FeatureOutcome
  = RoutedTo Stage
  | HumanCheckpoint CheckpointReason
  | DispatchGoalDriver Command            -- 先尝试可见 Task agent；失败才降级为 GoalHandoff
  | GoalHandoff Command                   -- 可粘贴 `/goal` 或 driver handoff
  | ReportDriver DriverInfo               -- 已有可见 driver：只汇报，不重复派发
  | Completed FeatureSummary
  | NeedsHuman Reason

data CheckpointReason = ConfirmDesign | ConfirmScopeChange
```

`restoreFeatureStage` 从仓库事实选下一步（**must not auto-approve design**：design-review passed 后必须停等用户确认）：

```haskell
restoreFeatureStage :: FeatureState -> EntryIntent -> FeatureOutcome
restoreFeatureStage(s, intent)
  | ambiguousTarget(s, intent)                     -> NeedsHuman "which feature?"
  | changesApprovedScope(s, intent)                -> HumanCheckpoint ConfirmScopeChange
  | lane == Quick && s.quickRunState == QuickImplementationPending -> RoutedTo FastForward
  | lane == Quick && s.quickRunState == QuickReviewReady           -> RoutedTo CodeReview
  | lane == Quick && s.quickRunState == QuickReviewFixing          -> RoutedTo FastForward
  | lane == Quick && s.quickRunState == QuickComplete               -> Completed summary
  | s.designStatus == Missing                      -> RoutedTo Design
  | s.designStatus == Approved && s.designReviewStatus /= ReviewPassed
      -> NeedsHuman "approved design lacks passed design-review"
  | s.designReviewStatus in [ChangesRequested, ReviewBlocked] -> RoutedTo Design
  | s.designStatus == Draft && s.designReviewStatus == ReviewMissing -> RoutedTo DesignReview
  | hasRoadmapOwner(s) && s.designReviewStatus == ReviewPassed -> RoutedTo <return-to-cs-epic>
  | s.designReviewStatus == ReviewPassed && s.designStatus /= Approved
      -> if s.epicChildBatch then RoutedTo <return-to-cs-epic> else HumanCheckpoint ConfirmDesign
  | lane == Standard && s.standardRunState == StandardImplementationPending -> RoutedTo Implementation
  | lane == Standard && s.standardRunState == StandardReviewReady           -> RoutedTo CodeReview
  | lane == Standard && s.standardRunState == StandardReviewFixing          -> RoutedTo Implementation
  | lane == Standard && s.standardRunState == StandardAcceptanceReady       -> RoutedTo Acceptance
  | lane == Standard && s.standardRunState == StandardComplete              -> Completed summary
  | lane == Goal && s.goalRunState == GoalMissing -> RoutedTo GoalPackage
  | lane == Goal && s.goalRunState == GoalComplete              -> Completed summary
  | lane == Goal && s.goalRunState is GoalHandoffBlocked reason -> GoalHandoff (handoffCommand reason)
  | lane == Goal && s.goalRunState is GoalDriverActive driver   -> ReportDriver driver
  | lane == Goal && s.goalRunState == GoalReadyToDispatch       -> DispatchGoalDriver "/goal"
  | lane == Goal && s.goalRunState == GoalImplementationRunning -> RoutedTo Implementation
  | lane == Goal && s.goalRunState == GoalReviewReady           -> RoutedTo CodeReview
  | lane == Goal && s.goalRunState == GoalReviewFixing          -> RoutedTo Implementation
  | lane == Goal && s.goalRunState == GoalQAReady               -> RoutedTo QA
  | lane == Goal && s.goalRunState == GoalQAFixing              -> RoutedTo Implementation
  | lane == Goal && s.goalRunState == GoalAcceptanceReady       -> RoutedTo Acceptance
  | lane == Goal && s.goalRunState is GoalUnknown raw           -> NeedsHuman ("unknown goal-state: " <> raw)
  where lane = classifyExecutionLane(s, intent)
```

QuickRunState 从 `{slug}-ff-note.md` 和 `{slug}-review.md` 恢复：无 ff-note→FastForward，review 缺失/blocked→code review，changes-requested→Quick review-fix，有独立 reviewer 锚点的 passed→complete。StandardRunState 从 checklist、review、可选 QA 和 acceptance 恢复；failed/blocked QA 先 qa-fix，passed review 必须有独立 reviewer 锚点。旧 design 缺 `execution_lane` 且没有 goal state 时按 Standard；已有 goal state 始终按 Goal。

## Workflow

主执行主线（每次调用按序走；各 stage "怎么做" 的厚规则见对应 protocol，本节只定顺序与边界）：

```haskell
workflow :: FeatureRequest -> FeatureOutcome
workflow = preflight >=> parseEntryIntent >=> restoreFeatureStage
       >=> loadStageProtocol >=> executeOrRoute >=> exitRecoverable

preflight           -- 读 .codestable/attention.md；缺失 -> route to cs-onboard；不得用 AGENTS.md/CLAUDE.md 代替
parseEntryIntent    -- flag > compat-preset > utterance；repoFacts override requestedStage；空参不推断 stage
restoreFeatureStage -- 扫 .codestable/features/ + artifact + git diff 恢复 FeatureState，选 next stage（见 Spec）
loadStageProtocol   -- stageProtocol 映射（见下节）；进 stage 才加载该 stage 一个 protocol
executeOrRoute      -- authoring stage（design/design-review/goal-package）落盘 artifact；
                    -- DispatchGoalDriver 先尝试可见 driver，失败才输出 GoalHandoff；遇 HumanCheckpoint 必停
exitRecoverable     -- artifact 已落盘 / next stage 明确 / checkpoint reason 明确，任一即可让下次调用从 repoFacts 恢复
```

## 文件放哪儿

```text
.codestable/features/{YYYY-MM-DD}-{slug}/
├── {slug}-design.md / {slug}-checklist.yaml
├── {slug}-design-review.md
├── goal-plan.md / goal-state.yaml / goal-protocol.md  # 仅 Goal
├── {slug}-review.md / {slug}-acceptance.md
├── {slug}-qa.md                                      # Goal 或用户显式要求
└── {slug}-ff-note.md          # 仅 fastforward
```

目录命名取首次创建当天，slug 小写字母/数字/连字符。feature 过程发现的 bug 另开 issue，不在 feature 里偷修。

## Progressive Reference Loading

```haskell
stageProtocol :: Stage -> Protocol
stageProtocol Design         = "references/design/protocol.md"          -- 必要时 support/intent-template.md、codebase-design.md
stageProtocol DesignReview   = "references/design-review/protocol.md"   -- gate 纪律见下
stageProtocol GoalPackage    = "references/goal/protocol.md"
stageProtocol Implementation = "references/implementation/protocol.md"  -- 必要时 support/reference.md、tdd.md
stageProtocol CodeReview     = skill "cs-code-review"                   -- 公开横切 skill
stageProtocol QA             = "references/qa/protocol.md"
stageProtocol Acceptance     = "references/acceptance/protocol.md"
stageProtocol FastForward    = "references/fastforward/protocol.md"

-- 惰性加载（progressive reference loading）：进入某阶段才加载该阶段一个 protocol，不在启动时读全部
-- 禁止：启动即读全部 references；用 implementation 协议做 design；code review 未过就进 QA
```

design-review 首轮和实质变化后的复审必须使用独立 Task agent reviewer；只改文字、编号、链接、格式或不改变契约的映射时走 focused closure，不启动新 reviewer。无法确定是否实质变化时完整独立复审，细则见 protocol。

## Human Checkpoints

触发时机以 Spec 的 `restoreFeatureStage` 为唯一权威；本节只定义停下后的行为：

```haskell
onCheckpoint :: CheckpointReason -> Action
onCheckpoint ConfirmDesign          = 停等用户对 design 整体确认   -- must not auto-approve design，不得直接进 GoalPackage
onCheckpoint ConfirmScopeChange     = 停等用户确认范围变更
  -- 仅长程执行中（design 已 approved 后）要改 approved design、feature 范围或公开契约时触发；
  -- 入口阶段的 fastforward 不合格 / 大范围需求不触发本 checkpoint，直接 RoutedTo Design
```

Goal lane 的 implementation / code review / QA / acceptance 阻塞由 goal driver 按协议循环修复。Standard 在当前 run 继续，review passed 后直接进入带 Inline Verification Matrix 的 acceptance；独立 QA 报告不是默认阶段。
driver 不可见、派发失败或 driver 返回 handoff 时走 `GoalHandoff`，不是 `HumanCheckpoint` / `NeedsHuman` 的第二种写法。

## Failure Behavior

```haskell
needsHuman :: Situation -> Bool
needsHuman s = attentionMissing s        -- .codestable/attention.md 缺失 -> 先 cs-onboard
            || noRecoverableFeature s    -- 无可恢复 feature 目标
            || ambiguousScope s          -- feature 范围模糊
            || stageConflictsRepoFacts s -- requested stage 与仓库事实冲突
            || invalidArtifactState s    -- 例如 approved design 没有 passed design-review
            || unknownGoalState s        -- goal-state.yaml stage/status 无法识别
```

报告：当前 feature 目录、阻塞原因、下一步用户动作、已写文件、是否可安全重试。

## Output Contract

```haskell
mustContinue (RoutedTo _)            = True
mustContinue (DispatchGoalDriver _)  = True
mustStop     (HumanCheckpoint _)     = True
mustStop     (GoalHandoff _)         = True
mustStop     (NeedsHuman _)          = True
mustStop     (ReportDriver _)        = True
mustStop     (Completed _)           = True
```

退出或交接时必须报告：feature 目录、`executionLane`、对应 run state、本轮写入文件、下一动作或 checkpoint、已运行验证。Goal 的 `DispatchGoalDriver` 不得直接退化成 `/goal`：先按 agent conventions 尝试可见 driver，只有不可用或派发失败才输出 `GoalHandoff`。

完成 marker：Quick 为 `CS_FEATURE_QUICK_COMPLETE`，Standard 为 `CS_FEATURE_STANDARD_COMPLETE`，Goal 为 `CS_FEATURE_GOAL_COMPLETE`；Standard 的 accept-inline 模式通过公开入口 `cs-feat --stage accept` 进入。

## Quick / Fastforward

Quick 默认按任务事实自动选择；`requested_mode: quick|fastforward` 只是显式偏好，不是跳过安全的许可。不合格则解释命中的风险条件并进入 Standard design。新 Quick 的业务产物只有 `{slug}-ff-note.md`；从已有 design 降级时保留历史 design 并记录 `execution_lane: quick`，不再维护 checklist/QA/acceptance，但已存在的 QA/acceptance 只有 `passed` 可兼容保留，其他状态必须先解决冲突。横切 review 仍写 `{slug}-review.md`。`cs-feat-ff` 是兼容入口。

## Epic 子 Feature 批量上下文

`cs-epic` 批量生成子 feature design 时以内部上下文 `epicChildBatch: true` 调用；该上下文强制 Goal lane，并表示 CONTEXT / adrs / compound 已由 `cs-epic` 统一加载，design 阶段不重复读取这些全局输入。design-review passed 后 design 保持 `draft`，不执行单 feature 的人工整体 review checkpoint；不在这里停，回到 `cs-epic` 继续下一个子 feature，最终由 Epic 批量确认。不得用 final answer 要用户确认单个 child。恢复 child 时，design 的 `roadmap` / `roadmap_item` 必须同时为空或成对存在；成对 metadata 经 parent `items.yaml` 唯一条目及其 `feature` 指针证明，或 parent items 按同一指针/精确目录 slug、roadmap goal-state 按 `features[].feature_dir` 反向唯一认领当前目录时，即使没有 batch flag 也必须交回 `cs-epic`；错误 items/goal-state 结构或路径、forward/reverse 不一致、任意第二 claim 都 fail-closed。退出前运行 `codestable-workflow-next.py feature --epic-child-batch`，按 `next_action` 交回 `cs-epic`。

## 兼容入口

旧阶段技能保留为兼容入口（`cs-feat-design`、`cs-feat-design-review`、`cs-feat-impl`、`cs-feat-qa`、`cs-feat-accept`、`cs-feat-ff`）：只传入 `requested_stage` / `requested_mode`，不维护独立规则。新文档与新调用一律用 `--stage` / `--mode`。

## 退出条件

```haskell
mayExit :: State -> Bool
mayExit s = artifactPersistedAndRecoverable s   -- 当前阶段产物已落盘，状态可由 restoreFeatureStage 从仓库事实恢复
         && nextClearlyStated s                 -- 阻塞项、HumanCheckpoint 或下一阶段已明确说明

fullyDone :: FeatureState -> Bool
fullyDone s = case executionLane s of
  Quick    -> ffNoteWritten s && reviewPassed s
  Standard -> designApproved s && reviewPassed s && acceptancePassed s
  Goal     -> designApproved s && reviewPassed s && qaPassed s && acceptancePassed s
```

需要外部文档提示 `cs-docs`；阶段收尾/记忆同步提示 `cs-docs-neat`。

## 相关入口

- `cs-code-review`：实现后横切只读审查 gate。
- `cs-issue` / `cs-refactor` / `cs-docs` / `cs-epic` / `cs-docs-neat`。
