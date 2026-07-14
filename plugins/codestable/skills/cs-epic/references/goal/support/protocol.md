# CodeStable Roadmap Goal Protocol

本文件复制到 `{roadmap-path}/goal-protocol.md` 后，由 `/goal` 会话读取。详细执行规则拆到同目录子文档，避免单个 md 超过 300 行。

## 1. 先读文件

- `{roadmap-path}/goal-state.yaml`
- `{roadmap-path}/goal-plan.md`
- `{roadmap-file}`
- `{items-file}`
- `{roadmap-path}/goal-features/*.md`
- `{roadmap-path}/goal-protocol-feature-loop.md`
- `{roadmap-path}/goal-protocol-gates.md`
- `{roadmap-path}/goal-protocol-audit.md`

## 2. 启动检查

- 所有 feature design frontmatter 必须是 `status: approved`。
- `goal-state.yaml` 使用 `current_feature_index`，语义为 0-based。
- `baseline_ref` 在 git 仓库内必须能解析为 SHA。
- `goal-plan.md` 必须包含 roadmap 核心验收路径、最终聚合命令、DoD Policy、Gate Policy、Provider Policy。
- checklist `steps` 和 `checks` 初始状态必须为 `pending`；goal 执行中按阶段更新。

## 3. Goal 模式接管

用户粘贴 `/goal`，或主流程按 Goal driver 派发规则启动可见 Task agent，代表授权 goal 会话连续执行各 feature 的 impl / review / QA / accept。普通流程中逐 feature 停等用户确认的 checkpoint，在 goal 模式下改为写入报告、状态和审计记录。

```haskell
data GoalHandoffReason
  = OwnerStop | ScopeChange | IndependentReviewUnavailable
  | UnapprovedHOnlyCoreCheck | CoreEvidenceUnavailable
  | CorePathUnverified | RepeatedFailure
data GoalRun = RunFeature Index | RunFinalAudit | Complete | Handoff GoalHandoffReason

handoffReason :: GoalState -> Maybe GoalHandoffReason
handoffReason s
  | ownerStopped s                   = Just OwnerStop
  | approvedScopeChanged s           = Just ScopeChange
  | reviewerBlocked s                = Just IndependentReviewUnavailable
  | unapprovedHOnlyCoreCheck s       = Just UnapprovedHOnlyCoreCheck
  | coreEnvironmentMissing s         = Just CoreEvidenceUnavailable
  | corePathUnverified s             = Just CorePathUnverified
  | sameFailureCount s >= 3          = Just RepeatedFailure
  | otherwise                        = Nothing

nextGoal :: GoalState -> GoalRun
nextGoal s
  | Just reason <- handoffReason s    = Handoff reason
  | Just i <- nextPendingFeature s    = RunFeature i
  | not (finalAuditPassed s)          = RunFinalAudit
  | otherwise                         = Complete
```

## 4. 启动标记

```text
CS_ROADMAP_GOAL_START
Roadmap: {roadmap-slug}
Features: <数量>
Baseline ref: <sha|no-git>
Plan: {roadmap-path}/goal-plan.md
Protocol: {roadmap-path}/goal-protocol.md
```

## 5. 执行顺序

`nextGoal` 是顺序真相。`RunFeature i` 读取 goal-feature/design/checklist，执行 feature loop 与
stage gates；accepted 后更新 state/items、scoped-commit，工作树干净才推进 index。
`RunFinalAudit` 执行 `goal-protocol-audit.md`。

## 6. 完成标记

只有最终审计通过后，先把 `goal-state.yaml` 顶层更新为 `status: complete`，再打印：

```text
CS_ROADMAP_GOAL_COMPLETE
```

如果无法继续：

先把 `goal-state.yaml` 顶层更新为 `status: handoff`，并写入
`handoff_reason` / `handoff_next`；保留 `current_feature_index`、features 和 driver
字段，使主流程能从仓库事实恢复 handoff。然后打印：

```text
CS_ROADMAP_GOAL_HANDOFF
Reason: <具体阻塞>
Next: <建议动作>
```
