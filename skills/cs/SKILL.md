---
name: cs
description: CodeStable 用 vision / project / epic spec 与 issue 分层管理目标世界、当前真相、有边界变化和可关闭行动；按用户意图讨论、提问、快改、直接改、穿刺打通风险、受管理推进或按需 review。用户说 cs/CodeStable、快速/快改、穿刺、review、问系统如何工作或改动影响、或项目已有 `.cs/` 且在处理愿景/规格/bug/实现/关闭时使用；只有用户明确要求接入时才初始化 `.cs/`。
---

# cs — CodeStable

CodeStable 不是强制任务流程，也不是 Agent 编排器。它是一套供 AI 参考的软件演化结构：

- **Vision Spec**：用户想要的应用全景（目标世界）
- **Project Spec**：当前仍然成立的项目真相
- **Epic Spec**：有边界、仍在变化的大需求规格
- **Issue**：可关闭行动与快改痕迹（见命名约定）

简单明确的改变可以**快改**或**直接改**并验证；快改在 `issues/` 留下 `ff` 痕迹，不写 Design。

先理解这套结构，再决定当前要做什么。**行动名称只是内部工作方式，不要求用户记住或报模式名；** 同一会话可连续完成多步，不必每步向用户宣布“进入某模式”。

## 统一术语

后文只用这些词；旧说法视为同义别名，不再并列使用。

| 标准词 | 含义 | 不要混成 |
|---|---|---|
| **快改** | 小改快速通道：轻检索、不写 Design、实现后必留 `ff` issue | 不等于无痕迹乱改；不等于完整受管理 |
| **直接改** | 不建常规 issue 的实现路径；需要痕迹时用快改 `ff` | “直接路径 / 直接做 / 直接改变” |
| **受管理** | 用常规 issue（或 epic）跨步骤/跨会话追踪 | “受管理路径 / 建档 / 持续管理实体” |
| **现状说明** | 跨模式动作：紧凑讲清“触发如何产生结果” | 不等于建立 Explore issue |
| **Explore issue** | 独立探索事项（目录 + `index.md` + 路径文章） | 只有需要完整/可复用探索时才建 |
| **回写** | 把结论写回正确实体/章节 | 动作本身 |
| **毕业** | 关闭时把仍成立的结论提升到上层真相（project / epic spec） | 仅用于进入上层真相 |
| **有界简化** | 有意采用的简单方案，并写清已知上限、升级触发、升级方向 | 无上限的“先这样”不算 |
| **活规格** | Epic：圈住仍在演化的大需求，隔离不确定性 | 不是任务桶，也不是 project spec 缩小版 |
| **epic 内直接推进** | Epic 里已够清楚、不必建 issue 的切片 | 不是“直接改 / 快改” |
| **完成** | 实现与验证做完，目标已达成 | 不等于关闭 |
| **关闭** | 更新状态（`o`→`x`）、毕业回写、按契约提交；须用户授权收尾 | 实现默认不自动关闭；**不等于**挪进 `done/` |
| **整理进 done** | 用户主动要求时，把已 `-x-` 的事项挪到 `done/` 子目录，清扫工作区视线 | 不是关闭步骤；不自动做 |
| **Review** | 用户要求时，对指定范围的代码/diff 做结构与风险审阅（尺子主要来自 code-design） | **动作不是流程步骤**；实现/快改/关闭后不自动出现 |
| **穿刺** | 对明确需求按风险垂直打通：先证明关键点走得通，再加厚实现 | 不是限时可扔 spike；不是 Explore（现状）；不是默认流程步骤 |

**信息安全性（Security）** 与 **安全性（Safety）** 不得混称“安全”：前者防未授权访问与篡改，后者防危及生命、健康、财产或环境。

## 为什么这样组织

软件信息的范围、成熟度和稳定度不同。若混在一起：

- 只有 issue：方向与取舍关完就丢
- 只有当前 spec：奇思妙想与互斥方向无处安放
- 一切写进 project spec：分不清“现在如此”还是“以后可能”
- 巨型 issue：探索、规格、实现缠在一起，长期关不掉

因此按**信息该由谁负责、成熟到哪一步**分层，而不是按角色或固定流水线分层。它改变 AI 的判断，但不凌驾用户意图：该讨论就讨论，用户明确要直接改就直接改。只有值得跨会话管理的信息才写入 `.cs/`。

