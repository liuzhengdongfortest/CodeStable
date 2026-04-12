---
name: easysdd
description: easysdd 工作流家族的根技能——介绍工作流体系并把用户路由到正确子技能。触发场景：用户提到"easysdd"、"sdd"、"规约驱动"、"怎么用这套流程"、"我该用哪个技能"、"从哪开始"，或描述了新功能但还没决定切入阶段。已知意图（brainstorm/设计/实现/验收/BUG/探索等）优先触发对应子技能而非本技能。
---

# easysdd

**Easy Spec-Driven Development** —— 本项目的规约驱动开发工作流家族的根技能。

本技能是中心,不替代任何子技能干活。它的职责只有四件事:**介绍**、**路由**、**沉淀共识**、**承载扩展**。具体阶段的操作手册都在子技能里,本技能不重复。

---

## 一、easysdd 是什么

一句话:**任何非 trivial 的工作,先产出 spec,再写代码,最后做闭环验收。**

直接给 AI 一段需求描述就让它写代码,典型失败模式有三种:

1. **术语跟既有代码撞车**:AI 引入的新名词和老代码已有概念语义重叠但叫法不同,后续每次改动都要分辨"这里的 X 是哪种 X"
2. **范围不受控**:AI 顺手改了不该动的地方,或把简单需求实现成过度设计的小框架
3. **不留存档**:功能做完没留下可追溯的设计决定,下次有人在这上面修 BUG 等于从零理解一遍

easysdd 在"需求"和"代码"之间加缓冲层(spec → 不变量 → 分步实现 → 闭环验收),让新代码落地时已经有完整的约束和存档。**核心原则**(适用于所有 easysdd 子工作流):

1. **不从需求直奔代码**。任何非 trivial 的工作都先产出 spec doc,用户 review 通过后再动手
2. **术语先锁死**。spec 里第一节就是术语表;新引入的概念必须显式命名,不能和既有概念撞车
3. **不变量比测试用例更重要**。"测试设计"的核心是列"代码上线后必须永远满足的断言",测试用例只是验证手段
4. **实现分阶段,阶段间有人工 checkpoint**。不允许一口气铺完几百行——早一步截停总比晚一步好
5. **spec doc 是交付物的一部分**。代码交付时同步留下 doc,下一次维护才有据可查

> 这五条原则是所有 easysdd 子工作流共享的——如果某个子技能没有显式提到,默认仍然适用。

---

## 二、目录安排(整个 easysdd 家族共享)

**本节是整个 easysdd 家族目录约定的唯一定义处**。本技能下文以及所有子技能、工作流文档在正文里都**用自然语言术语**(方案 doc、feature 目录……)引用产物,它们的字面位置看下面这棵目录树就能找到。目录结构要改,只在本节改一次。

### easysdd 根目录下有什么

`easysdd/` 下有八个子目录,每个的用途都固定:

- **`architecture/`** —— 项目级架构权威目录(AGENTS.md 钦定的"架构中心"),长期存在、跨 feature 共享。里面有 `DESIGN.md`(架构总入口),以及各子系统架构 doc。
- **`features/`** —— 所有 feature spec 的聚合根。每个 feature 一个子目录 `{feature}/`,里面住着该 feature 的 `brainstorm.md`(Stage 0 brainstorm note,可选)、`design.md`(方案 doc,含 YAML frontmatter + 测试设计)、`acceptance.md`(验收报告)。同一 feature 的所有 spec 产物(包括可选的 brainstorm note)永远聚合在一起。
- **`issues/`** —— 所有 issue spec 的聚合根。每个 issue 一个子目录 `{issue}/`,里面住着 `report.md`(问题报告)、`analysis.md`(根因分析)、`fix-note.md`(修复记录,Stage 3 必出产物)。
- **`learnings/`** —— 知识沉淀目录。存放 easysdd-compound 产出的坑点/知识文档,累积式只增不删,按 `YYYY-MM-DD-{slug}.md` 命名。
- **`decisions/`** —— 决策归档目录。存放 easysdd-decisions 产出的技术选型、架构决定、长期约束和编码规约文档,按 `YYYY-MM-DD-{slug}.md` 命名。status=superseded 的文档保留原文不删除。
- **`tricks/`** —— 技巧库目录。存放 easysdd-tricks 产出的编程模式、库用法、技术技巧文档,累积式只增不删,按 `YYYY-MM-DD-{slug}.md` 命名。与 `learnings/` 的区别:learnings 是事件驱动的回顾("做完 X 发现了 Y"),tricks 是面向问题的处方("要做 X 就这样做"),可在任意时间主动写入。
- **`explores/`** —— 探索归档目录。存放 easysdd-explore 产出的仓库探索记录(问题、证据、结论、未决事项),累积式只增不删,按 `YYYY-MM-DD-{slug}.md` 命名。与 `tricks/` 的区别:explores 记录的是"这次为了回答某个问题,在代码里看到了什么"(证据导向),tricks 记录的是"这类问题推荐怎么做"(处方导向)。
- **`tools/`** —— 跨工作流共享的脚本工具目录。目前有 `search-yaml.py`(通用 YAML frontmatter 搜索工具)。新增工具时在此登记。

