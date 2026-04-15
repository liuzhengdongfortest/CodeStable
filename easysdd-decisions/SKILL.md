---
name: easysdd-decisions
description: 决策归档子工作流——将已拍板的技术选型、架构决定、约束和规约记录为可检索文档。触发场景："记录决定"、"归档技术选型"、"ADR"、"记录这条约束"、"把规约写下来"，或 feature-design/issue-analyze 后做出重要选择时主动推送。
---

# easysdd-decisions

**决策归档子工作流** —— 把项目中已经拍板的技术选型、架构决定、长期约束和编码规约记录成可检索的永久性文档。

> "六个月后，没人记得为什么当初选了 X。有了决策文档，下次改动之前至少能先读懂背景。"

---

## 一、为什么需要决策归档

项目里有两类知识容易丢失：

1. **踩过的坑**（由 easysdd-compound 坑点轨道负责）
2. **有意做出的选择**（本工作流负责）

第二类更隐蔽——它不会触发报错，没人会注意到它消失了，但它的消失会产生严重后果：

- 新人（或六个月后的自己）不知道约束的来龙去脉，在"已经决定过的问题"上重复耗时讨论
- AI 在没有决策上下文的情况下给出"合理但与项目规约冲突"的方案
- 当约束需要修改时，找不到当初的理由，无法评估修改的影响范围

easysdd-decisions 的职责就是让每一条重要的"已经决定了"都有完整的存档：**是什么、为什么、考虑过什么替代方案、后果是什么**。

---

## 二、涉及的路径

> 共享路径与命名约定以根技能 `easysdd` 第二节为准。本节只补充本工作流特有信息：文件命名为 `YYYY-MM-DD-{slug}.md`。

---

## 三、四种决策类型

每条决策文档归属以下四类之一，在 YAML frontmatter 的 `category` 字段标注：

| 类型 | 适用情境 | 示例 |
|---|---|---|
| `tech-stack` | 技术/库/框架的选型 | "使用 Vite 而非 Webpack"、"状态管理用 Pinia" |
| `architecture` | 系统结构、模块划分、数据流方向 | "前后端完全分离"、"事件总线只在顶层使用" |
| `constraint` | 硬约束——某些事情**不允许**做 | "不引入 jQuery"、"所有 API 调用必须通过统一的 http 模块" |
| `convention` | 软规约——某些事情**统一这样做** | "组件命名用 PascalCase"、"副作用集中在 composables/" |

**类型的区别实践意义**：

- 查"我们用什么工具"→ `tech-stack`
- 查"系统是怎么组织的"→ `architecture`
- 查"这里为什么不能改"→ `constraint`
- 查"统一的做法是什么"→ `convention`

---

## 四、文档格式

决策文档的 frontmatter、正文模板和示例已拆到同目录 `reference.md`。本技能只保留流程约束：

- `category` 仍然只允许 `tech-stack` / `architecture` / `constraint` / `convention`
- `status` 仍然只允许 `active` / `superseded` / `deprecated`
- `考虑过的替代方案` 与 `相关文档` 仍然是可选节，用户说"没什么"就省略

---

## 五、工作流阶段

### Phase 1：识别决策（和用户对话）

用**一个问题**确认关键信息，不要给用户一张大表格：

1. "这个决定是关于什么的？（技术选型 / 架构结构 / 约束 / 规约）" → 确定 `category`
2. "这个决定是已经拍板了，还是还在讨论中？" → **本工作流只归档已拍板的决定**，讨论中的决定不归档（建议用户讨论完再来）
3. 如果用户描述不够清楚，问"当时为什么选这个而不选别的？"

### Phase 2：提炼要点（一次一个问题）

按以下顺序问，用户可以随时说"没什么"跳过某个问题：

1. "当时面对的背景或问题是什么？"
2. "决定的结论是什么？"（如果用户已经说清楚了就跳过）
3. "为什么选这个？最重要的理由是什么？"
4. "有没有考虑过其他方案？为什么没选？"（鼓励写，哪怕只是直觉）
5. "这个决定对后续工作有什么影响或约束？"

**规则**：用户对某个问题说"没什么"或"跳过"，就跳过。

### Phase 3：确认内容（AI 起草，用户 review）