## 四个核心实体

```text
Vision Spec ──摘取目标切片──> Epic Spec ──分批推进──> Issues（NNN-o|x-…）
     │                         │                        │
     │                         └──关闭毕业──────────────┤
     │                                                  ↓
     └──目标世界                         Project Spec（当前现实）

快改 ──轻检索 + 实现 + 验证──> issues/NNN-x-ff-名称.md
                              └── 真相失效时同步 Project Spec
```

### Vision Spec（`.cs/vision/`）

回答：应用最终长什么样、用户如何获得结果、能力区域、候选/互斥方向、哪些已在建设或已成现实。

以用户旅程为主阅读路径、能力版图为辅；每层 `index.md` 建地图并可递归展开。允许目标与候选并存；不是 roadmap 或进度表。普通 issue / 快改不更新 Vision；Epic 经用户确认关闭时，才按事实更新实现程度与链接；改目标内容须用户确认。

### Project Spec（`.cs/spec/`）

回答：项目现在是什么、为什么、服务谁、能力与边界、如何理解与修改。

按使用场景与能力组织，不按代码目录索引。只收当前仍成立的结论。快改/直接改在真相失效时同步；受管理变化在关闭时毕业回写。

### Epic Spec（`.cs/epics/`）

回答：这次大变化准备怎样改变 project spec、已确定/仍变化什么、哪部分可推进。

**命名（扁平目录，无日期）：**

| 状态 | 路径 |
|---|---|
| 进行中 | `.cs/epics/{NNN}-o-{名称}/spec.md` |
| 已关闭 | `.cs/epics/{NNN}-x-{名称}/spec.md` |
| 已关闭且已整理 | `.cs/epics/done/{NNN}-x-{名称}/spec.md` |

- `NNN`：对该目录树（含 `done/`）内文件名/目录名开头数字取 **最大值 + 1**；至少三位补零（`001`…`999` 后自然为 `1000`…，**无上限**）。关闭时序号不变，只把 `-o-` 改为 `-x-`。
- 每 epic 仅一个权威 `spec.md`（状态、方案、统一语言、当前推进、epic 内直接推进与 issue 链接、阻碍、关闭条件、毕业候选）。可有相邻材料，不得形成第二份状态或计划。

价值是**隔离不确定性**。

### Issue（`.cs/issues/`）

回答：哪项改变值得追踪、验证和关闭；**快改**也落在这里，用 `ff` 标记，不写 Design。

**命名（扁平，无日期目录）：**

| 形态 | 路径 |
|---|---|
| 进行中 | `.cs/issues/{NNN}-o-{名称}.md` |
| 进行中（快改） | `.cs/issues/{NNN}-o-ff-{名称}.md` |
| 已完成/关闭 | `.cs/issues/{NNN}-x-{名称}.md` |
| 已完成（快改） | `.cs/issues/{NNN}-x-ff-{名称}.md` |
| Explore（进行中） | `.cs/issues/{NNN}-o-{名称}/` + `index.md` |
| Explore（已关闭） | `.cs/issues/{NNN}-x-{名称}/` |
| 已关闭且已整理 | `.cs/issues/done/{NNN}-x-…`（同上文件名/目录名） |

- **`NNN`**：对 `issues/` 树（**含 `done/`**）内开头数字取最大值 + 1；至少三位补零，超过 999 后为 `1000`、`1001`…，无上限。关闭与整理时序号都不变。
- **`o`** = open（进行中）；**`x`** = 已完成/关闭。
- **`ff`** = 快改痕迹；`type: ff`。模板 `templates/entities/ff-issue.md`。
- **`{名称}`**：短横线短语，点题即可（如 `rename-cwd-helper`）。
- **关闭**：路径 `-o-` → `-x-`（保留 `NNN`、`ff`、名称）；frontmatter `status: closed`。**关闭不挪进 `done/`。**

常规可实现 issue 须有可观察目标、范围、归属与验证；Explore 须有探索问题、停止条件、证据与关闭结论；**ff issue 只保留最简四节**（做了什么 / 改了哪些 / 怎么验证 / 对 `.cs/` 的影响），禁止写成迷你 Design。

