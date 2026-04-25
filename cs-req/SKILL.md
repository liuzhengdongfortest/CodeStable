---
name: cs-req
description: 维护 `codestable/requirements/` 下的需求文档，用用户故事 + 平铺语言描述已存在能力的"因何而生 / 如何解决 / 边界在哪"。两种模式 backfill / update。触发：用户说"刷新 requirements"、"这份 req 和代码对不上了"、"这块能力一直没写 req 补上"，或 acceptance 阶段同步回写。只记现状不记计划（计划走 cs-roadmap）。
---

# cs-req

`codestable/requirements/` 是项目的"能力清单"——每份文档描述**一个能力因什么问题而产生、怎么解决、边界在哪**，写成人话，非技术读者也能扫一眼看懂。架构文档讲"怎么搭"，需求文档讲"为什么要有这个"。两者分开记录的好处是：单独讨论需求时不被实现细节干扰，单独讨论架构时也不被产品视角牵着走。

**requirement 是现状档案，不是计划档案**。只描述"这个能力现在已经存在、边界长这样"。新建（backfill）和刷新（update）的主路径都是 feature-acceptance 阶段——feature 做完才有"现状"可写：新增了用户可感能力就 backfill 首次落档，改了已有能力的用户故事 / 边界 / pitch 就 update。本技能也支持用户在 feature 流程外主动调起（盘点遗漏的能力 / 修订过时表述）。**design 阶段不走本技能**——能力还没实现就建 req 等同于把"计划态"塞进现状档案。**不记"打算做什么"、不记"下一步会加什么"**——那些属于 `cs-roadmap` 的规划层。用户说"我想要 X 能力"但 X 还没做出来时，不要在这里开新 req——走 roadmap 拆解 + 后续 feature-acceptance 落档 req。

需求文档的价值在于**扫一眼就能抓到重点**——用户故事在最前面、痛点和解法各一段短的、边界用列表。AI 写需求文档最容易出的几种问题都会破坏"扫一眼就抓到重点"这个特性：

- 写成 PRD 格式（字段堆）——读者要一格一格读才能拼出全貌。
- 语气过于 explain——像在上课，不是在介绍。
- 起花哨标题或用比喻——标题像广告词，读者要读半段才知道这能力是什么。
- 把实现细节塞进需求里——"通过 XXX 服务调用 YYY 接口"，这是架构 doc 的事。

下面整套规则就是为了不让这四种情况发生。

> 共享路径与命名约定看 `codestable/reference/shared-conventions.md`。
> 一份样例文档看 `codestable/reference/requirement-example.md`——起草前读一遍对齐语气。

---

## 适用场景

- feature-acceptance 阶段第 6 节触发：本次 feature 新增了用户可感能力 → `backfill` 首次落档；改了已有能力的用户故事 / 边界 / pitch → `update` 刷新（**主路径**）
- 用户主动盘点：一个**已经在跑**的能力从没写过 req，想补一份（`backfill`）
- 用户主动修订：能力演进了（新增用户故事 / 痛点表述过时 / 边界变化），要刷新（`update`）

不适用：

- 用户要写的是"这个系统技术上怎么搭" → 转 `cs-arch`
- 用户要写的是单次 feature 的方案 → 转 `cs-feat-design`
- 用户要拍板一条长期规约 / 选型 → 转 `cs-decide`
- 用户要写外部读者的"怎么用" → 转 `cs-guide`
- 用户抛出一块大需求想拆成几轮做（"我想要一个 X 系统"）→ 转 `cs-roadmap`——那是规划层，不往 req 里塞"待做能力"

---

## 单目标规则

每次只动一份文档，二选一：

- **backfill**：给一个已经存在、但从没写过档的能力补一份需求文档（`codestable/requirements/{slug}.md`）
- **update**：按新素材 / 实现变化刷新一份已有需求文档

为什么不允许一次写多份？需求文档的价值在于**每份都被读过**——一次吐多份 AI 起草稿，用户没精力逐份仔细 review，最后要么全部粗糙合入、要么全部放着不看。

### 允许"没有 requirement 的 feature"

纯内部重构 / 技术债清理 / 工具链改造这类**不新增用户可感能力**的 feature，不强制要有对应 requirement。feature-design 里在对应位置标记"本次不新增能力"即可，不要为了凑一份 req 硬写。

---

## 工作流

### Phase 1：锁定目标

确认三件事：

