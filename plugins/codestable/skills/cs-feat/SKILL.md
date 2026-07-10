---
name: cs-feat
description: "Feature 主入口。用于新功能或功能改造，从需求恢复并推进 design、design-review、goal package、implementation、code review、QA、acceptance。不要用于单纯 bug 修复(cs-issue)、行为等价重构(cs-refactor)、对外文档(cs-docs)、大需求拆解(cs-epic)。"
argument-hint: "[--stage design|design-review|impl|qa|accept|goal-package] [--mode fastforward] <feature>"
contracts:
  - grep: "restoreFeatureStage"
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

`cs-feat` 是 feature 的唯一推荐入口，是一个 workflow skill：从仓库事实恢复当前阶段、加载对应阶段协议、在人工 checkpoint 停下。用户只需持续调用本技能；本技能在 design gate 停下来等用户确认。确认 design 后默认生成单 feature goal 包，并尝试通过可见 Task agent goal driver 长程执行；派发失败则打印 `/goal` 指令让用户粘贴执行。真正的 design/QA/acceptance 怎么做由各阶段 protocol 负责（见下方 Progressive Reference Loading）。

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
| `--mode fastforward` | `requested_mode: fastforward` |

入口意图只是偏好；**仓库事实优先**（`restoreFeatureStage`），也优先于聊天历史。

无参数默认行为：没有 flag / 需求描述时，不猜阶段；扫描 `.codestable/features/`、目标产物与当前 git diff，用状态机恢复下一步。没有可恢复 feature 且用户原话也无新功能目标时，返回 `NeedsHuman` 问处理哪个 feature。

## Spec

```haskell
csFeat :: FeatureRequest -> FeatureOutcome

data FeatureRequest = FeatureRequest
  { requestedStage : Maybe Stage
  , requestedMode  : Maybe Mode          -- fastforward
  , userGoal       : Maybe Text
  , repoFacts      : RepoFacts           -- 优先于 args / 聊天历史
  }

data Stage = Design | DesignReview | GoalPackage | Implementation | CodeReview | QA | Acceptance | FastForward

data DesignReviewStatus = ReviewMissing | ReviewPassed | ChangesRequested | ReviewBlocked

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

data FeatureState = FeatureState          -- 全部从 .codestable/features/{slug}/ 恢复
  { featureDir         : Maybe Path
  , designStatus       : Missing | Draft | Approved
  , designReviewStatus : DesignReviewStatus
  , goalRunState       : GoalRunState
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
  | wantsFastForward(intent) && ffEligible(s)      -> RoutedTo FastForward
  | wantsFastForward(intent) && not ffEligible(s)  -> RoutedTo Design            -- 不合格（含跨公开契约/大范围）：结果是 RoutedTo Design（不是 NeedsHuman、不是 checkpoint），在推进 design 的同时说明降级原因
  | s.designStatus == Missing                      -> RoutedTo Design
  | s.designStatus == Approved && s.designReviewStatus /= ReviewPassed
      -> NeedsHuman "approved design lacks passed design-review"
  | s.designReviewStatus in [ChangesRequested, ReviewBlocked] -> RoutedTo Design
  | s.designStatus == Draft && s.designReviewStatus == ReviewMissing -> RoutedTo DesignReview
  | s.designReviewStatus == ReviewPassed && s.designStatus /= Approved
      -> if s.epicChildBatch then RoutedTo <return-to-cs-epic> else HumanCheckpoint ConfirmDesign
  | s.goalRunState == GoalMissing                  -> RoutedTo GoalPackage
  | s.goalRunState == GoalComplete                 -> Completed summary
  | s.goalRunState is GoalHandoffBlocked reason    -> GoalHandoff (handoffCommand reason)
  | s.goalRunState is GoalDriverActive driver      -> ReportDriver driver
  | s.goalRunState == GoalReadyToDispatch          -> DispatchGoalDriver "/goal"
  | s.goalRunState == GoalImplementationRunning    -> RoutedTo Implementation
  | s.goalRunState == GoalReviewReady              -> RoutedTo CodeReview
  | s.goalRunState == GoalReviewFixing             -> RoutedTo Implementation   -- review-fix
  | s.goalRunState == GoalQAReady                  -> RoutedTo QA
  | s.goalRunState == GoalQAFixing                 -> RoutedTo Implementation   -- qa-fix，修完重跑 review+QA
  | s.goalRunState == GoalAcceptanceReady          -> RoutedTo Acceptance
  | s.goalRunState is GoalUnknown raw              -> NeedsHuman ("unknown goal-state: " <> raw)
```

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
├── goal-plan.md / goal-state.yaml / goal-protocol.md
├── {slug}-review.md / {slug}-qa.md / {slug}-acceptance.md
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