适合有范围取舍、多轮/跨会话、交接留痕，或用户明确要求管理；快改用于「小且快但仍要可追溯」。不是每次改代码都要常规 issue。

### 整理进 `done/`（仅用户主动）

工作区变挤时，用户可能想把**已经 `-x-` 的**事项挪开，只让根下留下进行中的。子目录名固定为 **`done`**（不要用 archive）。

| 规则 | 说明 |
|---|---|
| **何时** | 仅当用户明确说整理、收拾、挪进 done、清扫已完成事项等；或用户**问**怎么整理、能否归档时，说明规则并**等用户确认再动手** |
| **何时不做** | 关闭 issue/epic 时、快改落盘时、会话结束时——**一律不自动**挪 `done/` |
| **挪什么** | 仅 `-x-` 的 issue 文件/目录、已关闭的 epic 目录；**不要**挪 `-o-` |
| **怎么挪** | `issues/{NNN}-x-….md` → `issues/done/{NNN}-x-….md`；epic 同理 `epics/done/…`；文件名不变 |
| **notes / talks** | 默认不强制；用户点名整理某批旧 note/talk 时，可挪到各自的 `done/` 子目录，规则相同 |
| **检索** | `done/` **仍是制度记忆**：grep `.cs/` 必须扫到；不是隔离区 |
| **链接** | 挪动后更新 epic/spec/其他文件里指向旧路径的链接；若不确定，至少在汇报里列出变更路径 |

示例：

```text
.cs/issues/
  015-o-fix-timeout.md
  done/
    012-x-ff-rename-cwd.md
    014-x-auth-flow/
.cs/epics/
  003-o-billing/
  done/
    001-x-auth-migration/
```

## 决策表

### 快改 / 直接改 / Issue / Epic

| 条件 | 出口 |
|---|---|
| 用户要快（快速/快改/直接开干/别走流程）且需求小、一次可做完 | **快改**（见 [fast](references/fast.md)）→ 必留 `ff` issue |
| 目标明确、一次做完、低风险，用户未要求快改痕迹 | **直接改**（可升级为快改以留痕） |
| 需求明确但有技术/集成/迁移等风险，需先证明走得通 | **穿刺**（见 [pierce](references/pierce.md)），再 Do 加厚 |
| 有范围取舍、多轮推进、交接、显著风险或长期质量承诺 | **Issue**（`NNN-o-名称`，非 ff） |
| 跨模块、多批推进、规格会在可圈住范围内反复演化 | **Epic**（再按需切 issue 或 epic 内直接推进） |
| 用户明确要求管理 / 明确不要建档 | **服从用户** |
| 意图不清，且选快改/直接改还是受管理会实质改变后续工作 | 说明推荐与理由，**请用户选** |

复杂度只是线索，不能盖过用户当前授权。快改细则与跳出条件见 [fast](references/fast.md)。

### 谁可以写哪一层

| 写入目标 | 允许时机 |
|---|---|
| Vision 目标内容 | 用户确认的 Vision 整理；实现结论要改目标时须再确认 |
| Vision 实现程度 / 链接 | Epic 关闭（按事实；不复制 issue 清单） |
| Project Spec | 独立 issue / Explore issue **关闭**毕业；Epic **关闭**合并；**快改/直接改**且已记录真相失效；**Spec 模式**维护当前真相 |
| Epic Spec | Spec 模式；epic 下 issue **关闭**回写 |
| Issue（含 ff） | Design / Do / Complain（受管理）；快改完成后写/关 `ff` issue |
| Talk / Notes / Tools / Agent 指令 | 各自模式；见辅助实体 |

冲突时先判断在回答哪类问题：

```text
目标方向：用户最新确认 > 相关 vision 分支
当前现实：代码与验证证据 > project spec 中疑似过时的表述
Epic 交付判断：用户最新确认 > 当前 epic spec > 来源 vision 旧表述
具体行动：用户最新确认 > 当前 issue（如有）> 旧设计与历史证据
```

不要静默绕过冲突。Epic 与 Vision 不一致时，先说明是收窄实现还是改变目标。

### 完成 vs 关闭 vs Git

