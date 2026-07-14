---
name: cs-refactor
description: "Refactor 主入口。触发：优化/重构/拆分/性能/代码太长，且不改变行为、不新增需求。不要用于新增功能(cs-feat)、修复 bug(cs-issue)、对外文档(cs-docs)、大需求拆解(cs-epic)。"
argument-hint: "[--stage scan|design|apply] [--mode standard|fastforward] <target>"
contracts:
  - grep: "restoreRefactorStage"
  - grep: "progressive reference loading"
  - grep: "行为等价"
  - not-grep: "git push"
  - not-grep: "read all references"
---

# cs-refactor

## 启动必读

动作前先跑 CodeStable preflight：读 `.codestable/attention.md`（缺失先 `cs-onboard`）；不要用 `AGENTS.md`/`CLAUDE.md` 等外部入口代替它；细则见 `.codestable/reference/execution-conventions.md`。

`cs-refactor` 是重构的唯一推荐入口。它统一判定标准模式和 fastforward 模式，核心底线是行为等价：一旦会改变外部可观察行为，就转 `cs-feat` 或 `cs-issue`。

`cs-refactor-ff` 长期保留为兼容入口，只传入 `requested_mode: fastforward`。

---

## 入口意图

本次调用参数：$ARGUMENTS

意图来源按优先级：调用参数 flag > 兼容入口预设 > 用户话术。参数为空或未被替换（仍是字面 `$ARGUMENTS`）时跳过该来源；调用参数用 `--stage <stage>` 表示阶段意图，用 `--mode <mode>` 表示执行模式，其余文本作为重构目标。

| 参数 | 入口意图 |
|---|---|
| `--stage scan` | `requested_stage: scan` |
| `--stage design` | `requested_stage: design` |
| `--stage apply` | `requested_stage: apply` |
| `--mode standard` | `requested_mode: standard` |
| `--mode fastforward` | `requested_mode: fastforward` |

旧裸 token（如 `ff`、`scan`）只作为历史提示词兼容识别；新文档和新调用一律用 `--stage` / `--mode`。

无参数默认行为：没有 flag / 目标描述时，先按 `.codestable/refactors/`、scan/design/checklist/apply-notes 和当前 git diff 恢复；若没有可恢复重构且用户原话也没有目标，先问用户要优化哪个范围。

入口意图只是偏好。仓库事实优先：已有 scan/design/checklist/apply-notes 时按真实状态续跑。

---

## Spec

```haskell
csRefactor :: RefactorRequest -> RefactorOutcome

data RefactorRequest = RefactorRequest
  { requestedStage : Maybe Stage         -- scan | design | apply
  , requestedMode  : Maybe Mode          -- standard | fastforward
  , userGoal       : Maybe Text
  , repoFacts      : RepoFacts           -- 优先于 args / 聊天历史
  }

data Stage = Scan | Design | Apply | CodeReview
data Mode  = Standard | Fastforward
data RouteTarget = StandardStage Stage | FastforwardStage Stage | ExternalSkill SkillName
data DesignStatus = Draft | Approved
data ReviewStatus = Missing | Passed | Blocking
data VerificationOwner = AIVerification | HumanVerification
data StepState
  = NoCurrentStep | PendingApply StepId VerificationOwner
  | AppliedAwaitingHuman StepId | StepVerified StepId
data FastforwardStatus = FastforwardInactive | FastforwardActive | FastforwardSwitchRequired | FastforwardComplete

data RefactorState = RefactorState       -- 全部从 .codestable/refactors/{slug}/ 恢复
  { refactorDir    : Maybe Path
  , mode           : Mode
  , hasScan        : Bool
  , scanSelected   : Bool                -- 用户已勾选 ✓/✗
  , hasDesign      : Bool
  , designStatus   : DesignStatus        -- {slug}-refactor-design.md 的 status
  , hasChecklist   : Bool                -- {slug}-checklist.yaml
  , currentStep    : StepState           -- checklist + apply-notes 恢复；只有 AppliedAwaitingHuman 才停
  , applyDone      : Bool                -- apply-notes 每步验证齐
  , fullVerificationPassed : Bool
  , finalValidationPending : Bool
  , reviewStatus   : ReviewStatus
  , fastforwardStatus : FastforwardStatus -- {slug}-ff-state.yaml
  }

data RefactorOutcome
  = RoutedTo RouteTarget
  | HumanCheckpoint CheckpointReason
  | Completed RefactorSummary
  | NeedsHuman Reason
  | Blocked Reason

data CheckpointReason
  = ScanSelection            -- scan 产物待用户勾选
  | DesignConfirmation       -- design 整体待用户 review 放行
  | HumanValidation StepId   -- 该步已应用，HUMAN 验证待确认
  | FinalValidation          -- 全量验证和 code review 后的最终人工确认
  | ConfirmMethodAndScope    -- fastforward 对齐
  | ConfirmEffect            -- fastforward 完成效果确认
  | PartialChangeDisposition -- fastforward 退回 standard 时处理本轮部分改动

data CheckpointAnswer = ApproveCheckpoint | RejectCheckpoint | ReviseCheckpoint
resumeCheckpoint :: RefactorState -> CheckpointAnswer -> RefactorState
resumeCheckpoint s answer = persistApprovalAnswer s answer
```