### 目录树示意

```
easysdd/
├── architecture/               ← 架构中心目录
│   ├── DESIGN.md               ← 架构总入口
│   └── {子系统架构 doc}.md
├── features/                   ← feature 聚合根
│   └── {feature}/              ← feature 目录
│       ├── brainstorm.md       ← brainstorm note(Stage 0,可选)
│       ├── design.md           ← 方案 doc(含 YAML frontmatter + 测试设计)
│       └── acceptance.md       ← 验收报告
├── issues/                     ← issue 聚合根
│   └── {issue}/                ← issue 目录
│       ├── report.md           ← 问题报告(Stage 1)
│       ├── analysis.md         ← 根因分析(Stage 2)
│       └── fix-note.md         ← 修复记录(Stage 3,必出产物)
├── learnings/                  ← 知识沉淀目录
│   └── YYYY-MM-DD-{slug}.md    ← 坑点或知识文档(easysdd-compound 产物)
├── decisions/                  ← 决策归档目录
│   └── YYYY-MM-DD-{slug}.md    ← 技术选型/架构决定/约束/规约(easysdd-decisions 产物)
├── tricks/                     ← 技巧库目录
│   └── YYYY-MM-DD-{slug}.md    ← 编程模式/库用法/技术技巧文档(easysdd-tricks 产物)
├── explores/                   ← 探索归档目录
│   └── YYYY-MM-DD-{slug}.md    ← 仓库探索记录(easysdd-explore 产物)
└── tools/                      ← 工具目录(跨工作流共享的脚本)
    └── search-yaml.py          ← 通用 YAML frontmatter 搜索工具
```

> `{feature}` 和 `{issue}` 都是占位符,代表具体 feature / issue 的**目录名**。命名格式统一为 `YYYY-MM-DD-{英文 slug}`(例如 `2026-04-11-user-auth`、`2026-04-11-null-pointer-login`),各部分的规则如下:
>
> - **日期前缀**(`YYYY-MM-DD`)—— 取该 feature 目录**首次创建**当日的日期,一经确定就不变。前缀的作用是让 `features/` 下的子目录天然按时间排序,方便后续翻阅。哪怕后续 design 阶段把 feature 改名了,**日期前缀也不改**,只替换后半段的 slug。
> - **英文 slug**(`{英文 slug}`)—— 小写字母 + 数字 + 连字符,不允许大写/下划线/空格/中文。长度短且能一眼看出是什么功能即可。
> - 两部分之间用一个连字符 `-` 连接,整串就是 feature 目录名,也就是本文档里所有 `{feature}` 占位符要被替换成的东西。
>
> 书写约定:正文一律用自然语言术语,不写 `$VAR` 形式的变量,也不在正文里散落字面路径。读者看到不熟的术语回本节目录树查一次即可。

### 组织规则

