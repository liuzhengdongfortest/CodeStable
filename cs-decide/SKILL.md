---
name: cs-decide
description: 把项目里已经拍板的技术选型、架构决定、长期约束、编码规约记成可检索的永久性文档。六个月后没人记得为什么当初选了 X，但有了决策文档，下次改动之前至少能先读懂背景。四种类型：tech-stack（用什么工具 / 库 / 框架）、architecture（系统怎么组织）、constraint（什么不允许做）、convention（什么统一这样做）。触发场景：feature-design 或 issue-analyze 后做出重要选择时主动推送，或用户说"记录决定"、"归档技术选型"、"ADR"、"记录这条约束"、"把规约写下来"。只归档已拍板的决定，讨论中的方案不归档。
---

# cs-decide

项目里"有意做出的选择"——技术选型、架构决定、长期约束、编码规约——特别容易丢失。它不会触发报错、没人会注意到它消失了，但消失的代价很具体：

- 新人（或六个月后的自己）不知道约束的来龙去脉，在"已经决定过的问题"上重复耗时讨论
- AI 在没有决策上下文的情况下给出"合理但与项目规约冲突"的方案
- 当约束需要修改时找不到当初的理由，无法评估修改的影响范围

本工作流的职责就是让每一条重要的"已经决定了"都有完整存档：**是什么、为什么、考虑过什么替代方案、后果是什么**。

> 共享路径与命名约定看 `codestable/reference/shared-conventions.md`。本技能的产物写入 `codestable/compound/`，文件命名 `YYYY-MM-DD-decision-{slug}.md`，frontmatter 带 `doc_type: decision`。

---

## 四种决策类型

每条决策文档归属下面四类之一，在 frontmatter 的 `category` 字段标注：

| 类型 | 适用情境 | 示例 |
|---|---|---|
| `tech-stack` | 技术 / 库 / 框架的选型 | "使用 Vite 而非 Webpack"、"状态管理用 Pinia" |
| `architecture` | 系统结构、模块划分、数据流方向 | "前后端完全分离"、"事件总线只在顶层使用" |
| `constraint` | 硬约束——某些事情**不允许**做 | "不引入 jQuery"、"所有 API 调用必须通过统一的 http 模块" |
| `convention` | 软规约——某些事情**统一这样做** | "组件命名用 PascalCase"、"副作用集中在 composables/" |

类型在实际查询时各有用途：

- 查"我们用什么工具"→ `tech-stack`
- 查"系统是怎么组织的"→ `architecture`
- 查"这里为什么不能改"→ `constraint`
- 查"统一的做法是什么"→ `convention`

---

## 文档格式

决策文档的 frontmatter、正文模板和示例已拆到同目录 `reference.md`。本技能只保留流程约束：

- `category` 只允许 `tech-stack` / `architecture` / `constraint` / `convention`
- `status` 只允许 `active` / `superseded` / `deprecated`
- `考虑过的替代方案` 与 `相关文档` 是可选节，用户说"没什么"就省略

---

## 工作流阶段

### Phase 1：识别决策（和用户对话）

用**一个问题**确认关键信息，不要给用户一张大表格：

1. "这个决定是关于什么的？（技术选型 / 架构结构 / 约束 / 规约）" → 确定 `category`
2. "这个决定是已经拍板了，还是还在讨论中？" → **本工作流只归档已拍板的决定**，讨论中的不归档（建议用户讨论完再来）。理由是讨论中的方案如果归档，下次有人查到会以为已经定了，反而误导
3. 如果用户描述不够清楚，问"当时为什么选这个而不选别的？"

### Phase 1.5：查重叠与意图分流（必做）

按 `codestable/reference/shared-conventions.md` §6 第 5 / 6 条执行：

- 用户话里含"改 / 更新 / 推翻 / 某条决策 / 某个选型"或明确指向某份旧决策 → 直接走**更新或 supersede** 路径。决策文档的特性是：**结论本身变更几乎总要 supersede**（旧结论要留痕，不能原地覆盖）；只是补背景 / 替代方案 / 影响描述时才走"更新已有条目"
- 否则用下面"搜索工具"按 `category` + 关键词查一遍，命中相近旧决策时把候选列给用户，让用户选：更新 / supersede / 确实不同主题

