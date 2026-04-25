<div align="center">

# CodeStable

![](./asset/PromotionalImage.png)

[English](./README.en.md) · **中文**

**面向严肃工程的 AI 编码工作流**

厌倦了 OpenSpec 的草台、Oh-My-OpenAgent 的过度设计、Superpowers 的散装——我从 0 写了一套简单轻巧、围绕**人在环**的 AI Harness。

<p>
  <img src="https://img.shields.io/badge/status-beta-F59E0B?style=flat-square" alt="Status"/>
  <img src="https://img.shields.io/badge/skills-22-6366F1?style=flat-square" alt="Skills"/>
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

<table>
<tr><th>分组</th><th>技能</th><th>用途</th></tr>
<tr><td><b>根入口</b></td><td><code>cs</code></td><td>统一入口——介绍体系全貌 + 把开放式诉求路由到正确的 cs-* 子技能。不知道用哪个时就喊它</td></tr>
<tr><td rowspan="1"><b>接入</b></td><td><code>cs-onboard</code></td><td>把 CodeStable 接入到一个新仓库 / 已有零散文档的仓库</td></tr>
<tr><td rowspan="2"><b>需求 & 架构</b></td><td><code>cs-req</code></td><td>整理 / 沉淀原始需求文档</td></tr>
<tr><td><code>cs-arch</code></td><td>起草或更新 <code>codestable/architecture/</code> 下的架构文档</td></tr>
<tr><td><b>路线图</b></td><td><code>cs-roadmap</code></td><td>承载一块大需求的事前规划：概设（模块拆分）+ 架构层详设（接口契约 / 共享协议）+ 子 feature 拆解清单</td></tr>
<tr><td><b>讨论入口</b></td><td><code>cs-brainstorm</code></td><td>想法模糊时的统一讨论入口，做分诊：直接 design / 进 feature 写 brainstorm.md / 移交 roadmap</td></tr>
<tr><td rowspan="5"><b>特性流程</b></td><td><code>cs-feat</code></td><td>新特性子流程入口</td></tr>
<tr><td><code>cs-feat-design</code></td><td>起草 <code>{slug}-design.md</code> 作为后续唯一输入</td></tr>
<tr><td><code>cs-feat-impl</code></td><td>按 design 的推进顺序写代码</td></tr>
<tr><td><code>cs-feat-accept</code></td><td>逐层对照 design 核对实现，做完整验收闭环</td></tr>
<tr><td><code>cs-feat-ff</code></td><td>超轻量通道：不写 design、不分阶段，让 AI 直接做</td></tr>
<tr><td rowspan="4"><b>问题流程</b></td><td><code>cs-issue</code></td><td>问题修复子流程入口</td></tr>
<tr><td><code>cs-issue-report</code></td><td>把脑子里的问题落成可复现、可追溯的 report</td></tr>
<tr><td><code>cs-issue-analyze</code></td><td>找根因、评估修复风险、给方案</td></tr>
<tr><td><code>cs-issue-fix</code></td><td>定点修复 + 验证 + 写 fix-note</td></tr>
<tr><td rowspan="2"><b>重构流程</b></td><td><code>cs-refactor</code></td><td>(beta) 重构主流程</td></tr>
<tr><td><code>cs-refactor-ff</code></td><td>(beta) 轻量重构通道</td></tr>
<tr><td rowspan="3"><b>知识沉淀</b></td><td><code>cs-learn</code></td><td>把踩过的坑 / 好做法沉淀成 learning 文档</td></tr>
<tr><td><code>cs-trick</code></td><td>把可复用的编程模式 / 库用法整理成处方性参考</td></tr>
<tr><td><code>cs-decide</code></td><td>把已拍板的技术选型、架构决定、长期约束记成永久文档</td></tr>
<tr><td rowspan="2"><b>探索 & 文档</b></td><td><code>cs-explore</code></td><td>定向代码探索，把"提问 → 读代码 → 得结论"沉淀成证据</td></tr>
<tr><td><code>cs-guide</code> / <code>cs-libdoc</code></td><td>对外的开发者指南 / 库参考文档</td></tr>
</table>

---

## 工作流示意

CodeStable 的技能不是一条线性流水，而是**分层 + 事件驱动**的：