1. **一个 feature = 一个 feature 目录**。同一 feature 的 brainstorm / design / acceptance 永远聚合在一起;
2. **一个 issue = 一个 issue 目录**。同一问题的 report / analysis / fix-note 永远聚合在一起;
3. **两类 doc 不要混**。`architecture/` 下是**项目架构权威**(长期存在),方案 doc 是**单功能方案**(短期,跟随 feature 生命周期)。两者通过方案 doc 第 8 节"与项目级架构文档的关系"连接。
4. **feature 和 issue 的产物不要混**:`features/` 和 `issues/` 是并列的,不允许交叉存放。
5. **learning 文档单独归档**。`learnings/` 是累积性知识库,只放 easysdd-compound 产出的坑点/知识文档;spec 产物(design/acceptance/report)不放进来,learning 文档也不放进 `features/` 或 `issues/`。
6. **decisions 文档单独归档**。`decisions/` 是决策归档库,只放 easysdd-decisions 产出的技术选型/架构决定/约束/规约文档;已被取代(status=superseded)的文档保留不删,只加标注。decisions 文档与 learning 文档不混:前者是"我们决定了什么"(规范性),后者是"我们发现了什么"(经验性)。
7. **tricks 文档单独归档**。`tricks/` 是技巧参考库,只放 easysdd-tricks 产出的编程模式/库用法/技术技巧文档。tricks 文档与 learning 文档不混:前者是"要做 X 就这样做"(处方性),后者是"做完 X 发现了 Y"(回顾性);与 decisions 文档也不混:前者是可复用的操作技巧,后者是一次性做出的规范性决定。
8. **explore 文档单独归档**。`explores/` 是探索档案库,只放 easysdd-explore 产出的证据导向探索记录。explores 文档与 tricks 文档不混:前者是"这次探索看到了什么"(现状证据),后者是"同类问题推荐怎么做"(可复用处方);与 decisions 文档也不混:前者是分析输入,后者是拍板结论。
9. **工具脚本统一放 `tools/`**。跨工作流共享的脚本都放在 `tools/` 下,不要散落在项目根目录或子工作流目录里。新增工具时同步在本节目录树登记。
10. **Stage 0 brainstorm 也归属 feature 目录**。brainstorm note 就住在它所属 feature 的目录下(`brainstorm.md`),和 design/acceptance 聚合在一起——同一 feature 的所有 spec 产物一律同址。由于 brainstorm 开始时 feature slug 可能还没最终敲定,做法是:和用户商定一个**临时 slug**,按上文 `YYYY-MM-DD-{英文 slug}` 的格式拼出 feature 目录名(日期就取开 brainstorm 当天),然后以此创建 feature 目录。如果 design 阶段把后半段 slug 改了,**只改 slug、不改日期前缀**,连同 feature 目录一起重命名,brainstorm note 跟着走。严禁再往 `easysdd/brainstorms/` 这种并列目录塞文件。
11. **新加子工作流 / 新产物类型**,默认在 `easysdd/` 下开新子目录,并在本节登记。不要往别处塞新东西,也不要只在子技能里加路径而不回中心登记。
12. **路径变更唯一源**:要改目录结构,先改本节的目录树和说明,其他地方自动跟随。

---

## 三、目前包含的子工作流

### easysdd-feature(新功能开发,可选 Stage 0 + 三个正式阶段)

适用于:**从零实现一个还没做过的功能,或在已有功能上加新的能力**。

| 阶段 | 子技能 | 主导者 | 产出 |
|---|---|---|---|
| ⓪ brainstorm(可选) | `easysdd-feature-brainstorm` | AI 做思考伙伴,用户拍板 | brainstorm note |
| ① 方案设计(含测试设计) | `easysdd-feature-design` | AI 起草,用户分层拍板 | 方案 doc(含 YAML frontmatter + 0 术语 + 1 决策与约束 + 2 接口契约 + 3 实现提示 + 4 架构关系) |
| ② 分步实现 | `easysdd-feature-implement` | AI 按方案执行 | 代码 + 阶段汇报 |
| ③ 验收闭环 | `easysdd-feature-acceptance` | AI 逐层核对方案,用户终审 | 验收报告 + 架构归并 + 收尾提交确认 |

