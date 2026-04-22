---
name: cs-guide
description: 给项目写或更新对外的指南文档——开发者指南（dev-guide，给贡献者 / 集成方 / 下游开发者读）和用户指南（user-guide，给终端用户读）。产物落到项目 docs/ 目录，跟代码一起维护，可被搜索工具检索。和 libdoc 的区别：guidedoc 是任务导向（"如何用 X 做 Y"），libdoc 是参考导向（"X 的每个零件长什么样"）。触发场景：用户说"写文档"、"开发者指南"、"用户指南"，或 feature-acceptance 收尾时主动推送。
---

# cs-guide

代码解决问题，文档让别人能用它解决问题。spec 文件记录了"做了什么、为什么这么做"，但下游开发者和终端用户不需要、也不应该读 spec——他们需要的是面向自己角色的、可发布的指南。

guidedoc 就是从 spec 和代码出发，写成读者真正能用的指南。

---

## 两条轨道

| 轨道 | 目标读者 | 典型内容 | 输出路径 |
|---|---|---|---|
| `dev-guide` | 贡献者、集成方、下游开发者 | 本地 setup、架构解说、API 说明、扩展方式 | `docs/dev/{slug}.md` |
| `user-guide` | 终端用户 | 功能概述、操作步骤、概念解释、常见问题 | `docs/user/{slug}.md` |

**轨道选择从"谁读"出发，不从"写的是接口还是步骤"出发**——同一个 feature 经常需要两份：API 变化进 dev-guide，对应的用户操作进 user-guide。

> 路径 `docs/dev/` 和 `docs/user/` 是默认约定，项目已有自己的 docs 结构就以项目为准——开始前先确认。

---

## 触发时机

| 情境 | 说明 |
|---|---|
| feature-acceptance 结束 | 按 `codestable/reference/shared-conventions.md` 主动推：方案 doc 第 2 节（接口契约）有变更就问"需要更新 dev-guide 吗？"，方案 doc 第 1 节（用户可见行为）有变更就问"需要更新 user-guide 吗？" |
| 用户主动触发 | "写文档"、"guidedoc"、"补一份开发者指南" |
| onboarding 完成后 | 新仓库可触发本工作流补全基础文档骨架 |

主动推送一句话即可，用户说"不用"就别再提——多次推会让用户觉得 AI 在加戏。

---

## 涉及路径

guidedoc 产物**不在 `codestable/` 下**——指南是面向外部读者的可发布产物，和 spec 工件分开。

- dev-guide → `docs/dev/{slug}.md`
- user-guide → `docs/user/{slug}.md`

文件命名 `{slug}.md`（英文小写 + 连字符，**无日期前缀**）——指南持续更新，按主题管理而不是按创建日期。

检索已有指南：

```
python codestable/tools/search-yaml.py --dir docs/dev --filter doc_type=dev-guide --filter status=current
python codestable/tools/search-yaml.py --dir docs/user --filter doc_type=user-guide --filter component={feature-slug}
```

---

## YAML frontmatter

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

`status` 三态：

- `draft`：初稿待 review
- `current`：当前有效
- `outdated`：对应代码已变，文档没跟上（保留原文，标记后推送更新）

---

## 文档格式

### dev-guide 正文结构

```markdown
## 概述
一段话描述功能定位和适用场景。

## 前置依赖
集成此模块所需的环境、依赖或配置（如有）。

## 快速上手
最小可运行示例。代码优先，文字辅助。

## 核心概念
（可选）理解接口/API/模块行为所需的关键术语和设计决定。

## 接口参考
主要 API、配置选项、事件、钩子。表格或逐项列举。

## 常见场景
2-4 个实际使用场景的代码示例，覆盖 happy path 和常见边界。

## 已知限制与注意事项
（可选）边界、性能考虑、已知 bug 绕过方式。

## 相关文档
关联的 user-guide、方案 doc、架构 doc 或外部参考。
```

### user-guide 正文结构

```markdown
## 功能简介
一段话描述功能是什么、解决什么问题。

## 前置条件
（可选）使用前的前提（账号权限、需先完成的操作等）。

## 如何使用
步骤化操作。每步一行，关键操作配截图占位（`![描述](./assets/xxx.png)` 或注明"此处需截图"）。

## 常见问题
Q: ...
A: ...

## 相关功能
（可选）关联功能的跳转链接或说明。
```

---

## 工作流步骤

### Step 1：明确任务范围

确认三件事：

1. 轨道：dev-guide / user-guide / 都要
2. 覆盖范围：新写一份还是更新已有
3. 信息来源：方案 doc 是否已有？已有同 component 的 guide 吗？需要读哪些代码？

### Step 2：收集输入

并行：

- 读方案 doc（重点：第 0 节术语、第 2 节接口契约、第 1 节用户可见行为）
- 用 `search-yaml.py` 搜 docs/，确认有无同 component 的已有 guide

发现已有 guide 标 `outdated` → 任务定性为**更新**而非新建。

### Step 3：起草

按对应轨道结构起草，frontmatter `status` 先填 `draft`。

约束：

- 正文只写面向目标读者的内容——**不要把方案 doc 里的"实现提示"或内部设计搬过来**。读者不同关注点不同，spec 内容混进 guide 会让指南失焦
- 术语与方案 doc 第 0 节保持一致
- 代码示例必须来自实际代码，不虚构接口

### Step 4：用户 review

展示草稿，逐节确认覆盖范围、描述准确性、是否有读者看不懂的地方。

### Step 5：落盘

用户放行后：

1. 写入对应路径
2. `status` 从 `draft` 改为 `current`，`last_reviewed` 填当天
3. 更新已有文档时：小修直接在原文件上改，`last_reviewed` 填当天；大改（结构重组、读者定位调整）先把旧文档 `status` 改为 `outdated` 留作参考，再新写一份

---

## 与其他工作流的关系

| 来源 | 关系 |
|---|---|
| `cs-feat-accept` | 验收后按 `shared-conventions.md` 主动推：接口变更推 dev-guide，用户可见行为变更推 user-guide |
| `cs-feat-design` | 方案第 2 节是 dev-guide 主要信息源；第 1 节是 user-guide 主要信息源 |
| `cs-onboard` | 新仓库接入后可补全基础文档骨架 |
| `cs-arch` (check 模式) | 检测到 design 与代码不一致时，对应 guide 应同步标 `outdated` |
| `cs-decide` | dev-guide 引用的技术选型应来自 decisions，不独立发明 |
| `cs-trick` | dev-guide 用法示例若与 tricks 重合，交叉引用而不重复写 |
| `cs-libdoc` | guide 引用 libdoc 条目做详细参考；libdoc 是零件参考，guidedoc 是任务教程 |

---

## 容易踩的坑

- ❌ 把方案 doc 里的"实现提示"原文搬进 dev-guide——那是内部 spec
- ❌ 没检查已有 guide 就新建——可能造成两份内容冲突
- ❌ guide 写完 `status` 还是 `draft`——落盘必须改 `current`
- ❌ 代码已更新，相关 guide 还是 `current`——应标 `outdated` 并推送更新
- ❌ dev-guide 和 user-guide 内容高度重叠——重叠说明其中一份定位有误
- ❌ 用 guide 存放 spec 信息（不变量、测试约束、根因分析）——这类内容属于 `codestable/`