- 模式（`backfill` / `update`）
- 目标文档（backfill：新 slug + 一句话能力描述 + 确认该能力在代码里已经存在；update：已有文档路径）
- 本次覆盖的范围（整份 / 某几节）

一份需求 doc 描述**一个能力**。用户说"把这个模块的需求全写了"时要先问清楚：这模块对外提供几个独立能力？每个独立能力一份 doc，不要把多个能力塞进同一份。

### Phase 2：读取材料

共同必读：

- `AGENTS.md`
- `codestable/requirements/` 下的其他需求文档（判断"这份要不要和它们互相引用"、"有没有和哪份重复")
- 用户提供的素材（口述、产品想法、用户反馈、已有 feature 方案里散落的需求描述）

按情况读：

- 可能承载这个能力的 architecture doc（`codestable/architecture/`）——用于 `implemented_by` 字段
- 和本能力相关的已有 feature 方案（了解这个能力最近是怎么演进的）
- 相关的 compound 沉淀（explore / decision 里可能记过这块能力的背景）：

  ```bash
  python codestable/tools/search-yaml.py --dir codestable/compound --query "{能力关键词}"
  ```

**update 模式额外必读**：当前版本文档全文 + 该文档 `last_reviewed` 之后相关实现的变化（`git log` 粗扫 `implemented_by` 里那些 architecture doc 对应的代码模块即可）。

### Phase 3：一次性起草

按下文"文档结构"写出**完整初稿**，不分批吐半成品。用户故事 / 痛点 / 解法 / 边界四块之间经常有跨块矛盾（用户故事里描述的场景和解法里描述的路径对不上），只有放在一起才看得出来。

### Phase 4：自查清单（起草完就地跑一遍）

用户 review 前，自己先把下面这组检查过一遍。每一条都针对一种 AI 默认会犯的错：

1. **语气是不是人话？**——挑一段读出来，像在跟朋友介绍这东西吗？还是像在上课 / 写 PRD？像后者就重写。
2. **标题是不是平铺？**——标题直接说这能力是什么，不要比喻、不要花哨。"修 bug 时先探索和分析" > "让 AI 当你的第一个读者"。
3. **用户故事够具体吗？**——每条用户故事要能想象出一个具体场景。"作为用户，我希望系统好用"这种是废话，删掉。
4. **有没有把实现细节塞进来？**——需求文档里不该出现"通过 X 接口"、"调用 Y 服务"、"用 Z 算法"这种。有就移到对应 architecture doc。
5. **边界写了没？**——没写边界的需求会被误用。至少给一条"它不管什么"。
6. **pitch 字段能当宣传词用吗？**——frontmatter 的 `pitch` 要去技术化、一句话、读者不用上下文也能看懂。做不到就改。
7. **update 模式专项**：本次新加 / 改动的段落是否都有对应的素材或实现依据？纯凭空"加一句听起来更完整的描述"是漂移的开端。

自查结果简短汇报给用户——发现问题就说发现了、怎么处理（删掉 / 改写 / 补），不要当成"走过场"隐形步骤。

### Phase 5：用户 review

把初稿完整贴给用户，提示 review。用户提意见就改，反复直到用户明确"这份 doc 可以了"。用户放行后才进入 Phase 6。

### Phase 6：落盘 + 索引更新

- backfill 模式：写入 `codestable/requirements/{slug}.md`，frontmatter `status: current`，`last_reviewed` 填当天
- update 模式：覆盖已有文件，`last_reviewed` 更新为当天；如果结构性改动大，在文档末尾 `变更日志` 节加一条"YYYY-MM-DD：{一句话描述}"
- **索引更新**：如果 `codestable/requirements/` 下有 `README.md` 或索引文件，顺带加一行链接。没有就不强求——requirements 目前扁平，`ls` 本身就是索引

---

## 文档结构

### frontmatter

```yaml
---
doc_type: requirement
slug: {英文描述，连字符分隔；和文件名一致}
pitch: {一句话去技术化说清楚这能力是什么，可直接当宣传素材}
status: current | draft | outdated
last_reviewed: YYYY-MM-DD
implemented_by: []   # 承载这个能力的 architecture doc slug 列表，可空
tags: []
---
```

### 正文节

