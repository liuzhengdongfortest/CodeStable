---
name: easysdd-feature
description: 新功能开发子工作流入口——检查已有产物，路由到 brainstorm/design/implement/acceptance。触发场景："做新功能"、"加个 X 能力"、"有个新需求"、"帮我实现 XX"，且不属于 BUG 修复。已知阶段意图优先触发对应子技能。
---

# easysdd-feature

**easysdd 家族的新功能开发子工作流**——从模糊想法到验收闭环，全程有 spec 存档，防止术语撞车、范围失控、设计决定无从追溯。

本技能是路由中心，不替代子技能干活。

---

## 一、为什么需要 feature 工作流

直接把需求描述丢给 AI 让它写代码，典型失败模式：

1. **术语跟既有代码撞车**：AI 引入的新名词和老代码已有概念语义重叠但叫法不同，后续每次改动都要分辨"这里的 X 是哪种 X"
2. **范围不受控**：AI 顺手改了不该动的地方，或把简单需求实现成过度设计的小框架
3. **不留存档**：功能做完没留下可追溯的设计决定，下次有人在这上面修 BUG 等于从零理解一遍

easysdd-feature 在"需求"和"代码"之间加缓冲层：

```
(想法模糊时 brainstorm) → 方案设计(含测试设计) → 分步实现 → 验收闭环
```

---

## 二、目录安排

本节是 easysdd-feature 子工作流目录约定的唯一定义处。

### feature 目录位置

`easysdd/features/` 下，每个 feature 一个子目录 `{feature}/`，里面住着该 feature 的所有 spec 产物：

```
easysdd/
└── features/                   ← feature 聚合根
    └── {feature}/              ← feature 目录
        ├── brainstorm.md       ← brainstorm note（Stage 0，可选）
        ├── design.md           ← 方案 doc（Stage 1，含 YAML frontmatter + 测试设计）
        └── acceptance.md       ← 验收报告（Stage 3）
```

**feature 目录命名格式**：`YYYY-MM-DD-{英文 slug}`

- **日期前缀**：取该 feature 目录**首次创建**当天的日期，一经确定不变（哪怕后续 slug 改了，日期前缀也不动）
- **英文 slug**：小写字母 + 数字 + 连字符，简短且能一眼看出功能（如 `user-auth`、`export-csv`）
- 两部分用连字符 `-` 连接

> `{feature}` 是占位符，代表具体 feature 目录名。正文用自然语言术语（方案 doc、feature 目录），字面路径看上面目录树。

### 组织规则

1. **一个 feature = 一个 feature 目录**。同一 feature 的 brainstorm / design / acceptance 永远聚合在一起，不允许分散
2. **brainstorm note 也归属 feature 目录**。Stage 0 开始时 slug 未定，先和用户商定临时 slug 建目录；Stage 1 design 如果改了 slug，只改 slug 不改日期前缀，整个目录一起重命名
3. **feature 和 issue 的产物不要混**：`easysdd/features/` 和 `easysdd/issues/` 是并列的，不允许交叉存放

---

## 三、四个阶段（标准流程）

| 阶段 | 子技能 | 主导者 | 产出 |
|---|---|---|---|
| ⓪ brainstorm（可选） | `easysdd-feature-brainstorm` | AI 做思考伙伴，用户拍板 | brainstorm note |
| ① 方案设计（含测试设计） | `easysdd-feature-design` | AI 起草，用户分层拍板 | 方案 doc（YAML frontmatter + 三层结构 + 不变量） |
| ② 分步实现 | `easysdd-feature-implement` | AI 按方案执行 | 代码 + 阶段汇报 |
| ③ 验收闭环 | `easysdd-feature-acceptance` | AI 逐层核对方案，用户终审 | 验收报告 + 架构归并 + 收尾提交确认 |

**阶段之间有硬 checkpoint**：每个阶段退出条件未满足，下一阶段不得开始。用户没明确放行，AI 不自作主张往下走。

**Stage 0 是可选的**：只有想法明显模糊时才走。想法已经清晰的用户直接从 Stage 1 方案设计开始。

## 三·五、Fastforward 模式（快速通道）

当用户需求**已经清晰**且功能**范围足够小**时，可以跳过完整方案设计流程，直接走 fastforward：

```
用户交代需求 → AI 产出紧凑 design.md（含验收标准）→ 用户一次确认 → 直接实现
```

| 触发条件 | 子技能 |
|---|---|
| 用户说"快速模式"、"fastforward"、"直接开干"、"别那么多步骤" | `easysdd-feature-fastforward` |

fastforward 的 `design.md` 与标准流程共用同一 feature 目录，但同样必须带统一 YAML frontmatter；正文内容是精简的 4 节结构（需求摘要 + 设计方案 + **验收标准** + 推进步骤），验收标准在这里就写好，不留占位，后续 `easysdd-feature-acceptance` 直接从中抽取验收点。

**不适合 fastforward 的情况**：跨多个子系统、有术语撞车风险、推进步骤超过 4 步——遇到这些情况告知用户走标准流程。

---

## 四、路由：用户该用哪个子技能

启动本技能后，先 **Glob 检查 `easysdd/features/` 下的已有产物**，不要只听用户口头描述。用户说"设计写完了"不等于方案真的完整——主动读一遍确认。

### 路由表

| 当前状态 | 触发哪个子技能 |
|---|---|
| 只有模糊想法，说不清真问题、边界、或"不做什么" | 询问用户是否先走 brainstorm（见下方判断注意事项） |
| 只有想法但已经清晰（知道做什么、为谁、怎么算成功） | `easysdd-feature-design` |
| 用户主动说"先 brainstorm 一下 / 帮我想想" | `easysdd-feature-brainstorm` |
| 用户说"快速模式"、"fastforward"、"直接开干"、"别那么多步骤" | `easysdd-feature-fastforward` |
| brainstorm note 已存在，用户说"可以进设计了" | `easysdd-feature-design` |
| 方案 doc 三层结构完整（含不变量与架构关系），但代码还没动 | `easysdd-feature-implement` |
| fastforward design.md 已确认（含 YAML frontmatter + 验收标准） | `easysdd-feature-implement` |
| 代码已写完，需要做验收 | `easysdd-feature-acceptance` |
| 不确定方案 doc 是否完整 | 自己读一遍，按上面的表对号入座 |

### Stage 0 的判断注意事项

Stage 0 的识别信号不是"用户描述的字数少"，而是"用户能不能清楚说出这三项"：

- 要解决的**真问题**是什么
- 用户感知的**核心行为**是什么
- 有没有一条明确的**"不做什么"**

三项只要有一项模糊，就是 Stage 0 的候选。但 Stage 0 **不强制**：如果用户明确说"我想清楚了，直接做设计"，不要强行拉他去 brainstorm。如果不确定，问用户一次，让用户选——宁可漏判（让用户直接进设计）也不要误判（逼用户做觉得多余的发散）。

---

## 五、与 easysdd-issue 工作流的边界

- **feature 工作流处理**：新功能、新能力——"从来没有的东西要加进来"
- **issue 工作流处理**：已有代码里的 BUG、异常行为、文档错误——"本来应该好的东西坏了"
- **灰色地带**：如果在 feature 实现阶段发现了顺手可以修的 BUG，**记录为 issue，不在 feature PR 里偷偷修**。保持每条路径的退出条件清晰；混路径会让 checkpoint 失效

---

## 六、相关文档

- `easysdd/SKILL.md` — easysdd 家族根技能，跨阶段共同约束在那里
- `AGENTS.md` — 全项目代码规范，feature 实现时同样遵守
- 架构总入口 — 方案设计阶段需要查阅
