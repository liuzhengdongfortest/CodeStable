---
doc_type: issue-report
issue: cs-skills-release-contract-hardening
status: confirmed
severity: P0
summary: 发布前 cs skills 存在依赖死锁、授权绕过和不可恢复状态契约
tags: [skills, workflow, spec, release]
---

# CS Skills 发布契约加固 Issue Report

## 1. 问题现象

发布候选中的 cs skills 存在七组已确认问题：

1. Epic child batch 要求依赖 feature `done` 才能设计，但 batch 又要求所有设计先通过后才进入实现，形成 P0 死锁。
2. Goal acceptance 仍会落入普通人工确认；Epic goal 又会在未取得独立提交授权时执行 scoped commit。
3. code-review 修复后的 focused closure 入口不可达；多个 skill 的 checkpoint / Task agent 等待态缺少可持久恢复输入或 agent id。
4. `cs-goal` 仅凭 acceptance passed 即完成，未机械要求 final iteration 引用；reviewer 不可用时还可能退化为自审。
5. 发布测试命令未覆盖完整 `tests/`，doctor 又被一个已完成 refactor 缺 canonical review artifact 阻断。
6. `cs-note` 的长度 / 频率 guard 先于临时信息和结构性决策 guard，可能把错误内容写进 attention。
7. 四个 deprecated agent prompt 仍推荐旧命令，`cs-onboard` 完成输出又漏列 `feedback/`。

## 2. 复现步骤

1. 构造两项 DAG：B `depends_on: [A]`，在 Epic child batch 中先让 A 的 design-review passed，但保持 A `in-progress`。
2. 尝试为 B 启动 design；现有 `cs-feat` 规则仍要求 A `done`，而 Epic 在全部 design-review passed 前不允许实现 A。
3. 分别沿 Goal acceptance、Epic goal feature loop、review-fix closure、各 skill checkpoint 恢复、`cs-goal` completion/reviewer failure 路径读取 Spec。
4. 运行 release protocol 当前 pytest 命令与 `python3 -m pytest -q tests`，比较收集范围。
5. 运行 `codestable-doctor.py --root . --json`，观察历史 refactor 缺 review artifact 的 P1 blocker。

## 3. 期望行为

- child batch 的 design admission 接受依赖项 `done`、`dropped` 或已通过独立 design-review；implementation admission 仍要求依赖 `done`。
- Goal acceptance 使用显式、可持久的 goal 授权输入；任何 commit 都先取得并记录 owner 授权。
- 每个 checkpoint 都有显式 resume union；每个 `Awaiting` Task agent 状态都持久化可观察 agent id。
- Goal 完成必须同时满足 acceptance passed 与 final iteration 已记录并引用 acceptance；review gate 不允许无授权自审。
- release gate 覆盖完整测试、runtime sync、doctor 和 diff check；doctor 无历史证据缺口。
- P2 项目均有确定性语义测试防回归。

## 4. 环境信息

- 分支：`feat/cs-agent`
- runtime：CodeStable `1.0.3`，preflight health `ok`
- reviewer：Paseo 独立 reviewers（分批 Claude Fable；最终全量与 closure 使用 Codex high-reasoning）
- 修复前全量基线：`496 passed, 1 skipped`

## 5. 严重程度

整体按 **P0** 处理：首项会阻断合法 Epic DAG；其余 P1/P2 会绕过授权、误判完成或使发布证据不完整。
