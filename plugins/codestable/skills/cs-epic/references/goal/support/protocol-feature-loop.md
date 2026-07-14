# Goal Feature Loop

```haskell
data FeatureStage = Implementation | Review | QA | Acceptance
data FailureCause = ImplementationDefect | StageEvidenceDefect
data StageResult
  = Passed | Failed FailureCause | Awaiting ExternalRef
  | NeedsHuman Reason | Blocked Reason
data FeatureStep
  = Run FeatureStage | Remediate FeatureStage FeatureStage
  | WaitFor FeatureStage ExternalRef | RequestHuman FeatureStage Reason
  | HandoffStage FeatureStage Reason | Accepted

advance :: FeatureStage -> StageResult -> FeatureStep
advance Implementation Passed = Run Review
advance Review Passed         = Run QA
advance QA Passed             = Run Acceptance
advance Acceptance Passed     = Accepted
advance Implementation (Failed _)                       = Remediate Implementation Implementation
advance Review (Failed _)                               = Remediate Implementation Review
advance QA (Failed _)                                   = Remediate Implementation Review
advance Acceptance (Failed ImplementationDefect)        = Remediate Implementation Review
advance Acceptance (Failed StageEvidenceDefect)         = Remediate Acceptance Acceptance
advance stage (Awaiting ref)                            = WaitFor stage ref
advance stage (NeedsHuman reason)                       = RequestHuman stage reason
advance stage (Blocked reason)                          = HandoffStage stage reason
```

## 1. 进入 Feature

读取：

- `goal-features/<feature-slug>.md`
- feature design
- feature checklist
- roadmap item
- 当前代码上下文

打印：

```text
CS_ROADMAP_GOAL_FEATURE_START
Feature: <N>/<总数> <feature-slug>
Design: <路径>
Checklist: <路径>
Depends on: <依赖|none>
Mandatory commands: <命令列表>
Evidence required: <证据列表>
```

把 `goal-state.yaml` 当前 feature 状态改为 `implementing`。

## 2. 实现阶段

必须显式进入 `cs-feat` implementation 阶段执行；禁止仅凭本协议摘要替代主入口协议。开始写代码前先打印：

```text
CS_STAGE_START feature=<feature-slug> stage=implementation skill=cs-feat
```

如果不能加载 `cs-feat` 主入口，必须停下说明原因，不得降级为普通实现。

按 `cs-feat` implementation 阶段执行：

- 先做基线预检。
- 按 checklist steps 顺序实现。
- 每步完成后只把该 step 的 `status` 从 `pending` 改为 `done`。
- 不修改 `checks`；checks 只由 acceptance 更新。
- 每步留下命令、手工、API、浏览器或 diff 证据。
- 每步执行清洁度检查。

实现结束后运行 `implementation.before_review` gates。

## 3. Code Review 阶段

按 `cs-code-review` 执行：

- 读取 design、checklist、evidence pack、gate results、git diff。
- 只读审查，不直接修代码。
- 写 `{feature-slug}-review.md`。
- review 必须解释 gate warnings 和 provider warnings。
- review 的 Test And QA Focus 交给 QA。

`advance Review` 返回 `Remediate Implementation Review` 时打印 `CS_ROADMAP_GOAL_REVIEW_FIX`。

## 4. QA 阶段

按 `cs-feat` QA 阶段 执行：

- 读取 design、checklist、review、evidence pack、gate results、git diff。
- 只读运行验证，不直接修代码。
- 写 `{feature-slug}-qa.md`。
- 覆盖 design 关键场景、DoD commands、review QA focus、evidence pack residual risks。
- 功能性核心路径必须有实际运行证据。
- 非功能性 feature 必须写明替代证据理由。

`advance QA (Failed _)` 返回 `Remediate Implementation Review` 时打印 `CS_ROADMAP_GOAL_QA_FIX`；
`Awaiting` 只等待已启动工作，`NeedsHuman` 请求缺失输入，`Blocked` 直接持久化 handoff；三者都不进入 review-fix 循环。
`WaitFor` 保留 external ref；`RequestHuman` / `HandoffStage` 退出前写 `goal-state.yaml` 的 `status: handoff`、reason 与 next。

## 5. Acceptance 阶段

按 `cs-feat` acceptance 阶段 执行：

- 确认 review passed 且无 unresolved blocking。
- 确认 QA passed 且无 unresolved failed / blocked。
- 复核 evidence pack、DoD Results、Gate Results。
- 填 `{feature-slug}-acceptance.md`。
- 把 checklist checks 从 `pending` 改为 `passed`。
- 按 design 第 4 节处理 reference / architecture / requirement 回写。
- 按 roadmap / roadmap_item 回写 items.yaml 和 roadmap 主文档。

Acceptance 失败必须先归因：实现行为不满足验收是 `ImplementationDefect`，回 implementation 修复后重跑 review / QA / acceptance；仅报告、checklist 或证据落盘缺口是 `StageEvidenceDefect`，只修 acceptance 后重验。

## 6. Feature 完成

打印 `CS_ROADMAP_GOAL_FEATURE_VERIFY`，列出 Implementation / Review / QA / Acceptance / Commands / Deliverables / Cleanliness / Roadmap item。

全部通过后：

- 当前 feature 状态改为 `accepted`。
- 立即 scoped-commit 本 feature 的代码、spec、review、QA、acceptance、roadmap 回写和 goal-state 更新；commit 成功且 `git status --short` 干净后，才能进入下一条。
- `current_feature_index` 加 1。
- 打印 `CS_ROADMAP_GOAL_FEATURE_DONE`。
