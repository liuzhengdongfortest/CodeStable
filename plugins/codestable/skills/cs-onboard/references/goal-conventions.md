# Goal 约定

本文件会由 `cs-onboard` 复制到 `.codestable/reference/goal-conventions.md`。它定义
`cs-goal` 的共享运行形态。

## 用途

Goal 是有界起点/终点工作单元。owner 定义结果和验收信号；AI 简短 interview / grill，
写起点报告，实现、验证、自主迭代，并写 iteration 报告。只有 Task agent 对产出结果做完
功能验收后，goal 才能关闭。

当请求是“达成这个结果”、“跑到被验收”、“自主迭代”、“AI 自主实现”或“先 grill me”时，
使用 goal。

## Spec

```haskell
data GoalStatus = Active | Complete | Blocked
data StopReason
  = AcceptanceConflict | AmbiguousTerminal | ScopeBoundaryChange
  | RepeatedBlocker | BudgetExhausted | RiskAcceptanceNeeded | AcceptanceAgentUnavailable

nextIteration :: GoalState -> [IterationArtifact] -> Int
nextIteration state existing =
  max (currentIteration state) (highestIteration existing) + 1

ownerStop :: GoalState -> Maybe StopReason
ownerStop g
  | acceptanceConflicts g                 = Just AcceptanceConflict
  | objectiveOrTerminalAmbiguous g        = Just AmbiguousTerminal
  | changesLongLivedContract g            = Just ScopeBoundaryChange
  | sameBlockerCount g >= 3               = Just RepeatedBlocker
  | budgetExhaustedOrNear g               = Just BudgetExhausted
  | needsRiskSecretDestructiveOrDeploy g  = Just RiskAcceptanceNeeded
  | requiredTaskAgentUnavailable g        = Just AcceptanceAgentUnavailable
  | otherwise                             = Nothing

mayComplete :: GoalState -> Bool
mayComplete g =
  isNothing (ownerStop g)
    && acceptanceCriteriaPassed g
    && functionalAcceptanceRecorded g
```

## 报告语言

所有 goal 报告正文遵守 `.codestable/attention.md`。如果 attention 没有报告语言策略，
使用 owner 当前对话语言。不要在共享约定中硬编码必须双语。

默认使用下列无后缀 canonical 文件。只有 attention 明确要求多语言副本时，才添加语言后缀副本。

## Directory

```text
.codestable/goals/YYYY-MM-DD-{slug}/
├── state.yaml
├── goal.md
├── functional-acceptance.md
└── iterations/
    └── 001.md
```

目录日期是 goal 创建日期。`state.yaml.goal` 保留裸 slug，方便人和 agent 在不解析文件系统
名称的情况下比较相关 dated unit。

`state.yaml` 是机器 source of truth。Markdown 是面向人的上下文。恢复优先级是：
`state.yaml` > latest iteration frontmatter > Markdown body。

`functional-acceptance.md` 只在终端验收 gate 创建，不在 goal 开始时创建空文件。

`goal.md` 是 interview / grill 产生的起点报告。它必须在实现前存在，并包含 objective、
start point、acceptance、non-goals、owner decisions、unresolved assumptions 和
next action。

## State Model

`GoalStatus` 落盘为 `active | complete | blocked`；`Blocked` 的原因同时写入 blocker 字段。

必需的 `state.yaml` 字段：

- `schema_version`
- `goal`
- `status`
- `objective`
- `start_point`
- `acceptance`
- `non_goals`
- `budget`
- `current_iteration`
- `next_action`
- `blocker_signature`
- `blocker_count`
- `owner_stop`
- `updated_at`

`current_iteration` 表示最后一个已完成 iteration，不表示下一次进行中的尝试。

## Iteration 编号

修改 `current_iteration` 前按 `nextIteration` 计算下一个 `{nnn}`。

写入 `iterations/{nnn}.md` 后，让 `state.yaml.current_iteration` 等于该已完成编号。
不要覆盖已有 iteration 文件。如果 attention 要求语言变体，同时写对应的
`iterations/{nnn}.{lang}.md` 副本。

## 报告

每个已完成 iteration 写 canonical 报告：

- `iterations/{nnn}.md`

报告不是命令日志。一次 iteration 等于一次连贯的实现与验证尝试。即使 attention 要求额外
语言变体，也要包含相同语义内容：understanding、implementation approach、changes、
verification evidence、problems、next attempt 和 state update。

在 `status: complete` 前写：

- `functional-acceptance.md`

该报告记录 Task agent 根据 owner acceptance criteria 对产品 / 产物做的功能验收。包括
reviewer、scope、functional evidence、verdict、residual risks，以及引用它的 final
iteration。只有测试不足以完成 goal。

## 严格 Owner Stop

只按 `ownerStop` 停止；它与 `cs-goal.CheckpointReason` 一一对应，改口径需同步。
`RiskAcceptanceNeeded` 包含风险接受、secrets、破坏性操作、外部购买、merge / deployment 批准；
`AcceptanceAgentUnavailable` 需先按生命周期重试，再写 approval report，禁止自验收。日常技术选择和普通失败尝试由 AI 负责。
