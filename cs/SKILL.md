---
name: cs
description: CodeStable 工作流根入口，介绍体系全貌并把诉求路由到对应 cs-* 子技能。触发：用户只输入 `cs`、说"介绍一下 codestable"、"该用哪个技能"、"不知道用哪个"，或诉求还很开放未收敛。本技能只做路由不做事。
---

# cs

`cs` 是 CodeStable 工作流家族的统一入口。用户开口时大概率不会指名某个 `cs-xxx` 子技能——他可能只说"我想加个权限校验"、"这个地方有 bug"、"你给我介绍下 codestable"，甚至只发一个 `cs`。本技能负责接住这些开放式输入，弄清意图，再把用户路由到对的子技能。

**两件事，仅此两件**：

1. 当用户带着具体诉求来 → 匹配场景路由表，告诉用户该触发哪个 `cs-*`，并简单说明为什么是这个
2. 当用户只是想了解体系 / 说不清想做什么 → 给一段精简的体系速读 + 让用户挑或描述更具体的诉求

**本技能不做事**：不写 spec、不读写 `codestable/` 下的内容产物、不替子技能跑流程。它的产出只有"建议触发哪个子技能"。

---

## 收到调用先做的扫描

在回应用户之前先做这些（每次都做，不长，几个 tool 调用就够）：

1. **看仓库有没有接入 CodeStable**——`Glob codestable/` 看顶层目录是否存在
2. **如果存在**——`Read codestable/reference/system-overview.md`（如果有）作为更全的体系参考；`Glob` 一下 `codestable/features/` `codestable/issues/` `codestable/roadmap/` 看现在进行中的工作有哪些（拿目录名就够，不要逐份读）
3. **如果不存在**——记下来，后面提示用户先走 `cs-onboard`
4. **看用户原话**——TA 是开放式提问还是带着具体诉求？带诉求就匹配路由表，没诉求就给体系介绍

扫完才能回应。让用户感觉你心里有数，不是凭空在问。

---

## 体系一图速读（用户没具体诉求 / 让你介绍时讲这个）

CodeStable 把软件开发活动建模成 **6 个实体 + 3 个流程**，所有产物都聚在项目根的 `codestable/` 目录下：

```
codestable/
├── requirements/    需求实体（"为什么要有这个能力"，只记现状）
├── architecture/    架构实体（"系统现在长什么样"，只记现状）
├── roadmap/         规划层（"接下来打算怎么做这块大需求 + 模块怎么切 + 接口怎么定"）
├── features/        新增能力的 spec 聚合根（design / impl / accept）
├── issues/          修 bug 的 spec 聚合根（report / analyze / fix）
├── refactors/       重构的 spec 聚合根（beta）
└── compound/        知识沉淀（learning / trick / decision / explore）
```

**三条流程**：

- **新增能力**：`cs-feat-design` → `cs-feat-impl` → `cs-feat-accept`（想法模糊先走 `cs-brainstorm` 分诊）
- **修 bug**：`cs-issue-report` → `cs-issue-analyze` → `cs-issue-fix`
- **重构**（beta）：`cs-refactor` / `cs-refactor-ff`

**横切**：任何流程跑完发现"这事值得记下来" → `cs-learn` / `cs-trick` / `cs-decide` / `cs-explore` 沉淀到 `compound/`。

**核心理念**：编排的是软件本身的生命周期（需求、架构、特性、bug、决策），而不是 Agent。人在环——程序员对整体把控负责，AI 是高效的执行体。

> 项目已 onboard 的话，更详细的总览看 `codestable/reference/system-overview.md`。

---

## 场景路由表

匹配用户的话到表里某行，然后告诉用户："你这个诉求建议走 `cs-xxx`，因为 {一句话理由}"。

| 用户说什么 / 想做什么 | 路由到 |
|---|---|
| 仓库还没有 `codestable/` 目录 | **先 `cs-onboard`**——所有其他 cs-* 技能都依赖这个目录存在 |
| 想法还模糊 / "有个想法没想清楚" / "先聊聊" / "不知道是不是新功能" | `cs-brainstorm`（分诊后路由到 design / feature-brainstorm 落盘 / roadmap） |
| 新功能 / 新能力 / "加个 X" / "实现 XX" | `cs-feat`（路由 design / ff / impl / accept） |
| BUG / 异常 / 报错 / "这里不对" / "文档错了" | `cs-issue`（路由 report / analyze / fix） |
| 代码优化 / 重构 / 重写（行为不变） | `cs-refactor` / `cs-refactor-ff`（beta） |
| 摸代码 / "X 是怎么实现的" / 提问调研 | `cs-explore` |
| 补 / 更新需求文档 | `cs-req` |
| 补 / 更新 / 检查架构文档 / "刷新架构 doc" / "做架构体检" | `cs-arch` |
| 大需求拆解 / "我想要一个 X 系统" / 排期规划 / 设计模块拆分 + 接口契约 | `cs-roadmap` |
| 技术选型 / 长期约束 / 编码规约 | `cs-decide` |
| 踩坑回顾 / 经验总结 / "这事值得记下来" | `cs-learn` |
| 可复用编程模式 / 库用法 / "以后做 X 就该这样" | `cs-trick` |
| 开发者指南 / 用户指南 | `cs-guide` |
| 库 API 参考 | `cs-libdoc` |
| 用户在 feature / issue 流程中间，问"下一步该干啥" | 路由到对应流程的入口（`cs-feat` / `cs-issue`），让该入口判断当前阶段 |