```
═══════════════════════════════════════════════════════════════════════
 根入口 · 路由                              （任何时刻都可以调用）
───────────────────────────────────────────────────────────────────────
   cs ──▶ 介绍体系 / 把开放式诉求路由到下面任一具体子技能
          （本身不做事，只做分诊和提示）
═══════════════════════════════════════════════════════════════════════
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        （未接入）        （已接入）      （想了解体系）
         走阶段 0       直达 1~4 层 / 横切    给速读
              │
              ▼
═══════════════════════════════════════════════════════════════════════
 阶段 0 · 接入                                  （只在新项目跑一次）
───────────────────────────────────────────────────────────────────────
   cs-onboard ──▶ 生成 codestable/ 骨架 + 释放 reference/、tools/
═══════════════════════════════════════════════════════════════════════
                              │
                              ▼
═══════════════════════════════════════════════════════════════════════
 第 1 层 · 长效档案（"系统现在长什么样"，只记现状）
───────────────────────────────────────────────────────────────────────
   cs-req   ──▶ codestable/requirements/{slug}.md
   cs-arch  ──▶ codestable/architecture/ARCHITECTURE.md
                                       └─ {type}-{slug}.md（子系统）
═══════════════════════════════════════════════════════════════════════
                              │
                              ▼
═══════════════════════════════════════════════════════════════════════
 第 2 层 · 规划（"接下来打算怎么做这块大需求"，大需求才需要）
───────────────────────────────────────────────────────────────────────
   cs-roadmap ──▶ codestable/roadmap/{slug}/
                  把一个"我想要 X 系统"做成完整的事前规划：
                    ① 概设          —— 拆成哪几个模块 / 组件
                    ② 架构层详设    —— 模块间接口契约 / 共享协议
                    ③ 子 feature    —— 把方案分解成多条可执行的 feature
                  ② 是 feature-design 的硬约束输入
                  （小需求可跳过本层，直接进第 3 层）
═══════════════════════════════════════════════════════════════════════
                              │
                              ▼
═══════════════════════════════════════════════════════════════════════
 讨论入口（可选 · 想法模糊时进入，做分诊后路由到下游）
───────────────────────────────────────────────────────────────────────
                          ┌── case 1 已经够清楚 ──▶ cs-feat-design
   cs-brainstorm ────────▶┼── case 2 小需求方向定 ─▶ feature 流（落 brainstorm.md）
                          └── case 3 大需求只有一个词 ─▶ cs-roadmap
═══════════════════════════════════════════════════════════════════════
                              │
                              ▼
═══════════════════════════════════════════════════════════════════════
 第 3 层 · 执行流程（按事件类型选一条进入）
───────────────────────────────────────────────────────────────────────

  ▸ 事件：新增能力                                          ┌──────────┐
       cs-feat-design ──▶ cs-feat-impl ──▶ cs-feat-accept  │ features │
       cs-feat-ff     ──(轻量直通车，跳过 design/accept)─▶  │ /YYYY-…/ │
                                                            └──────────┘

  ▸ 事件：修复缺陷                                          ┌──────────┐
       cs-issue-report ──▶ cs-issue-analyze ──▶ cs-issue-fix│  issues  │
                                                            │ /YYYY-…/ │
                                                            └──────────┘

  ▸ 事件：代码腐化（beta）                                   ┌──────────┐
       cs-refactor / cs-refactor-ff                         │refactors │
                                                            │ /YYYY-…/ │
                                                            └──────────┘
═══════════════════════════════════════════════════════════════════════
                              │
                ▼ 任意阶段觉得"这个值得记下来"都能触发 ▼
═══════════════════════════════════════════════════════════════════════
 横切层 · 知识沉淀（复利工程）
───────────────────────────────────────────────────────────────────────
   cs-learn   ──▶ ┐
   cs-trick   ──▶ ├─▶ codestable/compound/YYYY-MM-DD-{doc_type}-{slug}.md
   cs-decide  ──▶ │     doc_type ∈ { learning, trick, decision, explore }
   cs-explore ──▶ ┘
                   ↑
          下一次 cs-arch / cs-feat-design / cs-issue-analyze
          会回头读 compound/，让经验在新工作里被复用
═══════════════════════════════════════════════════════════════════════
```

**怎么读这张图：**

- **纵向是层次**，不是严格的时间顺序——长效档案层会反复被刷新，规划层只在大需求时进入
- **第 3 层是事件入口**：来了新需求走 feature 流，发现 bug 走 issue 流，发现腐化走 refactor 流
- **横切层是飞轮**：任何流程跑完发现"这事值得记下来"都可以触发沉淀，沉淀的产物又会被下一次同类工作读到——这是 CodeStable "复利"的物理实现

