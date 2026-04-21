---
name: easysdd-architecture-gen
description: 为项目起草或更新 `easysdd/architecture/` 下的架构文档——描述一个子系统/模块现在长什么样、怎么划分、对外接口怎么走，给后续 feature-design 做前置定位输入。信息源是代码 + 用户素材（口述、散落文档、compound 沉淀、已有 decision），产物锚到具体 `file:line` 可反向校验。两种模式：new（从零起草一份新架构文档）、update（按代码最新状态和用户新素材刷新已有文档）。单目标规则——一次只动一份文档。触发场景：用户说"补一份架构 doc"、"起草架构文档"、"更新 architecture 目录"、"把这个模块的结构写下来"，或 feature-design / feature-acceptance 阶段发现"架构里应该有但没有"的一块。
---

# easysdd-architecture-gen

`easysdd/architecture/` 是项目的"地图"——feature-design 写方案前读它定位，issue-analyze 做根因时读它理解模块边界，新人读它知道系统大致长什么样。但这份地图不会自己长出来：需要有人在合适的时候把脑子里 / 代码里隐含的结构沉淀成文字。本技能就是专门干这件事的。

地图的价值在于**准、稳、可查**。AI 写架构文档最常翻的几种车都直接砸这三点：

- 凭空造系统——文档里写了 `AuthManager 协调 TokenService`，代码里根本没 `AuthManager` 这层。
- 替用户拍板架构决策——悄悄选了某种分层方式，读者以为这是既定事实。
- 把文档写成代码复述——每节都只说"这里有什么"，不说"为什么这么分"，读完和 `ls -R` 的信息量一样。

下面整套规则都是为了让这三种车开不起来。

> 共享路径与命名约定看 `easysdd/reference/shared-conventions.md`。

---

## 适用场景

- 有一个子系统 / 模块缺架构文档，想补一份
- 代码演进了，已有架构文档和现实脱节，要刷新
- `easysdd/architecture/DESIGN.md` 本身需要更新（新加索引 / 新加一节关键架构决定）
- feature-design 阶段发现"应该有但没有"的一块架构 doc，先停下来补上再继续

不适用：

- 用户要写的是单次 feature 的方案 → 转 `easysdd-feature-design`
- 用户要拍板一条长期规约 → 转 `easysdd-decisions`
- 用户要检查已有架构 doc 是否自洽 / 是否和代码对得上 → 转 `easysdd-architecture-check`
- 用户要写外部读者看的"怎么用"文档 → 转 `easysdd-guidedoc`
- 用户要写库公开接口的逐条目参考 → 转 `easysdd-libdoc`

---

## 单目标规则

每次只动一份文档，二选一：

- **new**：起草一份新架构文档（`easysdd/architecture/{slug}.md`，或更新 `DESIGN.md` 本身）
- **update**：按代码最新状态 + 用户新素材刷新一份已有架构文档

为什么不允许一次写两份？架构文档的价值在于**每份都被读过**——一次吐一堆 AI 起草稿，用户没精力逐份仔细 review，最后要么全部粗糙合入、要么全部放着不看。单目标 + 逐份确认是强制 review 的机制。

---

## 工作流

### Phase 1：锁定目标

确认三件事：

- 模式（`new` / `update`）
- 目标文档（new：新 slug + 受众 + 范围；update：已有文档路径）
- 本次覆盖的范围（整份 / 某几节）

范围不收敛就问用户收敛——一份架构文档要是要"全模块重写"，往往意味着底下其实有多个相对独立的子系统，应该拆成多份分别做。

### Phase 2：读取材料

共同必读：

- `AGENTS.md`
- `easysdd/architecture/DESIGN.md`（总入口）
- `easysdd/architecture/` 下的其他架构文档（用于判断"这份 doc 是不是要和它们互相引用"、"有没有重复描述同一块"）
- 目标模块 / 子系统的代码入口和核心文件（由用户指认或你先 grep 后汇报候选让用户确认）

按情况读：

- 用户提供的素材（口述、散落文档、白板照片转述）
- 相关的 compound 沉淀：

  ```bash
  python easysdd/tools/search-yaml.py --dir easysdd/compound --filter doc_type=decision --filter status=active --query "{模块关键词}"
  python easysdd/tools/search-yaml.py --dir easysdd/compound --filter doc_type=explore --query "{模块关键词}"
  python easysdd/tools/search-yaml.py --dir easysdd/compound --filter doc_type=learning --query "{模块关键词}"
  ```

- 和本模块相关的已有 feature 方案（了解这个模块最近经历了什么设计演进）

**update 模式额外必读**：当前版本文档全文 + 该文档 frontmatter 里 `last_reviewed` 之后的代码变更（`git log` 粗扫涉及文件的 commit 信息即可，不必逐个 diff）。

### Phase 3：一次性起草

按下文"文档结构"写出**完整初稿**，不分批吐半成品。分批 review 会让用户看不到全局一致性——第 2 节描述的结构和第 4 节记录的决策经常有跨节矛盾，只有放在一起才看得出来。