```markdown
# {标题 — 直接平铺说这能力是什么，不玩比喻}

## 用户故事

- 作为 {具体角色 / 处境}，我希望 {能做什么}，而不是 {现在怎么难受}。
- ...（2-4 条，每条一行）

## 为什么需要

一段短的，讲这能力不存在时的痛点。对象是非技术读者也能读懂的程度。这段内容直接就是宣传素材——痛点描述得越真切，对外讲这系统解决什么问题时就越有抓手。

## 怎么解决

一段短的，讲这能力大概是怎么工作的。**不写实现细节**——不提模块名、接口、算法。讲"用户体验上发生了什么"就够。

## 边界

- 它不管什么（哪些事情看起来相关但它不负责）
- 什么情况下别用它
- 用的前提（用户需要先做什么）
```

### 变更日志（update 模式才有）

```markdown
## 变更日志

- YYYY-MM-DD：{一句话描述}
```

---

## 硬性边界

1. **语气是人话，不是 PRD**——字段堆、上课腔、花哨标题都不行；每段都要能被非技术读者一眼看懂。
2. **不写实现细节**——需求文档只讲"是什么 / 为什么 / 解决什么"，不讲"怎么搭"。涉及实现的描述一律移到 architecture。
3. **不替用户编用户故事**——用户故事必须来自用户素材或可追溯的场景（已有 feature、用户反馈、explore 记录）。AI 不允许凭空造一个"听起来合理"的使用场景。
4. **单目标**——一次只动一份文档。
5. **不改代码、不改 architecture doc**——本技能只写需求 doc。发现 architecture 有问题就记为"观察项"交给用户决定是否另开工作流处理。
6. **不发散**——用户描述的范围外问题一律不扩展，记成观察项即可。

---

## 退出条件

- [ ] 已锁定单一模式（backfill / update）和单一目标文档
- [ ] Phase 4 自查清单逐条跑过，并已汇报处理结果
- [ ] 文档 frontmatter 完整，`doc_type: requirement`、`pitch`、`status`、`last_reviewed` 都填了
- [ ] 正文四节齐全（用户故事 / 为什么需要 / 怎么解决 / 边界）
- [ ] 用户故事每条都能想象出具体场景，没有"作为用户希望系统好用"这种废话
- [ ] 没有把实现细节塞进需求 doc
- [ ] `pitch` 字段读起来能直接当宣传词
- [ ] update 模式：如有结构性改动，`变更日志` 节已加一条
- [ ] 用户明确 review 通过
- [ ] 没有顺手修改代码 / architecture doc / 其他 spec
- [ ] 没有范围外的额外文档改动

---

## 和其他工作流的关系

| 方向 | 关系 |
|---|---|
| `cs-arch` 配合 | requirement 描述"为什么要有"、architecture 描述"怎么搭"；architecture doc 的 frontmatter 里用 `implements: [req-slug]` 反向链到承载的需求 |
| `cs-feat-design` 只读 | feature 设计阶段只**读**已有 req 对齐用户故事和边界，**不调用本技能**；新能力的 req 留到 accept 阶段 backfill |
| `cs-feat-accept` 主路径 | 验收时统一处理 req 落档：新增能力触发本技能 `backfill` 首次落档（accept 完成后回填 slug 到方案 frontmatter），改了已有能力触发 `update` 刷新——req 是现状档案，feature 做完才有"现状"，所以 backfill 和 update 都在这里发生 |
| `cs-roadmap` 配合 | req 记"这个能力现在是什么"，roadmap 记"打算怎么把它继续推进 / 从无到有做出来"。roadmap 拆解过程里如果发现缺 req，让用户先触发本技能；roadmap 不改 req |
| `cs-onboard` 创建者 | onboarding 阶段建 `codestable/requirements/` 空目录，之后由本技能填实 |

---

## 常见错误

- 把"打算做的事"写进来：req 是现状档案，没做的能力归 roadmap，不走 backfill
- 走 backfill 时没先确认能力是否真的在代码里跑：凭用户一句话就写了一份"听起来合理"的 req
- 写成 PRD 字段堆：读者要一格一格读才能拼出全貌
- 语气像在上课："本能力旨在提供……"这种开头立刻扔掉
- 标题用比喻："修 bug 时让 AI 当你的第一个读者" < "修 bug 时先探索和分析"
- 用户故事太抽象："作为用户，我希望系统好用"——删掉
- 把实现细节塞进来："通过调用 X 接口实现 Y" —— 这是架构 doc 的事
- 没写边界：需求会被误用然后失望
- `pitch` 字段塞了技术黑话：宣传时抽不出来用
- 一次起草多份：用户 review 不深，全部粗糙合入
- 范围太大：一份 doc 塞了多个独立能力——拆
- update 模式凭空加段：内容会越写越飘离实际