---

## 运行时结构

`/cs-onboard` 跑完后，会在你的项目根下生成一个 `codestable/` 目录——这是 CodeStable 所有产物的聚合根，也是各个子技能在运行时**唯一**会读写的工作区。

```
你的项目/
├── codestable/
│   ├── requirements/                     # 需求实体（"为什么要有这个能力"）
│   │   └── {slug}.md                     # 一个能力一份，扁平不分组
│   │
│   ├── architecture/                     # 架构实体（"用什么结构实现"）
│   │   ├── ARCHITECTURE.md               # 架构总入口 / 索引
│   │   └── {type}-{slug}.md              # 子系统架构 doc（同类 ≥6 份自动收进子目录）
│   │
│   ├── roadmap/                          # 路线图（"接下来打算怎么走"）
│   │   └── {slug}/
│   │       ├── {slug}-roadmap.md         # 主文档：背景 / 拆解 / 排期
│   │       ├── {slug}-items.yaml         # 机器可读子 feature 清单，acceptance 回写状态
│   │       └── drafts/                   # 可选：草稿 / 调研
│   │
│   ├── features/                         # 特性流程聚合根
│   │   └── YYYY-MM-DD-{slug}/            # 一个 feature 一个目录
│   │       ├── {slug}-brainstorm.md      # 可选（cs-brainstorm 产出）
│   │       ├── {slug}-design.md          # 方案（cs-feat-design）
│   │       ├── {slug}-checklist.yaml     # 推进清单（impl 跑、accept 回写）
│   │       └── {slug}-acceptance.md      # 验收报告（cs-feat-accept）
│   │
│   ├── issues/                           # 问题流程聚合根
│   │   └── YYYY-MM-DD-{slug}/
│   │       ├── {slug}-report.md          # 问题报告
│   │       ├── {slug}-analysis.md        # 根因分析（不显然时才有）
│   │       └── {slug}-fix-note.md        # 修复记录
│   │
│   ├── refactors/                        # 重构流程聚合根（beta）
│   │   └── YYYY-MM-DD-{slug}/
│   │       ├── {slug}-scan.md
│   │       ├── {slug}-refactor-design.md
│   │       ├── {slug}-checklist.yaml
│   │       └── {slug}-apply-notes.md
│   │
│   ├── compound/                         # 知识沉淀（复利工程）统一目录
│   │   └── YYYY-MM-DD-{doc_type}-{slug}.md
│   │       # doc_type ∈ {learning, trick, decision, explore}
│   │
│   ├── tools/                            # 跨工作流共享脚本（onboarding 释放）
│   └── reference/                        # 共享参考文档（onboarding 释放）
│       ├── shared-conventions.md         # 跨技能口径 / 路径命名 / 元数据规范
│       ├── system-overview.md            # CodeStable 体系总览 + 场景路由
│       └── ...
│
└── AGENTS.md                             # 在项目根，不在 codestable/ 里
```

**几条要点：**

- 所有产物都聚在 `codestable/` 下，让"上次那个 feature / bug 当时怎么搞的"三秒能找到
- `requirements/` 和 `architecture/` 是**长效档案**（只记现状），`roadmap/` 是**规划层**（接下来怎么走），两者刻意分开
- `features/` `issues/` `refactors/` 用 `YYYY-MM-DD-{slug}/` 一个目录装齐所有相关 spec，不交叉
- `compound/` 是**唯一**的知识沉淀目录，learning / trick / decision / explore 通过 `doc_type` 字段区分而不是分目录——好搜
- `reference/` 是 `cs-onboard` 从技能包复制过来的；要改共享口径，改 `cs-onboard/reference/` 模板，新项目 onboarding 自动带上新版

### 硬约束

> Skill 是独立安装单元，运行时**每个 skill 只能看到自己包内的文件**。A 技能的 SKILL.md 里写 `B-skill/reference/xxx.md` 这种引用在运行时**根本读不到**。
>
> 跨 skill 共享的参考文档必须走"工作项目"这一层：由 `cs-onboard` 从技能包复制到项目的 `codestable/reference/`，其他 skill 用项目相对路径读取。

要改共享口径，改 `cs-onboard/reference/` 下的模板，新项目 onboarding 时带上新版本。

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

<div align="center">

MIT License · 作者 [@liuzhengdong](https://github.com/liuzhengdongfortest)

</div>
