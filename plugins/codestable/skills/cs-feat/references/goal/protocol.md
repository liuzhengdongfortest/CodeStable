# Feature Goal Package Protocol

## 目标

把一个已通过 design-review、并由用户确认的单个 feature 变成可恢复、可长程执行的 goal 包。

## Spec

```haskell
data GoalState
  = ReadyToDispatch | ImplementationRunning | ReviewReady | ReviewFixing
  | QAReady | QAFixing | AcceptanceReady | Complete | Handoff Reason
data GoalEvent
  = DriverStarted | ImplementationPassed | ReviewPassed | ReviewFailed | ReviewFixed
  | QAPassed | QAFailed | QAFixed | AcceptancePassed | NeedsHandoff Reason
data AuthorizationState = AuthorizationMissing | AuthorizationApproved ApprovalRef | AuthorizationRejected
data PackageOutcome = PackageBlocked Reason | HumanCheckpoint Reason | GoalHandoff Reason | PersistGoalAuthorization AuthorizationState | WriteGoalPackage | DispatchOrPrintLiteralGoal
data TransitionResult = Next GoalState | Reject GoalState GoalEvent

transition :: GoalState -> GoalEvent -> TransitionResult
transition Complete event                   = Reject Complete event
transition (Handoff reason) event           = Reject (Handoff reason) event
transition _ (NeedsHandoff reason)          = Next (Handoff reason)
transition ReadyToDispatch DriverStarted    = Next ImplementationRunning
transition ImplementationRunning ImplementationPassed = Next ReviewReady
transition ReviewReady ReviewFailed         = Next ReviewFixing
transition ReviewFixing ReviewFixed         = Next ReviewReady
transition ReviewReady ReviewPassed         = Next QAReady
transition QAReady QAFailed                 = Next QAFixing
transition QAFixing QAFixed                 = Next ReviewReady
transition QAReady QAPassed                 = Next AcceptanceReady
transition AcceptanceReady AcceptancePassed = Next Complete
transition state event                      = Reject state event

resumeGoalAuthorization :: ResumeInput -> GoalPackageState -> PackageOutcome
resumeGoalAuthorization (AuthorizeGoalAcceptance ref) s
  | approvalArtifactApproved s ref "goal-acceptance" = PersistGoalAuthorization (AuthorizationApproved ref)
  | otherwise                                         = PackageBlocked InvalidGoalAcceptanceApprovalRef
resumeGoalAuthorization RejectCheckpoint _            = PersistGoalAuthorization AuthorizationRejected
resumeGoalAuthorization _ _                           = PackageBlocked InvalidGoalAuthorizationResume

buildPackage :: GoalPackageState -> PackageOutcome
buildPackage s
  | not (designApproved s && designReviewPassed s) = PackageBlocked DesignGateNotPassed
  | goalAcceptanceRejected s                       = GoalHandoff GoalAcceptanceAuthorizationRejected
  | not (goalAcceptanceAuthorized s)               = HumanCheckpoint ConfirmGoalAcceptanceAuthorization
  | not (goalFilesPersisted s)                     = WriteGoalPackage
  | otherwise                                      = DispatchOrPrintLiteralGoal
```

每次 event 后立即持久化 `Next`；`Reject` 进入 handoff，不静默吞掉非法跃迁。driver 中断时以仓库产物校正 state，再从该状态恢复。
`PersistGoalAuthorization` 先更新同 feature 的 `approval-report.md` 命名决策，再写 goal-state；goal-state 尚未创建时由随后 `WriteGoalPackage` 复制 status/ref。拒绝必须写 rejected 并 handoff，不能回到授权 checkpoint。

---

## 目录

在 feature 目录下新增：

```text
.codestable/features/YYYY-MM-DD-{slug}/
├── {slug}-design.md
├── {slug}-checklist.yaml
├── {slug}-design-review.md
├── goal-plan.md
├── goal-state.yaml
├── goal-protocol.md
├── {slug}-review.md
├── {slug}-qa.md
└── {slug}-acceptance.md
```

---

## 生成文件

`goal-plan.md` 必须包含：

- feature、design、checklist、design-review 路径
- 用户已确认 design 的时间和依据
- owner 对 Goal 最终 acceptance 的独立授权及 `approval-report.md` 引用；确认 design 本身不等于该授权
- 必跑验证命令
- implementation TDD policy：代码行为 step 默认 RED → GREEN → VERIFY，例外必须写 `TDD exception`
- 核心验收路径；非功能性 feature 写替代证据
- DoD / gate policy 摘要
- handoff 条件

`goal-state.yaml`：

```yaml
feature: "{slug}"
status: ready-to-dispatch
baseline_ref: "{git rev-parse HEAD 或 no-git}"
stage: implementation
driver_kind: none            # host-agent|none，派发成功后写回
driver_id: ""
acceptance_authorization: approved # approved|rejected；缺失时不得派发
acceptance_authorization_ref: "approval-report.md#goal-acceptance"
handoff_reason: ""           # stage=handoff/status=blocked 时必填
handoff_next: ""             # stage=handoff/status=blocked 时必填
design: ".codestable/features/YYYY-MM-DD-{slug}/{slug}-design.md"
checklist: ".codestable/features/YYYY-MM-DD-{slug}/{slug}-checklist.yaml"
review: ".codestable/features/YYYY-MM-DD-{slug}/{slug}-review.md"
qa: ".codestable/features/YYYY-MM-DD-{slug}/{slug}-qa.md"
acceptance: ".codestable/features/YYYY-MM-DD-{slug}/{slug}-acceptance.md"
```

