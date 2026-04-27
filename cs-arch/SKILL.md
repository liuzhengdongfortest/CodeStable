---
name: cs-arch
description: 维护 `codestable/architecture/` 这份只记现状的系统地图，三种模式 update / check / backfill。触发：用户说"刷新 architecture"、"做架构检查"、"补这个模块的架构文档"、"方案和代码对得上吗"，或 feature 阶段需要先做架构动作。不写未来规划（走 cs-roadmap）。
---

# cs-arch

`codestable/architecture/` 是项目"地图"——design 写方案前读它定位、issue-analyze 做根因时读它理解模块边界、新人读它知道系统大致长什么样。本技能是"起草 / 刷新 / 体检"三件事的统一入口。

**architecture 是累积的、自给自足的系统地图**，不是某次 feature 的详细方案，而是所有已落地 feature 沉淀下来的"系统现在长什么样"总图。读者打开应能看懂整体结构而不需要跳回历史 design。design 是临时增量稿，acceptance 把稳定下来的名词 / 编排 / 约束提炼回这里；design 文件归档，只在追究具体决策细节时翻。

**只记现状不记计划**——默认在 acceptance 跟着代码同步，必要时本技能主动 backfill / update。**不写"未来会加什么层"、"下一步打算拆出 X 模块"**——那些归 `cs-roadmap`。用户说"我想重构成 X 架构"先走 roadmap 拆 feature，每次 acceptance 把实际达到的结构提炼回 architecture。

详略判据：**够不够让读者不跳转就读懂系统**——稳定、跨 feature 可见的那一层写全；模块内部循环、辅助函数、一次性实现决定不进来。

架构文档价值在**准、稳、可查**。AI 容易破坏这三点的几种问题：

- **凭空造系统**——文档说 `AuthManager 协调 TokenService`，代码里根本没 `AuthManager`
- **替用户拍板**——悄悄选某种分层方式，读者以为是既定事实
- **代码复述**——每节都说"这里有什么"，不说"为什么这么分"，信息量等于 `ls -R`
- **检查时看一眼感觉没问题**——没给具体位置证据

> 共享路径与命名约定看 `codestable/reference/shared-conventions.md`。文档结构模板、check 覆盖项、报告格式看同目录 `reference.md`。

---

## 模式分流

启动先判断模式三选一（不让用户选菜单）：

| 用户说什么 | 模式 |
|---|---|
| "刷新 {某文档}"、"代码变了把架构 doc 同步"、"更新到最新" | `update` |
| "检查 design 自洽"、"方案和代码对得上吗"、"几份文档有没有打架"、"做架构体检" | `check` |
| "补一份架构 doc"、"这块模块一直没写档"、"把已经在跑的子系统结构写下来" | `backfill` |

判断不出问用户。用户说"我想重构成 X / 打算新做 Y 模块"——不是本技能的事，转 `cs-roadmap`。

---

## 单目标规则

每次只跑一个模式，且只锁定一个目标：

- `backfill`：给已存在但从没写过档的模块补一份（`architecture/{type}-{slug}.md` 或更新 `ARCHITECTURE.md`）
- `update`：按代码最新状态 + 用户素材刷新一份已有 doc
- `check`：三个子目标之一
  - `design-internal` — 一份 design 内部一致性
  - `design-vs-code` — design 与代码一致性
  - `architecture-folder-internal` — `architecture/` 多份文档间一致性

为什么不一次做多件？起草时一次吐多份用户 review 不过来；检查时三个子目标视角和材料完全不同，同时做每边都不深。用户提多个目标让 TA 选一个。

---

## 工作流骨架（三模式共用 6 阶段）

```
Phase 1：锁定目标
Phase 2：读取材料
Phase 3：执行（backfill/update = 起草；check = 检查）
Phase 4：自查（backfill/update）或 输出报告（check）
Phase 5：用户 review
Phase 6：落盘（backfill/update）或 等用户拍板（check）
```

