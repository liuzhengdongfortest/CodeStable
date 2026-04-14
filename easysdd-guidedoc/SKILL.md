---
name: easysdd-guidedoc
description: 文档写作子工作流——为项目编写或更新开发者指南（dev-guide）和用户指南（user-guide），产物落到项目 docs/ 目录，可被 search-yaml.py 检索。触发场景："写文档"、"开发者指南"、"用户指南"、"guidedoc"、"更新 API 文档"、"补一份指南"，或 feature-acceptance 结束后主动推送。
---

# easysdd-guidedoc

**文档写作子工作流** —— 根据方案 doc 和代码实现，编写（或更新）面向外部读者的开发者指南和用户指南，产物落到项目 `docs/` 目录，与代码一同维护。

> "代码解决问题，文档让别人能用它解决问题。"

---

## 一、两条轨道

| 轨道 | 目标读者 | 典型内容 | 输出路径 |
|---|---|---|---|
| `dev-guide` | 贡献者、集成方、下游开发者 | 本地 setup、架构解说、API/接口说明、贡献指南、扩展方式 | `docs/dev/{slug}.md` |
| `user-guide` | 终端用户、产品使用者 | 功能概述、操作步骤、概念解释、常见问题 | `docs/user/{slug}.md` |

**轨道选择原则**：从"谁会读这份文档"出发，而不是从"写的是接口还是步骤"出发。同一个 feature 可能同时需要两份文档（例如：API 变化 → dev-guide；对应的用户操作步骤 → user-guide）。

> 路径 `docs/dev/` 和 `docs/user/` 是**默认约定**，如果项目已有其他 docs 目录结构，以项目约定为准——开始工作前先确认。

---

## 二、触发时机

以下任一条件满足，触发本工作流：

| 情境 | 说明 |
|---|---|
| feature-acceptance 结束后 | 验收通过后，AI 检查方案 doc：第 2 节有接口变更 → 推送"需要更新 dev-guide 吗？"；第 1 节有用户可见行为变更 → 推送"需要更新 user-guide 吗？" |
| 用户主动触发 | "写文档"、"guidedoc"、"更新用户指南"、"补一份开发者指南" |
| 接入 easysdd 后 | 新仓库 easysdd-onboarding 完成后，可触发本工作流补全项目基础文档骨架 |

**主动推送原则**：一句话提示即可，用户说"不用"立刻跳过，不再提。

---

## 三、涉及的路径

本技能的产物**不在 `easysdd/` 目录下**——指南是面向外部读者的可发布产物，不是 spec 工件。

- dev-guide → `docs/dev/{slug}.md`
- user-guide → `docs/user/{slug}.md`

**文件命名**：`{slug}.md`（英文小写 + 连字符，**无日期前缀**——指南持续更新，不按创建日期管理）。

**用 `search-yaml.py` 检索已有指南**：

```
python easysdd/tools/search-yaml.py --dir docs/dev --filter doc_type=dev-guide --filter status=current
python easysdd/tools/search-yaml.py --dir docs/user --filter doc_type=user-guide --filter component={feature-slug}
```

---

## 四、YAML frontmatter

```yaml
---
doc_type: dev-guide | user-guide
slug: {英文描述，连字符分隔}
component: {关联的模块名或 feature slug}
status: draft | current | outdated
summary: {一句话描述此文档涵盖什么}
tags: []
last_reviewed: YYYY-MM-DD
---
```

**必填字段**：`doc_type`、`slug`、`component`、`status`、`summary`、`tags`、`last_reviewed`。

**status 字段语义**：

- `draft`：初稿，待用户 review
- `current`：当前有效文档
- `outdated`：对应代码/接口已变更，文档尚未同步（保留原文，标记后推送更新）

---

## 五、文档格式

### dev-guide 正文结构

```markdown
## 概述

一段话描述该模块/接口/系统的功能定位和适用场景。

## 前置依赖

使用/集成此模块所需的环境、依赖或配置（如有）。

## 快速上手

最小可运行示例。代码优先，文字辅助。

## 核心概念

（可选）理解接口/API/模块行为所需的关键术语和设计决定。

## 接口参考

主要 API、配置选项、事件、钩子的签名与说明。推荐表格或逐项列举。

## 常见场景

2–4 个实际使用场景的代码示例，覆盖 happy path 和常见边界。

## 已知限制与注意事项

（可选）使用时需要注意的边界、性能考虑、已知 bug 绕过方式。

## 相关文档

关联的 user-guide、方案 doc、架构 doc 或外部参考。
```

