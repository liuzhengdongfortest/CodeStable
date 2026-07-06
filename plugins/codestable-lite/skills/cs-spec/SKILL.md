---
name: cs-spec
description: 维护 project spec 或 epic spec：把需求、架构考量、统一语言和本轮可计划范围写成面向开发者阅读的规格。触发：更新项目主线 spec、创建/调整 epic spec、规格补充/修改/推翻、上游 PRD/SE 澄清。
---

# cs-spec

把当前理解写进正确层级的 spec：项目主线进入 `.cs/spec/`，大需求变更线进入 `.cs/epics/YYYY/MM/DD/{短语}/spec.md`。

## 背景

真实开发不是“规格全清楚再实现”。通常先讨论出一个初始需求，形成 epic，切出一批 issue；做着做着发现规格补充、修改甚至推翻，于是回到 spec 重新整理，再生成新 issue、修改旧 issue 或关闭旧 issue。

`cs-spec` 的职责不是记流水账，而是维护“当前为什么这样”的说明。project spec 是主线真相；epic spec 是大需求的活规格。独立 issue 可以直接引用 project spec；epic issue 先服从 epic spec，等 epic 人工关闭后再把毕业结论合并回 project spec。

## 原则

**文档面向查看。** spec 写出来是给开发者看的。入口文档先让读者知道“这是什么”，再让读者选择“往哪里深入”。不要把 `index.md` 写成文件清单。

**spec 是树，不是二级目录。** 简单内容一篇写完；复杂子系统可以继续拆层。只要一个目录下有多篇文档，就要有该层 `index.md` 统领方向感、统一语言和阅读路径。

**统一语言就近放置。** 不另起 domain 体系。术语放在离它生效范围最近的 `index.md`；术语太多时可拆相邻 `terms.md`，但必须由该层入口指过去。

**写考量，不写流水。** 不创建 `changes.md`。规格变化要呈现为当前需求、架构考量、被排除方案、边界和影响，而不是“某时从 A 变成 B”。

**主线只收毕业结论。** epic 过程中的变化先进入 epic spec；epic 下 issue 关闭也先回写 epic spec。只有 epic 人工关闭后，才把稳定结论合并回 project spec。

**plan 可以分批。** 不必等 epic spec 全局完美。某一批目标、范围、依赖和验证足够清楚，就在 epic `plan.md` 标出本轮可计划范围，交给 `cs-plan`。

## 行动指南

先判断目标层级：

- 项目长期真相、独立小需求沉淀、全局统一语言或架构方向 → 更新 `.cs/spec/`。
- 大需求、跨模块变更、会分多批 issue、规格会反复变化 → 更新 `.cs/epics/YYYY/MM/DD/{短语}/spec.md`。
- 没有现成 epic 但明显需要一条变更线 → 建议先由 `cs-plan` 创建 epic 骨架，或在用户同意后创建目录型 epic。

更新 project spec 时，先读 `.cs/spec/index.md`。按阅读路径找到最近的子层；缺少合适位置时，先补该层 `index.md` 或新建子层入口，不要把结论散落成平级文件。

更新 epic spec 时，先读该 epic 的 `index.md`、`spec.md`、`plan.md` 和相关 project spec。epic spec 要说明它相对 project spec 改变什么、为什么现在这样设计、哪些术语只在本 epic 生效、哪些范围本轮可计划、哪些还悬着。

遇到未知系统、术语、角色、状态和流程，先查 `.cs/`、README、代码、历史 issue/epic、notes 和 project spec。查不到或存在多个可能含义时，向用户提带证据的问题；需要成块调查时，转成 `cs-spec-explore` 的探索型 issue。

## 产物契约

project spec 默认入口是 `.cs/spec/index.md`，使用 `templates/entities/project-spec-index.md`。子层入口用 `templates/entities/spec-section-index.md`。

epic 默认结构是：

- `.cs/epics/YYYY/MM/DD/{短语}/index.md`
- `.cs/epics/YYYY/MM/DD/{短语}/spec.md`
- `.cs/epics/YYYY/MM/DD/{短语}/plan.md`

`spec.md` 必须覆盖：当前方案、需求变化、架构考量、统一语言、本轮可计划范围、暂不计划范围、未确认问题、合并回 project spec 的候选。

`plan.md` 只记录本轮可计划范围、issue 列表、暂停/废弃 issue 和剩余阻碍；不要替 `cs-plan` 生成 issue 正文。

## 收尾汇报

先讲 spec 更新后的当前判断：这次澄清了什么、为什么现在这样考虑、哪些范围本轮可以 plan、哪些仍悬着、是否影响已有 issue。再给文件路径作为索引。

## 应用场景

更新 project spec、创建或调整 epic spec、规格补充/修改/推翻、PRD/SE 文档需要落到开发者能读的规格、实现中发现原规格不成立时使用。

不适用：目标本身还在脑暴时用 `cs-talk`；只需要从已明确范围生成 issue/epic 时用 `cs-plan`；单个 issue 的实现方案用 `cs-design`；project spec 缺口需要先调查时用 `cs-spec-explore`。
