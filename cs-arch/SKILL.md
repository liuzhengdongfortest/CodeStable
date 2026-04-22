---
name: cs-arch
description: 项目架构中心的一站式技能——起草新架构文档、刷新已有架构文档、或做一次架构体检。根据用户说的话自动判断模式：`new`（起草）/ `update`（按代码最新状态刷新）/ `check`（只看不改，出问题清单）。check 再分三个子目标：一份 feature design 自洽、design 和代码对得上、`codestable/architecture/` 下多份文档之间对得上。单目标规则——一次只动一份文档或只查一个目标。触发场景：用户说"补一份架构 doc"、"起草架构文档"、"刷新 architecture 目录"、"把这个模块结构写下来"、"做架构检查"、"design 内部一致吗"、"方案和代码对得上吗"、"architecture 文件夹里几份文档有没有打架"，或 feature-design / feature-acceptance / implement 阶段发现需要先做一次架构动作再继续。
---

# cs-arch

`codestable/architecture/` 是项目的"地图"——feature-design 写方案前读它定位、issue-analyze 做根因时读它理解模块边界、新人读它知道系统大致长什么样。这份地图不会自己长出来，也不会自己保持准确——有人在合适的时候起草、刷新、体检。本技能就是这三件事的统一入口。

**architecture 是累积的、自给自足的系统地图**。它不是某一次 feature 的详细方案，而是所有已落地 feature 沉淀下来的"系统现在长什么样"的总图。读者打开它应该能看懂系统整体结构，而不需要频繁跳回某份历史 design 才能补齐理解。design 是临时的增量详细稿，架构里稳定下来的名词 / 编排 / 约束由 acceptance 阶段提炼回这里；design 文件本身归档，只在追究具体决策细节时才翻。

**architecture 只记现状，不记计划**。默认只在 feature-acceptance 阶段跟着代码同步更新，必要时才由本技能主动 new / update。**不写"未来会加什么层"、"下一步打算拆出 X 模块"**——那些属于 `cs-roadmap` 的规划层。用户抛出"我想重构成 X 架构"这种目标态描述时，先走 roadmap 拆成若干 feature，每次 feature acceptance 把实际达到的阶段性结构提炼回 architecture。

这意味着 architecture 的详略判据是"够不够让读者不跳转就读懂系统"——不是"写得越少越好"，也不是"把 design 里所有细节都搬过来"。系统里稳定、跨 feature 可见的那一层要写全；某个模块内部的循环、辅助函数、一次性实现决定不进来。

架构文档的价值在于**准、稳、可查**。AI 写架构文档和查架构文档时最容易出的几种问题都直接破坏这三点：

- 凭空造系统——文档里写了 `AuthManager 协调 TokenService`，代码里根本没 `AuthManager` 这层。
- 替用户拍板架构决策——悄悄选了某种分层方式，读者以为这是既定事实。
- 把文档写成代码复述——每节都只说"这里有什么"，不说"为什么这么分"，读完和 `ls -R` 的信息量一样。
- 检查时"看一眼感觉没问题"——没给出具体位置证据，用户无从判断是不是真的 ok。

下面整套规则就是为了不让这几种情况发生。

> 共享路径与命名约定看 `codestable/reference/shared-conventions.md`。
> 文档结构模板、check 覆盖项清单、报告格式看同目录 `reference.md`。

---

## 模式分流

启动时先判断模式，三选一——AI 根据用户说的话自动判断，不让用户选菜单：

| 用户说什么 | 模式 |
|---|---|
| "补一份架构 doc"、"起草 {模块} 的架构文档"、"把这块结构写下来" | `new` |
| "刷新 {某文档}"、"代码变了，把架构 doc 同步一下"、"把 architecture 目录更新到最新" | `update` |
| "检查一下 design 自洽吗"、"方案和代码对得上吗"、"architecture 几份文档有没有打架"、"做架构体检" | `check` |

判断不出来就问用户一句，不要硬猜。

---

## 单目标规则

每次只跑一个模式，且该模式内只锁定一个目标：

- `new`：起草一份新架构文档（`codestable/architecture/{type}-{slug}.md`，或更新 `DESIGN.md` 本身）
- `update`：按代码最新状态 + 用户新素材刷新一份已有架构文档
- `check`：三个子目标之一
  - `design-internal` — 一份 feature design 文档内部一致性
  - `design-vs-code` — 一份 feature design 与代码的一致性
  - `architecture-folder-internal` — `codestable/architecture/` 下多份架构文档之间的一致性

为什么不允许一次做多件？起草时一次吐多份 AI 稿用户 review 不过来；检查时三个子目标的视角和读取材料完全不同，同时做会导致每边都不深、问题混在一起说不清责任。用户提多个目标就让 TA 选一个，其余留到下次。

---

## 工作流骨架（三模式共用）

所有模式走六个阶段，细节按模式分流：

```
Phase 1：锁定目标
Phase 2：读取材料
Phase 3：执行（new/update = 起草；check = 检查）
Phase 4：自查（new/update）或 输出报告（check）
Phase 5：用户 review
Phase 6：落盘（new/update）或 等用户拍板下一步（check）
```

