---
name: cs-req
description: 维护 `codestable/requirements/` 下的需求文档，用用户故事 + 平铺语言描述已存在能力的"因何而生 / 如何解决 / 边界在哪"。两种模式 backfill / update。触发：用户说"刷新 requirements"、"这份 req 和代码对不上了"、"这块能力一直没写 req 补上"，或 acceptance 阶段同步回写。只记现状不记计划（计划走 cs-roadmap）。
---

# cs-req

`codestable/requirements/` 是项目的"能力清单"——每份描述**一个能力因什么问题而产生、怎么解决、边界在哪**，写成人话非技术读者也能看懂。架构文档讲"怎么搭"，需求文档讲"为什么要有"。

**req 是现状档案不是计划档案**——只描述"这个能力现在已经存在、边界长这样"。backfill 和 update 主路径都是 feature-acceptance：feature 做完才有"现状"。**design 阶段不走本技能**——能力还没实现就建 req 等于把"计划态"塞进现状档案。**不记"打算做什么"**——那归 `cs-roadmap`。用户说"我想要 X 能力"但 X 还没做出来 → 走 roadmap + 后续 acceptance 落档 req。

需求文档价值在**扫一眼就抓到重点**——用户故事在最前、痛点和解法各一段短的、边界用列表。AI 容易破坏这个特性的几种问题：

- 写成 PRD 格式（字段堆）——读者要一格一格读才能拼出全貌
- 语气过于 explain——像在上课不是介绍
- 起花哨标题或用比喻——读者要读半段才知道这能力是什么
- 把实现细节塞进来——"通过 XXX 服务调用 YYY 接口"

> 共享路径与命名约定看 `codestable/reference/shared-conventions.md`。一份样例看 `codestable/reference/requirement-example.md`——起草前读一遍对齐语气。

---

## 适用场景

- feature-acceptance 第 6 节触发：新增了用户可感能力 → `backfill`；改了已有能力的用户故事 / 边界 / pitch → `update`（**主路径**）
- 用户主动盘点：已经在跑的能力从没写过 req（`backfill`）
- 用户主动修订：能力演进了要刷新（`update`）

不适用：要写"技术上怎么搭" → `cs-arch`；写单次 feature 方案 → `cs-feat-design`；拍板长期规约 → `cs-decide`；写外部"怎么用" → `cs-guide`；大需求拆几轮做 → `cs-roadmap`。

---

## 单目标规则

每次只动一份文档：

- **backfill**：给已存在但从没写档的能力补一份
- **update**：按新素材 / 实现变化刷新一份

为什么不允许多份？req 价值在**每份都被读过**——一次吐多份用户没精力逐份 review，最后要么粗糙合入要么放着不看。

### 允许"没有 requirement 的 feature"

纯内部重构 / 技术债清理 / 工具链改造**不新增用户可感能力**的 feature 不强制要 req。feature-design 标"本次不新增能力"即可，不要为凑一份硬写。

---

## 工作流

### Phase 1：锁定目标

模式 + 目标文档 + 范围。

一份 req 描述**一个能力**。用户说"把这模块的需求全写了"先问清：模块对外提供几个独立能力？每个独立能力一份不要塞一起。

### Phase 2：读取材料

**共同必读**：`AGENTS.md` + `requirements/` 下其他 req（判断要不要互引、有没有重复）+ 用户素材（口述 / 产品想法 / 用户反馈 / 已有 feature 散落需求描述）。

**按情况读**：可能承载这能力的 architecture doc（用于 `implemented_by`）；相关已有 feature 方案；compound 沉淀（`python codestable/tools/search-yaml.py --dir codestable/compound --query "{能力关键词}"`）。

**update 额外**：当前文档全文 + `last_reviewed` 之后相关实现的变化（`git log` 粗扫 `implemented_by` 对应的代码模块）。

### Phase 3：一次性起草

按下文"文档结构"写**完整初稿**不分批。用户故事 / 痛点 / 解法 / 边界四块经常有跨块矛盾（用户故事描述的场景和解法描述的路径对不上），只有放在一起才看得出来。

### Phase 4：自查清单

review 前自跑一遍。每条针对一种 AI 默认会犯的错：

1. **语气是人话吗**——挑一段读出来像在跟朋友介绍吗？还是像在上课 / 写 PRD？后者就重写
2. **标题平铺吗**——直接说能力是什么，不要比喻 / 花哨。"修 bug 时先探索和分析" > "让 AI 当你的第一个读者"
3. **用户故事够具体吗**——每条要能想象出具体场景。"作为用户希望系统好用"是废话
4. **有没有把实现细节塞进来**——不该出现"通过 X 接口"、"用 Z 算法"。有就移到 architecture
5. **边界写了没**——没写边界的需求会被误用
6. **pitch 能当宣传词吗**——去技术化、一句话、读者不用上下文也能看懂
7. **update 专项**：本次新加 / 改的段落都有素材或实现依据？凭空加听起来更完整的描述是漂移开端