### Phase 4：自查清单（起草完就地跑一遍）

用户 review 前，自己先把下面这组信号过一遍。每一条都是一次"AI 默认会翻的车"的截停点：

1. **每个结构化断言能不能锚到代码？**——"A 模块通过 X 调用 B"、"Y 持有 Z 的状态"、"所有写入经 W"——每一条在文档的"代码锚点"节或节内注释里能不能给出 `file:line` 支撑？锚不到的断言要么删掉、要么标 `TODO: 待确认` 交给用户。
2. **有没有替用户拍板？**——"关键决策"节里的条目是"引用已有 decision + 简述原文结论" / "引用用户素材里用户说过的原话"，还是 AI 自己编的选型理由？后者一律不许进文档——停下来问用户。
3. **有没有变成代码复述？**——每节至少一句话说"为什么这么分"，没有这一句的节基本就是 `ls` 贴文字。
4. **术语冲突检查做了吗？**——新引入的架构术语做一遍 grep（代码、`easysdd/architecture/` 下所有文档、`easysdd/compound/`）。冲突了就换名字或在第 0 节明确"本文里 X 指 Y，和代码里的 X' 不是一个东西"。
5. **是否和现有 architecture / decision 冲突？**——写的过程中如果发现和某条 decision 或其他架构文档描述的事实对不上，不许"写自己的那版"，要么引用那条、要么停下来问用户"是不是那条也该更新了"。
6. **单节长度**——每节超过 1 屏就该砍或拆。架构文档是给人快速定位的，不是用来读一遍的。
7. **update 模式专项**：本次新加 / 改动的段落是否都有对应的代码变化作为依据？纯凭空"加一句听起来更完整的描述"是漂移的开端。

自查结果简短汇报给用户——发现问题就说发现了、怎么处理（删掉 / 标 TODO / 改写），不要当成"走过场"隐形步骤。

### Phase 5：用户 review

把初稿完整贴给用户，提示 review。用户提意见就改，反复直到用户明确"这份 doc 可以了"。用户放行后才进入 Phase 6。

### Phase 6：落盘 + 索引更新

- new 模式：写入 `easysdd/architecture/{type}-{slug}.md`（命名规则见 `easysdd/reference/shared-conventions.md` 第 0 节），frontmatter `status: current`，`last_reviewed` 填当天
- update 模式：覆盖已有文件，`last_reviewed` 更新为当天；如果结构性改动大，在文档末尾 `变更日志` 节加一条"YYYY-MM-DD：{一句话描述}"
- **同类聚合检查**（落盘前必跑）：按 `easysdd/reference/shared-conventions.md` 的"架构 doc 的分组规则"判断本次落盘后某个 type 在 `architecture/` 根目录是否达到 ≥6 份
  - 命中阈值：本次操作要把这一类全部搬进 `architecture/{type}/` 子目录、去掉文件名前缀，并同步改 `DESIGN.md` 里所有相关链接；搬迁清单（旧路径 → 新路径列表 + DESIGN.md 改动）必须在 Phase 5 一并给用户 review
  - 未命中：按平铺路径落盘
  - 已经在子目录里的同类直接就地新增 / 更新，不需要再判
- **索引更新**：打开 `easysdd/architecture/DESIGN.md`，检查有没有对本文档的引用链接
  - new 模式下**必定**要加链接——新架构 doc 如果不进入总入口，等于写了没人会读
  - update 模式下只在 scope 或 summary 变化影响索引描述时更新
  - DESIGN.md 的修改同样给用户 review，不要直接悄悄改

---

## 文档结构

### frontmatter

```yaml
---
doc_type: architecture
slug: {英文描述，连字符分隔；和文件名一致}
scope: {一句话说清楚这份 doc 覆盖的范围}
summary: {一句话总结这块架构的要点}
status: current | draft | outdated
last_reviewed: YYYY-MM-DD
tags: []
depends_on: []   # 其他 architecture doc 的 slug，可选
implements: []   # 这块架构承载的 requirement slug 列表（`easysdd/requirements/` 下），可空——纯基础设施 / 工具层没有对应 requirement 是正常的
---
```

### 正文节