### user-guide 正文结构

```markdown
## 功能简介

一段话描述这个功能是什么、解决什么问题。

## 前置条件

（可选）使用这个功能需要满足的前提（账号权限、需先完成的操作等）。

## 如何使用

步骤化操作说明。每步一行，关键操作配截图占位符（`![描述](./assets/xxx.png)`）或注明"此处需截图"。

## 常见问题

Q: ...
A: ...

## 相关功能

（可选）关联功能的跳转链接或说明。
```

---

## 六、工作流步骤

### Step 1：明确任务范围

询问（或从上下文推断）：

1. **轨道**：dev-guide、user-guide，还是两者都要？
2. **覆盖范围**：新写一份，还是更新已有文档？
3. **信息来源**：
   - 方案 doc（design.md）是否已有？
   - 已有 guide 用 `search-yaml.py` 搜 `component` 字段确认（避免重复写）
   - 需要读哪些代码文件？

### Step 2：收集输入

并行做：

- 读方案 doc（重点：第 0 节术语约定、第 2 节接口契约、第 1 节用户可见行为）
- 用 `search-yaml.py` 搜 `docs/` 目录，确认有无同 component 的已有 guide

若发现已有 guide 但 `status=outdated`，此次任务定性为**更新**而非新建。

### Step 3：起草

按对应轨道的正文结构起草，同时写好 YAML frontmatter（`status` 先填 `draft`）。

**约束**：

- 正文只写面向目标读者的内容，不把方案 doc 里的"实现提示"或内部设计细节搬进来
- 术语与方案 doc 第 0 节保持一致
- 代码示例来源于实际代码，不虚构接口

### Step 4：用户 review

展示草稿，逐节确认：覆盖范围是否完整、描述是否准确、是否有读者看不懂的地方。

### Step 5：落盘

用户放行后：

1. 写入对应路径（`docs/dev/{slug}.md` 或 `docs/user/{slug}.md`）
2. 把 frontmatter `status` 从 `draft` 改为 `current`，`last_reviewed` 填当天日期
3. 如果是更新已有文档，同步把旧文档 frontmatter `status` 改为 `outdated`（或直接覆盖更新，视情况）

---

## 七、与其他工作流的关系

| 来源工作流 | 关系说明 |
|---|---|
| `easysdd-feature-acceptance` | 验收结束后主动推送：有接口变更推 dev-guide，有用户可见行为变更推 user-guide |
| `easysdd-feature-design` | 方案 doc 第 2 节（接口契约）是 dev-guide 的主要信息来源；第 1 节（用户可见行为）是 user-guide 的主要信息来源 |
| `easysdd-onboarding` | 新仓库接入 easysdd 后，可触发本工作流补全项目基础文档骨架 |
| `easysdd-architecture-check` | 检测到 design 与代码不一致时，对应 guide 应同步标记 `status=outdated` |
| `easysdd-decisions` | dev-guide 里引用的技术选型原则应来自 decisions 目录，不独立发明 |
| `easysdd-tricks` | dev-guide 里的用法示例若与 tricks 目录已有记录重合，可交叉引用而不重复写 |
| `easysdd-libdoc` | guide 内引用 libdoc 条目做详细参考（"完整 props 见 xxx"）；libdoc 是零件级参考（reference），guidedoc 是任务级教程（how-to），互补不替代 |

---

## 反模式（看到就停）

- ❌ 把方案 doc 里的"实现提示"节原文搬进 dev-guide —— 那是内部 spec，不是给外部读者看的
- ❌ 没检查已有 guide 就新建 —— 可能造成两份文档内容冲突
- ❌ guide 写完但 `status` 还是 `draft` —— 落盘时必须改成 `current`
- ❌ 代码已更新，相关 guide `status` 还是 `current` 没改 —— 应标为 `outdated` 并推送更新
- ❌ dev-guide 和 user-guide 两份文档内容高度重叠 —— 读者不同意味着关注点不同，重叠说明其中一份定位有误
- ❌ 用 guide 存放 spec 信息（不变量、测试约束、根因分析）—— 这类内容属于 `easysdd/` 目录，不属于 `docs/`
