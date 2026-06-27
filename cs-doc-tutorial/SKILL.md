---
name: cs-doc-tutorial
description: 写或更新对外指南——开发者指南（dev-guide）和用户指南（user-guide），产物在项目 docs/ 目录。任务导向（怎么用 X 做 Y），与 doc-api 的零件参考不同。触发：用户说"写文档"、"开发者指南"、"用户指南"，或 issue / epic 收尾时推送。
---

# cs-doc-tutorial

遵循 `.codestable/convention.md`。

代码解决问题，文档让别人能用它。spec / issue 记"做了什么、为什么"，但下游开发者和终端用户不读这些——他们要面向自己角色、可发布的指南。doc-tutorial 从代码和 context 出发，写成读者真能用的指南。

## 两条轨道

| 轨道 | 读者 | 内容 | 路径 |
|---|---|---|---|
| `dev-guide` | 贡献者 / 集成方 / 下游开发者 | setup / 架构解说 / API 说明 / 扩展方式 | `docs/dev/{slug}.md` |
| `user-guide` | 终端用户 | 功能概述 / 操作步骤 / 概念 / FAQ | `docs/user/{slug}.md` |

轨道从"谁读"出发——同一变更常需两份。`docs/dev/` `docs/user/` 是默认，项目有自己结构就从项目。产物**不在 `.codestable/` 下**（面向外部、可发布）。命名 `{slug}.md` 无日期前缀。

## 触发时机

- issue / epic 收尾：接口变了推 dev-guide，用户可见行为变了推 user-guide
- 用户主动 / onboard 后补基础骨架

一句话推，用户说"不用"就别再提。

## frontmatter

```yaml
doc_type: dev-guide | user-guide
slug: {英文连字符}
component: {模块名或 issue/epic slug}
status: draft | current | outdated
summary: {一句话描述涵盖什么}
last_reviewed: YYYY-MM-DD
```

status：draft 待 review；current 有效；outdated 代码已变文档没跟上（留原文，标记后推更新）。正文结构模板见 `reference.md`。

## 工作流

1. **范围**——轨道（dev / user / 都要）+ 新写还是更新 + 信息源（context？同 component 已有 guide？读哪些代码？）
2. **收集**——读 context（术语 / 取舍 / 用户可见行为）+ `search-yaml.py` 搜 docs/ 查已有。已有 guide 标 outdated → 定性为更新
3. **起草**——按轨道结构，status draft。只写面向读者的；**不搬内部实现细节**；术语与 context 一致；代码示例来自实际代码不虚构
4. **review**——逐节确认覆盖 / 准确 / 有没有读者看不懂的
5. **落盘**——放行后 status current + last_reviewed 当天；大改先把旧的标 outdated 再新写

## 坑

- 把内部实现细节搬进 dev-guide
- 没查已有 guide 就新建（两份冲突）
- 落盘还是 draft / 代码变了还 current
- dev 和 user 内容高度重叠（定位有误）
- 用 guide 存 spec 信息（不变量 / 测试约束 → 进 context）
