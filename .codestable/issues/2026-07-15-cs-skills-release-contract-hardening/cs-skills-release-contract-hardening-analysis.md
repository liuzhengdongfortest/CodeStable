---
doc_type: issue-analysis
issue: cs-skills-release-contract-hardening
status: confirmed
root_cause_type: contract-inconsistency
related: [cs-skills-release-contract-hardening-report.md]
tags: [skills, workflow, spec, release]
---

# CS Skills 发布契约加固根因分析

## 1. 问题定位

| 组 | 关键位置 | 根因 |
|---|---|---|
| A | `cs-feat/references/design/protocol.md`、`cs-epic/SKILL.md`、`codestable-workflow-next.py` | design admission 与 implementation admission 共用 `depends_on=done`，没有 batch 设计就绪层。 |
| B | `cs-feat/references/acceptance/protocol.md`、feature/epic goal 协议 | Goal checkpoint 被描述为自动推进，却没有显式授权事件；Epic feature loop 又直接 commit。 |
| C | `cs-code-review/SKILL.md` 及带 checkpoint/agent 的主 skill | focused closure 只接受 passed 前态；恢复 union、持久等待态和 workflow dispatch 没形成闭环。 |
| D | `cs-goal/SKILL.md`、goal conventions/reference | completion guard 未消费 final iteration 证据；reviewer failure 分支违背独立 review gate。 |
| E | eval release protocol、历史 refactor 目录 | 发布命令只覆盖部分测试；已完成 refactor 缺 canonical review artifact。 |
| F | `cs-note/SKILL.md` | guard 优先级把格式适配置于内容归属之前。 |
| G | deprecated `agents/openai.yaml`、`cs-onboard/SKILL.md` | 兼容入口展示元数据和完成输出未随 canonical contract 同步。 |

## 2. 失败路径还原

核心失败模式一致：协议声明了一个安全边界，但状态类型、恢复输入、runtime 决策或发布测试没有共同编码该边界。因此文本看似完整，重入、Goal driver、Task agent 失败或 release gate 实际执行时仍能进入冲突或绕过路径。

## 3. 根因

**根因类型**：跨层契约不一致。

**根因描述**：本轮 host-agnostic contract 改造补充了 outcome 术语和 agent 生命周期，但没有逐一验证 `规则 -> 状态 -> 恢复输入 -> runtime/tool -> scenario test -> release gate` 的闭环；局部旧规则继续生效，形成死锁、隐式授权和不可恢复状态。

## 4. 影响面

- 活跃 skill：`cs-audit`、`cs-code-review`、`cs-docs`、`cs-epic`、`cs-feat`、`cs-goal`、`cs-issue`、`cs-note`、`cs-onboard`、`cs-refactor`。
- 共享参考：`cs-onboard/references/{shared,agent,goal,system-overview}.md` 及相关模板。
- Epic/Feature 协议：design、acceptance、goal、goal feature loop 与 command/state 模板。
- runtime tool：`cs-onboard/tools/codestable-workflow-next.py`。
- 发布与兼容元数据：eval release protocol、四个 deprecated `agents/openai.yaml`。
- 证据：历史 refactor canonical review、本 issue report/analysis/fix-note/review。
- 测试：workflow-next、contract semantics、workflow scenarios、entry simplification、plugin package 与 doctor/release 相关测试。

## 5. 已确认修复方案

1. 新增明确的 design dependency readiness；runtime 按 DAG 选择 design-ready child，并保留 implementation `done` gate。
2. 为 Goal acceptance 和 Epic commit 分别增加显式授权输入与持久字段；未授权时 checkpoint/handoff，不执行副作用。
3. 让 focused closure 接受原独立 review 的 `changes-requested` 前态；所有 checkpoint/agent wait 统一补齐 resume union、持久 id 和 dispatch。
4. `cs-goal` completion 同时验证 final iteration 引用；reviewer unavailable 复用统一 review gate 并停 owner，不自审。
5. release gate 改跑完整 `tests/`、runtime sync、doctor、diff check；以本轮独立 Fable 复核补齐历史 refactor review artifact。
6. 调整 `cs-note` guard 顺序，更新 deprecated prompts 与 onboard 输出。
7. 每组修改先跑针对性测试，再由独立只读 reviewer 审查；blocking/important 清零后才进入下一组和最终全量门禁。

## 6. 明确不做

- 不修改与上述根因无关的 skill 文案或抽象。
- 不删除 legacy compatibility 入口或 `.codestable/tools/`。
- 不执行 `git commit`、push 或版本号 bump；这些需要发布 owner 的独立授权。