`restoreRefactorStage` 从仓库事实选下一步（一旦会改外部可观察行为 → 转 `cs-feat` 新需求或 `cs-issue` 修 bug，行为等价是底线）：

```haskell
restoreRefactorStage :: RefactorState -> EntryIntent -> RefactorOutcome
restoreRefactorStage(s, intent)
  | changesBehavior intent                            -> RoutedTo (ExternalSkill (behaviorRoute intent))
  | s.mode == Fastforward && s.fastforwardStatus == FastforwardComplete
                                                       -> Completed summary
  | s.mode == Fastforward && s.fastforwardStatus == FastforwardSwitchRequired
                                                       -> RoutedTo (StandardStage Scan)
  | s.mode == Fastforward && smallSafe s              -> RoutedTo (FastforwardStage Apply)
  | s.mode == Fastforward                              -> RoutedTo (StandardStage Scan)
  | not s.hasScan                                     -> RoutedTo (StandardStage Scan)
  | s.hasScan && not s.scanSelected                  -> HumanCheckpoint ScanSelection
  | s.scanSelected && not s.hasDesign                -> RoutedTo (StandardStage Design)
  | s.hasDesign && s.designStatus == Draft           -> HumanCheckpoint DesignConfirmation
  | AppliedAwaitingHuman step <- s.currentStep        -> HumanCheckpoint (HumanValidation step)
  | s.designStatus == Approved && not s.applyDone    -> RoutedTo (StandardStage Apply)
  | s.applyDone && not s.fullVerificationPassed      -> RoutedTo (StandardStage Apply)
  | s.applyDone && s.reviewStatus == Missing         -> RoutedTo (StandardStage CodeReview)
  | s.reviewStatus == Blocking                       -> RoutedTo (StandardStage Apply)
  | s.reviewStatus == Passed && s.finalValidationPending
                                                       -> HumanCheckpoint FinalValidation
  | s.reviewStatus == Passed                         -> Completed summary
  | otherwise                                        -> Blocked InvalidRefactorState
```

## Workflow

主执行主线（每次调用按序走；各 stage "怎么做" 的厚规则见对应 protocol，本节只定顺序与边界）：

```haskell
workflow :: RefactorRequest -> RefactorOutcome
workflow = preflight >=> parseEntryIntent >=> restoreRefactorStage
       >=> loadStageProtocol >=> executeOrRoute >=> exitRecoverable

preflight            -- 读 .codestable/attention.md；缺失 -> route to cs-onboard；不得用 AGENTS.md/CLAUDE.md 代替
parseEntryIntent     -- flag > compat-preset > utterance；repoFacts override requestedStage/requestedMode；空参不推断 stage
restoreRefactorStage -- 扫 .codestable/refactors/ + scan/design/checklist/apply-notes + git diff 恢复 RefactorState，
                     -- 选 next stage（见 Spec）；会改外部可观察行为 -> route to cs-feat 或 cs-issue
loadStageProtocol    -- 「Reference 加载」映射（见下节）；进 stage 才加载该 stage 所需文件
executeOrRoute       -- scan 落盘清单待勾选；design 起草+抽 checklist 待整体放行；
                     -- apply 逐条改+验证+记 apply-notes；遇 HumanCheckpoint 必停
exitRecoverable      -- apply-notes 每步验证齐、design status: approved、next stage 或 checkpoint reason 明确；
                     -- 不夹带 feature / issue 改动
```