### Phase 1：锁定目标（所有模式）

确认三件事：

- 模式（`new` / `update` / `check`）
- 目标对象：
  - `new`：新 slug + 受众 + 范围
  - `update`：已有文档路径
  - `check`：子目标 + 检查对象（feature 名 / architecture 子范围）
- 本次覆盖的范围（整份 / 某几节 / 哪几份文档）

范围不收敛就问用户收敛——一份架构文档要是要"全模块重写"往往意味着底下其实有多个相对独立的子系统，应该拆成多份分别做；一次检查要覆盖一整个 `architecture/` 目录出来的报告读起来反而抓不到重点。

### Phase 2：读取材料

共同必读：

- `codestable/reference/shared-conventions.md`
- `codestable/architecture/DESIGN.md`（总入口）
- `codestable/architecture/` 下的其他架构文档（判断要不要互相引用、有没有重复）

**new / update 额外必读**（见 `reference.md` 的"读取清单"）：

- 目标模块 / 子系统的代码入口和核心文件（由用户指认或你先 grep 后汇报候选让用户确认）
- 用户提供的素材（口述、散落文档、白板照片转述）
- 相关的 compound 沉淀（decision / explore / learning）
- 和本模块相关的已有 feature 方案
- **update 专项**：当前版本文档全文 + 该文档 `last_reviewed` 之后的代码变更（`git log` 粗扫）

**check 额外必读**（按子目标不同，详见 `reference.md`）：

- `design-internal` / `design-vs-code`：方案 doc 全文 + 架构中心目录相关文档
- `design-vs-code` 再额外：与 design 第 2/3 节直接对应的代码文件
- `architecture-folder-internal`：用户圈定的那几份 `codestable/architecture/**/*.md`（或某个 type 下的全部同类文档） + 索引 + 顺藤摸到的被引用文档（不扩展到代码）

### Phase 3：执行

**new / update 模式**：按 `reference.md` 的"文档结构"写出**完整初稿**，不分批吐半成品。分批 review 会让用户看不到全局一致性——第 2 节描述的结构和第 4 节记录的决策经常有跨节矛盾，只有放在一起才看得出来。

**check 模式**：按 `reference.md` 的"检查覆盖项"（三个子目标各 6 类）逐条执行。每条不一致都要记录**可定位位置**（`file:line` 或 `design 第X节`）+ 现象 + 影响 + 修复建议。

### Phase 4：自查（new/update）或 输出报告（check）

**new / update**：按 `reference.md` 的"自查清单"（7 条）就地跑一遍，发现问题就在交给用户 review 前处理掉（删掉 / 标 TODO / 改写）。自查结果简短汇报给用户——发现问题就说发现了、怎么处理，不要当成"走过场"隐形步骤。

**check**：按 `reference.md` 的"报告模板"输出完整报告，包含检查摘要 / 不一致清单（表格，带严重级别）/ 观察项（范围外）/ 一致性良好项 / 建议下一步。

### Phase 5：用户 review

**new / update**：把初稿完整贴给用户，提示 review。用户提意见就改，反复直到用户明确"这份 doc 可以了"。

**check**：报告给用户，等用户确认结论——是否接受、要不要再补一类检查、还是直接进入用户自己决定的下一步。本技能不替用户拍板。

### Phase 6：落盘（new/update）或 结束（check）

**new 模式**：

- 写入 `codestable/architecture/{type}-{slug}.md`（命名规则见 `codestable/reference/shared-conventions.md` 第 0 节），frontmatter `status: current`、`last_reviewed` 填当天
- **同类聚合检查**（落盘前必跑）：按 shared-conventions 的"架构 doc 的分组规则"判断本次落盘后某个 type 在 `architecture/` 根目录是否达到 ≥6 份——命中阈值就把这类全部搬进 `architecture/{type}/` 子目录、去掉文件名前缀、同步改 `DESIGN.md` 所有相关链接；搬迁清单必须在 Phase 5 一并给用户 review
- **索引更新**：打开 `codestable/architecture/DESIGN.md` 加对新文档的引用链接——new 模式下**必定**要加，不加等于写了没人会读；DESIGN.md 改动同样给用户 review，不要偷偷改

**update 模式**：

- 覆盖已有文件，`last_reviewed` 更新为当天
- 结构性改动大的话在文档末尾 `变更日志` 节加一条"YYYY-MM-DD：{一句话描述}"
- DESIGN.md 只在 scope 或 summary 变化影响索引描述时更新

**check 模式**：不落盘，结束。用户可能基于报告决定触发 `new` / `update` 或别的工作流——那是下一轮的事。

---

## 硬性边界

