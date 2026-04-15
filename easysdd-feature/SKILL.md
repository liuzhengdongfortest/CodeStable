---
name: easysdd-feature
description: 做新功能开发时进入这套子流程——把"加个 X 能力"从模糊想法走到验收闭环，中间有方案文件做存档，AI 和用户后面回头都能查到当时怎么想的、为什么这样定的。触发场景偏向新增能力（"做新功能"、"加个 X"、"实现 XX"），不处理已有代码的 bug。本技能只做路由，根据已有产物决定下一步走 brainstorm / design / fastforward / implement / acceptance 中的哪一个。
---

# easysdd-feature

新功能开发是 easysdd 里走得最完整的一条流程。AI 直接拿到需求就写代码，三个老问题会反复出现——名字跟原代码对不上、改着改着改出范围、改完不留存档。这条流程在"需求"和"代码"之间塞了一份方案文件，让两边都有个交接点。

整套流程是这样的：

```
(想法还模糊时先 brainstorm) → 方案设计（含测试设计）→ 分步实现 → 验收闭环
```

本技能本身不写代码、不写文档，只做一件事：看一下当前 feature 走到哪一步了，告诉用户该触发哪个子技能。

---

## 文件放哪儿

整套 feature 流程的产物都聚在 `easysdd/features/` 下，每个 feature 一个独立目录：

```
easysdd/
└── features/
    └── {feature}/
        ├── brainstorm.md       ← 阶段 0 的产物（可选）
        ├── design.md           ← 阶段 1 的方案文件（带 YAML frontmatter + 测试设计）
        ├── checklist.yaml      ← 阶段 1 顺手生成，2/3 阶段更新
        └── acceptance.md       ← 阶段 3 的验收报告
```

目录命名是 `YYYY-MM-DD-{英文 slug}`：

- 日期取**首次创建当天**，定了就不动——后续 slug 改了，日期前缀也保持原样
- slug 用小写字母、数字、连字符，简短能一眼看出做的是什么（`user-auth`、`export-csv` 这种）

为什么所有产物聚在一个目录？这样以后回头查"上次那个导出 CSV 的功能当时怎么决定的"，brainstorm、design、acceptance 都在一处，不用东找西找。这也是为什么 feature 和 issue 的产物分别放在 `easysdd/features/` 和 `easysdd/issues/`——两类问题的归档逻辑不一样，混在一起后面找东西会乱。

如果实现 feature 时顺手发现了一个 bug，正确做法是把它记成新的 issue，**不要在 feature 的 PR 里偷偷修**。混着改会让验收时分不清"这次新增的范围到底是哪些"，后面回头看也找不到为什么改了那行代码。

---

## 四个阶段

| 阶段 | 子技能 | 产出 | 谁主导 |
|---|---|---|---|
| 0 brainstorm（可选） | `easysdd-feature-brainstorm` | brainstorm.md | AI 做思考伙伴，用户拍板 |
| 1 方案设计 | `easysdd-feature-design` | design.md + checklist.yaml | AI 起草，用户整体 review |
| 2 分步实现 | `easysdd-feature-implement` | 代码 + 阶段汇报 | AI 按方案执行 |
| 3 验收闭环 | `easysdd-feature-acceptance` | acceptance.md | AI 逐层核对，用户终审 |

阶段之间有人工 checkpoint。为什么要这样卡？一是让用户在每个阶段结束时有一次明确的把关机会，二是防止 AI 一口气从需求跑到代码、跑出来用户才发现走偏了。所以默认情况下，上一个阶段没拿到用户明确放行，下一个阶段就别开始。

阶段 0 是可选的——只有想法明显模糊时才走。如果用户已经能清楚说出"做什么、为谁做、怎么算成功"，直接从阶段 1 开始更省事。

### Fastforward 模式

需求已经很清楚、范围又小的时候，走完整四阶段会嫌啰嗦。这时候有 fastforward：

```
用户说需求 → AI 写一份精简 design.md（包含验收标准）→ 用户一次确认 → 直接实现
```

触发：用户说"快速模式"、"fastforward"、"直接开干"、"别那么多步骤"这一类，去 `easysdd-feature-fastforward`。

fastforward 的 design.md 跟标准流程共用同一个 feature 目录，frontmatter 也一致，只是正文压成 4 节（需求摘要 + 设计方案 + 验收标准 + 推进步骤）。验收标准在这里就要写好，不留占位——因为后面 acceptance 阶段会直接从这里抽。

什么时候**别**走 fastforward：跨多个子系统、有术语撞车风险、推进步骤超过 4 步。遇到这几种情况就劝用户走标准流程，原因是范围一大，跳过 design 阶段意味着 AI 和用户在同一份方案上没对齐过，实现完很容易发现彼此理解的不是同一回事。

---

## 路由：用户现在该走哪个子技能

进入本技能后，先 Glob 一下 `easysdd/features/` 看已经有哪些产物。**不要只听用户口头描述**——用户说"设计写完了"不一定真完整，自己读一遍才有数。

| 当前状态 | 触发哪个子技能 |
|---|---|
| 想法模糊，说不清真问题 / 边界 / 不做什么 | 问一下要不要先走 brainstorm（判断方法见下） |
| 想法清晰（知道做什么、为谁、怎么算成功） | `easysdd-feature-design` |
| 用户主动说"先 brainstorm 一下" | `easysdd-feature-brainstorm` |
| 用户说"快速模式"、"fastforward"等 | `easysdd-feature-fastforward` |
| brainstorm.md 已存在，用户说可以进设计了 | `easysdd-feature-design` |
| design.md 三层结构完整、代码还没动 | `easysdd-feature-implement` |
| fastforward design.md 已确认 | `easysdd-feature-implement` |
| 代码已写完，要做验收 | `easysdd-feature-acceptance` |
| 不确定 design.md 是否完整 | 自己读一遍，按上面对号入座 |

### 怎么判断用户该不该走阶段 0

判断信号不是"用户描述的字数少"，而是用户能不能清楚说出这三件事：

- 要解决的真问题是什么
- 用户感知的核心行为是什么
- 有没有一条明确的"不做什么"

三项有一项模糊，brainstorm 就值得走。但别强推——如果用户明确说"我想清楚了，直接做设计"，就尊重他的判断。不确定的时候问一句让用户选。宁可漏判（让用户直接进设计），也别误判（逼一个想清楚的用户做他觉得多余的发散）。

---

## 与 issue 工作流的边界

- feature 处理"从来没有的东西要加进来"——新功能、新能力
- issue 处理"本来应该好的东西坏了"——bug、异常、文档错误

灰色地带在前面已经讲过：feature 实现时发现的 bug 记成新 issue，不在 feature PR 里顺手修。

---

## 相关文档

- `easysdd-core/SKILL.md` — easysdd 家族根技能，跨阶段共同约束在那里
- `AGENTS.md` — 全项目代码规范，feature 实现时同样遵守
- 项目架构总入口 — 方案设计阶段需要查