**判不出来 / 用户说得太抽象**："听起来像 {猜测}，但你描述里 {缺什么}。是 {选项 A} 还是 {选项 B}？" 让用户选，不要硬猜。

---

## 几种需要特别留心的情况

### 仓库还没接入

用户开口想做任何 cs-* 流程的事，但 `codestable/` 不存在 → 说明这一点，建议**先 `cs-onboard`**。不要自作主张直接路由到 cs-feat / cs-issue 等——它们的 SKILL.md 都假设 `codestable/` 已经存在。

### 大需求被误当成 feature

用户说的是"我想要一个权限系统 / 通知中心 / SSO 接入"这类**一眼看出做不完一个 feature** 的诉求 → 不要路由到 `cs-feat`，路由到 `cs-brainstorm`（大概率会判为 case 3 → `cs-roadmap`）或直接 `cs-roadmap`。理由：直接起 feature 会变成巨型 design 塞不下。

### "改一下 X" 但 X 是已有功能

用户说"改一下 X 的 Y 行为" → 先问一句这是 **bug 修复**（X 现在表现错了）还是 **需求变更**（X 现在的表现没错，但产品策略变了）：
- bug → `cs-issue`
- 需求变更 → `cs-req`（改需求文档）+ 之后 `cs-feat` 跑实现

### 进行中的工作

扫描看到 `codestable/features/` 或 `codestable/issues/` 下已经有跟用户描述相关的目录 → 提一句"看到 `features/2026-04-22-xxx/` 已经存在，是接着做这个吗？" 让用户确认是续作还是开新的，避免无意中创建重复 feature。

### 沉淀类技能的细分

learning / trick / decision / explore 容易混。判别口诀：

- 回顾"做 X 时踩了 Y" → `cs-learn`
- 处方"以后做 X 就这样做" → `cs-trick`
- 规定"全项目今后都按 X 来" → `cs-decide`
- 调查"X 现在是什么样" → `cs-explore`

判不出问用户："这个你想记成 {踩坑回顾 / 复用处方 / 长期规约 / 调研存档} 哪一种？"

---

## 介绍模式（用户只说想了解 / 不知道做什么）

按这个顺序讲，**不要一次倒出全部**：

1. 一句话：CodeStable 是面向严肃工程的 AI 编码工作流，编排软件生命周期而不是 Agent
2. 6 实体 + 3 流程的速读图（见上面"体系一图速读"）
3. 问用户："你现在最想从哪儿开始？" 给三个具体引子：
   - "我有个新功能想做" → cs-feat
   - "代码里有个 bug" → cs-issue
   - "项目还没接入 CodeStable" → cs-onboard

收住，别把所有子技能的细节都讲一遍。用户问到具体某个再展开。

---

## 退出

本技能没有"落盘"步骤。退出条件就一条：

- [ ] 已经告诉用户下一步触发哪个具体的 `cs-*` 子技能（或确认用户只是来了解体系，没要做事）

输出形如：

> 你这个诉求建议走 **`cs-xxx`**——{一句话理由：因为它专门处理 X 类场景}。
> 触发后它会 {简述会发生什么：会先扫已有 spec / 会让你先描述 / 会进入分诊 / ...}。
> 现在切到 `cs-xxx` 吗？

确认后由用户触发那个子技能（或在同一会话里直接用对应技能名），本技能这次的工作结束。

---

## 不做的事

- **不读写 `codestable/` 下的内容产物**——不打开 design.md、不改 items.yaml、不创建 feature 目录。这些是子技能的事
- **不替子技能做决策**——比如不在本技能里做 brainstorm 分诊（那是 `cs-brainstorm` 的事），不在本技能里判 cs-arch 走哪个模式
- **不一次推荐多个技能**——每次只指一条路。用户有两个独立诉求就分两轮：先做完 A 再回来做 B
- **不重复体系总览的细节**——`codestable/reference/system-overview.md`（onboard 后存在）才是权威完整版，本技能只放精简速读
- **不绕过 `cs-onboard`**——仓库没接入就先 onboard，不要试图直接路由到下游