> 术语对应的实际路径见第二节"目录安排"。本表只引用术语,不重复字面路径。

**正式阶段(① ~ ③)不可跳、不可合并、不可并行**。每个阶段退出条件未满足,下一阶段不得开始。Stage 0 的"可选"是指它可以**不存在于某条路径上**,而不是可以"半路跳过";一旦开始走 Stage 0,就必须走到其退出条件才能进 Stage 1。

feature 的 `design.md`(标准流程与 fastforward 共用)统一要求带 YAML frontmatter,便于 `search-yaml.py` 检索。必填字段: `doc_type: feature-design`、`feature`、`status`(`draft` / `approved` / `superseded`)、`summary`、`tags`; 初稿生成时写 `draft`,用户明确放行后改成 `approved`。

**底层入口**:`easysdd-feature` 子技能(含路由表、Stage 0 判断逻辑、目录规则)。

### easysdd-issue(问题修复,三个阶段)

适用于:**项目里发现的 BUG、异常行为、文档错误等——即"本来应该好的东西坏了"**。

**标准路径**(根因不明或问题复杂):

| 阶段 | 子技能 | 主导者 | 产出 |
|---|---|---|---|
| ① 问题报告 | `easysdd-issue-report` | 用户描述,AI 引导结构化 | 问题报告(`report.md`) |
| ② 根因分析 | `easysdd-issue-analyze` | AI 读代码分析,用户确认 | 根因分析(`analysis.md`) |
| ③ 修复验证 | `easysdd-issue-fix` | AI 定点修复,用户验证 | 代码修复 + 修复记录(`fix-note.md`) + 收尾提交确认 |

**快速通道**(根因一眼确定、改动范围很小):AI 读代码 → 告知根因 → 用户确认 → 修复 → 用户验证 → 仅写 `fix-note.md`

**与 easysdd-feature 的边界**:

- issue 工作流处理"坏了的东西";feature 工作流处理"新加的东西"
- 如果修复过程中发现需要新增能力才能真正解决问题,先走完 issue 工作流存档,再另开 feature 工作流——不在 issue 里做新功能
- easysdd-feature 实现阶段发现的"顺手发现"记录,进入 easysdd-issue 工作流处理,不在 feature PR 里偷偷修

**底层入口**:`easysdd-issue` 子技能(含路由表和目录规则)。

### easysdd-compound(知识沉淀,单工作流)

适用于:**任何非 trivial 的工程实践结束后——将踩过的坑、发现的最佳实践提炼为可检索文档**。不绑定特定阶段,可在 feature 或 issue 工作流结束后触发,也可独立触发。

| 轨道 | 适用情境 | 产出 |
|---|---|---|
| 坑点轨道(Pitfall) | BUG 修复、调试经历、环境陷阱 | `learnings/YYYY-MM-DD-{slug}.md`(track: pitfall) |
| 知识轨道(Knowledge) | 最佳实践、工作流改进、可复用模式 | `learnings/YYYY-MM-DD-{slug}.md`(track: knowledge) |

**与其他工作流的关系**:

- `easysdd-feature-acceptance` 结束时,AI 应主动提议运行一次 easysdd-compound
- `easysdd-issue-fix` 结束时,AI 应主动提议把这次的坑记录为 pitfall 文档
- `easysdd-feature-design` 和 `easysdd-issue-analyze` 阶段,主动 Grep 知识沉淀目录查有无历史记录可复用

**底层入口**:`easysdd-compound` 子技能(含两轨道格式、五个阶段、守护规则)。

### easysdd-decisions(决策归档,单工作流)

适用于:**将项目中已经拍板的技术选型、架构决定、长期约束和编码规约归档为可检索文档**。不绑定特定开发阶段,可独立触发,也可在 feature-design 或 issue-analyze 阶段做出重要决策后顺带触发。

| 类型 | 适用情境 | 产出 |
|---|---|---|
| `tech-stack` | 技术/库/框架的选型 | `decisions/YYYY-MM-DD-{slug}.md` |
| `architecture` | 系统结构、模块划分、数据流方向 | `decisions/YYYY-MM-DD-{slug}.md` |
| `constraint` | 硬约束——某些事情不允许做 | `decisions/YYYY-MM-DD-{slug}.md` |
| `convention` | 软规约——某些事情统一这样做 | `decisions/YYYY-MM-DD-{slug}.md` |

