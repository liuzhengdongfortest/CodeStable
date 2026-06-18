<div align="center">

# CodeStable

![](./asset/PromotionalImage.png)

[English](./README.en.md) · **中文**

**面向严肃工程的 AI 编码工作流**

厌倦了 OpenSpec 的草台、Oh-My-OpenAgent 的过度设计、Superpowers 的散装——我从 0 写了一套简单轻巧、围绕**人在环**的 AI Harness。

<p>
  <img src="https://img.shields.io/badge/status-beta-F59E0B?style=flat-square" alt="Status"/>
  <img src="https://img.shields.io/badge/skills-23-6366F1?style=flat-square" alt="Skills"/>
  <img src="https://img.shields.io/badge/license-MIT-10B981?style=flat-square" alt="License"/>
</p>

</div>

---

## 安装

```bash
npx skills add https://github.com/liuzhengdongfortest/CodeStable
```

只需要一键，开始工作：

```bash
/cs-onboard
```

之后日常使用时，不知道该用哪个技能就喊根入口：

```bash
/cs
```

`cs` 会读你的诉求，告诉你这次该走哪个 `cs-xxx`。

---

## 缘起

我在开发一套新的 Harness Agent（[MA](https://github.com/liuzhengdongfortest/MA)），一开始当然是 VibeCoding——我只写设计和需求，代码由 AI 来改。这样支撑了大部分特性的开发。直到有一天 Codex 反复解决不了一个我认为比较简单的问题，并且反复在同一个地方犯错。我就知道项目需要一套工作流来维持它继续进行了。

我调研了 OpenSpec、SuperPowers、Oh-My-OpenAgent 这一类工具，没一个用着顺手：

- **OpenSpec** 太简单，没有复利工程，生成的 Spec 抽象到人类没法读
- **SuperPowers** 没有流程约束，不知道该用哪个
- **Oh-My-OpenAgent** 太重，且哲学上认为"人介入 = 失败"

CodeStable 的目标是**解决严肃工程的软件实现和编码问题**，不是造一个新名词、追求热点。

---

## 与其他框架的核心区别：编排的目标是谁

我看了一圈现在主流的 AI 编码框架——Superpowers、CCW、Oh-My-OpenAgent 等等——它们其实都在做**同一件事**：

> **如何把 Agent 编排得更好。** 让它们组队、协作、头脑风暴、跑流水线、自动接力。围绕的实体始终是 **Agent**。

CodeStable 走的是**另一个方向**：

> **编排的不是 Agent，而是软件本身的生命周期。** 围绕的实体是**构成软件的要素**——每一个需求、每一个架构决定、每一个特性、每一个 bug、每一条历史里留下来的约束。

<table>
<tr><th></th><th>Agent 编排派</th><th>CodeStable</th></tr>
<tr><td><b>核心实体</b></td><td>Agent / Role / Team</td><td>Requirement / Architecture / Feature / Issue / Decision</td></tr>
<tr><td><b>主线问题</b></td><td>Agent 之间怎么分工、传递、协调？</td><td>软件的需求、约束、决策怎么被记下来、被检索、被复用？</td></tr>
<tr><td><b>状态存在哪</b></td><td>Agent 的 session / 消息总线 / 队列</td><td>项目里的 <code>codestable/</code> 文件树（人和 AI 都能读）</td></tr>
<tr><td><b>解决的痛点</b></td><td>单 Agent 能力不够，需要协同放大</td><td>软件复杂度膨胀撑破上下文、隐知识丢失、需求漂移</td></tr>
<tr><td><b>对人的定位</b></td><td>人少介入越好，理想是全自动</td><td>人在环 —— 程序员对整体把控负责，AI 是高效的执行体</td></tr>
</table>

![](./asset/CodeStableVSAgent.png)


**这两个方向没有谁对谁错。**

如果你的任务是"用 AI 跑一个端到端的自动化产线"、"让多个 Agent 互相讨论方案"，Agent 编排派会更顺手。

如果你的任务是"维护一个会跨年迭代的严肃软件"、"让今天写下的需求和决策三个月后还能被准确召回"——那 CodeStable 这套以软件要素为中心的建模会更合适。

我做 CodeStable 是因为我相信：**软件工程的混乱本质上不是 Agent 不够强，而是要素没被组织好**。Agent 再强，也写不了一个把需求、架构、历史决策全丢失的项目。

---

## 设计：6 个实体 + 3 个流程

CodeStable 顺着软件编码的真实流程来设计，把开发活动建模成 **6 个实体** 和 **3 个流程**。

### 6 个实体

| 实体 | 英文 | 干什么 |
|------|------|--------|
| **需求** | requirements | 原始用户故事、当时的讨论与权衡。最终的逃生通道——代码烂成一坨屎时，可以摒弃所有代码、让 AI 重新生成 |
| **架构** | architecture | 为实现需求，系统的编排层长什么样。文档要尽可能精简、统一，**给人读的**，不是给 AI 自嗨的 |
| **路线图** | roadmap | "我想要一个权限校验系统"——直接塞 feature AI 接不住，先拆成路线图分步推进 |
| **特性** | feature | 实际落地的工程执行过程，人与 AI 共同协作，对 design / 实现 / 验收负责 |
| **问题** | issue | 开发完成后的 BUG 单子，AI 和人一同解决 |
| **知识** | compound | 复利工程的知识库，沉淀踩过的坑、好做法、技术决策 |

### 3 个流程

| 流程 | 关键技能链 | 说明 |
|------|------------|------|
| **特性引入** | `cs-feat` → `cs-feat-design` → `cs-feat-impl` → `cs-feat-accept` | 想清楚 → 综合架构设计 → 逐步编码 → 验收测试。各位程序员怎么顺手怎么来 |
| **问题修改** | `cs-issue-report` → `cs-issue-analyze` → `cs-issue-fix` | 跟 AI 说哪里有问题 → 让 AI 分析根因 → 让 AI 定点修复 |
| **代码重构** | `cs-refactor` (beta) | 软件架构腐化不是一蹴而就的。AI 辅助重构，但**终归是人在重构**——还在迭代中，欢迎赐教 |


---

## 技能总览

完整技能目录见 [SKILL_CATALOG.md](./SKILL_CATALOG.md)。日常不知道用哪个时直接调用 `/cs`，它会按诉求路由到对应技能。

---

## 工作流示意

CodeStable 的技能不是一条线性流水，而是**分层 + 事件驱动**的：根入口路由、onboard、长效档案、roadmap 规划、feature / issue / refactor 执行流，以及横切的知识沉淀。

完整示意图见 [WORKFLOW.md](./WORKFLOW.md)。

---

## 运行时结构

`/cs-onboard` 跑完后，会在你的项目根下生成 `codestable/`，作为 requirements、architecture、roadmap、features、issues、refactors、compound、tools 和 reference 的聚合根。

完整目录说明和跨 skill 引用约束见 [WORKFLOW.md](./WORKFLOW.md)。

---

## 设计哲学

CodeStable 与 OMO 做的是**完全相反**的哲学。

- OMO 认为：人只要干预就是失败的信号
- CodeStable 认为：**程序员是软件编码中的在环对象**——可以对黑盒实现不了解，但对整体实现必须有所把控，必要时也可深入

软件架构必须要 **可演进**、**可观测**、**可控制**。

也许这一点在 AI 发展强大以后会变得不再重要，但**当下这样做能让程序员在现状下舒服**——这就是价值所在。

CodeStable 面向真实开发场景，对此进行建模，期望通过一个闭环系统处理开发中常见的问题。**现有大部分框架围绕 AI 建模，而不是围绕人。** 我认为这些框架的作者驱动 AI 的能力很强，但绝对不是严肃软件的开发者——因为缺少对软件开发中需求和设计的基础组织能力，缺乏对代码实现的尊重。

---

## Roadmap

CodeStable 会根据模型能力的发展进行调整。如果未来某个模型做到某个模块的稳定产出，那么这个模块就可以删除。

- [ ] 代码重构流程需要强化（`cs-refactor` 还在 beta）
- [ ] ……

欢迎在 Issue 区贴你的真实开发困境和重构经验。

---
## Star History

[![Star History Chart](https://api.star-history.com/chart?repos=liuzhengdongfortest/CodeStable&type=date&legend=top-left)](https://www.star-history.com/?repos=liuzhengdongfortest%2FCodeStable&type=date&legend=top-left)

<div align="center">

MIT License · 作者 [@liuzhengdong](https://github.com/liuzhengdongfortest)

</div>