- AI 根据对话起草完整文档（含 YAML frontmatter + 所有正文节）
- 一次性展示给用户 review，**不要逐节展示逐节问**
- 用户确认后写入文件；有修改则按用户意见调整再写

### Phase 4：归档

- 文件写入决策归档目录，命名 `YYYY-MM-DD-{slug}.md`
- 写完后报告完整文件路径
- 用搜索工具查是否有语义重叠的已有决策（见第六节），如有，在新文档末尾 `相关文档` 节列出来，并提示用户"这里有一条类似的决策，请确认两者是否需要合并或其中一条 supersede 另一条"

### Phase 5：相关工作流更新提示

写完后检查以下两项，有则提示用户（不自作主张改文件）：

1. `easysdd/architecture/DESIGN.md` 的"关键架构决定"节是否应该引用这条决策——如果是 `architecture` 或 `tech-stack` 类型，通常应该
2. `AGENTS.md` 的"禁止事项"或"代码规范"节是否应该追加这条约束——如果是 `constraint` 或 `convention` 类型，通常应该

---

## 六、搜索工具

> 完整语法和示例见 `easysdd/reference/tools.md`。本节只列 decisions 特有的典型查询。

```bash
# 列出所有当前有效的决策
python easysdd/tools/search-yaml.py --dir easysdd/decisions --filter status=active

# 按类型 + 状态组合筛选
python easysdd/tools/search-yaml.py --dir easysdd/decisions --filter category=constraint --filter status=active

# 归档后查重叠
python easysdd/tools/search-yaml.py --dir easysdd/decisions --query "{关键词}" --json
```

---

## 七、与其他 easysdd 工作流的关系

| 关系 | 说明 |
|---|---|
| `easysdd-feature-design` → 读 decisions | 方案设计开始前，搜索决策归档目录，确认方案不违反已有约束，并优先沿用已有技术选型 |
| `easysdd-feature-design` → 写 decisions | 设计阶段做出的重要技术选择（影响超出单个 feature），设计完成后推荐记录进决策归档 |
| `easysdd-issue-analyze` → 读 decisions | 根因分析时，有时"这里为什么这么做"的答案在决策归档里，先搜再分析 |
| `easysdd-feature-acceptance` 结束 → 可选推荐 | 验收完成后，按 `easysdd/reference/shared-conventions.md` 的收尾推荐判断：如果这次 feature 引入了新约定或技术，推荐记录一次 |
| `easysdd-compound` vs `easysdd-decisions` | compound 记录的是"发现了什么坑 / 最佳实践"（经验性）；decisions 记录的是"我们决定了什么"（规范性）。有时两者都要写，互不替代 |
| `architecture/DESIGN.md` vs `decisions/` | DESIGN.md 是架构总览（高层次，跨模块，长期稳定）；decisions 是单条决策的完整存档（含理由和替代方案）。DESIGN.md 的"关键架构决定"节应链接到相关的 decisions 文档 |

**关于 `easysdd-feature-design` 读 decisions**：这个工作流的对应子技能**不需要显式调用** easysdd-decisions，直接搜索决策归档目录读文件即可。easysdd-decisions 只负责写入，不负责被动读取。

---

## 八、产物示例

完整示例已拆到同目录 `reference.md`。本技能正文不再嵌入长示例。

---

## 九、守护规则

> 归档类工作流共享守护规则（只增不删、宁缺毋滥、不替用户写、可发现性、归档后查重叠）见根技能 `easysdd` 第五节约束 10。以下为本技能特有或细化规则：

1. **只归档已拍板的决定**。讨论中的方案不归档；"也许我们应该用 X"不归档
2. **status=superseded 不等于删除**。被取代的决策保留原文，加 `superseded-by` 字段，正文顶部加一行"**[已取代]** 见 {新文档 slug}"
3. **不替用户写理由**。用户说不出理由的，写"未做系统评估"，不要 AI 编造看起来合理的理由
4. **不主动修改 AGENTS.md 和 DESIGN.md**。Phase 5 只提示，由用户决定是否追加——这两个文件的内容必须项目 owner 拍板
5. **跨技能一致性**：如果某条 decisions 文档与 AGENTS.md 的禁止事项描述不同，以 decisions 文档为详细版，AGENTS.md 为摘要版，两者应链接，不应矛盾
