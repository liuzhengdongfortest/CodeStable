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

仍必须 handoff 的情况：

- 需要改变已批准 design、roadmap item、接口契约或 feature 范围。
- 独立 Task agent reviewer pending / failed / blocked，且没有用户明确降级。
- 同一失败项三轮修复仍不通过。
- 外部凭证或环境缺失导致核心行为无法判断。
- 功能性核心路径或 roadmap 级核心验收路径无法验证。
- 用户主动要求暂停、改方向或终止。

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

1. 按 `goal-state.yaml.current_feature_index` 找到下一个 pending feature。
2. 读取对应 `goal-features/<feature-slug>.md`、design、checklist。
3. 按 `goal-protocol-feature-loop.md` 执行 feature loop。
4. 每个阶段按 `goal-protocol-gates.md` 执行 Gate Policy。
5. 每个 feature accepted 后更新 `goal-state.yaml` 和 roadmap items，立即 scoped-commit；`git status --short` 干净后才进入下一 feature。
6. 所有 feature accepted 后按 `goal-protocol-audit.md` 做最终审计。

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