### Phase 1：锁定目标

确认：模式 + 目标对象 + 范围。

- backfill：新 slug + 受众 + 范围（+ 确认模块在代码里已存在）
- update：已有文档路径
- check：子目标 + 检查对象（feature 名 / architecture 子范围）

范围不收敛就问用户收敛——一份 doc"全模块重写"往往意味着底下其实有多个独立子系统应该拆；一次检查覆盖整个 `architecture/` 报告读起来抓不到重点。

### Phase 2：读取材料

**共同必读**：`shared-conventions.md` + `ARCHITECTURE.md` + `architecture/` 下其他文档。

**backfill / update 额外**（详见 `reference.md` "读取清单"）：目标模块代码入口和核心文件 + 用户素材 + 相关 compound 沉淀（decision / explore / learning）+ 相关已有 feature 方案。**update 专项**：当前 doc 全文 + `last_reviewed` 之后的代码变更（`git log` 粗扫）。

**check 额外**（按子目标）：
- `design-internal` / `design-vs-code`：方案 doc 全文 + 架构相关 doc
- `design-vs-code` 再额外：与 design 第 2/3 节直接对应的代码
- `architecture-folder-internal`：用户圈定的几份 doc + 索引 + 顺藤摸到的被引用文档（不扩展到代码）

### Phase 3：执行

**backfill / update**：按 `reference.md` "文档结构"写**完整初稿**不分批吐半成品——分批 review 用户看不到全局一致性，第 2 节描述的结构和第 4 节决策经常有跨节矛盾。

**check**：按 `reference.md` "检查覆盖项"（三个子目标各 6 类）逐条执行。每条不一致都要记**可定位位置**（`file:line` 或 `design 第X节`）+ 现象 + 影响 + 修复建议。

### Phase 4：自查 / 输出报告

**backfill / update**：按 `reference.md` "自查清单"（7 条）就地跑一遍，发现问题在 review 前处理掉（删 / 标 TODO / 改写）。自查结果简短汇报——发现了就说，不要走过场。

**check**：按 `reference.md` "报告模板"输出完整报告（检查摘要 / 不一致清单带严重级别 / 观察项 / 一致性良好项 / 建议下一步）。

### Phase 5：用户 review

**backfill / update**：完整初稿贴给用户 review。
**check**：报告给用户，等确认结论。本技能不替用户拍板。

### Phase 6：落盘 / 结束

**backfill**：

- 写入 `architecture/{type}-{slug}.md`（命名规则见 `shared-conventions.md` 第 0 节），frontmatter `status: current`、`last_reviewed` 填当天
- **同类聚合检查**（落盘前必跑）：按"架构 doc 分组规则"判断本次落盘后某 type 在根目录 ≥6 份——命中就把这类全搬进 `architecture/{type}/`、去掉文件名前缀、同步改 `ARCHITECTURE.md` 链接；搬迁清单在 Phase 5 一并 review
- **索引更新**：`ARCHITECTURE.md` 加新文档引用——backfill **必定**要加，否则写了没人会读；改动同样 review，不偷偷改

**update**：覆盖已有文件，`last_reviewed` 更新当天；结构性改动大时文末 `变更日志` 节加一条；`ARCHITECTURE.md` 只在 scope/summary 影响索引描述时更新。

**check**：不落盘结束。用户可能基于报告决定触发 backfill/update——那是下一轮的事。

---

## 硬性边界

1. **只锚代码不造系统**（backfill/update）——每条结构化断言必须能锚到 `file:line`；锚不到标 `TODO: 待确认`。模块在代码里还没写就不该走 backfill —— 那是规划转 `cs-roadmap`
2. **不替用户拍板决策**（backfill/update）——关键决策节实质内容必须来自用户或可追溯的 decision，AI 只起草结构和串联语言
3. **只检查不修复**（check）——禁止改 design / 代码 / 配置。check 和修复分开做，用户才能看到完整不一致清单后整体决定优先级
4. **证据化**（check）——每条不一致有可定位位置
5. **可执行建议**（check）——具体到"改哪里、怎么改"，但不落盘
6. **单目标**（所有模式）
7. **不改代码、不动 spec**（所有模式）——只写架构 doc 或出报告。发现代码 / 方案 / decision 有问题记成"观察项"
8. **不发散**——范围外问题不扩展，记观察项

