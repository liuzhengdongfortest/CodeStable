---
name: cs-explore
description: 对仓库做定向代码探索并把"提问→读代码→得结论"沉淀为可检索证据，三种类型 question / module-overview / spike。触发：用户说"先 explore 一下"、"这个仓库里 X 怎么实现"、"快速熟悉这个模块"、"把探索结果存档"。
---

# cs-explore

同一个问题第一次花两小时查代码，第二次应该五分钟内找到答案——前提是第一次做完留下了证据化的记录。cs-explore 就是把一次完整的"提问 → 读代码 → 得结论"过程沉淀成可检索的探索文档。

---

## 适用场景

- 新人入仓，需要快速理解模块边界、调用链、入口文件
- 用户提出一个具体问题，但暂时不要求直接产出方案 / 修复
- feature-design / issue-analyze / issue-fix 前先补一轮证据化探索
- 技术方向还在讨论，需要先做轻量 spike（只探索，不拍板）

本技能只负责"看到了什么"的证据化记录。如果用户的意图其实是别的（拍板、处方、修 bug），让用户按场景选对应子技能，不要在这里自作主张接过去。

> 共享路径与命名约定看 `codestable/reference/shared-conventions.md`。本技能的产物写入 `codestable/compound/`，文件命名 `YYYY-MM-DD-explore-{slug}.md`，frontmatter 带 `doc_type: explore`。

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

用户描述已清楚就直接进入 Phase 1.5。

### Phase 1.5：查重叠与意图分流（必做）

按 `codestable/reference/shared-conventions.md` §6 第 5 / 6 条执行：

- 用户话里含"更新 / 复查 / 某次 explore / 这个模块之前探过"或明确指向某份旧 explore → 直接走**更新或 supersede** 路径。explore 的特性是：**代码已经变了导致旧结论失效**时，旧文档标 `status=outdated` 并新建一份（supersede）；只是补证据 / 收紧结论但核心结论未变时走"更新已有条目"
- 否则用下面"搜索工具"按关键词 / 模块查一遍，命中相近旧 explore 时先读它，能直接回答就告诉用户"已有一份可用的 explore 在 {路径}，是要复用还是重新探一遍？"

**更新路径**：读旧文档 → 按 Phase 2 补充证据 → 改写速答节 → 写回原文件，补 `updated: YYYY-MM-DD`。

### Phase 2：证据化探索

- 用 Glob / Grep / Read **真实读代码**，不靠猜
- 边读边积累证据；**同步思考每条证据支撑哪个结论**——不支撑任何结论的证据不记录
- 关键证据目标 3–8 条，每条都要能标注到 `文件:行号`
- 涉及多模块协作，或者类型是 `module-overview` / `spike` 时，准备一张 Mermaid 图，放在 Phase 3 起草的速答节里
- 形成初步结论后主动检查：已有证据能否说服一个持怀疑态度的人？够了就停，不必继续扩大搜索范围

为什么要"够了就停"？探索不是穷举，是建立到"读者能信"为止的证据链。继续扩大范围只会让文档变长而不变可信。

### Phase 3：起草与确认

- **先写速答节，再回填关键证据**——这个顺序很重要：先有结论再回头看证据是否真的支持，能逼你检查每条证据的实际效力
- AI 一次性起草完整 explore 文档，用户 review 后确认
- 有修改就按反馈修订后再落盘

### Phase 4：归档

- 新建路径：写入 `codestable/compound/`，命名 `YYYY-MM-DD-explore-{slug}.md`，frontmatter 顶部带 `doc_type: explore`（见 `reference.md`）
- 更新路径：写回 Phase 1.5 定位到的原文件，frontmatter 补 `updated: YYYY-MM-DD`
- supersede 路径：按 `shared-conventions.md` §6 第 5 条处理；旧文档改 `status=outdated` 并加 `superseded-by`

### Phase 5：给出下一步建议

证据已经收齐后，一句话提示用户接下来可能的方向（比如"要不要基于这份 explore 去设计方案"）。用户说"不用"就跳过，不要把用户拖进新的工作流——下一步工作流由用户自己决定。

---

## 搜索工具

> 完整语法和示例见 `codestable/reference/tools.md`。本节只列 explore 特有的典型查询。

```bash
# 按类型筛选
python codestable/tools/search-yaml.py --dir codestable/compound --filter doc_type=explore --filter type=module-overview --filter status=active

# 归档后查重叠
python codestable/tools/search-yaml.py --dir codestable/compound --filter doc_type=explore --query "{关键词}" --json
```

---

## 退出条件

- [ ] 已明确探索问题与范围
- [ ] 速答节已给出核心结论（结论前置，不埋在证据之后）
- [ ] 关键证据 3-8 条，每条标注文件:行号，并说明支撑哪个结论
- [ ] 涉及多模块协作或 module-overview / spike 类型时，速答节有 Mermaid 图
- [ ] 文档已归档到 `codestable/compound/`，文件名为 `YYYY-MM-DD-explore-{slug}.md`
- [ ] 已给出后续建议（路由到哪个子工作流）

---

## 守护规则

> 归档类工作流共享守护规则（只增不删、宁缺毋滥、不替用户写、可发现性、归档后查重叠）见 `codestable/reference/shared-conventions.md` 第 6 节。本技能特有的反模式：

- 不读代码直接给结论
- 证据只写"看起来像"，不写文件:行号
- 结论写在证据之后——速答节必须在关键证据节之前
- 证据节比速答节长数倍——先精简证据，选不支撑结论的条目删掉
- 跨模块流程没有 Mermaid 图，只靠文字描述多模块协作
- 提前拍板——explore 只记"看到了什么"，不下"以后应该怎么做"的结论
- 直接给处方没有证据链——每条结论都必须回溯到具体的文件:行号
- 历史 explore 已过期却继续引用，不做 `status` 标注
- 读写 `compound/` 目录里 `doc_type` 不是 `explore` 的文档——本技能只负责 explore 文档