**判断 update vs supersede 的简单规则**：结论变了 → supersede；结论没变只补充 → update。拿不准就问用户。

### Phase 2：提炼要点（一次一个问题）

按下面顺序问，用户可以随时说"没什么"跳过：

1. "当时面对的背景或问题是什么？"
2. "决定的结论是什么？"（用户已经说清楚就跳过）
3. "为什么选这个？最重要的理由是什么？"
4. "有没有考虑过其他方案？为什么没选？"（鼓励写，哪怕只是直觉——后人最想知道的就是"为什么不选 X"）
5. "这个决定对后续工作有什么影响或约束？"

### Phase 3：确认内容（AI 起草，用户 review）

- AI 根据对话起草完整文档（含 YAML frontmatter + 所有正文节）
- 一次性展示给用户 review，**别逐节展示逐节问**——用户拿到完整版才能判断节之间的逻辑是否自洽
- 用户确认后写入文件；有修改就按用户意见调整再写

### Phase 4：归档

- 新建路径：文件写入 `codestable/compound/`，命名 `YYYY-MM-DD-decision-{slug}.md`，frontmatter 顶部带 `doc_type: decision`（见 `reference.md`）
- 更新路径：写回 Phase 1.5 定位到的原文件，frontmatter 补 `updated: YYYY-MM-DD`
- supersede 路径：按 `shared-conventions.md` §6 第 5 条处理；旧文档 `status=superseded` 并加 `superseded-by`（和本技能守护规则 #2 一致）
- 写完后报告完整文件路径

### Phase 5：相关工作流更新提示

写完后检查这两项，有则提示用户（**不自作主张改文件**——这两个文件都是高影响入口）：

1. `codestable/architecture/DESIGN.md` 的"关键架构决定"节是否应该引用这条决策——`architecture` 或 `tech-stack` 类型通常应该
2. `AGENTS.md` 的"禁止事项"或"代码规范"节是否应该追加这条约束——`constraint` 或 `convention` 类型通常应该

---

## 搜索工具

> 完整语法和示例见 `codestable/reference/tools.md`。本节只列 decisions 特有的典型查询。

```bash
# 列出所有当前有效的决策
python codestable/tools/search-yaml.py --dir codestable/compound --filter doc_type=decision --filter status=active

# 按类型 + 状态组合筛选
python codestable/tools/search-yaml.py --dir codestable/compound --filter doc_type=decision --filter category=constraint --filter status=active

# 归档后查重叠
python codestable/tools/search-yaml.py --dir codestable/compound --filter doc_type=decision --query "{关键词}" --json
```

---

## 和项目架构文档的关系

`architecture/DESIGN.md` 是架构总览（高层次、跨模块、长期稳定）；decision 文档是单条决策的完整存档（含理由和替代方案）。DESIGN.md 的"关键架构决定"节应链接到相关的 decision 文档（Phase 5 的可发现性检查会提示用户更新）。

---

## 守护规则

> 归档类工作流共享守护规则（只增不删、宁缺毋滥、不替用户写、可发现性、归档后查重叠）见 `codestable/reference/shared-conventions.md` 第 6 节。本技能特有或细化的规则：

1. **只归档已拍板的决定**——讨论中的方案不归档；"也许我们应该用 X"不归档
2. **status=superseded 不等于删除**——被取代的决策保留原文，加 `superseded-by` 字段，正文顶部加一行"**[已取代]** 见 {新文档 slug}"
3. **不替用户写理由**——用户说不出理由的写"未做系统评估"，不要 AI 编造看起来合理的理由（编造的理由会变成历史"事实"误导后人）
4. **不主动修改 AGENTS.md 和 DESIGN.md**——Phase 5 只提示，由用户决定是否追加。这两个文件的内容必须项目 owner 拍板
5. **跨技能一致性**——某条 decision 文档和 AGENTS.md 的禁止事项描述不同时，以 decision 文档为详细版，AGENTS.md 为摘要版，两者应链接，不应矛盾
6. **只认自己的 doc_type**——只读写 `doc_type: decision` 的文档，不感知 `compound/` 目录里其他 `doc_type` 的文档