| 动作 | 默认 |
|---|---|
| 实现 / 直接改 | 做到**验证完成**或真阻塞；**不**自动关闭常规 issue，**不** commit，**不** push / 部署 |
| **快改** | 验证完成后**必写** `ff` issue 并标完成（`o`→`x` 或直接落 `x-ff`）；**不**自动 commit / push |
| 用户只说“做完 / 实现 / 修好” | 完成实现与验证；常规 issue **不**自动关闭；快改仍须落 `ff` 痕迹 |
| 用户说“关闭 / 收尾 / 做完并沉淀” | 进入 Close：状态、毕业回写；git 仓库中按关闭契约 **commit 相关文件**；**不**自动进 `done/` |
| 用户说“整理 / 收拾 done / 把旧 issue 挪开”等 | 将已 `-x-` 项移入对应 `done/`；改链接；可一并 commit（若用户要） |
| 用户要求提交 | 可 commit 本次相关代码 + 相关 issue/ff/spec；仍不 push，除非明确要求 |
| push / 部署 / 破坏性操作 / 初始化或覆盖 `.cs/` / 关闭 epic | **必须**明确授权；破坏性操作执行前再确认 |

关闭时的毕业规则：

- 独立常规 issue → project spec
- Epic 下 issue → 先 epic spec
- Explore issue → 经用户确认的稳定**现状机制说明**按 project spec 结构毕业；与某次改动绑定的影响分析留在目标 issue
- Epic 关闭（须用户明确确认）→ 合并进 project spec，并检查来源 Vision
- **ff issue** → 默认不强制大段毕业；在「对 `.cs/` 的影响」中声明；真相失效则同步 project spec 或标已知漂移
- 直接改（无 ff）→ 仅当已记录真相失效时同步 project spec；不自动改 Vision

## 质量承诺链

统一语言用 ISO/IEC 25010:2023 九项产品质量特征，不是九项必填表，不宣称合规。细则见 [quality](references/quality.md)。

摘要：Vision 可记目标质量方向；Project / Epic Spec 记长期约束；Talk / 服务具体变化的 Explore / Complain **发现**风险；受管理 issue **选中即承诺**并落实到 Design / Do / Close；直接改不生成形式清单，但仍须守住 spec 约束、用户要求、输入校验、数据保护、**信息安全性**、**安全性**（若相关）、可访问性与必要验证。纯现状理解探索不扫九项。

## 辅助实体

扁平序号制（**无日期目录**）。各实体根目录（issues / epics / notes / talks）内 `NNN` **独立**编号：对该树（**含 `done/`**）内开头数字取最大值 + 1；至少三位补零，过 999 后为四位及以上，无上限。

| 实体 | 路径 | 说明 |
|---|---|---|
| Talk | `.cs/talks/{NNN}-{名称}.md` | 局部讨论收束稿 → 可导向快改/直接改、Vision、issue 或 epic；不是当前规格 |
| Note | `.cs/notes/{NNN}-{名称}.md` | 可复用坑点、调查结论、操作经验 |
| Tool | `.cs/tools/` | 已跑通、稳定、适合自动化的项目工具（按内容命名即可） |

Talk / Note **没有** `o`/`x`/`ff` 段（那是 issue 状态）；序号只保证可排序、可点名。更新已有 note 时改原文件，不新建同主题第二条（可在文末加日期小节）。

启动短规则：只写入项目根、由 **Agent 框架会自动注入** 的指令文件——跨 Agent 用 `AGENTS.md`，仅 Claude 用 `CLAUDE.md`（按各框架约定，不两处重复）。**CodeStable 不建模、不创建 `facts.md` 或任何平行“启动事实”文件**；复杂背景进 `notes/`，指令里最多放一行阅读指针。

## `.cs/` 是代码之外的制度记忆

代码只回答“现在怎么跑”。**为什么这样写、曾排除什么方案、坑点与解法、尚未毕业的理解**往往只在 `.cs/` 里。奇怪代码先查 **project / epic spec**；重复踩坑与操作解法先查 **notes**；同题历史取舍与验证先查 **issue**（含已关闭）。

### 何时必须检索

在**设计、穿刺、实现、修 bug、做现状说明、或维护规格**前，若项目存在 `.cs/`，必须先对 `.cs/` 做一轮与本次主题相关的检索。本会话已对同一主题做过且无新写入迹象时可复用结果，不机械重扫。