上面的 ref 只有在同目录 `approval-report.md` frontmatter 含 `doc_type: approval-report` 与 `approvals.goal-acceptance: approved` 时有效；runtime 会机械核对文件、unit 边界与命名决策，不能只写 goal-state 两个字段。

落盘 `(stage, status)` 与 `GoalState` 一一映射：`implementation/ready-to-dispatch`、
`implementation/running`、`review/ready|fixing`、`qa/ready|fixing`、`acceptance/ready`、
`complete/passed`、`handoff/blocked`。

每次 stage / status 变化都要立即写回 `goal-state.yaml`。driver 中断后，后续 agent 先读 `goal-state.yaml`，再按仓库事实核验对应产物是否存在且状态匹配；不一致时以仓库事实为准并修正 state。派发成功后写回 `driver_kind` / `driver_id`；重入是否重派按 `.codestable/reference/agent-conventions.md` 的 Goal driver 派发规则判定。`complete/passed` 与 `handoff/blocked` 是终态，即使仍残留 driver 元数据也必须优先识别。

`goal-protocol.md` 必须写明执行 loop：

1. 读取 design、checklist、goal-plan、goal-state。
2. 进入 `cs-feat` implementation 阶段完成 checklist steps；代码行为 step 默认按 TDD micro-loop 执行，不能 TDD 时写 `TDD exception` 和替代证据。
3. 运行 implementation gates，生成 evidence pack / gate results / DoD results。
4. 进入 `cs-code-review`；有 blocking 就 review-fix 后重跑 review。
5. review passed 后进入 `cs-feat` QA；QA failed / blocked 就 qa-fix 后重跑 review 和 QA。
6. QA passed 后从 goal-state 读取授权引用，以 `ResumeGoalAcceptance ApprovalRef` 进入 `cs-feat` acceptance，更新 checklist checks 和必要长期文档。
7. 全部通过后先写 `stage: complete` / `status: passed`，再打印 `CS_FEATURE_GOAL_COMPLETE`。

`goal-protocol.md` 还必须写明：

- Goal 模式接管：普通流程中各阶段停等用户确认的 checkpoint，在 goal 模式下改为写入报告、状态和证据记录；acceptance 仍必须消费 goal package 前独立取得的 `ApprovalRef`，不是隐式自动批准；只有命中 handoff 条件才停。
- Goal driver 不得绕过 implementation 的 TDD policy；行为代码 step 缺 RED / GREEN / VERIFY evidence 且无 `TDD exception` 时，implementation gate 不通过。
- 每个阶段 gate 通过后按上表更新 `goal-state.yaml` 的 `stage` / `status`，保证 driver 中断后可按仓库事实重派续跑；step 粒度的进度 ledger 与续跑判定见 `.codestable/reference/agent-conventions.md` 的"派发与审查精化"，续跑以 ledger + `git log` 为准，不重复派发已完成 step。
- handoff 前先写 `stage: handoff` / `status: blocked` / `handoff_reason` / `handoff_next`，再按以下格式输出：

```text
CS_FEATURE_GOAL_HANDOFF
Reason: <具体阻塞>
Next: <建议动作>
```

handoff 条件：

- 需要改变 approved design、feature 范围、公开契约或 roadmap item。
- 独立 Task agent reviewer pending / failed / blocked，且没有用户明确降级。
- 同一失败项三轮修复仍不通过。
- 外部凭证或环境缺失导致核心行为无法判断。
- 用户主动要求暂停、改方向或终止。

---

## Goal 指令

输出：

```text
/goal "执行 CodeStable feature 目录 .codestable/features/YYYY-MM-DD-{slug} 下的 goal 执行包。先读取 goal-protocol.md、goal-state.yaml、goal-plan.md、{slug}-design.md、{slug}-checklist.yaml；这是已由用户确认 design，并在 goal-state 记录独立 acceptance authorization 的 goal 模式。按 goal-protocol.md 连续执行 cs-feat implementation、cs-code-review、cs-feat QA、cs-feat acceptance；acceptance 必须以 goal-state 的 ApprovalRef 调用 ResumeGoalAcceptance，缺失或不匹配立即 handoff；implementation 的代码行为 step 默认用 TDD micro-loop，必须留下 RED/GREEN/VERIFY evidence，不能 TDD 时写 TDD exception 和替代证据；review blocking 时做 review-fix 并重跑 review；QA failed / blocked 时做 qa-fix 并重跑 review 和 QA。只有当 CS_FEATURE_GOAL_COMPLETE 出现在 transcript 中，且 review passed、QA passed、acceptance passed、没有 CS_FEATURE_GOAL_HANDOFF，本 goal 才算完成。"
```

---

## 派发

生成 goal 包后，按 `.codestable/reference/agent-conventions.md` 的 Goal driver 派发规则执行：

- 有满足共享契约的可见 host Agent 时，启动 driver 并把 agent id / run id / 查看方式告诉用户。
- driver 初始 prompt 必须是上面生成的同一条 literal `/goal` 指令；不要改写成普通 implementation 任务。
- driver 不可见、不可追踪、缺授权或启动失败时，不启动后台任务，只打印 fenced `/goal`。
- 主 agent 不能仅凭“已派发”宣布完成；完成必须由 goal 产物和 transcript 标记证明。

---

## 完成判据

- goal 包已落盘。
- 已尝试可见 Goal driver 派发，或已明确回退为用户手动粘贴 `/goal`。
- 长程执行完成后应存在 review、QA、acceptance，且最终 transcript 有 `CS_FEATURE_GOAL_COMPLETE`。
