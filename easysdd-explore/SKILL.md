---
name: easysdd-explore
description: 对仓库做一次定向代码探索，把"提问 → 读代码 → 得结论"的过程沉淀为可检索证据，下次同类问题直接复用。三种类型：question（围绕一个具体问题查代码并给结论）、module-overview（梳理某模块结构 / 边界 / 入口 / 依赖）、spike（对多个可能方向做轻量技术探查，不做最终决策）。触发场景：用户说"先 explore 一下"、"这个仓库里 X 怎么实现"、"快速熟悉这个模块"、"把探索结果存档"。和 tricks 的区别：explore 记"看到了什么"（证据），tricks 记"推荐怎么做"（处方）。和 decisions 的区别：explore 是输入，decisions 是拍板。
---

# easysdd-explore

同一个问题第一次花两小时查代码，第二次应该五分钟内找到答案——前提是第一次做完留下了证据化的记录。easysdd-explore 就是把一次完整的"提问 → 读代码 → 得结论"过程沉淀成可检索的探索文档。

---

## 适用场景

- 新人入仓，需要快速理解模块边界、调用链、入口文件
- 用户提出一个具体问题，但暂时不要求直接产出方案 / 修复
- feature-design / issue-analyze / issue-fix 前先补一轮证据化探索
- 技术方向还在讨论，需要先做轻量 spike（只探索，不拍板）

不适用的场景：

- 已经是明确的拍板动作 → 该用 `easysdd-decisions`
- 已经是可复用处方总结 → 该用 `easysdd-tricks`
- 已经在做 bug 修复并且根因明确 → 直接走 `easysdd-issue-fix`

> 共享路径与命名约定看根技能 `easysdd-core` 第二节。文件命名 `YYYY-MM-DD-{slug}.md`。

---

## 三种探索文档类型

每条探索文档归属下面三类之一，在 frontmatter 的 `type` 字段标注：

| 类型 | 适用情境 |
|---|---|
| `question` | 围绕一个具体问题查代码并给结论 |
| `module-overview` | 快速梳理某模块结构、边界、入口与依赖 |
| `spike` | 对多个可能方向做轻量技术探查（不做最终决策） |

---

## 文档格式

探索文档的 frontmatter、正文结构、各节写法说明和示例已拆到同目录 `reference.md`。本技能只保留流程约束：

- **速答必须先于证据出现**——读者打开文档先要看到结论，再决定要不要往下看证据
- 结论必须可回溯到证据，不允许纯猜测
- 证据不足时 `confidence` 必须降为 `medium` 或 `low`
- 旧探索过期时旧文档标 `outdated`，新增当前版本

---

## 工作流阶段

### Phase 1：收敛探索问题

最多问用户两个问题：

1. "你最想先回答的一个问题是什么？"
2. "希望聚焦哪个模块 / 目录？"

用户描述已清楚就直接进入 Phase 2。

### Phase 2：证据化探索

- 用 Glob / Grep / Read **真实读代码**，不靠猜
- 边读边积累证据；**同步思考每条证据支撑哪个结论**——不支撑任何结论的证据不记录
- 形成初步结论后主动检查：已有证据能否说服一个持怀疑态度的人？够了就停，不必继续扩大搜索范围

为什么要"够了就停"？探索不是穷举，是建立到"读者能信"为止的证据链。继续扩大范围只会让文档变长而不变可信。

### Phase 3：起草与确认

- **先写速答节，再回填关键证据**——这个顺序很重要：先有结论再回头看证据是否真的支持，能逼你检查每条证据的实际效力
- AI 一次性起草完整 explore 文档，用户 review 后确认
- 有修改就按反馈修订后再落盘

### Phase 4：归档

- 写入探索归档目录，命名 `YYYY-MM-DD-{slug}.md`
- 归档后用搜索工具查有无语义重叠的历史探索
- 存在冲突或过期记录就提示用户将旧文档标为 `outdated`

### Phase 5：向后续工作流回传

按下面"与其他工作流的关系"里的路由表给出下一步建议。

---

## 搜索工具

> 完整语法和示例见 `easysdd-core/reference/tools.md`。本节只列 explore 特有的典型查询。

```bash
# 按类型筛选
python easysdd/tools/search-yaml.py --dir easysdd/explores --filter type=module-overview --filter status=active

# 归档后查重叠
python easysdd/tools/search-yaml.py --dir easysdd/explores --query "{关键词}" --json
```

---

## 与其他工作流的关系

- `easysdd-feature-design` 开始前：先搜 explores，复用调用链与模块边界证据
- `easysdd-issue-analyze` 开始前：先搜 explores，减少重复定位
- `easysdd-issue-fix` 开始前：搜 explores，确认修复点与历史证据一致
- `easysdd-explore` vs `easysdd-tricks`：explore 记"看到了什么"，tricks 记"推荐怎么做"
- `easysdd-explore` vs `easysdd-decisions`：explore 是输入，decisions 是拍板

---

## 退出条件

- [ ] 已明确探索问题与范围
- [ ] 速答节已给出核心结论（结论前置，不埋在证据之后）
- [ ] 关键证据 3-8 条，每条标注文件:行号，并说明支撑哪个结论
- [ ] 涉及多模块协作或 module-overview / spike 类型时，速答节有 Mermaid 图
- [ ] 文档已归档到探索归档目录
- [ ] 已给出后续建议（路由到哪个子工作流）

---

## 容易踩的坑

> 归档类工作流共享守护规则（只增不删、宁缺毋滥、不替用户写、可发现性、归档后查重叠）见根技能 `easysdd-core` 第五节约束 10。本技能特有的反模式：

- 不读代码直接给结论
- 证据只写"看起来像"，不写文件:行号
- 结论写在证据之后——速答节必须在关键证据节之前
- 证据节比速答节长数倍——先精简证据，选不支撑结论的条目删掉
- 跨模块流程没有 Mermaid 图，只靠文字描述多模块协作
- 把 explore 文档写成 decisions（提前拍板）
- 把 explore 文档写成 tricks（直接给处方，没有证据链）
- 历史 explore 已过期却继续引用，不做 `status` 标注