**与其他工作流的关系**:

- `easysdd-feature-design` 开始前:搜索决策归档目录,确认方案不违反已有约束
- `easysdd-feature-design` 结束后:如果设计中做出了超出单个 feature 影响范围的重要选择,推荐记录进决策归档
- `easysdd-issue-analyze` 开始前:搜索决策归档目录,有时"这里为什么这么做"的答案就在里面
- `easysdd-compound` vs `easysdd-decisions`:compound 记录的是"发现了什么坑/最佳实践"(经验性);decisions 记录的是"我们决定了什么"(规范性)。互不替代

**底层入口**:`easysdd-decisions` 子技能。

### easysdd-onboarding(仓库接入,单工作流)

适用于:**把一个新仓库或有零散文档的仓库接入 easysdd 体系**——搭起标准骨架,并把已有文档归位。不绑定任何开发阶段,是开始用 easysdd 之前的"环境准备"步骤。

| 路径 | 适用情况 | 产出 |
|---|---|---|
| 绿地路径 | 仓库内无任何 spec 类文档,`easysdd/` 不存在 | 完整的 `easysdd/` 目录骨架 + 骨架文件 |
| 迁移路径 | 已有零散文档、`docs/` 目录、架构文档,或部分 `easysdd/` 结构 | 审计报告 + 迁移映射方案(用户逐一确认)+ 落盘 |

**与其他工作流的关系**:onboarding 是前置步骤,完成后才能顺畅运行 feature / issue / compound 工作流。已经跑通 easysdd 的仓库不需要再运行 onboarding。

**底层入口**:`easysdd-onboarding` 子技能。

### easysdd-tricks(技巧库,单工作流)

适用于:**将可复用的编程模式、库/框架用法、技术技巧整理为可检索文档**。不绑定特定开发阶段,可在任意时间主动写入,也可在 feature-design 或 issue-analyze 阶段顺带触发。

| 文档类型 | 适用情境 | 产出 |
|---|---|---|
| `pattern` | 设计模式、架构模式、编程惯用法 | `tricks/YYYY-MM-DD-{slug}.md` |
| `library` | 某个库/框架的用法、配置方式、常见坑 | `tricks/YYYY-MM-DD-{slug}.md` |
| `technique` | 具体操作技巧、工具用法、命令配方 | `tricks/YYYY-MM-DD-{slug}.md` |

**YAML frontmatter 必填字段**:`type`(上表三选一)、`topic`(一句话描述做什么)、`tags`(可检索标签列表)、`status`(`active` / `superseded`)。`language` 或 `framework` 字段按需加。`search-yaml.py` 可按任意字段检索。

**与其他工作流的关系**:

- `easysdd-feature-design` 开始前:搜索技巧库目录,看有无相关模式或库用法可直接参考
- `easysdd-issue-analyze` 开始前:搜索技巧库目录,有时根因正是某个库的已知坑或用法误区
- `easysdd-tricks` vs `easysdd-compound`:compound 记录"这次工作踩了什么坑/学到了什么"(事件锚定、回顾性);tricks 记录"要做这类事该怎么做"(问题锚定、处方性)。同一次工程实践可以同时产出两类文档
- `easysdd-tricks` vs `easysdd-decisions`:tricks 是可复用操作技巧(how);decisions 是一次性规范决定(what/must)。互不替代

**底层入口**:`easysdd-tricks` 子技能。

### easysdd-explore(探索归档,单工作流)

适用于:**仓库新人或上下文不足时,先对代码仓做定向探索并把结果归档**。例如用户说"先帮我 explore 一下"、"我想问这个仓库里 X 是怎么做的"、"把这次探索结论存档"。

