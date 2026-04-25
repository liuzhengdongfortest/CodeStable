---
name: cs-feat
description: 新功能开发的子流程入口，把"加个 X 能力"从想法走到验收闭环。触发：用户说"做新功能"、"加个 X"、"实现 XX"。只做路由，根据已有产物决定走 brainstorm / design / fastforward / implement / acceptance。不处理 bug。
---

# cs-feat

新功能开发是 CodeStable 里走得最完整的一条流程。AI 直接拿到需求就写代码，三个老问题会反复出现——名字跟原代码对不上、改着改着改出范围、改完不留存档。这条流程在"需求"和"代码"之间塞了一份方案文件，让两边都有个交接点。

整套流程是这样的：

```
(想法还模糊时先去 cs-brainstorm 做分诊) → 方案设计（含测试设计）→ 分步实现 → 验收闭环
```

brainstorm 本身不在 feature 流程内部——它是讨论层的统一入口，会先分诊：你是 case 1（其实已经够清楚，直接进 design）、case 2（小需求方向定了，在 feature 里继续讨论并落 `{slug}-brainstorm.md`）、还是 case 3（大需求装不进一个 feature，移交给 `cs-roadmap` 拆解）。只有 case 2 才会真的在 `codestable/features/{feature}/` 里产出 brainstorm note。

本技能本身不写代码、不写文档，只做一件事：看一下当前 feature 走到哪一步了，告诉用户该触发哪个子技能。

---

## 文件放哪儿

整套 feature 流程的产物都聚在 `codestable/features/` 下，每个 feature 一个独立目录：

```
codestable/
└── features/
    └── {feature}/
        ├── {slug}-brainstorm.md       ← 阶段 0 的产物（可选，仅 brainstorm 判为 case 2 时才落盘）
        ├── {slug}-intent.md           ← 阶段 1 的可选前置草稿（用户自己写的半成品方案）
        ├── {slug}-design.md           ← 阶段 1 的方案文件（带 YAML frontmatter + 测试设计）
        ├── {slug}-checklist.yaml      ← 阶段 1 顺手生成，2/3 阶段更新
        └── {slug}-acceptance.md       ← 阶段 3 的验收报告
```

目录命名是 `YYYY-MM-DD-{英文 slug}`：

- 日期取**首次创建当天**，定了就不动——后续 slug 改了，日期前缀也保持原样
- slug 用小写字母、数字、连字符，简短能一眼看出做的是什么（`user-auth`、`export-csv` 这种）

为什么所有产物聚在一个目录？这样以后回头查"上次那个导出 CSV 的功能当时怎么决定的"，brainstorm、design、acceptance 都在一处，不用东找西找。这也是为什么 feature 和 issue 的产物分别放在 `codestable/features/` 和 `codestable/issues/`——两类问题的归档逻辑不一样，混在一起后面找东西会乱。

如果实现 feature 时顺手发现了一个 bug，正确做法是把它记成新的 issue，**不要在 feature 的 PR 里偷偷修**。混着改会让验收时分不清"这次新增的范围到底是哪些"，后面回头看也找不到为什么改了那行代码。

---

## 四个阶段

| 阶段 | 子技能 | 产出 | 谁主导 |
|---|---|---|---|
| 0 brainstorm（可选，独立入口） | `cs-brainstorm` | case 2 时产出 {slug}-brainstorm.md；case 1 / 3 不落盘 | AI 做思考伙伴，用户拍板 |
| 1 方案设计 | `cs-feat-design` | {slug}-design.md + {slug}-checklist.yaml | AI 起草，用户整体 review |
| 2 分步实现 | `cs-feat-impl` | 代码 + 阶段汇报 | AI 按方案执行 |
| 3 验收闭环 | `cs-feat-accept` | {slug}-acceptance.md | AI 逐层核对，用户终审 |

阶段之间有人工 checkpoint。为什么要这样卡？一是让用户在每个阶段结束时有一次明确的把关机会，二是防止 AI 一口气从需求跑到代码、跑出来用户才发现走偏了。所以默认情况下，上一个阶段没拿到用户明确放行，下一个阶段就别开始。

阶段 0 是可选的，且是 feature 流程的**外部入口**——`cs-brainstorm` 同时服务 feature 和 roadmap。只有想法明显模糊时才走；已经能清楚说出"做什么、为谁做、怎么算成功"时直接从阶段 1 开始。brainstorm 判为 case 3（大需求）时讨论会被移交给 `cs-roadmap`，不再回到 feature 流程——等 roadmap 拆出子 feature 之后，每条子 feature 才会从 `cs-feat-design` 的"从 roadmap 条目起头"入口进来。

### Fastforward 模式

需求已经很清楚、范围又小的时候，走完整四阶段会嫌啰嗦。这时候有 fastforward：