### 怎么检索（路径优先，够用再深读）

不必通读整个 `.cs/`。推荐一次轻量扫描：

1. **列目录 / 按路径扫**：`spec/`、`epics/`、`issues/`、`notes/`、`talks/`、`vision/`、`tools/` 的路径与文件名本身就是索引（issue/epic 的 `NNN-o|x[-ff]-名称`、note/talk 的 `NNN-名称`、短语常已点题）。
2. **关键词 grep 整个 `.cs/`**：模块名、能力名、错误名、用户原话里的术语；路径命中与正文命中同等重要。
3. **按权重深读命中项**（不是平铺全读）：

| 权重 | 位置 | 通常提供什么 |
|---|---|---|
| **最高** | `.cs/spec/` 相关入口与子层 | 当前真相、边界、为何如此；解释“怪代码”的首选 |
| **高** | 相关 `.cs/epics/{NNN}-o|x-{名称}/spec.md` | 进行中的大变化边界与已定方案 |
| **高** | `.cs/notes/` 命中项 | 坑点、解法、操作步骤、调查结论 |
| **中高** | `.cs/issues/` 命中项（含 `-x-`、`-ff-`、**`done/`**） | 历史目标、快改痕迹、设计、验证、失败尝试 |
| **按需** | talks / vision / tools | 未收束讨论、目标方向、已沉淀工具 |

有目标 issue 时仍须确认其**当前版本**；epic 下工作须读对应 epic `spec.md`。检索结果与代码冲突时：先核对证据，再维护真相——不静默以代码覆盖已记录取舍，也不在无证据时盲信过期文档。

## 工作原则（指针）

全局规则只在此立纲；细节以对应 reference 为准，模式文件不重写全文。

| 原则 | 权威源 |
|---|---|
| 先判断用户此刻要什么；流程须证明价值；快改/直接改不被常规建档阻塞 | 上文决策表 |
| **先检索 `.cs/` 制度记忆，再只靠代码推断** | 上文「`.cs/` 是代码之外的制度记忆」 |
| 小改走**快改**（轻检索 + 必留 ff issue）；复杂跳出 | [fast](references/fast.md) |
| 改代码前先做**现状说明**（快改可极短）；不够则建 Explore issue | [explore](references/explore.md) |
| 复用已掌握上下文；写前确认目标文件当前版本 | 各模式行动指南的读前约定 |
| 能查先查，不明白再问；不把推测写成真相 | 各模式 + 用户确认边界 |
| 沿根因与责任举一反三；不借机全仓审计 | [complain](references/complain.md)、[debug](references/debug.md) |
| 最小充分实现、有界简化、不能省略的护栏 | [economy](references/economy.md) |
| 按风险选质量目标；选中即承诺 | [quality](references/quality.md) |
| UI 关系优先可版本化图示 | [ui-spec](references/ui-spec.md) |
| 模块往深里做；结构改进长在具体变化里 | [code-design](references/code-design.md) |
| 用户要时才 **Review**（不自动审） | [review](references/review.md) + [code-design](references/code-design.md) |
| 有技术/集成风险时 **穿刺** 打通再铺开 | [pierce](references/pierce.md) |
| 文档按读者任务与阅读路径组织 | [docs](references/docs.md) |

## 行动与授权边界

一个技能不等于跑完整条生命周期。按用户当前授权推进：

- **讨论、规划**：调查与出口草案；确认前不落盘、不创建 vision / issue / epic
- **整理 Vision**：确认后写入 `.cs/vision/`；不强迫产生开发事项
- **设计**：不写代码；有 issue 则回写，无则对话交付，不建 issue
- **穿刺**：对明确需求列风险并垂直打通；可写最小可运行骨架；不通则停；见 [pierce](references/pierce.md)
- **快改**：轻检索后实现与验证；必留 `ff` issue；不写 Design；不自动 commit / push
- **实现、修复**：可直接改、快改或按 issue 推进；常规 issue 回写执行记录；**完成 ≠ 关闭**（快改除外须落 `x-ff` 痕迹），不自动 commit / push / 发布
- **关闭、收尾**：更新状态（`o`→`x`）、毕业回写；git 中按关闭契约提交相关变更；**不**自动整理进 `done/`；**不**自动 Review
- **Review**：仅用户明确要求时；对指定范围只审不改（除非另授权修改）；见 [review](references/review.md)
- **整理进 done**：仅用户主动要求或确认后；只挪已 `-x-` 项；`done/` 仍参与检索
- 初始化 `.cs/`、覆盖入口、关闭 epic、危险操作、推送、部署、共享状态修改：须明确授权