1. **只锚代码，不造系统**（new / update）——每条结构化断言必须能锚到 `file:line`；锚不到就标 `TODO: 待确认`，不允许"根据命名推测"。
2. **不替用户拍板决策**（new / update）——关键决策节的实质内容必须来自用户或可追溯的 decision 文档。AI 只起草结构和串联语言。
3. **只检查，不修复**（check）——禁止改 design / 代码 / 配置。check 和修复分开做，用户才能看到完整不一致清单后整体决定优先级。
4. **证据化**（check）——每条不一致都要有可定位位置（`file:line` 或 `design 第X节`）。
5. **可执行建议**（check）——具体到"改哪里、怎么改"，但不落盘。
6. **单目标**（所有模式）——一次只跑一个模式，该模式内只锁定一个目标。
7. **不改代码、不动 spec**（所有模式）——本技能只写架构 doc 或出检查报告。发现代码 / 方案 doc / decision 有问题就记为"观察项"交给用户决定是否另开工作流处理。
8. **不发散**（所有模式）——用户描述的范围外问题一律不扩展，记成观察项即可。

---

## 退出条件

所有模式共通：

- [ ] 已锁定单一模式和单一目标
- [ ] 用户明确 review 通过（new / update）或确认本轮检查结论（check）
- [ ] 没有顺手修改代码 / 方案 doc / decision 文档
- [ ] 没有范围外的额外文档改动

**new / update 额外**：

- [ ] `reference.md` 的自查清单逐条跑过，并已汇报处理结果
- [ ] 文档 frontmatter 完整，`doc_type: architecture`、`status`、`last_reviewed` 都填了
- [ ] 每个结构化断言要么有 `file:line` 锚点、要么标了 `TODO: 待确认`
- [ ] 落盘前已按"分组规则"判断同类是否 ≥6 份，命中则搬迁清单已和用户 review 过
- [ ] **new**：`DESIGN.md` 已加指向新文档的链接（或用户明确决定暂不加）
- [ ] **update**：如有结构性改动，`变更日志` 节已加一条

**check 额外**：

- [ ] 已完成对应子目标的检查项覆盖（见 `reference.md`）
- [ ] 报告含不一致清单 + 修复建议
- [ ] 报告未包含任何实际修复动作

---

## 和其他工作流的关系

| 方向 | 关系 |
|---|---|
| `cs-req` 配合 | requirement 描述"为什么要有这个能力"、本技能描述"用什么结构实现"；architecture doc 的 frontmatter `implements` 反向链到承载的 req slug |
| `cs-feat-design` 上游 | design 写到"本 feature 和哪块架构对接"时读本技能产出的 doc；design 写完后可触发 check 模式做一次自洽体检 |
| `cs-feat-accept` 下游 | 验收阶段实际去更新本技能产出的 doc（acceptance 自己做归并，不回调本技能 new/update）；想确认实现和 design 对得上时触发 check 模式 `design-vs-code` |
| `cs-decide` 配合 | 拍板一条架构决策后，本技能 `update` 可把引用补进相关架构 doc 的第 4 节 |
| `cs-issue-analyze` 读者 | 根因分析阶段读本技能产出的 doc 定位模块边界 |
| `cs-onboard` 创建者 | onboarding 阶段建 `DESIGN.md` 占位，之后由本技能填实 / 扩充 |
| `cs-roadmap` 配合 | architecture 记"系统现在长什么样"，roadmap 记"接下来打算怎么把它推到下一步"。roadmap 起草时会读本技能产出的 doc 理解现状，但不改它；"目标态架构"属于规划，不进 architecture doc |

---

## 常见错误

**new / update 常踩的**：

- 把"打算重构成什么样"写进来：architecture 是现状档案，目标态结构归 roadmap 规划层
- 凭空造系统：文档里出现了一个代码里并不存在的"协调层 / 中枢 / 管理器"
- 替用户拍板架构决策：关键决策节里的选型理由其实是 AI 编的
- 代码复述：每节都只列"这里有什么"，没说"为什么这么分"
- 起草分批吐半成品：用户看不出跨节矛盾，review 不深
- 术语冲突：新引入的名字和代码 / 其他 architecture doc / compound 里已有的东西冲突了还不自知
- 一次写 / 改多份文档：审不过来，最后全部粗糙合入
- 和已有 decision 冲突不停下：自己写了一版和既定 decision 相悖的说法
- new 模式落盘后忘记在 `DESIGN.md` 加索引：写了没人能发现
- update 模式加了新内容但没有代码依据：只是"读起来更完整"，这是内容飘离实际的开端
- 顺手把代码 / 方案 doc 一起改了：越界，本技能只动架构 doc
- 同类已经 ≥6 份还继续往根目录平铺：触发了分组规则却没搬迁
- 文件名没遵循 `{type}-{slug}.md`：未来同类聚不起来，分组规则形同虚设

**check 常踩的**：

- 一次同时做多个子目标（design-internal / design-vs-code / architecture-folder-internal 只能选一个）
- `architecture-folder-internal` 顺手读代码去验证——那是 `design-vs-code` 的事
- 发现问题就顺手改代码或文档
- 只说"这里不太对"，不给证据位置
- 建议过于抽象（"优化一下架构"）
- 从一个目标无限扩展到全仓库审计
