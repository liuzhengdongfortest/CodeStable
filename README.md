# EasySDD

**Easy Spec-Driven Development** —— 让 AI 辅助编程不再失控的规约驱动工作流。

> 需求丢给 AI，代码跑出来了，但三个月后没人看懂它怎么设计的？  
> EasySDD 在"需求"和"代码"之间加一层 spec，让每次功能开发都有迹可查。

---

## 为什么需要它

把需求直接丢给 AI 写代码，有三种典型失败模式：

| 失败模式 | 表现 |
|---|---|
| **术语撞车** | AI 引入的新名词和老代码概念重叠，后续改动要反复分辨"这里的 X 是哪种 X" |
| **范围失控** | AI 顺手改了不该动的地方，或把简单需求做成了过度设计的小框架 |
| **无从追溯** | 功能做完没留下设计文档，下次维护等于从零理解一遍 |

EasySDD 的解法很简单：**先写 spec，再写代码，最后闭环验收**。

---

## 工作流一览

EasySDD 包含多条子工作流，覆盖开发全生命周期：

```
新功能   →  [brainstorm] → design → implement → acceptance
BUG 修复 →  report → analyze → fix
沉淀经验 →  compound / tricks / decisions / explore
```

### 新功能开发（easysdd-feature）

| 阶段 | 产出 | 说明 |
|---|---|---|
| ⓪ Brainstorm（可选） | `brainstorm.md` | 模糊想法磨清晰，AI 做思考伙伴 |
| ① Design | `design.md` | 术语表 + 接口契约 + 测试设计，用户分层拍板 |
| ② Implement | 代码 | AI 按方案分步实现，阶段间有 checkpoint |
| ③ Acceptance | `acceptance.md` | 逐层核对方案 + 架构归并 + 收尾确认 |

> 三个正式阶段**不可跳、不可合并、不可并行**。每个阶段退出条件未满足，下一阶段不开始。

### BUG 修复（easysdd-issue）

| 阶段 | 产出 |
|---|---|
| ① Report | `report.md` —— 结构化问题报告 |
| ② Analyze | `analysis.md` —— 根因分析 + 影响面评估 |
| ③ Fix | `fix-note.md` —— 修复记录 + 验证结果 |

### 知识资产沉淀

| 子工作流 | 适用场景 | 存放位置 |
|---|---|---|
| `easysdd-compound` | 踩坑回顾、最佳实践提炼 | `easysdd/learnings/` |
| `easysdd-decisions` | 技术选型、架构决定、约束、规约 | `easysdd/decisions/` |
| `easysdd-tricks` | 可复用的编程模式、库用法技巧 | `easysdd/tricks/` |
| `easysdd-explore` | 代码调研、模块结构梳理 | `easysdd/explores/` |

---

## 目录结构

所有产物统一放在项目根目录的 `easysdd/` 下：

```
easysdd/
├── architecture/        ← 项目架构权威（长期，跨 feature 共享）
├── features/            ← 每个 feature 一个子目录
│   └── 2026-04-11-user-auth/
│       ├── brainstorm.md
│       ├── design.md    ← 含 YAML frontmatter，可被脚本检索
│       └── acceptance.md
├── issues/              ← 每个 issue 一个子目录
│   └── 2026-04-12-login-crash/
│       ├── report.md
│       ├── analysis.md
│       └── fix-note.md
├── learnings/           ← 坑点 & 知识文档
├── decisions/           ← 技术选型 & 架构决定
├── tricks/              ← 编程技巧 & 库用法
├── explores/            ← 代码调研存档
└── tools/
    └── search-yaml.py   ← 按 frontmatter 字段检索所有 spec 文档
```

---

## 核心原则

1. **不从需求直奔代码** —— 任何非 trivial 的工作都先产出 spec，review 通过再动手
2. **术语先锁死** —— spec 第一节就是术语表，新概念必须显式命名，不和既有概念撞车
3. **不变量比测试用例更重要** —— 测试设计的核心是列出"必须永远满足的断言"
4. **阶段间有人工 checkpoint** —— 不允许一口气铺完几百行，截得早比截得晚好
5. **spec 是交付物的一部分** —— 代码交付时同步留下文档，下次维护才有据可查

---

## 快速上手

EasySDD 以 [GitHub Copilot Agent 技能](https://code.visualstudio.com/docs/copilot/copilot-customization) 的形式运行，无需安装额外工具。

**第一步：把技能文件放到你的 Agent 技能目录**（通常是 `~/.agents/skills/`）

**第二步：在已有项目里初始化 easysdd 目录骨架**
> 对 Copilot 说：「在这个项目里用 easysdd」，触发 `easysdd-onboarding` 技能

**第三步：开始第一个功能**
> 对 Copilot 说：「我要做一个用户登录功能」，触发 `easysdd-feature` 技能

---

## 子工作流速查

| 你想做什么 | 触发技能 |
|---|---|
| 新功能（需求清晰） | `easysdd-feature` |
| 新功能（需求模糊，先捋清楚） | `easysdd-feature-brainstorm` |
| 新功能（范围小，快速模式） | `easysdd-feature-fastforward` |
| 修复 BUG | `easysdd-issue` |
| 检查设计是否自洽 / 和代码是否一致 | `easysdd-architecture-check` |
| 新项目接入 easysdd | `easysdd-onboarding` |
| 沉淀踩坑经验 | `easysdd-compound` |
| 归档技术决策 | `easysdd-decisions` |
| 记录编程技巧 | `easysdd-tricks` |
| 探索 & 调研代码库 | `easysdd-explore` |

---

## 设计理念

EasySDD 不是要用繁文缛节拖慢开发。它的核心赌注是：

> **一份好的 spec 花 20 分钟，能省 2 小时的返工和 2 周后的困惑。**

每条子工作流都尽量短——能快速通过的就快速通过，不确定的才停下来对话。`fastforward` 模式专门为范围小的功能设计，写完 spec 直接进实现，没有多余步骤。

---

## License

MIT