```markdown
## 0. 术语

本文里首次引入的专有名词简要定义，外加和相近名词的区分（"本文里 X 指 Y，和代码里的 X' 不是同一个东西"）。没有新术语就省略本节。

## 1. 定位与受众

- 本 doc 描述的是项目里哪一块（模块 / 子系统 / 跨模块关注点）
- 谁会读这份 doc（feature-design / issue-analyze / 新人上手……）
- 读完能干嘛（定位到对应代码 / 了解对外接口 / 知道约束）

## 2. 结构与交互

- 模块怎么划分、依赖方向
- 对外接口（别人怎么用这块）、对内接口（这块怎么用别人）
- 跨模块契约（数据格式 / 调用协议 / 状态归属）
- 模块 ≤ 2 或关系线性时不画图；否则建议 Mermaid

每条结构化断言后附 `file:line` 锚点，或在节末尾的"代码锚点"小节集中给。

## 3. 数据与状态

- 关键类型 / 核心数据结构（简述 + 定义位置 file:line）
- 所有权归属（谁写、谁读）
- 持久化边界（内存 / 本地 / 数据库 / 外部服务）

## 4. 关键决策

不是决策全文，是**引用**——每条一两行：

- 结论一句话
- 引用：`easysdd/compound/YYYY-MM-DD-decision-{slug}.md` 或用户原话出处
- 为什么引用到这份架构 doc 里（和本模块的关系）

没有已落档的决策就省略本节，或记 `TODO: 某决定应沉淀为 decision`。

## 5. 代码锚点

集中列一份"想看代码从哪看"的清单：

- 入口文件 / 关键函数 / 关键类型定义
- 格式：`{file}:{function/class} — 一行说明`

## 6. 已知约束 / 边界情况

本模块现在有哪些"不能动 / 动了要小心"的硬约束，以及它们的来源（来自 AGENTS.md / 某条 decision / 某次 learning）。

## 7. 相关文档

- 依赖的其他 architecture doc
- 相关 decision / learning / trick / explore 的链接
- 使用本模块的代表性 feature design

## 变更日志（update 模式才有）

- YYYY-MM-DD：{一句话描述}
```

---

## 硬性边界

1. **只锚代码，不造系统**——每条结构化断言必须能锚到 `file:line`；锚不到就标 `TODO: 待确认`，不允许"根据命名推测"。
2. **不替用户拍板决策**——关键决策节的实质内容必须来自用户或可追溯的 decision 文档。AI 只起草结构和串联语言。
3. **单目标**——一次只动一份文档（含 `DESIGN.md` 本身也算一份）。
4. **不改代码、不动 spec**——本技能只写架构 doc，发现代码 / 方案 doc / decision 有问题就记为"观察项"交给用户决定是否另开工作流处理。
5. **不发散**——用户描述的范围外问题一律不扩展，记成观察项即可。

---

## 退出条件

- [ ] 已锁定单一模式（new / update）和单一目标文档
- [ ] Phase 4 自查清单逐条跑过，并已汇报处理结果
- [ ] 文档 frontmatter 完整，`doc_type: architecture`、`status`、`last_reviewed` 都填了
- [ ] 每个结构化断言要么有 `file:line` 锚点、要么标了 `TODO: 待确认`
- [ ] 落盘前已按"分组规则"判断同类是否 ≥6 份，命中则搬迁清单已和用户 review 过
- [ ] new 模式：`DESIGN.md` 已加指向新文档的链接（或用户明确决定暂不加）
- [ ] update 模式：如有结构性改动，`变更日志` 节已加一条
- [ ] 用户明确 review 通过
- [ ] 没有顺手修改代码 / 方案 doc / decision 文档
- [ ] 没有范围外的额外文档改动

---

## 和其他工作流的关系

| 方向 | 关系 |
|---|---|
| `easysdd-requirements` 配合 | requirement 描述"为什么要有这个能力"、本技能描述"用什么结构实现"；frontmatter `implements` 字段反向链到承载的 requirement slug |
| `easysdd-feature-design` 上游 | design 写到"本 feature 和哪块架构对接"时读本技能产出的 doc |
| `easysdd-feature-acceptance` 下游 | 验收时如果发现 feature 对某块架构有实质影响 → 可触发本技能 `update` 模式刷新那份 doc |
| `easysdd-decisions` 配合 | 拍板一条架构决策后，本技能 `update` 可把引用补进相关架构 doc 的第 4 节 |
| `easysdd-architecture-check` 配合 | 本技能写完后如果想确认"doc 内部自洽 / doc 和代码对得上"，触发 `architecture-check` 做一次体检 |
| `easysdd-issue-analyze` 读者 | 根因分析阶段读本技能产出的 doc 定位模块边界 |
| `easysdd-onboarding` 创建者 | onboarding 阶段建 `DESIGN.md` 占位，之后由本技能填实 / 扩充 |

---

## 容易踩的坑

- 凭空造系统：文档里出现了一个代码里并不存在的"协调层 / 中枢 / 管理器"
- 替用户拍板架构决策：关键决策节里的选型理由其实是 AI 编的
- 代码复述：每节都只列"这里有什么"，没说"为什么这么分"
- 起草分批吐半成品：用户看不出跨节矛盾，review 不深
- 术语冲突：新引入的名字和代码 / 其他 architecture doc / compound 里已有的东西冲突了还不自知
- 一次写 / 改多份文档：审不过来，最后全部粗糙合入
- 和已有 decision 冲突不停下：自己写了一版和既定 decision 相悖的说法
- new 模式落盘后忘记在 `DESIGN.md` 加索引：写了没人能发现
- update 模式加了新内容但没有代码依据：只是"读起来更完整"，这是漂移开端
- 顺手把代码 / 方案 doc 一起改了：越界，本技能只动架构 doc
- 同类已经 ≥6 份还继续往根目录平铺：触发了分组规则却没搬迁，下次再加只会更乱
- 文件名没遵循 `{type}-{slug}.md`：未来同类聚不起来，分组规则形同虚设