---

## 退出条件

**共通**：
- [ ] 已锁定单一模式和单一目标
- [ ] 用户明确 review 通过（backfill/update）或确认结论（check）
- [ ] 没有顺手修改代码 / 方案 doc / decision
- [ ] 没有范围外文档改动

**backfill / update 额外**：
- [ ] 自查清单逐条跑过并汇报处理
- [ ] frontmatter 完整（`doc_type: architecture` / `status` / `last_reviewed`）
- [ ] 每个结构化断言有 `file:line` 锚点或标 `TODO: 待确认`
- [ ] 落盘前已按"分组规则"判断同类 ≥6 份，命中则搬迁清单已 review
- [ ] **backfill**：`ARCHITECTURE.md` 已加链接（或用户明确决定暂不加）
- [ ] **update**：结构性改动有 `变更日志` 条目

**check 额外**：
- [ ] 已覆盖对应子目标的检查项
- [ ] 报告含不一致清单 + 修复建议
- [ ] 报告不含任何实际修复动作

---

## 和其他工作流的关系

| 方向 | 关系 |
|---|---|
| `cs-req` 配合 | req 写"为什么有这个能力"、本技能写"用什么结构实现"；frontmatter `implements` 反向链到 req slug |
| `cs-feat-design` 上游 | design 写"本 feature 和哪块架构对接"时读本技能产出的 doc；design 写完可触发 check 体检 |
| `cs-feat-accept` 下游 | 验收阶段实际去更新本技能产出的 doc（acceptance 自己归并，不回调本技能）；想确认实现 vs design 对得上时触发 check `design-vs-code` |
| `cs-decide` 配合 | 拍板架构决策后，update 模式把引用补进相关 doc 第 4 节 |
| `cs-issue-analyze` 读者 | 根因分析读本技能 doc 定位模块边界 |
| `cs-onboard` 创建者 | onboarding 建 `ARCHITECTURE.md` 占位，之后由本技能填实 |
| `cs-roadmap` 配合 | architecture 记现状、roadmap 记规划。roadmap 起草读本技能 doc 理解现状但不改它；目标态架构归 roadmap |

---

## 常见错误

**backfill / update**：
- 把"打算重构成什么样"写进来——目标态归 roadmap
- 凭空造系统——出现代码里不存在的"协调层 / 中枢 / 管理器"
- 替用户拍板——选型理由是 AI 编的
- 代码复述——每节只列"这里有什么"，没说"为什么这么分"
- 分批吐半成品——用户看不出跨节矛盾
- 术语冲突——新名字和代码 / 其他 architecture doc / compound 已有的冲突
- 一次写 / 改多份——审不过来全部粗糙合入
- 和已有 decision 冲突不停下——自己写了一版相悖的说法
- backfill 落盘后忘加 `ARCHITECTURE.md` 索引——写了没人能发现
- 把还没在代码里跑起来的模块走 backfill——那是目标态转 roadmap
- update 加新内容但没代码依据——内容飘离实际的开端
- 顺手把代码 / 方案 doc 一起改了——越界
- 同类 ≥6 份还往根目录平铺——触发分组规则没搬迁
- 文件名没遵循 `{type}-{slug}.md`——分组规则形同虚设

**check**：
- 一次同时做多个子目标
- `architecture-folder-internal` 顺手读代码——那是 `design-vs-code`
- 发现问题就顺手改代码或文档
- 只说"这里不太对"不给证据位置
- 建议过于抽象（"优化一下架构"）
- 从一个目标无限扩展到全仓库审计