---

## 文件放哪儿

```text
.codestable/refactors/{YYYY-MM-DD}-{slug}/
├── {slug}-scan.md
├── {slug}-refactor-design.md
├── {slug}-checklist.yaml
└── {slug}-apply-notes.md
```

fastforward 不生成 scan / design / checklist，但始终写
`.codestable/refactors/{YYYY-MM-DD}-{slug}/{slug}-ff-state.yaml` 保存 scope、method、approval、验证、
review 和 completion 状态；用户要求留人读记录时再加 `{slug}-refactor-note.md`。

---

## 模式选择

启动后先确认用户诉求是否真是行为不变的重构，再检查范围和测试自证能力。

标准模式读取 `references/standard/protocol.md`，流程是：

```text
scan → 用户勾选 → design → 用户确认 → apply → cs-code-review
```

fastforward 模式读取 `references/fastforward/protocol.md`。必须同时满足：

1. 行为真的不变，没有“顺便支持 X / 改成 Y”。
2. 范围小：单函数/单组件/少量动点，不跨模块。
3. 有测试、类型检查或等价证据能自证。

任何一条不满足，回标准模式；不能因为用户说“快点”就跳过安全边界。

---

## Reference 加载

```haskell
modeProtocol :: Mode -> Protocol
modeProtocol Standard    = "references/standard/protocol.md"
modeProtocol Fastforward = "references/fastforward/protocol.md"

stageSupport :: Stage -> [Support]
stageSupport Scan       = [ "references/library/methods.md"                 -- 方法库，scan 时才全量加载
                          , "references/library/methods-l4.md"
                          , "references/library/methods-architecture.md"
                          , "references/library/scan-checklist-format.md"   -- scan 格式
                          , "references/library/refusal-routing.md" ]       -- 拒绝路由
stageSupport CodeReview = [ skill "cs-code-review" ]                        -- 公开横切技能
stageSupport _          = []

-- 惰性加载（progressive reference loading）：按阶段加载，进 stage 才读该 stage 所需文件，不在启动时读全部
```

---

## 人工 checkpoint

触发时机以 Spec 的 `restoreRefactorStage` 为唯一权威；本节只定义停下后的行为：

```haskell
onCheckpoint :: CheckpointReason -> Action
onCheckpoint ScanSelection      = 停等用户勾选 scan 产物       -- AI 不替用户勾选
onCheckpoint DesignConfirmation = 停等用户整体 review design   -- 放行后才进入 apply
onCheckpoint (HumanValidation step) = 停等用户验证已应用的 step
onCheckpoint FinalValidation        = 停等用户做最终整体确认
onCheckpoint ConfirmMethodAndScope  = 停等用户批准 ff 方法与范围
onCheckpoint ConfirmEffect          = 停等用户确认 ff 结果
onCheckpoint PartialChangeDisposition = 停等用户选择保留 / 暂存 / 丢弃本轮部分改动
```

每个 checkpoint 的候选 artifact / state 和 pending approval 必须先落盘；owner 回答后先更新状态再
调用 `resumeCheckpoint`。apply 完成后进入 `cs-code-review`；blocking 未清零、important 未处理或未被明确接受时不提交。

---

## Failure Behavior

```haskell
needsHuman :: Situation -> Bool
needsHuman s = attentionMissing s          -- .codestable/attention.md 缺失 -> 先 cs-onboard
            || noRecoverableRefactor s     -- 无可恢复重构目标
            || ambiguousScope s            -- 重构范围模糊
            || stageConflictsRepoFacts s   -- requested stage 与仓库事实冲突
            || changesBehavior s           -- 诉求其实会改外部可观察行为 -> cs-feat 或 cs-issue
            || ffTurnedComplex s           -- fastforward 途中发现变复杂需切回标准模式
```

报告：当前产物（scan/design/checklist/apply-notes）、阻塞原因、下一步用户动作、已写文件、是否可安全重试。

## 退出条件

```haskell
mayExit :: State -> Bool
mayExit s
  | s.mode == Standard    = scanSelected s && designApproved s
                         && applyNotesEachStepVerified s && testsPassed s && reviewPassed s
                         && finalValidationSettled s
  | s.mode == Fastforward = s.fastforwardStatus == FastforwardComplete
                         && testsPassed s && reviewPassed s && effectConfirmed s
```

不夹带 feature 或 issue 改动。
