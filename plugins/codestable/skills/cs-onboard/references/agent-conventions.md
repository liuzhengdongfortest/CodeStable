# Task Agent 与 Goal Driver 约定

本文件由 `cs-onboard` 复制到 `.codestable/reference/agent-conventions.md`。
需要独立 review、QA runner、acceptance auditor、功能验收或 goal driver 时读取。

## Task Agent gate

`Task agent` 用于隔离 review、QA、audit、acceptance 或功能验收；Reviewer 的
provider/model 与启动方式按宿主当前暴露的多 Agent 能力发现。

```haskell
data TaskRole = Review | QA | Audit | Acceptance
data Isolation = Heterogeneous | Independent
data ReadOnlyControl = EnforcedReadOnly | VerifiedNoWrite
data AgentCapability = AgentCapability HostAgentAdapter Isolation ReadOnlyControl
data AgentConfig = Inherit | Explicit Provider Model Settings
data AgentSelection
  = Start AgentCapability AgentConfig
  | SelectionNeedsOwnerApproval Reason
  | SelectionBlocked Reason
data AgentRun = NotStarted | Active AgentRef | Finished Findings | Failed Reason
data OwnerApproval = ApproveLocalOnly
data AgentDecision
  = Launch AgentCapability AgentConfig
  | Await | MergeVerified Findings | LocalReview
  | NeedOwnerApproval Reason | Blocked Reason
data ReviewLane = IndependentLane | OwnerApprovedLocalLane
data ReviewVerdict = Passed | ChangesRequested | ReviewBlocked Reason

eligible :: AgentCapability -> Bool
eligible c = separateContext c && observableRun c && readOnlyControlled c

reviewRank :: AgentCapability -> Int
reviewRank (AgentCapability _ Heterogeneous EnforcedReadOnly) = 0
reviewRank (AgentCapability _ Heterogeneous VerifiedNoWrite)  = 1
reviewRank (AgentCapability _ Independent EnforcedReadOnly)   = 2
reviewRank (AgentCapability _ Independent VerifiedNoWrite)    = 3

bestFit :: TaskRole -> AgentConfig -> [AgentCapability] -> Maybe AgentCapability
bestFit Review config agents = headMaybe (sortOn reviewRank (matching config agents))
bestFit _      config agents = headMaybe (matching config agents)

selectTaskAgent :: TaskRole -> AgentEnv -> AgentSelection
selectTaskAgent r e
  | Just agent <- bestFit r config (filter eligible (hostAgentCapabilities r e))
                                                = Start agent config
  | isExplicit config                           = SelectionBlocked ExplicitConfigUnavailable
  | otherwise                                   = SelectionNeedsOwnerApproval IndependentAgentUnavailable
  where config = fromMaybe Inherit (attentionConfig r <|> ownerConfig r)

reviewGate :: AgentSelection -> AgentRun -> Maybe OwnerApproval -> AgentDecision
reviewGate _ (Finished findings) _ = MergeVerified findings
reviewGate _ (Active _) _ = Await
reviewGate _ (Failed _) (Just ApproveLocalOnly) = LocalReview
reviewGate _ (Failed reason) _ = Blocked reason
reviewGate (SelectionBlocked reason) NotStarted _ = Blocked reason
reviewGate (SelectionNeedsOwnerApproval _) NotStarted (Just ApproveLocalOnly) = LocalReview
reviewGate (SelectionNeedsOwnerApproval reason) NotStarted _ = NeedOwnerApproval reason
reviewGate (Start agent config) NotStarted _ = Launch agent config

toReviewLane :: AgentDecision -> Either Reason ReviewLane
toReviewLane (MergeVerified _) = Right IndependentLane
toReviewLane LocalReview = Right OwnerApprovedLocalLane
toReviewLane (Launch _ _) = Left LaneNotStarted
toReviewLane Await = Left LaneStillPending
toReviewLane (NeedOwnerApproval reason) = Left reason
toReviewLane (Blocked reason) = Left reason

reviewVerdict :: Either Reason ReviewLane -> Findings -> ReviewVerdict
reviewVerdict (Left reason) _ = ReviewBlocked reason
reviewVerdict (Right _) findings
  | hasBlocking findings = ChangesRequested
  | otherwise            = Passed
```

宿主能力可以来自原生 Agent、已安装的 MCP 或其他当前可用 adapter；skill 只依赖行为事实，
不依赖 backend 产品名或工具名。候选必须有独立上下文、可观察的 id / 状态 / result，以及
可核验的只读控制。宿主没有强制只读 mode 时，先记录 workspace baseline，完成后验证无写入，
才可记为 `VerifiedNoWrite`。