```
用户说需求 → AI 写一份精简 {slug}-design.md（包含验收标准）→ 用户一次确认 → 直接实现
```

触发：用户说"快速模式"、"fastforward"、"直接开干"、"别那么多步骤"这一类，去 `cs-feat-ff`。

fastforward 的 `{slug}-design.md` 跟标准流程共用同一个 feature 目录，frontmatter 也一致，只是正文压成 4 节（需求摘要 + 设计方案 + 验收标准 + 推进步骤）。验收标准在这里就要写好，不留占位——因为后面 acceptance 阶段会直接从这里抽。

什么时候**别**走 fastforward：跨多个子系统、有术语冲突风险、推进步骤超过 4 步。遇到这几种情况就劝用户走标准流程，原因是范围一大，跳过 design 阶段意味着 AI 和用户在同一份方案上没共同确认过，实现完很容易发现彼此理解的不是同一回事。

---

## 路由：用户现在该走哪个子技能

进入本技能后，先 Glob 一下 `codestable/features/` 看已经有哪些产物。**不要只听用户口头描述**——用户说"设计写完了"不一定真完整，自己读一遍才有数。

| 当前状态 | 触发哪个子技能 |
|---|---|
| 想法模糊，说不清真问题 / 边界 / 不做什么 | `cs-brainstorm`（判断方法见下） |
| 想法清晰（知道做什么、为谁、怎么算成功） | `cs-feat-design` |
| 用户说"开一个新需求 / 起个草稿 / 新建一个 feature"，想自己写半成品方案 | `cs-feat-design` 的"初始化模式"（建目录 + 空 `{slug}-intent.md`，让用户填完再回来） |
| 用户主动说"先 brainstorm 一下"、"有个想法没想清楚" | `cs-brainstorm` |
| `{slug}-intent.md` 已存在且填好，用户说可以进设计了 | `cs-feat-design`（读 intent 作输入） |
| 用户说"快速模式"、"fastforward"等 | `cs-feat-ff` |
| `{slug}-brainstorm.md` 已存在，用户说可以进设计了 | `cs-feat-design` |
| `{slug}-design.md` 已 approved、代码还没动 | `cs-feat-impl` |
| fastforward `{slug}-design.md` 已确认 | `cs-feat-impl` |
| 代码已写完，要做验收 | `cs-feat-accept` |
| 用户说的是"我想要一个 X 系统"这种大需求 | 转 `cs-brainstorm` 分诊（大概率判为 case 3 → `cs-roadmap`） |
| roadmap 里某条子 feature 该启动了 | `cs-feat-design` 的"从 roadmap 条目起头"入口 |
| 不确定 `{slug}-design.md` 是否完整 | 自己读一遍，按上面对号入座 |

### 怎么判断用户该不该走阶段 0

判断信号不是"用户描述的字数少"，而是用户能不能清楚说出这三件事：

- 要解决的真问题是什么
- 用户感知的核心行为是什么
- 有没有一条明确的"不做什么"

三项有一项模糊，brainstorm 就值得走。但别强推——用户明确说"我想清楚了，直接做设计"就尊重他的判断。不确定时问一句让用户选。宁可漏判（让用户直接进设计），也别误判（逼一个想清楚的用户做 TA 觉得多余的发散）。

### brainstorm 和 intent 怎么选

两者都是 design 的前置，区别在**谁在主导收敛**：

- brainstorm：用户脑子里还模糊，希望通过对话想清楚，AI 问用户答。**注意**：brainstorm 是独立入口，会先分诊；判为 case 3（大需求）时讨论会被移交给 `cs-roadmap`，不会回到 feature 流程。只有 case 2（小需求）才产出 `{slug}-brainstorm.md`
- intent：用户自己已经想好大致做法（比如一段 100 字的描述 + 相关数据结构），只是懒得口述，直接写成 `{slug}-intent.md` 给 AI 读

用户说"开一个新需求"这种模糊触发时，默认问一句"你想先聊清楚（brainstorm）还是自己写草稿（intent）？"，别自己挑一个推进。

---

## 与 issue 工作流的边界

- feature 处理"从来没有的东西要加进来"——新功能、新能力
- issue 处理"本来应该好的东西坏了"——bug、异常、文档错误

灰色地带在前面已经讲过：feature 实现时发现的 bug 记成新 issue，不在 feature PR 里顺手修。

---

## 相关文档

- `codestable/reference/system-overview.md` — CodeStable 体系总览和场景路由
- `codestable/reference/shared-conventions.md` — 跨阶段共享口径、目录结构、{slug}-checklist.yaml 生命周期
- `AGENTS.md` — 全项目代码规范，feature 实现时同样遵守
- 项目架构总入口 — 方案设计阶段需要查