自查结果简短汇报——发现问题就说怎么处理（删 / 改 / 补），不走过场。

### Phase 5：用户 review

完整初稿贴给用户。改到用户明确"可以了"。

### Phase 6：落盘 + 索引更新

- backfill：写入 `requirements/{slug}.md`，`status: current`、`last_reviewed` 当天
- update：覆盖已有，`last_reviewed` 当天；结构性改动大则文末 `变更日志` 加一条
- **索引更新**：`requirements/` 下有 `README.md` 或索引文件就加链接；没有不强求——`requirements/` 扁平 `ls` 本身就是索引

---

## 文档结构

### frontmatter

```yaml
---
doc_type: requirement
slug: {英文连字符；和文件名一致}
pitch: {一句话去技术化说清楚这能力，可直接当宣传素材}
status: current | draft | outdated
last_reviewed: YYYY-MM-DD
implemented_by: []   # 承载的 architecture doc slug 列表，可空
tags: []
---
```

### 正文节

```markdown
# {标题 — 直接平铺说这能力是什么，不玩比喻}

## 用户故事

- 作为 {具体角色 / 处境}，我希望 {能做什么}，而不是 {现在怎么难受}
- ...（2-4 条，每条一行）

## 为什么需要

一段短的，讲这能力不存在时的痛点。非技术读者也能读懂。直接当宣传素材——痛点描述得越真切，对外讲这系统解决什么问题时就越有抓手。

## 怎么解决

一段短的，讲这能力大概怎么工作。**不写实现细节**——不提模块名 / 接口 / 算法。讲"用户体验上发生了什么"就够。

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

1. **语气是人话不是 PRD**——字段堆 / 上课腔 / 花哨标题都不行
2. **不写实现细节**——只讲"是什么 / 为什么 / 解决什么"，涉及实现的一律移到 architecture
3. **不替用户编用户故事**——必须来自用户素材或可追溯场景（已有 feature / 用户反馈 / explore），不允许凭空造"听起来合理"的使用场景
4. **单目标**——一次一份
5. **不改代码、不改 architecture doc**——只写 req。发现 arch 有问题记"观察项"
6. **不发散**——范围外问题记观察项

---

## 退出条件

- [ ] 已锁定单一模式 + 单一目标
- [ ] Phase 4 自查清单逐条跑过并汇报
- [ ] frontmatter 完整（`doc_type: requirement` / `pitch` / `status` / `last_reviewed`）
- [ ] 正文四节齐全（用户故事 / 为什么需要 / 怎么解决 / 边界）
- [ ] 用户故事每条能想象具体场景，无"希望系统好用"废话
- [ ] 没有实现细节塞进来
- [ ] `pitch` 读起来能直接当宣传词
- [ ] update：结构性改动有 `变更日志`
- [ ] 用户 review 通过
- [ ] 没有顺手改代码 / architecture / 其他 spec
- [ ] 没有范围外文档改动

---

## 和其他工作流的关系

| 方向 | 关系 |
|---|---|
| `cs-arch` 配合 | req 写"为什么要有"、architecture 写"怎么搭"；arch doc frontmatter 用 `implements: [req-slug]` 反向链 |
| `cs-feat-design` 只读 | design 只**读**已有 req 对齐用户故事和边界，**不调本技能**；新能力的 req 留到 accept 阶段 backfill |
| `cs-feat-accept` 主路径 | 验收统一处理 req 落档：新增能力触发 `backfill`（accept 完成后回填 slug 到方案 frontmatter），改了已有能力触发 `update` |
| `cs-roadmap` 配合 | req 记"现在是什么"、roadmap 记"打算怎么继续推进 / 从无到有做出来"。roadmap 拆解发现缺 req 让用户先触发本技能；roadmap 不改 req |
| `cs-onboard` 创建者 | onboarding 建 `requirements/` 空目录 |

---

## 常见错误

- 把"打算做的事"写进来——req 是现状档案，没做的归 roadmap
- backfill 时没确认能力是否真的在代码里跑——凭用户一句话写了一份"听起来合理"的 req
- 写成 PRD 字段堆 / 语气像在上课 / 标题用比喻 / 用户故事太抽象 / 把实现细节塞进来 / 没写边界
- `pitch` 塞了技术黑话——宣传时抽不出来用
- 一次起草多份——用户 review 不深
- 范围太大塞了多个独立能力——拆
- update 凭空加段——内容会越写越飘离实际