review 优先选择与主 agent provider 或 model family 不同的 `Heterogeneous` 候选；只有差异事实
可证明时才这样标记，未知配置仍算 `Independent`。异构候选不可用不阻塞独立 review，继续使用
隔离的同类 reviewer。prompt 不带主 agent 结论；findings 经本地事实核验后才写 verdict。

`SelectionBlocked ExplicitConfigUnavailable` 表示 owner 显式 pin 的配置当前不可满足；
`ApproveLocalOnly` 不覆盖这个配置事实，owner 需要先修改或清除显式配置再重新选择。

每轮 review 都调用同一 `selectTaskAgent` / `reviewGate`。批量、赶时间、已自查或自评低风险
都不构成 `ApproveLocalOnly`；降级前按 `approval-conventions.md` 取得 owner 明确授权。

## Task Agent 生命周期

```haskell
data CreateRecovery = RetryCreate | CreateBlocked Reason

mayClose :: AgentRunState -> Bool
mayClose s = terminal s && resultConsumed s && not (permissionPending s)

recoverCreate :: Reason -> CreateRecovery
recoverCreate CapacityExhausted = closeOldest mayClose >> RetryCreate
recoverCreate reason            = CreateBlocked reason
```

记录 agent id、用途与查看方式；关闭失败只记 warning，不改已核验 verdict。用户取消、
owner-stop 或 handoff 时保留未消费/待授权 agent，交给用户接管。

## Goal Driver 派发

`Goal driver` 是一个可见 Task agent，用来执行已生成、已过用户 gate 的 goal 包。它不是
reviewer，不批准 design；它只按 goal 包协议执行 implementation / review / QA /
acceptance，并把证据写回仓库。

Goal driver 需要可写、可观察，并且能在自身执行环境内再次启动独立 reviewer。宿主 adapter
只要满足这些行为事实即可参与选择。

```haskell
data DriverDecision = StartHostDriver | PrintGoal Command | DriverBlocked Reason

selectGoalDriver :: GoalPackageState -> AgentEnv -> DriverDecision
selectGoalDriver s e
  | not (goalPackagePersisted s && designApproved s && baselineTracked s)
                                                  = DriverBlocked GoalPackageNotReady
  | visibleHostDriver e && canSpawnReviewer e     = StartHostDriver
  | otherwise                                     = PrintGoal "/goal"
```

派发 prompt 必须使用 goal 包协议生成的同一条 literal `/goal` 指令作为 driver 初始任务。
不要改写成普通“执行/实现这个 feature”的自然语言任务；那会绕开 goal 模式接管语义，导致
driver 在 implementation / review / QA / acceptance 普通 checkpoint 被截停。除 `/goal`
指令本身外，只能附加查看方式、agent id 写回要求和 complete / handoff 标记说明。

派发成功后立即把 driver 形态与标识写回对应 `goal-state.yaml`（`driver_kind:
host-agent`、`driver_id`）。重入时先读 goal-state：状态为 running 且该 driver 仍可见时，
汇报进度和查看方式，不重复派发；driver 已不可见时，以仓库事实修正 state，再续跑或重派。
driver 完成或 handoff 且结果已被主流程消费后，按 Task Agent 生命周期关闭。

## Task Agent 实现选择

review 在 Task agent 可用时必须使用。implementation Task agent 是可选项；当工作跨越三个以上
子系统、需要并行切片、触及高风险 migration / concurrency / runtime contract，或超过单线程
上下文容量时，应主动提出。主线程保留集成、验证和最终 review 责任。

## 派发与审查精化

- **进度 ledger**：goal 执行每完成一个 step，在 `goal-state.yaml` 的 ledger 段追加一行（step id + commit 范围 + 状态）。续跑以此 ledger + `git log` 为准，不重复派发已完成 step。
- **审查结论双维度**（不是新增 review 编排，`cs-code-review` 的环节 A/B 编排不变；这里只约束其结论必须分开落两维）：spec 合规（每需求指到步 / 无占位符 / 术语 · 类型一致）与代码质量，缺一不算 `passed`。
- **模型分级**：派发按任务复杂度显式指定模型档：机械转录 / 单文件小改→轻量；多文件集成→标准；架构决策 / 最终全量审查→最强。
- **file handoff**：大 diff / 报告经文件路径传递（`build-review-packet.py` / `build-context-packet.py` 产出），不粘进派发 prompt 或回传正文；不含 `.env`、token、secret。