design-review **gate 必需独立 Task agent reviewer**：主 agent 本地审查不得定稿 review、不得给 `passed`；design 修订后的**每一轮重审同样适用**（round 2+ 不得以"本地重审"代替），降级须 approval-report + 用户明确授权（细则见 protocol）。

## Human Checkpoints

触发时机以 Spec 的 `restoreFeatureStage` 为唯一权威；本节只定义停下后的行为：

```haskell
onCheckpoint :: CheckpointReason -> Action
onCheckpoint ConfirmDesign          = 停等用户对 design 整体确认   -- must not auto-approve design，不得直接进 GoalPackage
onCheckpoint ConfirmScopeChange     = 停等用户确认范围变更
  -- 仅长程执行中（design 已 approved 后）要改 approved design、feature 范围或公开契约时触发；
  -- 入口阶段的 fastforward 不合格 / 大范围需求不触发本 checkpoint，直接 RoutedTo Design
```

implementation / code review / QA / acceptance 的普通阻塞优先由 goal driver 按协议循环修复，不在每个阶段默认打断用户。
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

退出或交接时必须报告：feature 目录、恢复出的 `goalRunState`、本轮写入文件、下一动作或 checkpoint、已运行验证。`DispatchGoalDriver` 不得直接退化成 `/goal`：先按 agent conventions 尝试可见 driver，只有不可用或派发失败才输出 `GoalHandoff`。

## Fastforward

`requested_mode: fastforward` 只是模式请求，不是跳过安全的许可。进入前确认范围小、需求清楚、无跨系统术语/契约风险；不合格则解释原因并回标准 design 流程。产物固定 `{slug}-ff-note.md`，不生成标准 design/checklist/QA/acceptance 套件。`cs-feat-ff` 是兼容入口，不再单独维护快速模式规则。

## Epic 子 Feature 批量上下文

`cs-epic` 批量生成子 feature design 时以内部上下文 `epicChildBatch: true` 调用（非公开参数，不写入 argument-hint）。**该上下文还表示 CONTEXT / adrs / compound 等全局输入已由 `cs-epic` 在批量开始时统一加载，design 阶段复用、不重复读取这些全局输入**（幂等，省掉 N 个子 feature 各扫一遍）。此时：design-review passed 后 design 保持 `draft`、**不执行单 feature 的人工整体 review checkpoint**、不改 approved；design-review passed 但未 approved 时**不在这里停，回到 `cs-epic` 继续下一个子 feature**，等所有 design 统一确认；回写 design/checklist/design-review/items.yaml 后返回 `cs-epic`，**不得用 final answer 要用户确认单个 child**；退出前运行 `python3 <cs-onboard skill 目录>/tools/codestable-workflow-next.py feature --feature .codestable/features/YYYY-MM-DD-{slug} --epic-child-batch --json`，若输出 `final_answer_allowed: false` 按 `next_action` 交回 `cs-epic`。单独调用 `cs-feat` 或无该上下文时，仍按普通 checkpoint 停。

## 兼容入口

旧阶段技能保留为兼容入口（`cs-feat-design`、`cs-feat-design-review`、`cs-feat-impl`、`cs-feat-qa`、`cs-feat-accept`、`cs-feat-ff`）：只传入 `requested_stage` / `requested_mode`，不维护独立规则。新文档与新调用一律用 `--stage` / `--mode`。

## 退出条件

```haskell
mayExit :: State -> Bool
mayExit s = artifactPersistedAndRecoverable s   -- 当前阶段产物已落盘，状态可由 restoreFeatureStage 从仓库事实恢复
         && nextClearlyStated s                 -- 阻塞项、HumanCheckpoint 或下一阶段已明确说明

fullyDone :: FeatureState -> Bool               -- 标准流程最终门槛
fullyDone s = designApproved s && reviewPassed s && qaPassed s && acceptancePassed s
```

需要外部文档提示 `cs-docs`；阶段收尾/记忆同步提示 `cs-docs-neat`。

## 相关入口

- `cs-code-review`：实现后横切只读审查 gate。
- `cs-issue` / `cs-refactor` / `cs-docs` / `cs-epic` / `cs-docs-neat`。
