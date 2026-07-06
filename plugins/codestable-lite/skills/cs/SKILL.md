---
name: cs
description: CodeStable LITE 导览：当用户不知道该用哪个 cs-* 技能、想了解 CS 怎么走、或需要把开放诉求路由到合适技能时使用。只导览，不写产物。
---

# cs — CodeStable 导览

`cs` 只回答一个问题：**现在该用哪个技能？**

它不是实体百科，不维护模板，也不替任何子技能跑流程。各实体的产物契约由创建或维护它们的技能自己说明；`cs` 只提供一张轻量路线图，帮助用户少走弯路。

## 核心想法

CodeStable 编排的是软件生命周期，不是 Agent。人在环负责整体判断，AI 负责高效执行和沉淀。

当前主轴是：

```text
talk → spec → plan → design/test/do → close
```

但它不是强制流水线。小 bug、小功能可以直接进入独立 issue；大需求进入 epic spec 后分批切 issue；行为跑偏走投诉通道。

## 该用哪个技能

| 场景 | 用哪个 |
|---|---|
| 第一次接入项目，创建 `.cs/` 骨架 | `cs-onboard` |
| 想法还模糊，用户心里有感觉但没说清 | `cs-talk` |
| 维护项目主线规格或大需求规格 | `cs-spec` |
| 把已明确范围先商量成计划草案，确认后变成 issue / epic | `cs-plan` |
| 系统行为不符合预期、debug、修 bug | `cs-complain` |
| 摸清系统未知，把 project spec 缺口写成探索型 issue | `cs-spec-explore` |
| 为明确 issue 写实现设计 | `cs-design` |
| 执行明确 issue，改代码并验证 | `cs-do` |
| 关闭 issue 或人工确认后的 epic，沉淀 spec/notes/facts/tools | `cs-close` |
| 记可复用知识或启动必读事实 | `cs-note` |
| 人带 AI 跑通未知内部流程 | `cs-maketools` |

## 判断口诀

- **想不清**：`cs-talk`
- **规格要整理**：`cs-spec`
- **规格缺口要调查**：`cs-spec-explore`
- **要切事项**：`cs-plan`
- **坏了**：`cs-complain`
- **要写代码**：先看是否需要 `cs-design`，再 `cs-do`
- **做完了**：`cs-close`
- **值得以后复用**：`cs-note`

## LITE 约束

没有单独的 `cs-refactor`：需要重塑结构时，让它作为某个 feature/bug/issue 的一部分自然发生。

没有主动审计技能：软件没按预期跑时，通过 `cs-complain` 固定场景、建立反馈回路、修复并沉淀。

## 应用场景

用户说“cs 怎么用”“该用哪个技能”“介绍一下 CodeStable”“我现在这种情况走哪一步”时使用。

不适用：写 spec、建 issue、执行代码、关闭事项、记录知识。那些都交给对应子技能。