方向已确认且用户要求执行时，推进到**完成**或真阻塞，不在正常步骤间反复确认。仅在尚未授权改动，或快改/直接改 vs 受管理会实质改变后续工作时，才询问用户选择。

## 按需读取

确定意图后，**行动前完整读取对应 reference**；只读当前模式与真正相关的原则文件。模式切换仍在同一 `cs` 技能内。

同时读取规则：

- **quality**：具体变化的 Talk、质量回归的 Complain、带质量目标的 Design / Do / Close **必读**；Vision 记目标质量方向、Spec 记质量约束、Explore **服务具体变化**时按需；纯现状理解不需要
- **economy**：Design / Do / Complain / 穿刺作实现取舍时；Close 发现有界简化时
- **ui-spec**：Talk / Vision / Spec / Design / Do / Close 涉及 UI 空间关系、信息层级或多状态交互时
- **docs**：写或重组 vision / spec / explore / notes 等文档时（见下表）

| 当前意图 | 必读 | 同时读取 |
|---|---|---|
| 初始化或补齐 `.cs/` | [onboard](references/onboard.md) | — |
| 构想或整理目标应用全景 | [vision](references/vision.md) | [docs](references/docs.md)；目标质量 → [quality](references/quality.md)；UI → [ui-spec](references/ui-spec.md) |
| 想法模糊、讨论、初步规划 | [talk](references/talk.md) | [docs](references/docs.md)；具体变化 → [quality](references/quality.md)；UI → [ui-spec](references/ui-spec.md) |
| 维护 project / epic spec | [spec](references/spec.md) | [docs](references/docs.md)；质量约束 → [quality](references/quality.md)；UI → [ui-spec](references/ui-spec.md) |
| 现状说明或建立 Explore issue | [explore](references/explore.md) | [docs](references/docs.md)；服务具体变化 → [quality](references/quality.md) |
| 行为不符合预期、debug、修 bug | [complain](references/complain.md) | [debug](references/debug.md)、[economy](references/economy.md)、[quality](references/quality.md)；结构问题 → [code-design](references/code-design.md) |
| 为明确改变做实现设计 | [design](references/design.md) | [code-design](references/code-design.md)、[economy](references/economy.md)、[quality](references/quality.md)；UI → [ui-spec](references/ui-spec.md) |
| 穿刺 / 先打通风险 / 垂直打通需求通路 | [pierce](references/pierce.md) | [code-design](references/code-design.md)、[economy](references/economy.md)、[quality](references/quality.md)；现状不清 → [explore](references/explore.md) |
| 快速小改、别走流程、直接开干 | [fast](references/fast.md) | [economy](references/economy.md)；必要时 [quality](references/quality.md)；UI → [ui-spec](references/ui-spec.md) |
| 实现明确改变 | [do](references/do.md) | [code-design](references/code-design.md)、[economy](references/economy.md)、[quality](references/quality.md)；bug → [debug](references/debug.md)；UI → [ui-spec](references/ui-spec.md) |
| 评审代码 / review / 看 diff 或 PR（用户明确要求） | [review](references/review.md) | [code-design](references/code-design.md)、[economy](references/economy.md)；相关质量风险 → [quality](references/quality.md) |
| 关闭 issue 或 epic | [close](references/close.md) | [docs](references/docs.md)、[quality](references/quality.md)；有界简化 → [economy](references/economy.md)；UI → [ui-spec](references/ui-spec.md) |
| 记录可复用知识 | [note](references/note.md) | [docs](references/docs.md) |
| 用户带路跑通未知流程 | [maketools](references/maketools.md) | [docs](references/docs.md) |
| 写、改或审视技能 | [great-skills](references/great-skills.md) | [docs](references/docs.md) |

模板在 `templates/entities/`，初始化脚本在 `scripts/init_codestable.py`。产物格式以各 reference 的产物契约为准，不要凭文件名猜。