| 文档类型 | 适用情境 | 产出 |
|---|---|---|
| `question` | 围绕一个问题做证据收集与结论 | `explores/YYYY-MM-DD-{slug}.md` |
| `module-overview` | 新人快速理解某个模块边界与调用关系 | `explores/YYYY-MM-DD-{slug}.md` |
| `spike` | 对多个实现方向做轻量技术探查(不拍板) | `explores/YYYY-MM-DD-{slug}.md` |

**与其他工作流的关系**:

- `easysdd-feature-design` 开始前:先搜索探索归档目录,吸收已有代码阅读结论,减少重复探索
- `easysdd-issue-analyze` 开始前:先搜索探索归档目录,很多调用链与模块边界信息可直接复用
- `easysdd-issue-fix` 开始前:搜索探索归档目录,确认修复点和历史探索证据一致,避免误改
- `easysdd-explore` vs `easysdd-tricks`:explore 是"现状证据"(as-is),tricks 是"推荐做法"(to-be)
- `easysdd-explore` vs `easysdd-decisions`:explore 产出用于支持讨论,decisions 产出是拍板结果

**底层入口**:`easysdd-explore` 子技能。

### easysdd-architecture-check(架构一致性检查,单工作流)

适用于:**检查 design 是否自洽,或检查 design 与实际代码是否一致**。例如用户说"帮我做 architecture check"、"检查 design coherence"、"看 design 和代码一致吗"。

| 检查目标 | 适用情境 | 产出 |
|---|---|---|
| `design-internal` | 检查 design 内部术语/约束/步骤是否一致 | 架构一致性检查报告(只报告,不修复) |
| `design-vs-code` | 检查 design 承诺与实际代码实现是否一致 | 架构一致性检查报告(只报告,不修复) |

**与其他工作流的关系**:

- `easysdd-feature-design` 结束后可触发:在进入实现前做一次一致性体检
- `easysdd-feature-acceptance` 前可触发:核对 design 与代码收敛情况
- 本技能每次只允许检查一个目标(不发散),发现问题只给修复建议,不进行实际修复

**底层入口**:`easysdd-architecture-check` 子技能。

### (扩展位 — 未来子工作流挂在这里)

> 用户后续会往 easysdd 里加更多子工作流(例如重构、迁移等)。新工作流定型后,把入口写进这一节,保持中心技能始终是"easysdd 全家福"的目录。

---

## 四、路由:用户该用哪个子技能

启动本技能后,先做一次定位,**而不是直接开讲解**。问用户两个问题(或者根据上下文自己判断):

0. **这个仓库是否已经有 easysdd 目录结构?**
   - 还没有 / 有零散文档但没接入 easysdd → 触发 `easysdd-onboarding` 技能,先搭骨架再开工
   - 已有完整的 `easysdd/` 骨架 → 继续问 1

1. **要做的是什么类型的工作?**
   - 新功能 / 新能力 → 进 easysdd-feature 路径,继续问 2
   - BUG / 异常行为 / 文档错误 → 进 easysdd-issue 路径,触发 `easysdd-issue` 技能做路由
   - 仓库探索 / 提问调研 / 新人熟悉代码 → 触发 `easysdd-explore` 技能
   - 架构一致性检查 / design coherence 检查 → 触发 `easysdd-architecture-check` 技能
   - 推翻既有模块重做架构 → 不在 easysdd-feature 范围,应独立写重构方案 doc
   - 记录技术选型 / 约束 / 架构决定 / 规约 → 触发 `easysdd-decisions` 技能
   - 沉淀知识 / 记录踩坑经历 → 触发 `easysdd-compound` 技能
   - 记录编程模式 / 库用法 / 技术技巧 → 触发 `easysdd-tricks` 技能
2. **(如果是 easysdd-feature)目前手上已有哪些产物?**

### easysdd-onboarding 路由

触发 `easysdd-onboarding` 子技能——它自己会扫仓库判断走绿地路径还是迁移路径。本技能不重复那份逻辑。

### easysdd-feature 路由

触发 `easysdd-feature` 子技能——它是 feature 工作流的路由中心,持有完整路由表和 Stage 0 判断逻辑。本技能不重复那份逻辑。

### easysdd-decisions 路由

触发 `easysdd-decisions` 子技能——它会引导用户确认决策类型(tech-stack / architecture / constraint / convention),一次归档一条决策。本技能不重复那份逻辑。

### easysdd-tricks 路由

触发 `easysdd-tricks` 子技能——它会引导用户确认文档类型(pattern / library / technique)并填写 YAML frontmatter,最后落盘到技巧库目录。本技能不重复那份逻辑。

### easysdd-explore 路由

触发 `easysdd-explore` 子技能——它会引导用户明确探索问题与范围,做证据化代码阅读,并把探索结果落盘到探索归档目录。本技能不重复那份逻辑。

### easysdd-architecture-check 路由

触发 `easysdd-architecture-check` 子技能——它会先锁定单一检查目标(`design-internal` 或 `design-vs-code`),然后输出不一致清单和修复建议,不做实际修复。本技能不重复那份逻辑。

---

## 五、跨阶段的共同约束

下列规则在所有 easysdd 子工作流里都适用,子技能里如果没显式重复,默认仍然成立。

### 1. 文档是一等产物
- 所有 spec doc 都是交付物的一部分,代码交付时必须同步更新到与最终实现一致
- "doc 以后再补" = 永远不补
- feature 的方案 doc(`design.md`)必须带统一 YAML frontmatter,至少包含 `doc_type`、`feature`、`status`、`summary`、`tags`,这样才能被 `search-yaml.py` 稳定检索
- 目录结构和路径变量见第二节"目录安排",本节不重复。两条最容易出错的原则反复强调:
   - **一个 feature = 一个 feature 目录**——同一 feature 的 design / acceptance 永远聚合在一起
  - **两类 doc 不混**:架构中心目录下是项目架构权威(长期),方案 doc 是单功能方案(短期),通过方案 doc 第 8 节连接——方案里引用架构中心目录下的 doc,必要时反过来在那里补一段引用方案 doc

### 2. 术语锁定与防撞车
- 引入新概念前必须 grep 既有代码 + 架构中心目录 + 所有 feature 的方案 doc,确认没有同名概念
- 撞了:要么改新概念名,要么复用既有命名
- 这条规则从 design 阶段开始严格执行,但 brainstorm 阶段也要避免引入将来会被 design 否掉的术语

### 3. 阶段间硬 checkpoint
- 每个阶段的退出条件没满足,下一阶段不开始
- 用户没明确放行,AI 不自作主张往下走
- 哪怕用户说"看起来差不多了,继续吧",AI 也要逐项核对退出条件

### 4. 范围守护
- 阶段一锁死的"不做什么",后续每个阶段都要复核,防止偷偷扩范围
- 在实现阶段发现"顺手可以优化的代码",**记 issue,不顺手改**
- 引入方案外的新概念/抽象 → 先停下来更新方案 doc 第 0 节,再继续

### 5. 不变量 > 测试用例
- 测试用例本身没价值,**有价值的是它验证的不变量**
- 一条测试如果不对应任何不变量,基本是垃圾测试
- 阶段三列不变量时,验证手段按"便宜程度"优先选(类型系统 > 单测 > 运行时 assert > 人工)

### 6. UI 改动必须浏览器验证
- 涉及前端视觉/交互的不变量,自动化测试不够,必须在验收阶段人工肉眼验证
- 这是 `AGENTS.md` 的硬要求

### 7. 设计 / 分析前搜技巧库

- `easysdd-feature-design` 开始前:用 `search-yaml.py` 搜技巧库目录,按 `type`、`tags`、`topic` 等字段过滤,确认有无可复用的模式或库用法
- `easysdd-issue-analyze` 开始前:同上搜技巧库,特别关注 `type: library` 文档——问题根因有时正是某个库的已知误用
- 搜到相关记录:在方案 doc 或根因分析里注明引用,不要重复写它已经覆盖的内容
- 没搜到:继续正常推进;工作结束后如有值得归纳的新技巧,走 `easysdd-tricks` 工作流落盘

### 7.5 方案 doc 也纳入 YAML 检索

- feature 的 `design.md` 生成后,可以直接用 `search-yaml.py` 在 `features/` 下搜索,例如 `python easysdd/tools/search-yaml.py --dir easysdd/features --filter doc_type=feature-design --filter status=approved`
- frontmatter 只负责索引与粗筛;术语防撞车、契约核对仍要读正文并在需要时 grep 代码

### 8. 设计 / 分析 / 修复前搜探索归档

- `easysdd-feature-design`、`easysdd-issue-analyze`、`easysdd-issue-fix` 开始前:用 `search-yaml.py` 搜探索归档目录,优先复用已有证据(调用链、模块边界、历史结论)
- 搜到相关记录:在本次文档里注明引用,并标注"本次是否沿用该结论"
- 如果探索结论与当前代码不一致:在当前文档里显式写"探索记录已过期",并建议追加一条新的 explore 文档
- 没搜到:正常推进;如果本次做了较多代码阅读,结束后建议补一条 `easysdd-explore`

### 9. 不和 BUG 修复混路径
- easysdd-feature 工作流不处理 BUG。在功能开发完成后发现的 BUG,走 issue 修复路径,不要回到本工作流的某个阶段去补
- 这是为了保持每条路径的退出条件清晰;混路径会让 checkpoint 失效

---

## 六、当用户问"easysdd 是干嘛的"

如果用户的意图就是"了解 easysdd",不是要立刻开工,按下面顺序回答:

1. **一句话定义**:Easy Spec-Driven Development,本项目的规约驱动开发工作流。
2. **解决什么问题**:用第一节"是什么"里那三种典型失败模式,但**只挑用户当前情况最相关的 1-2 条讲**,不要全念一遍
3. **现在有哪些子工作流**:列第二节的子工作流列表,问用户是否有具体场景对应
4. **给一个最小可执行的下一步**:不要让用户陷在"先了解再决定"的死循环里。问"你现在手上有具体要做的功能吗?如果有,我们直接进 easysdd-feature 流程"

---

## 七、当用户提到一个具体的功能

如果用户在触发本技能时已经描述了一个具体功能(比如"我想给应用加个 X"),不要先长篇介绍 easysdd——介绍是次要的,**路由是主要的**。直接:

1. 简短确认这是新功能(不是 BUG / 重构)
2. 问"你之前写过 brainstorm note / 方案 doc 吗?"或者直接 Glob 所有 feature 目录下的 brainstorm note / 方案 doc,看有没有相关文件
3. 按第四节路由表把用户导到对应子技能
4. 把"easysdd 是什么、为什么这样分阶段"作为路由过程中的**自然解释**带出来,而不是单独的开场白

---

## 八、扩展点(给未来的自己)

这一节是留给项目演进时往里面加东西的固定位置。每次往 easysdd 加新东西时,先想一下要不要在这里登记。

### 扩展点 A:新增子工作流

新工作流定型后,在第三节"目前包含的子工作流"里加一段表格,链接到对应的子技能。若引入新的产物类型,先在第二节"目录安排"里登记新的路径变量,再在子技能里引用。

### 扩展点 B:跨阶段新约束

如果发现某条规则适用于所有阶段(比如"任何 spec doc 都必须有变更日志"),加到第五节"跨阶段共同约束"。子技能不重复写,只在本技能维护。

### 扩展点 C:新模板/产物类型

如果引入了新的 spec 产物(比如"风险评估表"、"回滚预案"),在第三节的表格里新增一列,并在对应阶段的子技能里加产出说明。**同步更新第二节的路径变量总表**——新产物的路径必须先注册成变量,才能在其他地方引用。

### 扩展点 D:术语表(全家共享)

如果以后 easysdd 自己有了一些共享术语(比如 "spec doc"、"不变量"、"对接点" 这些),在这里维护一份全家共用的术语表,子技能复用,不再各自定义。

> **维护规则**:每次扩展都要同步更新本技能,不允许只在某个子技能里加东西而不在中心登记——这正是工作流要避免的"信息散落"反模式。

---

## 九、相关文档

- `AGENTS.md` — 全项目通用的代码规范和"已知坑"清单,所有子技能都默认遵守
- 架构总入口 — 项目架构文档总入口(路径见第二节"目录安排")
